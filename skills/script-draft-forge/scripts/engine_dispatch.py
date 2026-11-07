#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
engine_dispatch.py — script-draft-forge 六档位自动调度引擎（MR-08）

定位：只做「按 MR-07 的 model id 逐档直调 API + 断点续跑 + 成本记账」，
不重新实现 Forge 的 S0–S5 编排，不做挑稿拍板，不改稿，不出终稿。

安全约定：
- 默认演练（dry-run，零外部调用）；只有显式 --live 才会真实计费。
- apiKey 只从自定义端点清单读入内存（默认 ~/.config/opencode/models.json，
  可用环境变量 OPENCODE_SKILL_MODELS 覆盖），绝不写入任何产物/日志/报告。
- dry-run 产物带显式占位标记，verify 会拒绝验收，防止假稿混入闸门A。

纯标准库。子命令：plan / run / status / verify / init-config / selftest。
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# 自定义端点清单：OpenCode 用户级配置目录；可用环境变量覆盖，便于多套端点/临时切换。
DEFAULT_MODELS = Path(
    os.environ.get("OPENCODE_SKILL_MODELS")
    or os.path.expanduser("~/.config/opencode/models.json")
)
PLAN_NAME = "dispatch-plan.json"
CONFIG_NAME = "dispatch-config.json"
COST_NAME = "dispatch-cost.md"
REPORT_NAME = "dispatch-report.md"
DRY_MARK = "> ⚠ DRY-RUN 占位，非真实初稿；删除本行前禁止进入闸门A。"

# MR-07 端点映射：档位 → API model id。可用 dispatch-config.json 的 role_models 覆盖。
ROLE_MODEL = {
    "outline": "deepseek-v4.1-flash",
    "tone": "claude-opus-5-5",
    "dialogue": "kimi-k3.1-pro",
    "bulk": "glm-5.3-flash",
    "pick": "hy4",
    "review": "claude-opus-5-5",
}
ROLE_LABEL = {
    "outline": "骨架档", "tone": "定调档", "dialogue": "台词档",
    "bulk": "批量档", "pick": "挑稿档", "review": "回顾档",
}
# 推理模型实测：max_tokens <=200 时 glm/hy4 可能只返回空 content（见 MR-07）。
ROLE_MIN_TOKENS = {
    "outline": 2500, "tone": 4000, "dialogue": 4000,
    "bulk": 4500, "pick": 3500, "review": 3500,
}
# Mode 3 细纲锁结构时，多版差异化只允许呈现层四轴（SO-03 / 铁律 6 唯一例外）。
AXES = [
    "切入点=从最接近卡点的场面倒叙切入",
    "场面调度=压缩群众场面、把冲突收进两人对话",
    "台词密度=短句高频互怼、减少动作提示",
    "卡点切法=把最强信息留在最后一个动作而非台词",
]
# Mode 1 结构参数（full-draft.md S3）。
STRUCTS = ["强冲突版", "悬念倒叙版", "情绪流版"]
VERSIONS = ["A", "B", "C"]

COMMON_RULES = """硬约束（违反即判杀）：
1. 只输出剧本正文，禁止输出自检表、解释、元叙述标注或「〔钩子〕」之类提示。
2. 台词口语化、短句为主；禁止把情绪名称词（愤怒/悲伤/震惊等）写进正文，用动作和台词呈现。
3. 系统/金手指规则不得新增条款，不得无触发源自动结算，不得凭空造物。
4. 人名、术语、既定事实严格沿用给定档案；禁止同音换字、禁止改名。
5. 单集结尾必须留卡点；钩子按给定预算行，不擅自增删类型。
6. 输出标准短剧剧本格式：场景头（场号 内外 地点）、△动作提示、人物名：台词、OS 标注。
"""

ROLE_SYSTEM = {
    "outline": "你是短剧结构编剧。任务：产出本批集数的骨架（每集一句话主线、反转节点、卡点设计、钩子预算行）。只给结构，不写完整正文。",
    "tone": "你是定调编剧。本集是整卷的语气基准，后续所有集要照它抄口音。请一次成型，写出完整单集剧本，人物声口、句式节奏、OS 密度都要可复用。",
    "dialogue": "你是台词精修编剧。给定初稿，只改台词与人物声口：口语化、短句、潜台词、破节奏的非常规表达。不得改事件顺序、不得新增事件、不得改设定。输出精修后的完整剧本。",
    "bulk": "你是短剧正文编剧。按给定生成包写出完整单集剧本，事件顺序、人物、设定严格照包执行。",
    "pick": "你是挑稿评估。给定同集多个版本与验收结论，只做比较与排序：逐版列出硬伤（带行号或原文引用）、给出推荐版与理由、列出需人工拍板的事项。禁止改写任何版本，禁止自报『细纲都写到了』。",
    "review": "你是卷级回顾编辑。给定本卷逐集一句话摘要，只检查三件事：①情绪强度曲线是否与开卷设定呼应 ②长线钩兑现进度是否滞后 ③人物言行是否漂移出小传。输出 ≤10 行结论，供后续批次注入，不写正文。",
}

DEFAULT_CONFIG = {
    "_comment": "engine_dispatch 配置。role_models 覆盖 MR-07 默认映射；price_per_1k 未填则只报 token 用量，不编造金额。",
    "role_models": {},
    "price_per_1k": {},
    "temperature": 0.8,
    "max_prompt_chars": 24000,
    "batch_size": 10,
    "versions": 2,
    "dialogue_pass": False,
    # 2026-11-04 实跑：glm-5.3-flash 在 3096 字符编剧 prompt 下把 4500 token 全花在
    # reasoning_content（11620 字符）导致正文为空；关闭思考后 1109 token 即出 1463 字正文。
    # 因此默认对推理型档位关思考，避免整批任务空正文白烧钱（MR-07 实测口径）。
    "disable_thinking": True,
    "retries": 3,
    "timeout": 180,   # 长文本生成偶发读超时（2026-11-04 kimi 台词档实测），重试时再递增
    "sleep_base": 2,
}


def today() -> str:
    return date.today().isoformat()


def jread(p: Path, default=None):
    if not p.exists():
        return default
    return json.loads(p.read_text(encoding="utf-8"))


