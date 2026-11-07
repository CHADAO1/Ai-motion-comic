#!/usr/bin/env python3
"""Seal one prompt for cold review and enforce a maximum two-round review gate.

The ``seal`` command embeds the exact UTF-8 candidate text in a candidate-free
rules template, applies an optional project JSON contract, and invokes the
sibling ``validate_combat_prompt.py`` before atomically publishing the packet.
The ``start`` and ``finish`` commands maintain one atomic JSON review ledger.

Optional contract shape (all top-level checks are opt-in)::

    {
      "expected_cut_count": 2,
      "voice_profiles": {
        "角色甲": {
          "region": {"required_terms": ["地域语境中国"]},
          "accent": {"required_regex": ["普通话"]},
          "timbre": {"required_terms": ["中低音"]},
          "speech_habits": {"required_terms": ["语速偏慢"]},
          "physiology": {"required_terms": ["呼吸稳定"]}
        }
      },
      "dialogue_windows": [{"text": "原句", "seconds": 1.0}],
      "crowd_ratios": {"前景": 40, "后景": 60},
      "required_state_tokens": ["道具已交接"],
      "forbidden_state_tokens": ["道具仍未交接"]
    }
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Iterator


PACKET_FORMAT = "SEALED_COLD_REVIEW_V1"
STATE_FORMAT = "SEALED_COLD_REVIEW_STATE_V1"
VALIDATOR = Path(__file__).with_name("validate_combat_prompt.py")

CANDIDATE_HEADING = "## 候选提示词"
REVIEW_HEADING = "## 审阅输出格式"
REPORT_FIELDS = (
    "VERDICT",
    "BLOCKING_FINDINGS",
    "OPTIONAL_FINDINGS",
    "PROTECTED_FACTS",
)
VOICE_DIMENSIONS = (
    "region",
    "accent",
    "timbre",
    "speech_habits",
    "physiology",
)
CONTRACT_FIELDS = {
    "expected_cut_count",
    "voice_profiles",
    "dialogue_windows",
    "crowd_ratios",
    "required_state_tokens",
    "forbidden_state_tokens",
}

LINE_BREAK_RE = re.compile(r"\r\n|\n|\r")
CUT_LABEL_RE = re.compile(r"(?m)^\s*CUT\s+(\d+)\b", re.IGNORECASE)
REPORT_FIELD_RE = re.compile(
    r"(?m)^(VERDICT|BLOCKING_FINDINGS|OPTIONAL_FINDINGS|PROTECTED_FACTS):[ \t]*(.*)$"
)
REPORT_FIELD_LINE_RE = re.compile(
    r"(?im)^\s*(VERDICT|BLOCKING_FINDINGS|OPTIONAL_FINDINGS|PROTECTED_FACTS)\s*:"
)
CANDIDATE_HEADING_RE = re.compile(
    r"(?im)^\s*#{1,6}\s*[^\r\n]*(?:候选|candidate)[^\r\n]*$"
)
CANDIDATE_FIELD_RE = re.compile(
    r"(?im)^\s*(?:候选|candidate)(?:[ _-]*(?:[A-Z]|\d+|[一二三四五]))?\s*[:：]"
)
CANDIDATE_BOUNDARY_RE = re.compile(
    r"(?im)^\s*(?:BEGIN|END|START|STOP)[ _-]*(?:CANDIDATE|候选)\b"
)
STALE_SEGMENT_RE = re.compile(r"(?m)^\s*###\s*第\d+段")
SEGMENT_ENVELOPE_RE = re.compile(r"(?m)^\s*###\s*第\s*\d+\s*段[^\r\n]*")
CODE_FENCE_RE = re.compile(r"(?m)^\s*(?:```|~~~)")
RESERVED_PACKET_LINE_RE = re.compile(
    r"(?im)^\s*(?:PACKET_FORMAT|REVIEW_ROUND|EXACT_MATCH|MECHANICAL_PASS|"
    r"CANDIDATE_TEXT_SHA256|CANDIDATE_CHARS|CONTRACT_APPLIED)\s*="
)
PRIOR_REVIEW_LEAK_RE = re.compile(
    r"(?:首轮|上轮|上一轮|旧审阅|旧报告|previous[ \t]+review|round[ \t]+1)"
    r"[^\r\n]{0,24}(?:结论|发现|问题|指出|建议|报告|verdict|finding|repair|pass)"
    r"|(?:疑似问题|期待修复|预期修复|根据首轮审阅|按照首轮审阅)",
    re.IGNORECASE,
)
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

TOOL_WRAPPER_PATTERNS = (
    (re.compile(r"\bExit[ \t]+code\b", re.IGNORECASE), "Exit code"),
    (re.compile(r"\bProcess[ \t]+exited\b", re.IGNORECASE), "Process exited"),
    (re.compile(r"\bOutput[ \t]*[:：]", re.IGNORECASE), "Output:"),
    (re.compile(r"\btool[ \t]+output\b", re.IGNORECASE), "tool output"),
    (re.compile(r"\btool[_ \t]+call\b", re.IGNORECASE), "tool call"),
    (re.compile(r"(?im)^\s*Command[ \t]*[:：]"), "Command:"),
)

STATE_KEYS = {"format", "status", "rounds", "terminal_reason"}
ROUND_KEYS = {
    "round",
    "snapshot_path",
    "snapshot_sha256",
    "snapshot_size",
    "reviewer",
    "status",
    "verdict",
    "structural_change",
    "report_sha256",
    "report_text",
}


class GateError(RuntimeError):
    """Expected input, validation, or state-gate failure."""


def positive_decimal_arg(value: str) -> str:
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise argparse.ArgumentTypeError(f"invalid decimal value: {value}") from exc
    if not parsed.is_finite() or parsed <= 0:
        raise argparse.ArgumentTypeError("value must be finite and greater than 0")
    return value


def positive_int_arg(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"invalid integer value: {value}") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("value must be greater than 0")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    seal = subparsers.add_parser(
        "seal",
        help="build and mechanically preflight one exact cold-review packet",
    )
    seal.add_argument("--candidate", type=Path, required=True)
    seal.add_argument("--template", type=Path, required=True)
    seal.add_argument("--output", type=Path, required=True)
    seal.add_argument(
        "--state",
        type=Path,
        required=True,
        help="review ledger path; absent means round 1, eligible ledger means round 2",
    )
    seal.add_argument("--contract", type=Path)
    seal.add_argument("--duration", type=positive_decimal_arg, required=True)
    seal.add_argument("--version", choices=("单镜", "多镜"), default="多镜")
    seal.add_argument("--mode", choices=("auto", "cut", "onetake"), default="auto")
    seal.add_argument(
        "--timestamp-policy",
        choices=("integer-preferred", "decimal-allowed", "integer-required"),
        default="integer-preferred",
    )
    seal.add_argument("--fps", type=positive_decimal_arg, default="24")
    seal.add_argument(
        "--reference-handle-policy",
        choices=("any-section", "lock-only"),
        default="any-section",
    )
    seal.add_argument("--max-chars", type=positive_int_arg, default=5000)

    start = subparsers.add_parser(
        "start",
        help="freeze one sealed snapshot for exactly one reviewer",
    )
    start.add_argument("--state", type=Path, required=True)
    start.add_argument("--snapshot", type=Path, required=True)
    start.add_argument("--reviewer", required=True)

    finish = subparsers.add_parser(
        "finish",
        help=(
            "record one strict four-field report and advance or terminate the gate; "
            "after first-round REPAIR, call only once the main agent has completed "
            "and classified the actual minimal repair"
        ),
    )
    finish.add_argument("--state", type=Path, required=True)
    finish.add_argument("--snapshot", type=Path, required=True)
    finish.add_argument("--reviewer", required=True)
    finish.add_argument("--report", type=Path, required=True)
    finish.add_argument(
        "--structural-change",
        choices=("true", "false"),
        help=(
            "required only for first-round REPAIR; describes the repair actually "
            "completed, not reviewer severity or a planned change"
        ),
    )
    return parser


def normalize_newlines(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def text_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def bytes_sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def read_utf8(path: Path, label: str) -> tuple[bytes, str]:
    try:
        payload = path.read_bytes()
    except OSError as exc:
        raise GateError(f"cannot read {label} '{path}': {exc}") from exc
    try:
        text = payload.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise GateError(f"{label} is not valid UTF-8: {path}: {exc}") from exc
    if text.startswith("\ufeff"):
        raise GateError(f"{label} contains more than one leading UTF-8 BOM: {path}")
    if "\x00" in text:
        raise GateError(f"{label} contains a NUL character: {path}")
    return payload, text


def resolved_path(path: Path, *, must_exist: bool) -> Path:
    try:
        return path.resolve(strict=must_exist)
    except OSError as exc:
        raise GateError(f"cannot resolve path '{path}': {exc}") from exc


def paths_equal(left: Path, right: Path) -> bool:
    return os.path.normcase(str(left)) == os.path.normcase(str(right))


def ensure_distinct_paths(named_paths: dict[str, Path]) -> None:
    items = list(named_paths.items())
    for index, (left_name, left_path) in enumerate(items):
        for right_name, right_path in items[index + 1 :]:
            if paths_equal(left_path, right_path):
                raise GateError(
                    f"{left_name} and {right_name} must be different paths: {left_path}"
                )


def choose_newline(*texts: str) -> str:
    for text in texts:
        match = LINE_BREAK_RE.search(text)
        if match:
            return match.group(0)
    return "\n"


def check_template_hygiene(template: str) -> None:
    errors: list[str] = []
    if not template.strip():
        errors.append("template is empty")
    if CODE_FENCE_RE.search(template):
        errors.append("template contains a code fence")
    if CANDIDATE_HEADING_RE.search(template):
        errors.append("template already contains a candidate heading or multi-candidate area")
    if CANDIDATE_FIELD_RE.search(template) or CANDIDATE_BOUNDARY_RE.search(template):
        errors.append("template already contains a candidate field or boundary marker")
    if STALE_SEGMENT_RE.search(template):
        errors.append("template contains a stale candidate-like segment heading")
    if REPORT_FIELD_LINE_RE.search(template):
        errors.append("template contains an old or filled review report")
    if REVIEW_HEADING in template:
        errors.append("template contains the reserved review-output section")
    if RESERVED_PACKET_LINE_RE.search(template):
        errors.append("template contains sealed-packet metadata")
    if PRIOR_REVIEW_LEAK_RE.search(template):
        errors.append("template contains prior-review conclusions or expected-fix language")
    for pattern, label in TOOL_WRAPPER_PATTERNS:
        if pattern.search(template):
            errors.append(f"template contains forbidden tool wrapper token: {label}")
    if errors:
        raise GateError("template contamination: " + "; ".join(errors))


def check_candidate_hygiene(candidate: str) -> None:
    if not candidate:
        raise GateError("candidate is empty")
    segment_count = len(SEGMENT_ENVELOPE_RE.findall(candidate))
    if segment_count != 1:
        raise GateError(
            "candidate must contain exactly one independent segment envelope; "
            f"found {segment_count}. Review multi-segment projects one segment at a time"
        )
    if CODE_FENCE_RE.search(candidate):
        raise GateError("candidate contains a code fence; packet embedding is plain text only")
    if PRIOR_REVIEW_LEAK_RE.search(candidate):
        raise GateError("candidate contains prior-review conclusions or expected-fix language")


def reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise GateError(f"JSON contains duplicate key: {key}")
        result[key] = value
    return result


def reject_json_constant(value: str) -> None:
    raise GateError(f"JSON contains non-finite number: {value}")


def load_json_text(text: str, label: str) -> Any:
    try:
        return json.loads(
            text,
            object_pairs_hook=reject_duplicate_pairs,
            parse_constant=reject_json_constant,
        )
    except json.JSONDecodeError as exc:
        raise GateError(
            f"{label} is invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}"
        ) from exc


def require_string_list(value: Any, label: str) -> list[str]:
    if not isinstance(value, list):
        raise GateError(f"{label} must be a JSON array of non-empty strings")
    result: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item:
            raise GateError(f"{label}[{index}] must be a non-empty string")
        result.append(item)
    return result


def json_decimal(value: Any, label: str, *, positive: bool) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise GateError(f"{label} must be a JSON number")
    try:
        parsed = Decimal(str(value))
    except InvalidOperation as exc:
        raise GateError(f"{label} is not a valid decimal number") from exc
    if not parsed.is_finite():
        raise GateError(f"{label} must be finite")
    if positive and parsed <= 0:
        raise GateError(f"{label} must be greater than 0")
    if not positive and parsed < 0:
        raise GateError(f"{label} must be nonnegative")
    return parsed


def spoken_character_count(text: str) -> int:
    return sum(1 for character in text if character.isalnum())


def validate_voice_profiles(value: Any, candidate: str, errors: list[str]) -> None:
    if not isinstance(value, dict) or not value:
        raise GateError("voice_profiles must be a non-empty JSON object")
    candidate_lines = candidate.splitlines()
    for role, dimensions in value.items():
        if not isinstance(role, str) or not role:
            raise GateError("voice_profiles role names must be non-empty strings")
        if not isinstance(dimensions, dict):
            raise GateError(f"voice_profiles.{role} must be a JSON object")
        dimension_keys = set(dimensions)
        required_keys = set(VOICE_DIMENSIONS)
        if dimension_keys != required_keys:
            missing = sorted(required_keys - dimension_keys)
            extra = sorted(dimension_keys - required_keys)
            details: list[str] = []
            if missing:
                details.append("missing " + ", ".join(missing))
            if extra:
                details.append("unknown " + ", ".join(extra))
            raise GateError(
                f"voice_profiles.{role} must define exactly five dimensions: "
                + "; ".join(details)
            )

        compiled: dict[str, tuple[list[str], list[re.Pattern[str]]]] = {}
        for dimension in VOICE_DIMENSIONS:
            specification = dimensions[dimension]
            if not isinstance(specification, dict):
                raise GateError(
                    f"voice_profiles.{role}.{dimension} must be a JSON object"
                )
            unknown = set(specification) - {"required_terms", "required_regex"}
            if unknown:
                raise GateError(
                    f"voice_profiles.{role}.{dimension} has unknown key(s): "
                    + ", ".join(sorted(unknown))
                )
            terms = require_string_list(
                specification.get("required_terms", []),
                f"voice_profiles.{role}.{dimension}.required_terms",
            )
            regex_strings = require_string_list(
                specification.get("required_regex", []),
                f"voice_profiles.{role}.{dimension}.required_regex",
            )
            if not terms and not regex_strings:
                raise GateError(
                    f"voice_profiles.{role}.{dimension} requires at least one term or regex"
                )
            regexes: list[re.Pattern[str]] = []
            for pattern in regex_strings:
                try:
                    regexes.append(re.compile(pattern))
                except re.error as exc:
                    raise GateError(
                        f"voice_profiles.{role}.{dimension} has invalid regex "
                        f"'{pattern}': {exc}"
                    ) from exc
            compiled[dimension] = (terms, regexes)

        role_lines = [line for line in candidate_lines if role in line]
        if not role_lines:
            errors.append(f"voice_profiles role is absent from candidate: {role}")
            continue

        def line_satisfies(line: str) -> bool:
            for terms, regexes in compiled.values():
                if any(term not in line for term in terms):
                    return False
                if any(regex.search(line) is None for regex in regexes):
                    return False
            return True

        if not any(line_satisfies(line) for line in role_lines):
            missing_dimensions: list[str] = []
            for dimension, (terms, regexes) in compiled.items():
                if not any(
                    all(term in line for term in terms)
                    and all(regex.search(line) is not None for regex in regexes)
                    for line in role_lines
                ):
                    missing_dimensions.append(dimension)
            if missing_dimensions:
                errors.append(
                    f"voice_profiles.{role} missing required five-dimensional evidence: "
                    + ", ".join(missing_dimensions)
                )
            else:
                errors.append(
                    f"voice_profiles.{role} evidence must coexist on one named-role line"
                )


def validate_contract(contract: Any, candidate: str) -> None:
    if not isinstance(contract, dict):
        raise GateError("contract root must be a JSON object")
    unknown = set(contract) - CONTRACT_FIELDS
    if unknown:
        raise GateError("contract has unknown key(s): " + ", ".join(sorted(unknown)))
    if not contract:
        raise GateError("contract must contain at least one opt-in check")

    errors: list[str] = []
    if "expected_cut_count" in contract:
        expected = contract["expected_cut_count"]
        if isinstance(expected, bool) or not isinstance(expected, int) or expected <= 0:
            raise GateError("expected_cut_count must be a positive integer")
        actual = len(CUT_LABEL_RE.findall(candidate))
        if actual != expected:
            errors.append(f"expected_cut_count={expected}, candidate has {actual}")

    if "voice_profiles" in contract:
        validate_voice_profiles(contract["voice_profiles"], candidate, errors)

    if "dialogue_windows" in contract:
        windows = contract["dialogue_windows"]
        if not isinstance(windows, list):
            raise GateError("dialogue_windows must be a JSON array")
        for index, window in enumerate(windows):
            label = f"dialogue_windows[{index}]"
            if not isinstance(window, dict):
                raise GateError(f"{label} must be a JSON object")
            if set(window) != {"text", "seconds"}:
                raise GateError(f"{label} must contain exactly text and seconds")
            dialogue = window["text"]
            if not isinstance(dialogue, str) or not dialogue:
                raise GateError(f"{label}.text must be a non-empty string")
            seconds = json_decimal(window["seconds"], f"{label}.seconds", positive=True)
            if dialogue not in candidate:
                errors.append(f"{label}.text is absent from candidate: {dialogue}")
            characters = spoken_character_count(dialogue)
            capacity = seconds * Decimal("5.5")
            if Decimal(characters) > capacity:
                errors.append(
                    f"{label} needs {characters} spoken characters but {seconds} seconds "
                    f"allow about {format(capacity, 'f')} at 5.5 characters/second"
                )

    if "crowd_ratios" in contract:
        ratios = contract["crowd_ratios"]
        if not isinstance(ratios, dict) or not ratios:
            raise GateError("crowd_ratios must be a non-empty JSON object")
        total = Decimal("0")
        for label, value in ratios.items():
            if not isinstance(label, str) or not label:
                raise GateError("crowd_ratios labels must be non-empty strings")
            total += json_decimal(value, f"crowd_ratios.{label}", positive=False)
        if total != Decimal("100"):
            errors.append(f"crowd_ratios total is {format(total, 'f')}, expected 100")

    if "required_state_tokens" in contract:
        tokens = require_string_list(
            contract["required_state_tokens"], "required_state_tokens"
        )
        for token in tokens:
            if token not in candidate:
                errors.append(f"required_state_tokens missing from candidate: {token}")

    if "forbidden_state_tokens" in contract:
        tokens = require_string_list(
            contract["forbidden_state_tokens"], "forbidden_state_tokens"
        )
        for token in tokens:
            if token in candidate:
                errors.append(f"forbidden_state_tokens present in candidate: {token}")

    if errors:
        raise GateError("project contract failed: " + "; ".join(errors))


def review_schema(newline: str) -> str:
    return newline.join(
        (
            REVIEW_HEADING,
            "将审阅报告另存为 UTF-8 纯文本；以下四个字段按顺序各出现一次，不得改写密封包：",
            "VERDICT:",
            "BLOCKING_FINDINGS:",
            "OPTIONAL_FINDINGS:",
            "PROTECTED_FACTS:",
        )
    )


def build_packet(
    template: str,
    candidate: str,
    *,
    round_number: int,
    contract_applied: bool,
    contract_hash: str | None,
    args: argparse.Namespace,
) -> str:
    newline = choose_newline(template, candidate)
    metadata = [
        "# SEALED COLD REVIEW PACKET",
        f"PACKET_FORMAT={PACKET_FORMAT}",
        f"REVIEW_ROUND={round_number}",
        "EXACT_MATCH=True",
        "MECHANICAL_PASS=True",
        f"CANDIDATE_TEXT_SHA256={text_sha256(candidate)}",
        f"CANDIDATE_CHARS={len(candidate)}",
        f"CONTRACT_APPLIED={'True' if contract_applied else 'False'}",
        f"VALIDATOR_VERSION={args.version}",
        f"VALIDATOR_DURATION={args.duration}",
        f"VALIDATOR_MODE={args.mode}",
        f"TIMESTAMP_POLICY={args.timestamp_policy}",
        f"REFERENCE_HANDLE_POLICY={args.reference_handle_policy}",
    ]
    if contract_hash is not None:
        metadata.append(f"CONTRACT_SHA256={contract_hash}")
    return (
        newline.join(metadata)
        + newline * 2
        + template.rstrip("\r\n")
        + newline * 2
        + CANDIDATE_HEADING
        + newline
        + candidate
        + newline * 2
        + review_schema(newline)
    )


def metadata_value(packet: str, key: str) -> str:
    matches = re.findall(
        rf"(?m)^{re.escape(key)}=([^\r\n]*)(?=\r?$)", packet
    )
    if len(matches) != 1:
        raise GateError(f"sealed packet must contain exactly one {key}= metadata line")
    return matches[0]


def validate_sealed_packet(packet: str, expected_round: int) -> str:
    if CODE_FENCE_RE.search(packet):
        raise GateError("sealed snapshot contains a code fence")
    if metadata_value(packet, "PACKET_FORMAT") != PACKET_FORMAT:
        raise GateError("sealed snapshot has an unsupported PACKET_FORMAT")
    if metadata_value(packet, "REVIEW_ROUND") != str(expected_round):
        raise GateError(
            f"sealed snapshot REVIEW_ROUND must be {expected_round} for this state"
        )
    if metadata_value(packet, "EXACT_MATCH") != "True":
        raise GateError("sealed snapshot does not record EXACT_MATCH=True")
    if metadata_value(packet, "MECHANICAL_PASS") != "True":
        raise GateError("sealed snapshot does not record MECHANICAL_PASS=True")
    if metadata_value(packet, "CONTRACT_APPLIED") not in {"True", "False"}:
        raise GateError("sealed snapshot has invalid CONTRACT_APPLIED metadata")

    hash_value = metadata_value(packet, "CANDIDATE_TEXT_SHA256")
    if SHA256_RE.fullmatch(hash_value) is None:
        raise GateError("sealed snapshot has invalid CANDIDATE_TEXT_SHA256 metadata")
    chars_value = metadata_value(packet, "CANDIDATE_CHARS")
    try:
        candidate_chars = int(chars_value)
    except ValueError as exc:
        raise GateError("sealed snapshot has invalid CANDIDATE_CHARS metadata") from exc
    if candidate_chars <= 0:
        raise GateError("sealed snapshot CANDIDATE_CHARS must be positive")

    candidate_matches = list(
        re.finditer(r"(?m)^## 候选提示词(?=\r?$)", packet)
    )
    review_matches = list(re.finditer(r"(?m)^## 审阅输出格式(?=\r?$)", packet))
    if len(candidate_matches) != 1:
        raise GateError("sealed snapshot must contain exactly one candidate section")
    if len(review_matches) != 1:
        raise GateError("sealed snapshot must contain exactly one review-output section")
    candidate_heading = candidate_matches[0]
    heading_break = LINE_BREAK_RE.match(packet, candidate_heading.end())
    if heading_break is None:
        raise GateError("sealed snapshot candidate heading must end with a line break")
    candidate_start = heading_break.end()
    candidate_end = candidate_start + candidate_chars
    if candidate_end > len(packet):
        raise GateError("sealed snapshot candidate length exceeds packet boundary")
    candidate = packet[candidate_start:candidate_end]
    check_candidate_hygiene(candidate)
    if text_sha256(candidate) != hash_value:
        raise GateError("sealed snapshot candidate hash does not match packet metadata")

    review_heading = review_matches[0]
    separator = packet[candidate_end:review_heading.start()]
    if re.fullmatch(r"(?:(?:\r\n)|\n|\r){2}", separator) is None:
        raise GateError("sealed snapshot candidate boundary is not exact")
    review_break = LINE_BREAK_RE.match(packet, review_heading.end())
    if review_break is None:
        raise GateError("sealed snapshot review heading must end with a line break")
    expected_tail = normalize_newlines(review_schema("\n").split("\n", 1)[1])
    actual_tail = normalize_newlines(packet[review_break.end():])
    if actual_tail != expected_tail:
        raise GateError("sealed snapshot review-output schema was changed or filled")
    if [match.group(1) for match in REPORT_FIELD_RE.finditer(packet)] != list(REPORT_FIELDS):
        raise GateError("sealed snapshot review fields are missing, duplicated, or reordered")
    return candidate


def validator_command(
    args: argparse.Namespace,
    project_rules: Path,
    candidate: Path,
) -> list[str]:
    return [
        sys.executable,
        str(VALIDATOR),
        "--version",
        args.version,
        "--duration",
        args.duration,
        "--mode",
        args.mode,
        "--timestamp-policy",
        args.timestamp_policy,
        "--fps",
        args.fps,
        "--reference-handle-policy",
        args.reference_handle_policy,
        "--max-chars",
        str(args.max_chars),
        "--project-rules",
        str(project_rules),
        "--candidate",
        str(candidate),
    ]


def run_validator(
    args: argparse.Namespace,
    project_rules: Path,
    candidate: Path,
) -> str:
    if not VALIDATOR.is_file():
        raise GateError(f"mechanical validator is missing: {VALIDATOR}")
    environment = os.environ.copy()
    environment["PYTHONUTF8"] = "1"
    try:
        result = subprocess.run(
            validator_command(args, project_rules, candidate),
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=environment,
            check=False,
        )
    except OSError as exc:
        raise GateError(f"could not launch mechanical validator: {exc}") from exc
    if result.returncode != 0 or result.stdout.strip() != "PASS":
        details = "\n".join(
            part.strip() for part in (result.stderr, result.stdout) if part.strip()
        )
        raise GateError(
            "mechanical preflight failed; no packet was published"
            + (f"\n{details}" if details else "")
        )
    return result.stderr.strip()


@contextlib.contextmanager
def state_lock(state_path: Path) -> Iterator[None]:
    parent = state_path.parent
    if not parent.is_dir():
        raise GateError(f"state parent directory does not exist: {parent}")
    lock_path = state_path.with_name(state_path.name + ".lock")
    try:
        descriptor = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        raise GateError(f"review state is locked by another operation: {lock_path}") from exc
    except OSError as exc:
        raise GateError(f"cannot create review-state lock '{lock_path}': {exc}") from exc
    try:
        with os.fdopen(descriptor, "w", encoding="ascii", newline="\n") as handle:
            handle.write(f"pid={os.getpid()}\n")
            handle.flush()
            os.fsync(handle.fileno())
        yield
    finally:
        try:
            lock_path.unlink()
        except FileNotFoundError:
            pass
        except OSError as exc:
            print(f"WARNING: could not remove state lock '{lock_path}': {exc}", file=sys.stderr)


def validate_state(state: Any) -> dict[str, Any]:
    if not isinstance(state, dict) or set(state) != STATE_KEYS:
        raise GateError("review state has an invalid top-level schema")
    if state.get("format") != STATE_FORMAT:
        raise GateError("review state has an unsupported format")
    if state.get("status") not in {"active", "awaiting_second_round", "terminated"}:
        raise GateError("review state has an invalid status")
    rounds = state.get("rounds")
    if not isinstance(rounds, list) or not 1 <= len(rounds) <= 2:
        raise GateError("review state must contain one or two rounds")
    for index, round_entry in enumerate(rounds, start=1):
        if not isinstance(round_entry, dict) or set(round_entry) != ROUND_KEYS:
            raise GateError(f"review state round {index} has an invalid schema")
        if round_entry["round"] != index:
            raise GateError(f"review state round numbering is invalid at round {index}")
        if round_entry["status"] not in {"active", "completed"}:
            raise GateError(f"review state round {index} has an invalid status")
        if not isinstance(round_entry["reviewer"], str) or not round_entry["reviewer"]:
            raise GateError(f"review state round {index} has an invalid reviewer")
        if not isinstance(round_entry["snapshot_path"], str) or not round_entry["snapshot_path"]:
            raise GateError(f"review state round {index} has an invalid snapshot path")
        if SHA256_RE.fullmatch(str(round_entry["snapshot_sha256"])) is None:
            raise GateError(f"review state round {index} has an invalid snapshot hash")
        if (
            isinstance(round_entry["snapshot_size"], bool)
            or not isinstance(round_entry["snapshot_size"], int)
            or round_entry["snapshot_size"] <= 0
        ):
            raise GateError(f"review state round {index} has an invalid snapshot size")
        if round_entry["status"] == "active":
            if any(
                round_entry[key] is not None
                for key in (
                    "verdict",
                    "structural_change",
                    "report_sha256",
                    "report_text",
                )
            ):
                raise GateError(f"active review state round {index} contains a result")
        else:
            if round_entry["verdict"] not in {"PASS", "REPAIR"}:
                raise GateError(f"completed review state round {index} has no verdict")
            if SHA256_RE.fullmatch(str(round_entry["report_sha256"])) is None:
                raise GateError(f"completed review state round {index} has no report hash")
            if not isinstance(round_entry["report_text"], str) or not round_entry["report_text"]:
                raise GateError(f"completed review state round {index} has no report text")

    if len(rounds) == 2:
        if rounds[0]["reviewer"] == rounds[1]["reviewer"]:
            raise GateError("review state reuses the same reviewer across rounds")
        if rounds[0]["snapshot_sha256"] == rounds[1]["snapshot_sha256"]:
            raise GateError("review state reuses the same snapshot across rounds")

    status = state["status"]
    if status == "active":
        if rounds[-1]["status"] != "active":
            raise GateError("active review state has no active round")
    elif status == "awaiting_second_round":
        first = rounds[0]
        if (
            len(rounds) != 1
            or first["status"] != "completed"
            or first["verdict"] != "REPAIR"
            or first["structural_change"] is not True
        ):
            raise GateError("review state is not eligible for a second round")
    elif rounds[-1]["status"] != "completed":
        raise GateError("terminated review state has an incomplete round")
    return state


def load_state(state_path: Path) -> dict[str, Any]:
    _, state_text = read_utf8(state_path, "review state")
    return validate_state(load_json_text(state_text, "review state"))


def atomic_write_state(state_path: Path, state: dict[str, Any]) -> None:
    validate_state(state)
    parent = state_path.parent
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{state_path.name}.", suffix=".tmp", dir=parent
    )
    temporary_path = Path(temporary_name)
    try:
        payload = (
            json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        ).encode("utf-8")
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, state_path)
    except BaseException:
        try:
            os.close(descriptor)
        except OSError:
            pass
        try:
            temporary_path.unlink()
        except FileNotFoundError:
            pass
        raise


def validate_reviewer(reviewer: str) -> str:
    if not reviewer or reviewer != reviewer.strip() or "\n" in reviewer or "\r" in reviewer:
        raise GateError("reviewer must be one non-empty identifier without outer whitespace")
    return reviewer


def parse_review_report(report: str) -> tuple[str, str]:
    normalized = normalize_newlines(report).strip()
    if not normalized:
        raise GateError("review report is empty")
    if CODE_FENCE_RE.search(normalized):
        raise GateError("review report must not use a code fence")
    matches = list(REPORT_FIELD_RE.finditer(normalized))
    if [match.group(1) for match in matches] != list(REPORT_FIELDS):
        raise GateError(
            "review report must contain VERDICT, BLOCKING_FINDINGS, "
            "OPTIONAL_FINDINGS, and PROTECTED_FACTS exactly once in that order"
        )
    if normalized[: matches[0].start()].strip():
        raise GateError("review report contains text before VERDICT")

    payloads: dict[str, str] = {}
    for index, match in enumerate(matches):
        next_start = matches[index + 1].start() if index + 1 < len(matches) else len(normalized)
        payload = (match.group(2) + normalized[match.end():next_start]).strip()
        if not payload:
            raise GateError(f"review report field {match.group(1)} must not be empty")
        payloads[match.group(1)] = payload
    verdict = payloads["VERDICT"]
    if verdict not in {"PASS", "REPAIR"}:
        raise GateError("review report VERDICT must be exactly PASS or REPAIR")
    return verdict, normalized


def report_leaks(packet: str, previous_report: str) -> bool:
    normalized_report = normalize_newlines(previous_report).strip()
    normalized_packet = normalize_newlines(packet)
    return bool(normalized_report and normalized_report in normalized_packet)


def state_round_for_seal(state_path: Path) -> tuple[int, str | None]:
    if not state_path.exists():
        return 1, None
    state = load_state(state_path)
    if state["status"] == "active":
        raise GateError("cannot seal another packet while a review round is active")
    if state["status"] == "terminated":
        raise GateError("review state is terminated; no further packet may be sealed")
    first = state["rounds"][0]
    return 2, first["report_text"]


def write_temporary_packet(output: Path, packet: str) -> Path:
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{output.name}.", suffix=".tmp", dir=output.parent
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(packet.encode("utf-8"))
            handle.flush()
            os.fsync(handle.fileno())
    except BaseException:
        try:
            os.close(descriptor)
        except OSError:
            pass
        try:
            temporary_path.unlink()
        except FileNotFoundError:
            pass
        raise
    return temporary_path


def command_seal(args: argparse.Namespace) -> int:
    candidate_path = resolved_path(args.candidate, must_exist=True)
    template_path = resolved_path(args.template, must_exist=True)
    state_path = resolved_path(args.state, must_exist=False)
    output_path = resolved_path(args.output, must_exist=False)
    contract_path = (
        resolved_path(args.contract, must_exist=True) if args.contract is not None else None
    )
    if not output_path.parent.is_dir():
        raise GateError(f"output parent directory does not exist: {output_path.parent}")
    if output_path.exists():
        raise GateError(f"output already exists; refusing to overwrite: {output_path}")
    named_paths = {
        "candidate": candidate_path,
        "template": template_path,
        "output": output_path,
        "state": state_path,
    }
    if contract_path is not None:
        named_paths["contract"] = contract_path
    ensure_distinct_paths(named_paths)

    candidate_bytes, candidate = read_utf8(candidate_path, "candidate")
    _, template = read_utf8(template_path, "template")
    del candidate_bytes
    check_candidate_hygiene(candidate)
    check_template_hygiene(template)

    contract_hash: str | None = None
    if contract_path is not None:
        contract_bytes, contract_text = read_utf8(contract_path, "contract")
        contract = load_json_text(contract_text, "contract")
        validate_contract(contract, candidate)
        contract_hash = bytes_sha256(contract_bytes)

    with state_lock(state_path):
        round_number, previous_report = state_round_for_seal(state_path)
        if previous_report is not None and (
            report_leaks(template, previous_report) or report_leaks(candidate, previous_report)
        ):
            raise GateError("second-round inputs leak the first-round review report")
        packet = build_packet(
            template,
            candidate,
            round_number=round_number,
            contract_applied=contract_path is not None,
            contract_hash=contract_hash,
            args=args,
        )
        validate_sealed_packet(packet, round_number)
        temporary_path = write_temporary_packet(output_path, packet)
        try:
            validator_warning = run_validator(args, temporary_path, candidate_path)
            os.replace(temporary_path, output_path)
        finally:
            try:
                temporary_path.unlink()
            except FileNotFoundError:
                pass
        if validator_warning:
            print(validator_warning, file=sys.stderr)

    print(f"PASS: sealed review packet published: {output_path}")
    print("EXACT_MATCH=True")
    print("MECHANICAL_PASS=True")
    return 0


def new_round_entry(
    round_number: int,
    snapshot_path: Path,
    snapshot_bytes: bytes,
    reviewer: str,
) -> dict[str, Any]:
    return {
        "round": round_number,
        "snapshot_path": str(snapshot_path),
        "snapshot_sha256": bytes_sha256(snapshot_bytes),
        "snapshot_size": len(snapshot_bytes),
        "reviewer": reviewer,
        "status": "active",
        "verdict": None,
        "structural_change": None,
        "report_sha256": None,
        "report_text": None,
    }


def command_start(args: argparse.Namespace) -> int:
    reviewer = validate_reviewer(args.reviewer)
    state_path = resolved_path(args.state, must_exist=False)
    snapshot_path = resolved_path(args.snapshot, must_exist=True)
    if paths_equal(state_path, snapshot_path):
        raise GateError("state and snapshot must be different paths")
    snapshot_bytes, snapshot = read_utf8(snapshot_path, "snapshot")

    with state_lock(state_path):
        if not state_path.exists():
            expected_round = 1
            validate_sealed_packet(snapshot, expected_round)
            state: dict[str, Any] = {
                "format": STATE_FORMAT,
                "status": "active",
                "rounds": [
                    new_round_entry(
                        expected_round, snapshot_path, snapshot_bytes, reviewer
                    )
                ],
                "terminal_reason": None,
            }
        else:
            state = load_state(state_path)
            if state["status"] == "active":
                raise GateError(
                    f"review round {len(state['rounds'])} is already active; "
                    "the snapshot cannot start again"
                )
            if state["status"] == "terminated":
                raise GateError(
                    f"review state is terminated ({state['terminal_reason']}); "
                    "no further review may start"
                )
            previous = state["rounds"][0]
            if report_leaks(snapshot, previous["report_text"]):
                raise GateError("second-round snapshot leaks first-round review report")
            expected_round = 2
            validate_sealed_packet(snapshot, expected_round)
            snapshot_hash = bytes_sha256(snapshot_bytes)
            if snapshot_hash == previous["snapshot_sha256"]:
                raise GateError("second round requires a new frozen snapshot")
            if reviewer == previous["reviewer"]:
                raise GateError("second round requires a new reviewer")
            state["rounds"].append(
                new_round_entry(expected_round, snapshot_path, snapshot_bytes, reviewer)
            )
            state["status"] = "active"
            state["terminal_reason"] = None
        atomic_write_state(state_path, state)

    print(
        f"PASS: review round {expected_round} started for reviewer {reviewer}; "
        f"snapshot_sha256={bytes_sha256(snapshot_bytes)}"
    )
    return 0


def command_finish(args: argparse.Namespace) -> int:
    reviewer = validate_reviewer(args.reviewer)
    state_path = resolved_path(args.state, must_exist=True)
    snapshot_path = resolved_path(args.snapshot, must_exist=True)
    report_path = resolved_path(args.report, must_exist=True)
    ensure_distinct_paths(
        {
            "state": state_path,
            "snapshot": snapshot_path,
            "report": report_path,
        }
    )
    snapshot_bytes, snapshot = read_utf8(snapshot_path, "snapshot")
    _, report_text = read_utf8(report_path, "review report")
    verdict, normalized_report = parse_review_report(report_text)

    with state_lock(state_path):
        state = load_state(state_path)
        if state["status"] != "active":
            raise GateError(f"review state is not active: {state['status']}")
        current = state["rounds"][-1]
        round_number = current["round"]
        validate_sealed_packet(snapshot, round_number)
        if reviewer != current["reviewer"]:
            raise GateError(
                f"reviewer mismatch: active reviewer is {current['reviewer']}, got {reviewer}"
            )
        if not paths_equal(Path(current["snapshot_path"]), snapshot_path):
            raise GateError("snapshot path differs from the frozen active snapshot")
        if (
            bytes_sha256(snapshot_bytes) != current["snapshot_sha256"]
            or len(snapshot_bytes) != current["snapshot_size"]
        ):
            raise GateError("snapshot changed after the review round started")

        structural_change: bool | None = None
        if round_number == 1 and verdict == "REPAIR":
            if args.structural_change is None:
                raise GateError(
                    "first-round REPAIR requires --structural-change true or false"
                )
            structural_change = args.structural_change == "true"
        elif args.structural_change is not None:
            raise GateError(
                "--structural-change is allowed only for a first-round REPAIR"
            )

        current["status"] = "completed"
        current["verdict"] = verdict
        current["structural_change"] = structural_change
        current["report_sha256"] = text_sha256(normalized_report)
        current["report_text"] = normalized_report

        if round_number == 1 and verdict == "REPAIR" and structural_change is True:
            state["status"] = "awaiting_second_round"
            state["terminal_reason"] = None
        else:
            state["status"] = "terminated"
            if round_number == 2:
                state["terminal_reason"] = "second-round-complete"
            elif verdict == "PASS":
                state["terminal_reason"] = "first-round-pass"
            else:
                state["terminal_reason"] = "first-round-nonstructural-repair"
        atomic_write_state(state_path, state)

    print(
        f"PASS: review round {round_number} finished with {verdict}; "
        f"STATE_STATUS={state['status']}"
    )
    return 0


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        if args.command == "seal":
            return command_seal(args)
        if args.command == "start":
            return command_start(args)
        if args.command == "finish":
            return command_finish(args)
        raise GateError(f"unsupported command: {args.command}")
    except GateError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"ERROR: filesystem operation failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
