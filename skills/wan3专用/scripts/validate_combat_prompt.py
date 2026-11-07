#!/usr/bin/env python3
"""Deterministic envelope and shot-mode-specific timeline checks for one Wan3.0 combat prompt."""

from __future__ import annotations

import argparse
import re
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path


SECTIONS = [
    "【角色/场景/素材锁定】",
    "【基础风格】",
    "【运镜与时间轴】",
    "【声音设计】",
    "【画面限制】",
]

SEGMENT_CONTRACT_LABELS = [
    "前提",
    "核心关系",
    "导演意图",
    "演员指令",
    "对白规则",
]

DIRECTOR_INTENT_META_RE = re.compile(
    r"用户(?:要求|希望|提供)|根据用户|原片|原视频|"
    r"参考(?:图|图片|视频|音频|素材)(?:用途|要求)?|"
    r"上一(?:版|段|次)|剧本(?:要求|说明)|提示词|冷审|"
    r"Wan3\.0|视频模型|生成模型|模型(?:理解|执行)|"
    r"制作(?:流程|说明)|复刻(?:原片|参考)|还原(?:原片|参考)",
    re.IGNORECASE,
)

RANGE_RE = r"（\s*(\d+(?:\.\d+)?)\s*[-–—]\s*(\d+(?:\.\d+)?)\s*秒\s*）"
CUT_RE = re.compile(rf"(?m)^\s*CUT\s+(\d+)\s*{RANGE_RE}", re.IGNORECASE)
BEAT_RE = re.compile(rf"(?m)^\s*BEAT\s+([A-Z0-9]+)\s*{RANGE_RE}", re.IGNORECASE)
CUT_LABEL_RE = re.compile(r"(?m)^\s*CUT\s+(\d+)\b", re.IGNORECASE)
BEAT_LABEL_RE = re.compile(r"(?m)^\s*BEAT\s+([A-Z0-9]+)\b", re.IGNORECASE)
TITLE_RE = re.compile(r"(?m)^###\s*第\d+段[^\n]*?(\d+(?:\.\d+)?)\s*秒")
SEGMENT_HEADING_RE = re.compile(r"(?m)^\s*###\s*第\s*\d+\s*段[^\r\n]*")
SECTION_RE = re.compile(r"(?m)^\s*(【[^】\n]+】)\s*$")
DECIMAL_SECOND_RE = re.compile(r"(?<!\d)\d+\.\d+\s*秒")
FRAME_RE = re.compile(
    r"(?<![A-Za-z])Frame[ \t]+([+-]?\d+(?:\.\d+)?)(?:\s*帧)?(?=\s|[：:，,。；;）)]|$)",
    re.IGNORECASE,
)
REFERENCE_HANDLE_RE = re.compile(r"@[^\s，。；：、）】]+")
VISIBLE_TIMESTAMP_RE = re.compile(
    r"(?<!\d)(?:\d+(?:\.\d+)?\s*[-–—]\s*\d+(?:\.\d+)?\s*秒|"
    r"第\s*\d+(?:\.\d+)?\s*秒|\d+(?:\.\d+)?\s*秒后)"
)
CANDIDATE_SECTION_RE = re.compile(
    r"(?m)^##[ \t]+候选提示词[ \t]*(?=\r?$)"
)
H2_SECTION_RE = re.compile(r"(?m)^##[ \t]+[^#\r\n][^\r\n]*(?=\r?$)")
LINE_BREAK_RE = re.compile(r"\r\n|\n|\r")
AUDIT_SEPARATOR_RE = re.compile(r"(?:(?:\r\n)|\n|\r){2}")

TIMESTAMP_POLICIES = (
    "integer-preferred",
    "decimal-allowed",
    "integer-required",
)

TOOL_WRAPPER_PATTERNS = [
    (re.compile(r"\bExit[ \t]+code\b", re.IGNORECASE), "Exit code"),
    (re.compile(r"\bProcess[ \t]+exited\b", re.IGNORECASE), "Process exited"),
    (re.compile(r"\bOutput[ \t]*[:：]", re.IGNORECASE), "Output:"),
    (re.compile(r"\btool[ \t]+output\b", re.IGNORECASE), "tool output"),
    (re.compile(r"\btool[_ \t]+call\b", re.IGNORECASE), "tool call"),
    (re.compile(r"(?im)^\s*Command[ \t]*[:：]"), "Command:"),
]