def jwrite(p: Path, data):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_models(path: Path) -> dict:
    if not path.exists():
        raise SystemExit("[FAIL] 找不到模型配置：%s（按 MR-07 补齐端点后再跑）" % path)
    cfg = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(cfg, list) or not cfg:
        raise SystemExit("[FAIL] 模型配置为空或格式错误：%s" % path)
    return {x["id"]: x for x in cfg}


def load_config(project: Path) -> dict:
    cfg = dict(DEFAULT_CONFIG)
    user = jread(project / "pipeline" / CONFIG_NAME, {}) or {}
    cfg.update(user)
    cfg.setdefault("role_models", {})
    return cfg


def resolve_role_models(config: dict, models: dict, strict=True) -> dict:
    out, missing = {}, []
    for role, default in ROLE_MODEL.items():
        mid = config["role_models"].get(role, default)
        out[role] = mid
        if mid not in models:
            missing.append("%s→%s" % (role, mid))
    if missing and strict:
        raise SystemExit("[FAIL] MR-07 端点未配齐：%s；请补齐自定义端点清单（默认 ~/.config/opencode/models.json，或设置 OPENCODE_SKILL_MODELS），或用 --allow-missing 生成待补计划" % "、".join(missing))
    return out


def detect_mode(project: Path) -> str:
    return "3" if (project / "pipeline" / "outline.json").exists() and (project / "pipeline" / "packets").is_dir() else "1"


def read_manifest(project: Path) -> dict:
    p = project / "pipeline" / "manifest.json"
    m = jread(p, None)
    if m is None:
        m = {"mode": detect_mode(project), "stages": {}, "modules_loaded": [],
             "engines": {}, "updated": today()}
    m.setdefault("stages", {})
    m.setdefault("engines", {})
    m.setdefault("modules_loaded", [])
    d = m.setdefault("dispatch", {})
    d.setdefault("plan", "pipeline/" + PLAN_NAME)
    d.setdefault("tasks", {})
    d.setdefault("batch", {})
    return m


def write_manifest(project: Path, m: dict):
    m["updated"] = today()
    jwrite(project / "pipeline" / "manifest.json", m)


def parse_range(s: str, hi: int) -> list:
    if not s:
        return list(range(1, min(hi, 10) + 1))
    out = []
    for part in s.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-", 1)
            out += list(range(int(a), int(b) + 1))
        elif part:
            out.append(int(part))
    return [x for x in sorted(set(out)) if 1 <= x <= hi]


def episode_summaries(project: Path, eps: list) -> str:
    outline = jread(project / "pipeline" / "outline.json", {}) or {}
    by = {e.get("ep"): e for e in outline.get("episodes", [])}
    lines = []
    for n in eps:
        e = by.get(n, {})
        beats = e.get("beats", [])
        txt = "；".join(str(b.get("text_clean") or b.get("text", ""))[:22] for b in beats[:3])
        lines.append("- 第%d集：%s（≤60字）" % (n, txt[:60] or "（无细纲摘要）"))
    return "\n".join(lines) or "- （无细纲摘要）"