FORBIDDEN_VISIBLE = [
    (re.compile(r"https?://", re.IGNORECASE), "visible URL"),
    (re.compile(r"\[[^\]\n]+\]\(https?://", re.IGNORECASE), "visible Markdown source link"),
    (re.compile(r"(?im)^\s*(研究增量|研究来源|来源链接|交接核验|核验结果|审阅结果)\s*[:：]"), "visible research/review appendix"),
    (re.compile(r"(?im)^\s*(VERDICT|BLOCKING_FINDINGS|OPTIONAL_FINDINGS|PROTECTED_FACTS)\s*:"), "visible cold-review record"),
    (re.compile(r"PROJECT_RULES\.md", re.IGNORECASE), "visible internal review artifact"),
    (
        re.compile(
            r"(?:画面|生成)?参考输入(?:仅使用下列|仅限以上|仅限下列)|"
            r"(?:后期[^\r\n。]*授权\s*BGM\s*母带|授权\s*BGM\s*母带[^\r\n。]*(?:后期|时码挂接))|"
            r"(?:本段)?独立冷启动|不依赖其他段落|未列出的素材|"
            r"项目窗口内分析证据|不作为(?:视频)?生成(?:参考)?输入|"
            r"(?:其余|全部环境|[\w\u4e00-\u9fff、，/]+和全部环境)(?:均|全部)?由文字(?:生成|建立)",
            re.IGNORECASE,
        ),
        "visible internal production/material-management metadata",
    ),
    (
        re.compile(
            r"具体.{0,10}由模型(?:自由生成|决定)|"
            r"交模型(?:决定|自由生成)?|"
            r"原文未指定[，,].{0,5}交模型|"
            r"本段不出现[，,].{0,10}仅作身份锚点",
            re.IGNORECASE,
        ),
        "visible material-sourcing meta-instruction (素材溯源meta)",
    ),
    (
        re.compile(
            r"延续.{0,15}(?:时间线|质感|空间|状态)|"
            r"承接上段|"
            r"Seg\s*\d+|"
            r"\S{1,6}已(?:飞离|离开|走远)",
            re.IGNORECASE,
        ),
        "visible implicit cross-segment reference (隐式跨段引用)",
    ),
    (re.compile(r"(?im)^\s*(PASS|REPAIR)\s*$"), "visible validation verdict"),
]


def positive_decimal(value: str) -> Decimal:
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise argparse.ArgumentTypeError(f"invalid decimal value: {value}") from exc
    if not parsed.is_finite() or parsed <= 0:
        raise argparse.ArgumentTypeError("value must be a finite number greater than 0")
    return parsed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", nargs="?", help="UTF-8 prompt file; omit to read stdin")
    parser.add_argument(
        "--duration",
        type=positive_decimal,
        required=True,
        help="expected exact seconds; decimal durations are supported",
    )
    parser.add_argument("--version", choices=("单镜", "多镜"), default="多镜")
    parser.add_argument("--mode", choices=("auto", "cut", "onetake"), default="auto")
    parser.add_argument(
        "--timestamp-policy",
        choices=TIMESTAMP_POLICIES,
        default="integer-preferred",
        help="Wan3.0 多镜模式 timestamp granularity policy",
    )
    parser.add_argument(
        "--fps",
        type=positive_decimal,
        default=Decimal("24"),
        help="frame rate used to bound optional Frame T帧 events (default: 24)",
    )
    parser.add_argument(
        "--project-rules",
        metavar="PATH",
        help="PROJECT_RULES.md audit packet; requires --candidate",
    )
    parser.add_argument(
        "--candidate",
        metavar="PATH",
        help=(
            "exact candidate file for audit comparison; also used as the prompt "
            "input when positional input is omitted"
        ),
    )
    parser.add_argument(
        "--reference-handle-policy",
        choices=("any-section", "lock-only"),
        default="any-section",
        help=(
            "project-specific @handle policy; lock-only requires every handle "
            "to appear once and only in the first lock section"
        ),
    )
    parser.add_argument("--max-chars", type=int, default=5000)
    args = parser.parse_args()
    if bool(args.project_rules) != bool(args.candidate):
        parser.error("--project-rules and --candidate must be supplied together")
    return args


def read_exact_text(path: str) -> str:
    """Read UTF-8 without universal-newline translation; tolerate one leading BOM."""
    return Path(path).read_bytes().decode("utf-8-sig")


def read_text(path: str | None) -> str:
    if path:
        return read_exact_text(path)
    return sys.stdin.read()


def format_decimal(value: Decimal) -> str:
    return format(value, "f")


def is_integer_value(value: Decimal) -> bool:
    return value == value.to_integral_value()


def check_segment_contract(
    timeline: str,
    version: str,
    errors: list[str],
) -> None:
    """Require one ordered, non-empty 多镜模式 segment contract before the first CUT."""
    if version != "多镜":
        return

    first_cut = CUT_LABEL_RE.search(timeline)
    positions: list[int] = []
    for label in SEGMENT_CONTRACT_LABELS:
        pattern = re.compile(
            rf"(?m)^\s*{re.escape(label)}\s*[：:]\s*(\S.*)\s*$"
        )
        matches = list(pattern.finditer(timeline))
        if len(matches) != 1:
            errors.append(
                f"Wan3.0 多镜模式 timeline contract label {label} occurs "
                f"{len(matches)} times, expected 1"
            )
            continue
        match = matches[0]
        if first_cut and match.start() > first_cut.start():
            errors.append(
                f"Wan3.0 多镜模式 timeline contract label {label} must appear "
                "before the first CUT"
            )
        if label == "导演意图":
            contaminated = DIRECTOR_INTENT_META_RE.search(match.group(1))
            if contaminated:
                errors.append(
                    "Wan3.0 多镜模式 director intent must be the compiler-authored "
                    "dramatic interpretation, not user/source/workflow metadata; "
                    f"found {contaminated.group(0)}"
                )
        positions.append(match.start())

    if len(positions) == len(SEGMENT_CONTRACT_LABELS) and positions != sorted(positions):
        errors.append(
            "Wan3.0 多镜模式 timeline contract labels must be ordered: "
            + " / ".join(SEGMENT_CONTRACT_LABELS)
        )


def check_ranges(
    label: str,
    ranges: list[tuple[Decimal, Decimal]],
    duration: Decimal,
    errors: list[str],
) -> None:
    if not ranges:
        errors.append(f"no {label} time ranges found")
        return
    if ranges[0][0] != 0:
        errors.append(
            f"{label} timeline starts at {format_decimal(ranges[0][0])}, expected 0"
        )
    for index, (start, end) in enumerate(ranges):
        if end <= start:
            errors.append(
                f"{label} range {index + 1} is non-positive: "
                f"{format_decimal(start)}-{format_decimal(end)}"
            )
        if index:
            previous_start, previous_end = ranges[index - 1]
            if start < previous_start:
                errors.append(
                    f"{label} range {index + 1} is out of chronological order: "
                    f"{format_decimal(start)} follows {format_decimal(previous_start)}"
                )
            if start > previous_end:
                errors.append(
                    f"{label} gap between {format_decimal(previous_end)} "
                    f"and {format_decimal(start)}"
                )
            elif start < previous_end:
                errors.append(
                    f"{label} overlap between {format_decimal(previous_end)} "
                    f"and {format_decimal(start)}"
                )
    if ranges[-1][1] != duration:
        errors.append(
            f"{label} timeline ends at {format_decimal(ranges[-1][1])}, "
            f"expected {format_decimal(duration)}"
        )


def check_frame_events(
    timeline: str,
    duration: Decimal,
    fps: Decimal,
    errors: list[str],
) -> None:
    frame_boundary = duration * fps
    for match in FRAME_RE.finditer(timeline):
        frame = Decimal(match.group(1))
        if not is_integer_value(frame):
            errors.append(f"Frame {match.group(1)} must use a whole-frame index")
            continue
        if frame < 0:
            errors.append(f"Frame {format_decimal(frame)} must be nonnegative")
        elif frame > frame_boundary:
            errors.append(
                f"Frame {format_decimal(frame)} exceeds duration boundary "
                f"{format_decimal(frame_boundary)} frames at {format_decimal(fps)} fps"
            )