def make_plan(project: Path, args, models: dict) -> dict:
    config = load_config(project)
    role_models = resolve_role_models(config, models, strict=not args.allow_missing)
    mode = detect_mode(project)
    outline = jread(project / "pipeline" / "outline.json", {}) or {}
    known = sorted(e.get("ep") for e in outline.get("episodes", [])) if mode == "3" else []
    hi = max(known) if known else (args.total_episodes or 10)
    eps = parse_range(args.episodes, hi)
    if mode == "3":
        eps = [e for e in eps if e in known]
    if not eps:
        raise SystemExit("[FAIL] 没有可排的集数（Mode 3 需先跑 source_outline.py ingest 产出 packets）")

    nv = min(max(1, args.versions or config["versions"]), 3)
    tasks = []

    def add(tid, role, ep, ver="", output="", depends=None, axis="", extra=None):
        tasks.append({
            "id": tid, "role": role, "stage": ROLE_LABEL[role], "ep": ep,
            "version": ver, "model": role_models[role],
            "output": output, "depends_on": depends or [],
            "max_tokens": max(args.min_tokens or 0, ROLE_MIN_TOKENS[role]),
            "axis": axis, "prompt_files": extra or [],
        })

    # S1 骨架：仅当尚未有钩子预算表时排一次（CC-02：便宜档）
    have_budget = (project / "pipeline" / "01_钩子预算表.md").exists()
    if not have_budget and not args.no_outline:
        add("outline-000", "outline", 0, output="pipeline/01_钩子预算表.md",
            extra=["pipeline/00_需求与体检.md"])

    draft_ids = {}
    for ep in eps:
        packet = "pipeline/packets/ep%03d.md" % ep
        files = [packet] if (project / packet).exists() else [
            "pipeline/00_需求与体检.md", "pipeline/01_钩子预算表.md",
            "pipeline/02_人物小传与术语表.md", "pipeline/前情卡.md",
        ]
        ids = []
        for i in range(nv):
            ver = VERSIONS[i]
            role = "tone" if ep % 10 == 1 and i == 0 else "bulk"  # MR-03 定调只做一次
            axis = (AXES[i % len(AXES)] if mode == "3" else STRUCTS[i % len(STRUCTS)])
            tid = "draft-%03d-%s" % (ep, ver)
            add(tid, role, ep, ver, "outputs/ep%03d_%s_v1.md" % (ep, ver),
                depends=(["outline-000"] if not have_budget and not args.no_outline else []),
                axis=axis, extra=files)
            ids.append(tid)
            if config["dialogue_pass"] or args.dialogue_pass:
                add("dialogue-%03d-%s" % (ep, ver), "dialogue", ep, ver,
                    "outputs/ep%03d_%s_v2.md" % (ep, ver), depends=[tid],
                    axis="台词精修（不改事件）", extra=[tid])
        draft_ids[ep] = ids
        pick_dep = [("dialogue-%03d-%s" % (ep, v) if (config["dialogue_pass"] or args.dialogue_pass) else "draft-%03d-%s" % (ep, v))
                    for v in VERSIONS[:nv]]
        add("pick-%03d" % ep, "pick", ep, output="pipeline/pick/ep%03d.md" % ep,
            depends=pick_dep, extra=pick_dep)

    # CC-03 卷级回顾：批次内凑满 10 集才排
    full_volumes = sorted({(e - 1) // 10 for e in eps if len([x for x in eps if (x - 1) // 10 == (e - 1) // 10]) == 10})
    for v in full_volumes:
        a, b = v * 10 + 1, v * 10 + 10
        deps = [t["id"] for t in tasks if t["role"] in ("tone", "bulk") and a <= t["ep"] <= b]
        add("review-%03d-%03d" % (a, b), "review", a,
            output="pipeline/04_卷级回顾_第%d-%d集.md" % (a, b), depends=deps)

    if "outline-000" in [t["id"] for t in tasks]:
        for t in tasks:
            if t["id"] != "outline-000" and "outline-000" not in t["depends_on"] and t["role"] in ("tone", "bulk"):
                t["depends_on"] = ["outline-000"] + t["depends_on"]

    return {
        "generated": today(), "project": str(project), "mode": mode,
        "episodes": eps, "versions": nv, "role_models": role_models,
        "dry_by_default": True, "config": {k: v for k, v in config.items() if k != "role_models"},
        "tasks": tasks,
    }


def task_output_path(project: Path, t: dict) -> Path:
    return project / t["output"]


def strip_product_head(text: str) -> str:
    """上游产物头（MR-06 版本标注 / 演练占位）不是稿件正文，注入下游前必须剥掉。
    2026-11-04 实跑：挑稿档把 `> 版本：…` 当成「输出非剧本正文内容」硬伤，属注入误判。"""
    lines = text.splitlines()
    while lines and (lines[0].startswith("> 版本：") or lines[0].startswith(DRY_MARK)
                     or not lines[0].strip()):
        lines.pop(0)
    return "\n".join(lines)


def collect_prompt_text(project: Path, t: dict, config: dict, records: dict) -> str:
    parts = []
    label = {"pick": "待评版本", "dialogue": "待精修初稿"}.get(t["role"], "上游产物")
    for f in t.get("prompt_files", []):
        if f in records and records[f].get("status") == "done":
            p = task_output_path(project, {"output": records[f]["output"]})
            if p.exists():
                parts.append("### %s：%s\n\n%s" %
                             (label, f, strip_product_head(p.read_text(encoding="utf-8"))))
            continue
        p = project / f
        if p.exists():
            parts.append("### 输入文件：%s\n\n%s" % (f, p.read_text(encoding="utf-8")))
    if t["role"] == "review":
        a = t["ep"]
        parts.insert(0, "### 本卷逐集一句话摘要（CC-03 前情压缩）\n\n" +
                     episode_summaries(project, list(range(a, a + 10))))
    text = "\n\n".join(parts)
    cap = int(config["max_prompt_chars"])
    if len(text) > cap:
        text = text[:cap] + "\n\n> ⚠ 输入已按 max_prompt_chars 截断（CC-01/03）。"
    return text


def build_prompt(project: Path, t: dict, config: dict, records: dict) -> str:
    extra = "\n### 本版差异化要求（MR-04 / SO-03）\n\n- %s\n" % (t["axis"] or "无")
    if t["role"] == "pick":
        extra += "- 只评估、不改写；结论须带行号或原文引用。\n"
    if t["role"] == "review":
        extra += "- 输出 ≤10 行结论，禁止输出正文。\n"
    return ("%s\n\n## 通用硬约束\n\n%s\n\n## 本任务\n\n第%d集｜%s｜版型 %s\n%s\n\n## 输入材料（唯一可入上下文范围）\n\n%s\n" %
            (ROLE_SYSTEM[t["role"]], COMMON_RULES, t["ep"], ROLE_LABEL[t["role"]],
             t["version"] or "-", extra,
             collect_prompt_text(project, t, config, records)))


RETRY_CODES = (404, 408, 409, 425, 429, 500, 502, 503, 504, 520, 522, 524)
# 瞬时网络故障（聚合网关读超时最常见）：必须重试，不能一次就判 failed
RETRY_EXC = (TimeoutError, ConnectionError, urllib.error.URLError)


def apply_no_think(body: dict, model_id: str) -> dict:
    """按聚合端点实测口径关思考；只对确认支持该参数的模型发送，未知模型不冒险。"""
    if model_id.startswith("glm-"):
        body["enable_thinking"] = False
    elif model_id.startswith("hy"):
        body["thinking"] = {"type": "disabled"}
    return body


def call_api(model_cfg: dict, system: str, user: str, t: dict, config: dict,
             transport=None, sleep_fn=time.sleep, on_call=None):
    mid = model_cfg["id"]
    base = {
        "model": mid,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "max_tokens": int(t["max_tokens"]),
        "temperature": float(config["temperature"]),
        "stream": False,
    }
    url = str(model_cfg.get("url") or "http://mock.invalid").rstrip("/") + "/chat/completions"
    force_no_think = bool(config.get("disable_thinking"))
    bump = 0                      # 空正文次数：每次抬高生成预算，避免思考吃光正文
    retries = int(config["retries"])
    last = ""
    for attempt in range(1, retries + 1):
        body = dict(base)
        body["max_tokens"] = int(base["max_tokens"] * (1 + 0.5 * bump))
        if force_no_think:
            apply_no_think(body, mid)
        try:
            t0 = time.time()
            if on_call is not None and transport is None:
                on_call()
            if transport is not None:
                content, usage, elapsed = transport(body)
                content = (content or "").strip()
            else:
                # 每次重试重建 Request，避免复用对象在网关重定向后残留状态
                req = urllib.request.Request(
                    url, data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
                    headers={"Authorization": "Bearer " + model_cfg["apiKey"],
                             "Content-Type": "application/json"})
                with urllib.request.urlopen(
                        req, timeout=int(int(config["timeout"]) * (1 + 0.5 * (attempt - 1)))) as r:
                    d = json.loads(r.read().decode("utf-8"))
                msg = d["choices"][0]["message"]
                content = (msg.get("content") or "").strip()
                usage, elapsed = d.get("usage", {}) or {}, time.time() - t0
            if content:
                return content, usage, elapsed
            # 空正文 = 思考预算吃光（MR-07）：自动关思考并抬高预算后重试，不原样白烧三次
            last = "空正文（reasoning_content 吃光 max_tokens，见 MR-07）"
            force_no_think = True
            bump += 1
        except urllib.error.HTTPError as e:
            last = "HTTP %d %s" % (e.code, e.read(200).decode("utf-8", "replace"))
            if e.code not in RETRY_CODES:
                break
        except Exception as e:
            last = "%s: %s" % (type(e).__name__, str(e)[:160])
            if not isinstance(e, RETRY_EXC):
                break
        if attempt < retries:
            sleep_fn(min(int(config["sleep_base"]) ** attempt, 8))
    raise RuntimeError(last or "未知错误")


def write_product(project: Path, t: dict, content: str, dry: bool, model_id: str) -> str:
    p = task_output_path(project, t)
    p.parent.mkdir(parents=True, exist_ok=True)
    name = Path(t["output"]).stem
    head = "> 版本：%s · 引擎：%s（%s） · 挂载模块：%s · 差异轴：%s · %s\n" % (
        name, model_id, t["stage"], "process/source-outline" if detect_mode(project) == "3" else "platform/structure-templates",
        t["axis"] or "无", today())
    if dry:
        head = DRY_MARK + "\n" + head
        body = "（演练未调用 API，本文件无正文，不得进入闸门A。）\n"
    else:
        body = content.strip() + "\n"
    p.write_text(head + "\n" + body, encoding="utf-8")
    return t["output"]


def run_project(project: Path, args, models: dict, transport=None):
    plan = jread(project / "pipeline" / PLAN_NAME)
    if not plan:
        raise SystemExit("[FAIL] 缺少 pipeline/%s，请先跑 plan" % PLAN_NAME)
    config = load_config(project)
    config.update({k: v for k, v in (plan.get("config") or {}).items()})
    manifest = read_manifest(project)
    recs = manifest["dispatch"]["tasks"]
    live = bool(getattr(args, "live", False)) or transport is not None
    dry = not live
    role_models = plan["role_models"]
    tmap = {t["id"]: t for t in plan["tasks"]}
    only = set(args.only.split(",")) if getattr(args, "only", None) else None
    done = failed = blocked = skipped = 0
    started = time.time()
    calls = [0]

    def wrapped_transport(body):
        calls[0] += 1
        return transport(body)

    def bump_calls():
        # 真实 HTTP 路径（无 mock transport）也要计入调用数，否则报告恒为 0
        calls[0] += 1

    for t in plan["tasks"]:
        tid = t["id"]
        if only and tid not in only:
            continue
        r = recs.get(tid, {})
        if r.get("status") == "done" and not getattr(args, "force", False):
            skipped += 1
            continue
        if getattr(args, "retry_failed", False) and r.get("status") not in ("failed", "blocked"):
            skipped += 1
            continue
        unmet = [d for d in t["depends_on"] if recs.get(d, {}).get("status") != "done"]
        if unmet:
            recs[tid] = {"status": "blocked", "reason": "依赖未完成：" + "、".join(unmet), "at": today()}
            blocked += 1
            print("  [BLOCK] %-22s %s" % (tid, "、".join(unmet)))
            continue
        mid = role_models.get(t["role"], t["model"])
        if mid not in models:
            recs[tid] = {"status": "failed", "reason": "端点缺失：" + mid, "at": today()}
            failed += 1
            print("  [FAIL]  %-22s 端点未配置 %s" % (tid, mid))
            continue
        try:
            if dry:
                content, usage, elapsed = "", {}, 0.0
                out = write_product(project, t, "", True, mid)
            else:
                prompt = build_prompt(project, t, config, recs)
                content, usage, elapsed = call_api(
                    models[mid], ROLE_SYSTEM[t["role"]], prompt, t, config,
                    transport=wrapped_transport if transport else None,
                    on_call=bump_calls if transport is None else None)
                out = write_product(project, t, content, False, mid)
            recs[tid] = {
                "status": "done", "model": mid, "role": t["role"], "output": out,
                "usage": usage, "elapsed": round(elapsed, 2), "at": today(), "dry": dry,
            }
            done += 1
            print("  [%s] %-22s %-24s %s" % ("DRY" if dry else "OK", tid, mid, out))
        except Exception as e:
            recs[tid] = {"status": "failed", "model": mid, "reason": str(e)[:300], "at": today()}
            failed += 1
            print("  [FAIL]  %-22s %s" % (tid, str(e)[:120]))
        write_manifest(project, manifest)

    manifest["dispatch"]["batch"] = {"start": min(plan["episodes"]), "end": max(plan["episodes"]),
                                     "live": live, "last_run": today()}
    manifest["engines"].update({"%s(%s)" % (ROLE_LABEL[r], r): m for r, m in role_models.items()})
    write_manifest(project, manifest)
    write_cost_report(project, plan, recs, live)
    write_run_report(project, plan, recs, done, failed, blocked, skipped, live, time.time() - started, calls[0])
    print("\n汇总：done=%d failed=%d blocked=%d skipped=%d｜模式=%s｜API 调用=%d" %
          (done, failed, blocked, skipped, "LIVE" if live else "DRY-RUN", calls[0]))
    return 1 if failed else 0


def write_cost_report(project: Path, plan: dict, recs: dict, live: bool):
    config = load_config(project)
    prices = config.get("price_per_1k") or {}
    agg = {}
    for tid, r in recs.items():
        if r.get("status") != "done" or r.get("dry"):
            continue
        u = r.get("usage") or {}
        a = agg.setdefault(r.get("model", "?"), {"tasks": 0, "prompt": 0, "completion": 0, "total": 0})
        a["tasks"] += 1
        for k, key in (("prompt_tokens", "prompt"), ("completion_tokens", "completion"), ("total_tokens", "total")):
            a[key] += int(u.get(k) or 0)
    lines = ["# 调度成本对账（engine_dispatch）", "",
             "> 日期：%s｜模式：%s。**未配置单价时只报 token 用量，不编造金额**（CC-04）。" %
             (today(), "LIVE" if live else "DRY-RUN"),
             "> 单价在 `pipeline/%s` 的 `price_per_1k` 填 `{\"model_id\": {\"input\": x, \"output\": y}}`，单位 ¥/千 token。" % CONFIG_NAME,
             "> **统计口径**：本表只汇总成功返回 `usage` 的任务；空正文/超时/404 重试若已被网关计费，"
             "不会计入本表，实际账单可能略高于此。",
             "", "| 模型 | 任务数 | prompt | completion | total | 估算金额 |", "|---|---|---|---|---|---|"]
    grand = 0.0
    for mid, a in sorted(agg.items()):
        pr = prices.get(mid) or {}
        amt = (a["prompt"] / 1000.0 * float(pr.get("input", 0)) +
               a["completion"] / 1000.0 * float(pr.get("output", 0))) if pr else None
        grand += amt or 0.0
        lines.append("| %s | %d | %d | %d | %d | %s |" %
                     (mid, a["tasks"], a["prompt"], a["completion"], a["total"],
                      ("¥%.4f" % amt) if amt is not None else "未配置单价"))
    if prices:
        lines += ["", "合计（仅已配置单价部分）：¥%.4f" % grand]
    lines += ["", "## 成本自检（CC-04）", "",
              "- 规则文件未随每次调用整读：系统提示只注入精简硬约束 + 本集生成包（CC-01）。",
              "- 高 token 低判断的 S0–S3 只用骨架/批量档；定调档每卷仅 1 集、挑稿档只喂同集版本（CC-02）。",
              "- 默认每批 ≤10 集，卷级回顾产物只以 ≤10 行结论进入下一批（CC-03）。",
              "- 演练模式零调用、零费用；`--live` 才产生外部计费。"]
    (project / "pipeline" / COST_NAME).write_text("\n".join(x for x in lines if x is not None), encoding="utf-8")


def write_run_report(project: Path, plan: dict, recs: dict, done, failed, blocked, skipped, live, elapsed, calls):
    lines = ["# 调度执行报告（engine_dispatch）", "",
             "> 日期：%s｜模式：%s｜批次：第 %d–%d 集｜版本数：%d｜耗时：%.1fs" %
             (today(), "LIVE" if live else "DRY-RUN", min(plan["episodes"]), max(plan["episodes"]), plan["versions"], elapsed),
             "", "## 档位路由（MR-07）", "",
             "| 档位 | API model id | 任务数 |", "|---|---|---|"]
    for role, mid in plan["role_models"].items():
        lines.append("| %s（%s） | `%s` | %d |" %
                     (ROLE_LABEL[role], role, mid, sum(1 for t in plan["tasks"] if t["role"] == role)))
    lines += ["", "## 任务明细", "", "| 任务 | 档位 | 状态 | 产物/原因 |", "|---|---|---|---|"]
    for t in plan["tasks"]:
        r = recs.get(t["id"], {"status": "pending"})
        lines.append("| %s | %s | %s | %s |" %
                     (t["id"], t["stage"], r["status"], r.get("output") or r.get("reason", "")))
    lines += ["", "## 汇总", "",
              "- done=%d failed=%d blocked=%d skipped=%d；API 调用 %d 次。" % (done, failed, blocked, skipped, calls),
              "- 失败任务不写产物、不标 done；下游依赖自动标 blocked，重跑用 `--retry-failed`。",
              "- 演练产物带 `%s`，`verify` 会拒绝验收。" % DRY_MARK,
              "- 端点不可用时按 MR-05 由用户在 GUI 切内置模型重跑，并在交付注明「降级：会话默认模型」；**禁止因此放松闸门A**。"]
    (project / "pipeline" / REPORT_NAME).write_text("\n".join(lines), encoding="utf-8")


def cmd_status(project: Path, args):
    plan = jread(project / "pipeline" / PLAN_NAME)
    manifest = read_manifest(project)
    recs = manifest["dispatch"]["tasks"]
    if not plan:
        print("（无计划，先跑 plan）")
        return 0
    print("项目：%s｜Mode %s｜第 %s 集｜生成于 %s" %
          (project, plan["mode"], ",".join(map(str, plan["episodes"])), plan["generated"]))
    print("%-24s %-8s %-9s %-24s %s" % ("任务", "档位", "状态", "模型", "产物"))
    for t in plan["tasks"]:
        r = recs.get(t["id"], {"status": "pending"})
        print("%-24s %-8s %-9s %-24s %s" %
              (t["id"], t["stage"], r["status"], r.get("model", "-"), r.get("output", "-")))
    cur_ids = {t["id"] for t in plan["tasks"]}
    hist = sorted(set(recs) - cur_ids)
    if hist:
        print("\n历史任务（断点归档、不在当前计划）：%s" %
              "、".join("%s(%s)" % (h, recs[h]["status"]) for h in hist))
    cnt = {}
    for r in recs.values():
        cnt[r["status"]] = cnt.get(r["status"], 0) + 1
    print("\n状态统计：当前计划 %d 个｜含历史共 %d 个｜%s" %
          (len(cur_ids), len(recs), "、".join("%s=%d" % kv for kv in sorted(cnt.items())) or "（空）"))
    nxt = max(plan["episodes"]) + 1
    print("下一批建议：plan --episodes %d-%d" % (nxt, nxt + 9))
    return 0


def cmd_verify(project: Path, args):
    outputs = project / "outputs"
    drafts = sorted(outputs.glob("ep*_*.md")) if outputs.exists() else []
    dry_hits = [p.name for p in drafts if DRY_MARK in p.read_text(encoding="utf-8", errors="replace")]
    lines = ["# 调度后验收（engine_dispatch verify）", "", "> 日期：%s｜只验不改，不产出终稿。" % today(), ""]
    if dry_hits:
        lines += ["## 结论：拒绝验收", "",
                  "以下文件含 DRY-RUN 占位标记，**不是真实初稿**：", ""] + ["- " + x for x in dry_hits] + [
                  "", "先跑 `run --live` 生成真实稿件，再执行本命令。"]
        (project / "pipeline" / "verify-report.md").write_text("\n".join(lines), encoding="utf-8")
        print("[FAIL] 存在 %d 个 DRY-RUN 占位文件，拒绝验收" % len(dry_hits))
        return 1
    if not drafts:
        lines += ["## 结论：无稿可验", "", "outputs/ 下没有 ep*.md，跳过闸门A。先跑 `run --live`。", ""]
        (project / "pipeline" / "verify-report.md").write_text("\n".join(lines), encoding="utf-8")
        print("[FAIL] outputs/ 无初稿文件，跳过闸门A")
        return 1
    script = lambda n: str(ROOT / "scripts" / n)
    cmds = []
    anchors = next((str(project / "pipeline" / x) for x in ("02_人物小传与术语表.md", "02_人物小传.md")
                    if (project / "pipeline" / x).exists()), None)
    ga = [sys.executable, script("check_gate_a.py"), "--draft", str(outputs),
          "--out", str(outputs / "01_体检报告_脚本.md")]
    if anchors:
        ga += ["--anchors", anchors]
    cfg = project / "pipeline" / "gate_a_config.json"
    if cfg.exists():
        ga += ["--config", str(cfg)]
    src_dir = project / "pipeline" / "source"
    if src_dir.is_dir():
        ga += ["--source-dir", str(src_dir)]   # GA-10 逐字直搬比对
    cmds.append(("check_gate_a.py（GA-01~12，含 GA-12 形态门）", ga))
    if detect_mode(project) == "3":
        cmds.append(("source_outline.py check（GA-06~08）",
                     [sys.executable, script("source_outline.py"), "check", "--draft", str(outputs),
                      "--pipeline", str(project / "pipeline"),
                      "--out", str(outputs / "01_体检报告_纲源.md")]))
    rc_all = 0
    for label, cmd in cmds:
        try:
            p = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
            tail = (p.stdout or "").strip().splitlines()[-3:]
            verdict = "通过" if p.returncode == 0 else ("判杀（正常验收结果）" if p.returncode == 1 else "执行异常：输入数据不完整或脚本报错")
            rc_all |= p.returncode
            lines += ["## %s" % label, "", "退出码：%d｜%s" % (p.returncode, verdict), ""] + ["    " + x for x in tail] + [""]
            print("[%s] %s exit=%d %s" % ("OK" if p.returncode == 0 else ("KILL" if p.returncode == 1 else "ERR"),
                                          label, p.returncode, verdict))
        except Exception as e:
            rc_all |= 1
            lines += ["## %s" % label, "", "执行异常：%s" % e, ""]
            print("[FAIL] %s %s" % (label, e))
    lines += ["## 边界", "", "- 退出码 1 = 判杀（验收正常执行，稿件不合格）；退出码 ≥2 = 执行异常，先查 pipeline 数据完整性，不要当成「稿子写得差」。",
              "- 覆盖判定只认脚本输出，禁止模型自报（铁律 8）。",
              "- 本报告不修改任何稿件；修复需另起改写流程或用户确认。"]
    (project / "pipeline" / "verify-report.md").write_text("\n".join(lines), encoding="utf-8")
    print("报告：pipeline/verify-report.md｜总退出码 %d" % rc_all)
    return rc_all


def cmd_init_config(project: Path):
    p = project / "pipeline" / CONFIG_NAME
    if p.exists():
        print("[SKIP] 已存在 %s" % p)
        return 0
    jwrite(p, DEFAULT_CONFIG)
    print("[OK] 生成 %s" % p)
    return 0


def cmd_selftest(args):
    import tempfile
    ok = 0

    def check(cond, msg):
        nonlocal ok
        assert cond, "SELFTEST FAIL: " + msg
        ok += 1
        print("  [PASS] " + msg)

    with tempfile.TemporaryDirectory(prefix="dispatch_st_") as td:
        proj = Path(td) / "proj"
        (proj / "pipeline" / "packets").mkdir(parents=True)
        (proj / "outputs").mkdir(parents=True)
        fake_key = "sk-SELFTEST_SECRET_DO_NOT_LEAK_9527"
        mpath = Path(td) / "models.json"
        mids = list(dict.fromkeys(ROLE_MODEL.values()))
        jwrite(mpath, [{"id": m, "name": m, "vendor": "Custom", "url": "https://example.invalid/v1",
                        "apiKey": fake_key, "supportsToolCall": True, "supportsImages": False,
                        "supportsReasoning": False, "useCustomProtocol": False} for m in mids])
        models = load_models(mpath)
        def beat(n, i, text):
            return {"id": "EP%03d-B%02d" % (n, i), "seq": i, "text": text, "text_clean": text,
                    "must_keep": True, "anchors": ["宁清和"]}
        outline = {"episode_count": 2, "warnings": [], "episodes": [
            {"ep": 1, "title": "测试", "beats": [beat(1, 1, "落水获救"), beat(1, 2, "系统绑定")]},
            {"ep": 2, "title": "测试", "beats": [beat(2, 1, "攒物资下乡")]}]}
        jwrite(proj / "pipeline" / "outline.json", outline)
        jwrite(proj / "pipeline" / "source-index.json", {
            "generated": today(), "novel_title": "selftest", "sources": [],
            "chapter_pattern": "测试", "chapters": [
                {"id": "CH001", "no": 1, "title": "第1集", "start": 0, "end": 10, "chars": 10}],
            "name_candidates": [{"name": "宁清和", "count": 1}],
            "term_candidates": [], "total_chars": 10})
        for n in (1, 2):
            (proj / "pipeline" / "packets" / ("ep%03d.md" % n)).write_text(
                "# 第%d集 生成包\n\n- EP%03d-B01 测试事件｜锚点：宁清和\n" % (n, n), encoding="utf-8")
        check(detect_mode(proj) == "3", "Mode 3 自动识别（outline.json + packets）")

        a = argparse.Namespace(episodes="1-2", versions=2, total_episodes=10, allow_missing=False,
                               no_outline=False, dialogue_pass=False, min_tokens=0)
        plan = make_plan(proj, a, models)
        roles = {t["role"] for t in plan["tasks"]}
        check({"outline", "tone", "bulk", "pick"} <= roles, "计划覆盖骨架/定调/批量/挑稿四档")
        check(plan["role_models"]["bulk"] == "glm-5.3-flash", "MR-07 角色→端点映射正确")
        tone = [t for t in plan["tasks"] if t["role"] == "tone"]
        check(len(tone) == 1 and tone[0]["ep"] == 1, "定调档每卷仅 1 集（MR-03 附则 2）")
        pick = [t for t in plan["tasks"] if t["id"] == "pick-001"][0]
        check(all(d in [t["id"] for t in plan["tasks"]] for d in pick["depends_on"]), "挑稿任务依赖本集全部版本")
        check(all(t["max_tokens"] >= 2500 for t in plan["tasks"]), "所有任务 max_tokens 避开推理模型空正文阈值")
        jwrite(proj / "pipeline" / PLAN_NAME, plan)

        # 六档位全覆盖：10 集批次 + 台词精修
        proj3 = Path(td) / "proj3"
        (proj3 / "pipeline" / "packets").mkdir(parents=True)
        jwrite(proj3 / "pipeline" / "outline.json", {
            "episode_count": 10, "warnings": [],
            "episodes": [{"ep": n, "title": "测试", "beats": [beat(n, 1, "事件%d" % n)]}
                         for n in range(1, 11)]})
        for n in range(1, 11):
            (proj3 / "pipeline" / "packets" / ("ep%03d.md" % n)).write_text("# 第%d集\n" % n, encoding="utf-8")
        p3 = make_plan(proj3, argparse.Namespace(
            episodes="1-10", versions=2, total_episodes=10, allow_missing=False,
            no_outline=False, dialogue_pass=True, min_tokens=0), models)
        check({t["role"] for t in p3["tasks"]} == set(ROLE_MODEL),
              "六档位全覆盖：10 集 + 台词精修时 dialogue/review 均排入")
        check(any(t["id"].startswith("review-") for t in p3["tasks"]), "CC-03 满 10 集自动排卷级回顾")
        check(len([t for t in p3["tasks"] if t["role"] == "tone"]) == 1, "10 集批次定调档仍仅 1 集")

        # 缺端点应被拦截
        try:
            make_plan(proj, a, {"claude-opus-5-5": models["claude-opus-5-5"]})
            raise AssertionError("缺端点未拦截")
        except SystemExit:
            check(True, "端点未配齐时 plan 明确报错，不静默降级")
        a2 = argparse.Namespace(**vars(a)); a2.allow_missing = True
        check(len(make_plan(proj, a2, {})["tasks"]) > 0, "--allow-missing 可生成待补计划")

        # 演练：零调用、零凭据、显式占位
        r = argparse.Namespace(live=False, only=None, force=False, retry_failed=False)
        rc = run_project(proj, r, models)
        check(rc == 0, "dry-run 全任务完成且退出码 0")
        mani = read_manifest(proj)
        check(all(v["status"] == "done" for v in mani["dispatch"]["tasks"].values()), "dry-run 后 manifest 全部 done")
        check(all(v.get("dry") for v in mani["dispatch"]["tasks"].values()), "manifest 明确标注 dry，不冒充真稿")
        prod = (proj / "outputs" / "ep001_A_v1.md").read_text(encoding="utf-8")
        check(DRY_MARK in prod, "演练产物带显式占位标记")
        check("引擎：" in prod and "版本：" in prod, "产物头符合 MR-06（版本/引擎/模块/日期）")
        leaked = [str(p) for p in proj.rglob("*") if p.is_file() and fake_key in p.read_text(encoding="utf-8", errors="replace")]
        check(not leaked, "apiKey 未出现在任何产物（凭据零外泄）")

        # verify 拒绝演练产物
        check(cmd_verify(proj, argparse.Namespace()) == 1, "verify 拒绝 DRY-RUN 稿件进入闸门A")

        # 断点续跑：done 的任务不再重跑
        calls = [0]
        seen = []

        def fake(body):
            calls[0] += 1
            seen.append(body)
            return "1-1 日内、测试\n△动作。\n甲：测试台词。", {"prompt_tokens": 100, "completion_tokens": 200, "total_tokens": 300}, 0.1

        # 全量重跑（force）走 mock live，验证真实链路 + 成本统计
        r3 = argparse.Namespace(live=True, only=None, force=True, retry_failed=False)
        rc = run_project(proj, r3, models, transport=fake)
        check(rc == 0 and calls[0] == len(plan["tasks"]), "mock live 全链路执行，每个任务调用一次 API")
        prod2 = (proj / "outputs" / "ep001_A_v1.md").read_text(encoding="utf-8")
        check(DRY_MARK not in prod2 and "测试台词" in prod2, "live 产物为真实正文且无占位标记")
        check(DEFAULT_CONFIG["disable_thinking"] is True, "默认关闭推理型档位思考（2026-11-04 实跑口径）")
        glm_b = [b for b in seen if b["model"].startswith("glm-")]
        hy_b = [b for b in seen if b["model"].startswith("hy")]
        check(bool(glm_b) and all(b.get("enable_thinking") is False for b in glm_b),
              "GLM 任务默认带 enable_thinking=false")
        check(bool(hy_b) and all(b.get("thinking", {}).get("type") == "disabled" for b in hy_b),
              "Hy4 任务默认带 thinking.type=disabled")
        check(strip_product_head("> 版本：x · 引擎：y\n\n第1集\n1-1 日外 河边\n") ==
              "第1集\n1-1 日外 河边", "下游注入前剥离 MR-06 产物头")
        pick_prompts = [b["messages"][1]["content"] for b in seen
                        if "### 待评版本" in b["messages"][1]["content"]]
        check(bool(pick_prompts) and all("> 版本：" not in x for x in pick_prompts),
              "挑稿档输入不含产物头，避免把版本标注误判为稿件硬伤")
        cost = (proj / "pipeline" / COST_NAME).read_text(encoding="utf-8")
        check("未配置单价" in cost and "不编造金额" in cost, "未配单价时只报 token，不编造金额")
        r4 = argparse.Namespace(live=True, only=None, force=False, retry_failed=False)
        before = calls[0]
        run_project(proj, r4, models, transport=fake)
        check(calls[0] == before, "断点续跑跳过全部 done，不重复计费")
        vrc = cmd_verify(proj, argparse.Namespace())
        vrep = (proj / "pipeline" / "verify-report.md").read_text(encoding="utf-8")
        check(vrc in (0, 1) and "check_gate_a.py" in vrep and "source_outline.py check" in vrep
              and "执行异常：" not in vrep and "判杀（正常验收结果）" in vrep,
              "live 产物可进入双脚本闸门A，且判杀与执行异常被明确区分")

        # 失败不写产物 + 下游 blocked
        proj2 = Path(td) / "proj2"
        (proj2 / "pipeline" / "packets").mkdir(parents=True)
        (proj2 / "outputs").mkdir(parents=True)
        jwrite(proj2 / "pipeline" / "outline.json", outline)
        for n in (1, 2):
            (proj2 / "pipeline" / "packets" / ("ep%03d.md" % n)).write_text("# 第%d集\n" % n, encoding="utf-8")
        plan2 = make_plan(proj2, argparse.Namespace(episodes="1-2", versions=2, total_episodes=10,
                                                    allow_missing=False, no_outline=True,
                                                    dialogue_pass=False, min_tokens=0), models)
        jwrite(proj2 / "pipeline" / PLAN_NAME, plan2)
        first = plan2["tasks"][0]["id"]

        def boom(body):
            raise RuntimeError("模拟 503")

        run_project(proj2, argparse.Namespace(live=True, only=None, force=False, retry_failed=False), models, transport=boom)
        m2 = read_manifest(proj2)["dispatch"]["tasks"]
        check(m2[first]["status"] == "failed", "调用失败标 failed、不标 done")
        check(not (proj2 / "outputs" / "ep001_A_v1.md").exists(), "失败任务不写产物")
        check(any(v["status"] == "blocked" for v in m2.values()), "依赖失败任务的下游自动 blocked")

        # init-config 模板
        cmd_init_config(proj2)
        c = jread(proj2 / "pipeline" / CONFIG_NAME, {})
        check("price_per_1k" in c and "role_models" in c, "init-config 生成可填单价与端点覆盖的模板")
        check(c["disable_thinking"] is True, "init-config 模板默认关思考")

        # 实跑暴露的两类故障：空正文吃光预算、聚合网关偶发 404
        import io
        seen2, n2 = [], [0]

        def flaky(body):
            seen2.append(body)
            n2[0] += 1
            if n2[0] == 1:
                return "", {}, 0.1
            return "恢复正文", {"total_tokens": 12}, 0.1

        cfg2 = dict(DEFAULT_CONFIG)
        cfg2["disable_thinking"] = False
        got, _, _ = call_api({"id": "glm-5.3-flash"}, "s", "u", {"max_tokens": 1000}, cfg2,
                             transport=flaky, sleep_fn=lambda s: None)
        check(got == "恢复正文" and len(seen2) == 2
              and seen2[1].get("enable_thinking") is False
              and seen2[1]["max_tokens"] > seen2[0]["max_tokens"],
              "空正文后自动关思考并抬高预算重试，不原样白烧三次")

        n3 = [0]

        def gateway_404(body):
            n3[0] += 1
            if n3[0] == 1:
                raise urllib.error.HTTPError("http://x", 404, "Not Found", {},
                                            io.BytesIO(b'{"error":"Invalid URL (GET /v1/chat/completions)"}'))
            return "恢复正常", {"total_tokens": 5}, 0.1

        got3, _, _ = call_api({"id": "glm-5.3-flash"}, "s", "u", {"max_tokens": 1000}, cfg2,
                              transport=gateway_404, sleep_fn=lambda s: None)
        check(got3 == "恢复正常" and n3[0] == 2, "聚合网关偶发 404（Invalid URL）纳入可重试并恢复")

        n4 = [0]

        def timed_out(body):
            n4[0] += 1
            if n4[0] == 1:
                raise TimeoutError("The read operation timed out")
            return "超时后恢复", {"total_tokens": 7}, 0.1

        got4, _, _ = call_api({"id": "kimi-k3.1-pro"}, "s", "u", {"max_tokens": 1000}, cfg2,
                              transport=timed_out, sleep_fn=lambda s: None)
        check(got4 == "超时后恢复" and n4[0] == 2, "长文本读超时纳入可重试异常并恢复")
        check(DEFAULT_CONFIG["timeout"] >= 180, "默认读超时给足长文本生成")

    print("\n[PASS] selftest 全部通过（%d 项）" % ok)
    return 0


def main():
    ap = argparse.ArgumentParser(description="六档位自动调度引擎（MR-08）")
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--models", default=str(DEFAULT_MODELS), help="models.json 路径")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("plan", parents=[common], help="按 MR-03/07 生成逐档任务清单")
    p.add_argument("--project", required=True)
    p.add_argument("--episodes", default="", help="集数范围，如 1-10；默认首批 1-10")
    p.add_argument("--total-episodes", type=int, default=10, help="Mode 1 的总集数")
    p.add_argument("--versions", type=int, default=0, help="每集版本数 1-3，默认取配置")
    p.add_argument("--dialogue-pass", action="store_true", help="追加台词精修档（v2）")
    p.add_argument("--no-outline", action="store_true", help="跳过 S1 骨架任务")
    p.add_argument("--min-tokens", type=int, default=0, help="统一抬高最小 max_tokens")
    p.add_argument("--allow-missing", action="store_true", help="端点未配齐也生成待补计划")

    r = sub.add_parser("run", parents=[common], help="执行计划（默认演练；--live 才真实计费）")
    r.add_argument("--project", required=True)
    r.add_argument("--live", action="store_true", help="真实调用外部端点（产生 DMXAPI 计费）")
    r.add_argument("--only", help="只跑指定任务 id，逗号分隔")
    r.add_argument("--force", action="store_true", help="忽略 done 记录，全部重跑")
    r.add_argument("--retry-failed", action="store_true", help="只重跑 failed 任务")

    s = sub.add_parser("status", parents=[common], help="查看任务进度与 token 汇总")
    s.add_argument("--project", required=True)

    v = sub.add_parser("verify", parents=[common], help="只验不改：拒绝演练稿 + 跑闸门A与覆盖验收")
    v.add_argument("--project", required=True)

    i = sub.add_parser("init-config", parents=[common], help="生成 dispatch-config.json 模板")
    i.add_argument("dir")

    t = sub.add_parser("selftest", parents=[common], help="离线自检（零 API 调用）")

    args = ap.parse_args()
    if args.cmd == "selftest":
        return cmd_selftest(args)
    if args.cmd == "init-config":
        return cmd_init_config(Path(args.dir))
    project = Path(args.project).resolve()
    if not project.exists():
        raise SystemExit("[FAIL] 项目目录不存在：%s" % project)
    if args.cmd == "plan":
        plan = make_plan(project, args, load_models(Path(args.models)))
        jwrite(project / "pipeline" / PLAN_NAME, plan)
        m = read_manifest(project)
        m["dispatch"]["plan"] = "pipeline/" + PLAN_NAME
        write_manifest(project, m)
        print("[OK] 生成 %d 个任务（Mode %s，第 %s 集，%d 版）→ pipeline/%s" %
              (len(plan["tasks"]), plan["mode"], ",".join(map(str, plan["episodes"])),
               plan["versions"], PLAN_NAME))
        for role, mid in plan["role_models"].items():
            print("  %-8s → %s" % (ROLE_LABEL[role], mid))
        print("下一步：run --project <dir>（演练）｜run --project <dir> --live（真实调用，会计费）")
        return 0
    if args.cmd == "run":
        return run_project(project, args, load_models(Path(args.models)))
    if args.cmd == "status":
        return cmd_status(project, args)
    if args.cmd == "verify":
        return cmd_verify(project, args)
    return 1


if __name__ == "__main__":
    sys.exit(main())