def check_reference_handles(text: str, policy: str, errors: list[str]) -> None:
    if policy != "lock-only":
        return
    lock_start = text.find(SECTIONS[0])
    base_start = text.find(SECTIONS[1], lock_start + 1)
    if lock_start < 0 or base_start < 0:
        return
    lock_text = text[lock_start:base_start]
    later_text = text[base_start:]
    lock_handles = REFERENCE_HANDLE_RE.findall(lock_text)
    later_handles = REFERENCE_HANDLE_RE.findall(later_text)
    if later_handles:
        errors.append(
            "reference-handle policy lock-only forbids @handles after the lock "
            f"section: {', '.join(sorted(set(later_handles)))}"
        )
    duplicates = sorted(
        handle
        for handle in set(lock_handles + later_handles)
        if (lock_handles + later_handles).count(handle) != 1
    )
    if duplicates:
        errors.append(
            "reference-handle policy lock-only requires each @handle exactly once: "
            + ", ".join(duplicates)
        )


def check_audit_package(
    project_rules: str,
    candidate: str,
    errors: list[str],
) -> None:
    for source_label, source_text in (
        ("PROJECT_RULES", project_rules),
        ("candidate", candidate),
    ):
        for pattern, wrapper_label in TOOL_WRAPPER_PATTERNS:
            if pattern.search(source_text):
                errors.append(
                    f"{source_label} contains forbidden tool wrapper token: {wrapper_label}"
                )

    candidate_headers = list(CANDIDATE_SECTION_RE.finditer(project_rules))
    if len(candidate_headers) != 1:
        errors.append(
            "PROJECT_RULES must contain exactly one '## 候选提示词' section; "
            f"found {len(candidate_headers)}"
        )
        return

    header = candidate_headers[0]
    header_break = LINE_BREAK_RE.match(project_rules, header.end())
    if not header_break:
        errors.append("PROJECT_RULES candidate section heading must end with a line break")
        return

    candidate_start = header_break.end()
    next_section = H2_SECTION_RE.search(project_rules, candidate_start)
    section_end = next_section.start() if next_section else len(project_rules)
    if not project_rules.startswith(candidate, candidate_start):
        errors.append(
            "PROJECT_RULES candidate EXACT_MATCH failed: embedded candidate differs "
            "from --candidate"
        )
        return

    separator = project_rules[candidate_start + len(candidate) : section_end]
    expected_separator = bool(next_section)
    separator_ok = (
        AUDIT_SEPARATOR_RE.fullmatch(separator) is not None
        if expected_separator
        else separator == ""
    )
    if not separator_ok:
        errors.append(
            "PROJECT_RULES candidate EXACT_MATCH failed: extra or missing characters "
            "at the candidate section boundary"
        )
    outside_candidate = (
        project_rules[:candidate_start]
        + project_rules[candidate_start + len(candidate) :]
    )
    if re.search(r"(?m)^###\s*第\d+段", outside_candidate):
        errors.append(
            "PROJECT_RULES contains a stale candidate-like segment heading outside "
            "the unique embedded candidate"
        )


def main() -> int:
    args = parse_args()
    audit_candidate = read_exact_text(args.candidate) if args.candidate else None
    if args.input:
        raw_text = read_exact_text(args.input)
    elif audit_candidate is not None:
        raw_text = audit_candidate
    else:
        raw_text = read_text(None)
    text = raw_text.strip()
    errors: list[str] = []
    warnings: list[str] = []

    if args.project_rules:
        assert audit_candidate is not None
        check_audit_package(
            read_exact_text(args.project_rules),
            audit_candidate,
            errors,
        )
        if args.input and raw_text != audit_candidate:
            errors.append(
                "positional input differs from --candidate; audit and validation "
                "must use the same exact prompt"
            )

    if not text:
        errors.append("prompt is empty")
    if len(text) > args.max_chars:
        errors.append(f"prompt has {len(text)} characters, limit is {args.max_chars}")
    segment_headings = SEGMENT_HEADING_RE.findall(text)
    if not re.match(r"^###\s*第\d+段", text):
        errors.append("prompt-only envelope must start with a segment heading")
    if len(segment_headings) != 1:
        errors.append(
            "prompt-only cold-review candidate must contain exactly one "
            f"independent segment envelope; found {len(segment_headings)}"
        )

    positions: list[int] = []
    for section in SECTIONS:
        count = text.count(section)
        if count != 1:
            errors.append(f"section {section} occurs {count} times, expected 1")
        positions.append(text.find(section))
    if all(position >= 0 for position in positions) and positions != sorted(positions):
        errors.append("five sections are out of order")
    visible_sections = SECTION_RE.findall(text)
    if visible_sections != SECTIONS:
        extras = [section for section in visible_sections if section not in SECTIONS]
        if extras:
            errors.append(f"unexpected visible section(s): {', '.join(extras)}")
    check_reference_handles(text, args.reference_handle_policy, errors)

    for pattern, label in FORBIDDEN_VISIBLE:
        if pattern.search(text):
            errors.append(label)

    title_match = TITLE_RE.search(text)
    if not title_match:
        errors.append("segment heading has no duration")
    else:
        title_duration = Decimal(title_match.group(1))
        title_mismatch = (
            title_duration != args.duration
            if args.version == "多镜"
            else abs(title_duration - args.duration) > Decimal("0.011")
        )
        if title_mismatch:
            errors.append(
                f"title duration is {title_match.group(1)}, "
                f"expected {format_decimal(args.duration)}"
            )

    cut_matches = CUT_RE.findall(text)
    beat_matches = BEAT_RE.findall(text)
    cut_labels = CUT_LABEL_RE.findall(text)
    beat_labels = BEAT_LABEL_RE.findall(text)
    cuts = [(Decimal(start), Decimal(end)) for _, start, end in cut_matches]
    beats = [(Decimal(start), Decimal(end)) for _, start, end in beat_matches]
    timeline_start = text.find("【运镜与时间轴】")
    sound_start = text.find("【声音设计】", timeline_start + 1)
    timeline = text[timeline_start:sound_start] if timeline_start >= 0 and sound_start > timeline_start else text
    check_segment_contract(timeline, args.version, errors)
    mode = args.mode
    if mode == "auto":
        mode = "onetake" if len(cut_labels) == 1 and beat_labels else "cut"

    frame_matches = list(FRAME_RE.finditer(timeline))
    check_frame_events(timeline, args.duration, args.fps, errors)

    if args.version == "单镜":
        if cut_matches or beat_matches or frame_matches or VISIBLE_TIMESTAMP_RE.search(timeline):
            errors.append("Wan3.0 单镜模式 timeline must use untimed CUT/BEAT labels and relative phases")
        if mode == "onetake":
            if len(cut_labels) != 1:
                errors.append(
                    f"单镜模式 one-take mode requires exactly 1 untimed CUT, found {len(cut_labels)}"
                )
            if not beat_labels:
                errors.append("单镜模式 one-take mode requires ordered untimed BEAT labels")
        elif len(cut_labels) < 2:
            errors.append(
                f"单镜模式 multi-CUT mode requires at least 2 untimed CUTs, found {len(cut_labels)}"
            )
    else:
        range_tokens = [
            token
            for match in (*cut_matches, *beat_matches)
            for token in match[1:]
        ]
        uses_decimal_timestamps = (
            not is_integer_value(args.duration)
            or bool(title_match and "." in title_match.group(1))
            or any("." in token for token in range_tokens)
            or bool(DECIMAL_SECOND_RE.search(timeline))
        )
        uses_frame_timestamps = bool(frame_matches)
        resolved_policy = args.timestamp_policy
        if uses_decimal_timestamps or uses_frame_timestamps:
            if resolved_policy == "integer-required":
                errors.append(
                    "Wan3.0 多镜模式 subsecond/frame timestamps violate resolved "
                    "timestamp policy integer-required"
                )
            elif resolved_policy == "integer-preferred":
                warnings.append(
                    "Wan3.0 多镜模式 uses decimal-second or Frame timestamps under "
                    "integer-preferred policy"
                )

        if mode == "onetake":
            if len(cuts) != 1:
                errors.append(f"多镜模式 one-take mode requires exactly 1 timed CUT, found {len(cuts)}")
            check_ranges("CUT", cuts, args.duration, errors)
            check_ranges("BEAT", beats, args.duration, errors)
        else:
            if len(cuts) < 2:
                errors.append(f"多镜模式 multi-CUT mode requires at least 2 timed CUTs, found {len(cuts)}")
            check_ranges("CUT", cuts, args.duration, errors)

    for warning in warnings:
        print(f"WARNING: {warning}", file=sys.stderr)

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
