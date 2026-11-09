#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""闸门A 脚本化硬指标核对（GA-01~12）。

动机：写作极限测试与挑稿测试均证明「轮次/字数靠模型自己数不可靠」，
且闸门A 缺「人设逐场核对」「系统条款不新增」两项。本脚本把可计算的判断
从模型手里收回来，只输出可核查证据，不写好坏评价。

GA-09~11（2026-11-06 补，对应 modules/process/dialogue-pass.md）：
对白二次调整此前没有独立工序，也没有机检项。补三项——单句 8-15 字区间
（按占比判，不逐句误杀）、旁白与原文连续重合、A/B 同一旁白逐字相同。
GA-10/11 与 scripts/adapt_gate.py 的 G9 共用 `_text_util.py`，口径必须一致。

GA-12（2026-11-06 第10-12集回归补）：12 份 DRY 占位稿（0 场、0 句对白）
被两个验收入口全判「验收通过」——门只查「有没有违规」，不查「有没有戏」。
补稿件形态门：演练占位标记／人物对白句为 0／场次标记为 0 任一命中 → 不予验收。
只量形态，不设字数下限、不判语义、不判质量；与内容违规分开陈述。
`_text_util.draft_shape()` 是唯一口径，check_adapt.py 必须共用。

用法：
  python check_gate_a.py --draft outputs/ --anchors pipeline/02_人物小传与术语表.md \
      --config pipeline/gate_a_config.json --source pipeline/source/ep001.txt \
      --out outputs/01_体检报告_脚本.md
  python check_gate_a.py --init-config pipeline/gate_a_config.json
  python check_gate_a.py --selftest

退出码：0=无 FAIL；1=有 FAIL（该版本判杀）；2=输入错误。
纯标准库，无第三方依赖。
"""
import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _text_util import (body_lines, cjk_only, cross_file_narration,
                        dialogue_sentences, draft_shape, iter_draft_files,
                        longest_common, sentence_len)

EMOTION_WORDS = [
    "愤怒", "震惊", "害怕", "紧张", "难过", "开心", "生气", "恐惧", "激动",
    "绝望", "欣喜", "悲伤", "焦虑", "羞愧", "屈辱", "得意", "失落", "感动",
    "惊讶", "恐慌", "崩溃", "狂喜", "嫉妒", "委屈", "尴尬", "释然",
]
AI_CLICHE = ["瞳孔骤缩", "眼底", "冷笑", "脸色一变", "嘴角勾起", "眼神一凛", "心头一震"]
SPEAKER_RE = re.compile(r"^\s*[-•*#> ]*(?P<name>[^：:「」\"']{1,16})[：:]\s*(?P<body>.+)$")
SYSTEM_RE = re.compile(r"(?:系统|金手指)[^。！？\n]{0,24}(?:自动|新增|升级|结算|每月|每天|规则|条款|到账|返现|奖励)|(?:自动结算|每月十块|仓储费|零花钱按时|凭空(?:出现|落下))")
CJK = re.compile(r"[\u4e00-\u9fff]")

# GA-04 顺口候选：只报数不判杀（拼音级绕口检测需注音库，本脚本不做）
AWKWARD_PUNCT = re.compile(r"[，。！？、；：]{2,}")
PAREN_INSERT = re.compile(r"[（(][^）)]*[）)]")


def norm(s):
    return re.sub(r"[\s，。！？、…—「」\"'（）()【】\[\]:：;,.!?\-–/／]+", "", s or "")


def edit_distance_one(a, b):
    """等长且仅差一个字（人名混用最常见形态，如 宁清河/宁清禾）。"""
    if len(a) != len(b) or a == b:
        return False
    return sum(x != y for x, y in zip(a, b)) == 1


def load_config(path):
    if not path or not Path(path).exists():
        return {}
    return json.loads(Path(path).read_text(encoding="utf-8"))


def draft_files(draft):
    """只扫稿件；报告/索引/登记表不得进入验收（口径见 _text_util.is_draft_candidate）。"""
    return iter_draft_files(draft)


def load_sources(source=None, source_dir=None):
    """原文切片：单文件全部共用；目录按文件名 epNNN 对应集号。"""
    import io
    out = {}
    if source and Path(source).is_file():
        out[None] = io.open(source, encoding="utf-8", errors="ignore").read()
    if source_dir and Path(source_dir).is_dir():
        for p in sorted(Path(source_dir).glob("*")):
            if p.is_file() and p.suffix.lower() in (".txt", ".md"):
                m = re.search(r"ep(\d{3})", p.name, re.I)
                out[int(m.group(1)) if m else None] = io.open(
                    p, encoding="utf-8", errors="ignore").read()
    return out


def source_for(path, sources):
    m = re.search(r"ep(\d{3})", Path(path).name, re.I)
    ep = int(m.group(1)) if m else None
    return sources.get(ep, sources.get(None, ""))


def check_one(path, cfg, anchors_text, cross=None, src_text=""):
    """返回 (findings, stats)。findings: [{code, level, line, evidence, note}]"""
    text = path.read_text(encoding="utf-8")
    # 正文口径：文末改编登记会逐字引用被删原句，扫进去会自污染（DP-08）。
    # 无场标记的文件返回全文，保持向后兼容。
    lines = body_lines(text)
    findings = []

    # ---- GA-01 轮次 / 字数：数值一律由脚本给出，不让模型报数 ----
    turns = []
    for i, line in enumerate(lines, 1):
        m = SPEAKER_RE.match(line)
        if m and len(norm(m.group("name"))) <= 12:
            turns.append((i, m.group("name").strip()))
    sents = dialogue_sentences(lines)
    lens = [sentence_len(s) for _, _, s in sents]
    dmin = cfg.get("dialogue_chars_min", 8)
    dmax = cfg.get("dialogue_chars_max", 15)
    dratio = cfg.get("dialogue_max_ratio", 0.20)
    n_short = sum(1 for n in lens if n < dmin)
    n_long = sum(1 for n in lens if n > dmax)
    outside = n_short + n_long
    # 判杀只看「超长句占比」：<8 字是短剧合法节奏句，按 DP-02 登记例外，
    # 计入分子会让 8-15 字这条口径变成「挂上即全杀」的错尺子。
    long_ratio = n_long / len(lens) if lens else 0.0
    stats = {
        "file": str(path),
        "turns": len(turns),
        "cjk_chars": len(cjk_only("".join(lines))),
        "lines": len(lines),
        "dialogue_sentences": len(lens),
        "dialogue_short": n_short,
        "dialogue_long": n_long,
        "dialogue_outside": outside,
        "dialogue_outside_ratio": round(outside / len(lens), 3) if lens else 0.0,
        "dialogue_long_ratio": round(long_ratio, 3),
        "dialogue_max_chars": max(lens) if lens else 0,
    }
    tmin, tmax = cfg.get("turns_min"), cfg.get("turns_max")
    if tmin is not None and tmax is not None and not (tmin <= len(turns) <= tmax):
        findings.append({"code": "GA-01", "level": "FAIL", "line": 0,
                         "evidence": "台词轮次=%d，允许 %d-%d" % (len(turns), tmin, tmax),
                         "note": "脚本计数，禁止模型自报"})
    seg_min, seg_max = cfg.get("segment_chars_min"), cfg.get("segment_chars_max")
    if seg_min is not None and seg_max is not None:
        blocks = [b for b in re.split(r"\n\s*\n", "\n".join(lines)) if norm(b)]
        for b in blocks:
            n = len(CJK.findall(b))
            if not (seg_min <= n <= seg_max) and n > 0:
                findings.append({"code": "GA-01", "level": "FAIL", "line": 0,
                                 "evidence": "段落汉字数=%d，允许 %d-%d｜%s" % (n, seg_min, seg_max, norm(b)[:24]),
                                 "note": "字数硬指标由脚本核对"})
                break

    # ---- GA-02 人设逐场核对：等长一字之差的人名疑似混用 ----
    names = Counter(norm(n) for _, n in turns)
    name_list = list(names)
    # 项目档案确认「等长一字之差但确为两个不同角色」时写进 name_whitelist，
    # 不再误杀（2026-11-04 实跑：原文中「青年甲」「青年乙」同时出现）。
    whitelist = set(norm(x) for x in cfg.get("name_whitelist", []) if x)
    for a_i, a in enumerate(name_list):
        for b in name_list[a_i + 1:]:
            if edit_distance_one(a, b):
                occ = [i for i, n in turns if norm(n) == b]
                if a in whitelist and b in whitelist:
                    findings.append({"code": "GA-02", "level": "INFO", "line": occ[0] if occ else 0,
                                     "evidence": "等长一字之差但均在白名单（不同角色）：%s / %s" % (a, b),
                                     "note": "已由原文/人物档案确认，不判杀"})
                    continue
                findings.append({"code": "GA-02", "level": "FAIL", "line": occ[0] if occ else 0,
                                 "evidence": "人名疑似混用：%s / %s（首见行 %s）" % (a, b, occ[0] if occ else "-"),
                                 "note": "逐场说话人核对；确认是不同角色则写入 config.name_whitelist"})
    fixed = cfg.get("fixed_traits", [])
    for trait in fixed:
        if trait and trait not in "\n".join(lines) and cfg.get("require_all_traits", False):
            findings.append({"code": "GA-02", "level": "FAIL", "line": 0,
                             "evidence": "固定特征未出现：%s" % trait,
                             "note": "对照 02_人物小传 ≥5 特征"})
    for alias, canonical in cfg.get("name_aliases", {}).items():
        if alias in "\n".join(lines):
            findings.append({"code": "GA-02", "level": "FAIL", "line": 0,
                             "evidence": "旧名/异写 %s 应统一为 %s" % (alias, canonical),
                             "note": "DR-02 / 术语表"})

    # ---- GA-03 系统条款不新增 ----
    allowed = cfg.get("system_rules", [])
    sys_hits = []
    for i, line in enumerate(lines, 1):
        if SYSTEM_RE.search(line):
            sys_hits.append((i, line.strip()))
    for i, line in sys_hits:
        if allowed:
            if not any(a and a in line for a in allowed):
                findings.append({"code": "GA-03", "level": "FAIL", "line": i,
                                 "evidence": line[:80], "note": "疑似新增系统条款，未命中既定规则白名单"})
        else:
            findings.append({"code": "GA-03", "level": "INFO", "line": i,
                             "evidence": line[:80],
                             "note": "未提供 config.system_rules，仅列出行号供人工逐条核对（不判杀）"})
    stats["system_lines"] = len(sys_hits)

    # ---- GA-04 情绪名称词 / AI 套话 ----
    for i, line in enumerate(lines, 1):
        s = line.strip()
        hit = [w for w in EMOTION_WORDS if w in s]
        cliche = [w for w in AI_CLICHE if w in s]
        has_action = bool(re.search(r"[「」\"']|[（(]|→|抬|放|停|走|抓|递|翻|按|转身|伸手|靠|坐|站", s))
        if hit and not has_action:
            findings.append({"code": "GA-04", "level": "FAIL", "line": i,
                             "evidence": s[:80], "note": "纯情绪名称词无行为支撑（CR-17）"})
        if cliche:
            findings.append({"code": "GA-04", "level": "FAIL", "line": i,
                             "evidence": s[:80], "note": "AI 套话，须替换为角色专属动作"})

    # ---- GA-05 术语零变体 ----
    for bad, canonical in cfg.get("term_aliases", {}).items():
        for i, line in enumerate(lines, 1):
            if bad in line:
                findings.append({"code": "GA-05", "level": "FAIL", "line": i,
                                 "evidence": "%s → 应统一为 %s｜%s" % (bad, canonical, line.strip()[:60]),
                                 "note": "DR-04 术语表零变体"})
                break

    # ---- GA-09 单句 8-15 字（按占比判；配置未启用时只报数） ----
    if cfg.get("enforce_dialogue", False) and lens:
        if long_ratio > dratio:
            findings.append({"code": "GA-09", "level": "FAIL", "line": 0,
                             "evidence": "对白句 %d｜> %d 字的超长句 %d 句（%.0f%% > %.0f%%）｜"
                                         "< %d 字的短节奏句 %d 句（按 DP-02 登记例外，不计入判杀）｜最长 %d 字"
                                         % (len(lens), dmax, n_long, long_ratio * 100,
                                            dratio * 100, dmin, n_short, max(lens)),
                             "note": "DP-02：超长句拆成两句说，不删信息、不改语义、不新增台词；"
                                     "短节奏句合法，只登记不算违规"})
        for ln, who, s in sents:
            n = sentence_len(s)
            if n > 25:
                findings.append({"code": "GA-09", "level": "INFO", "line": ln,
                                 "evidence": "%s：%d 字｜%s" % (who, n, s[:40]),
                                 "note": "DP-04 顺口候选：超长句需人工念一遍（仅提示）"})
    for ln, who, s in sents:
        if AWKWARD_PUNCT.search(s) or len(PAREN_INSERT.findall(s)) >= 2:
            findings.append({"code": "GA-09", "level": "INFO", "line": ln,
                             "evidence": "%s｜%s" % (who, s[:40]),
                             "note": "DP-04 顺口候选：连续标点或多组括号插入（仅提示）"})

    # ---- GA-10 旁白与原文连续重合（叙述腔直搬） ----
    lift_min = cfg.get("lift_min", 8)
    narr_lines = [(i, l.strip()) for i, l in enumerate(lines, 1)
                  if l.strip().startswith("旁白：")]
    stats["narration_lines"] = len(narr_lines)
    if src_text:
        src_cjk = cjk_only(src_text)
        for i, line in narr_lines:
            q = cjk_only(line.split("：", 1)[-1])
            if len(q) < lift_min:
                continue
            common = longest_common(q, src_cjk)
            if common >= lift_min:
                findings.append({"code": "GA-10", "level": "FAIL", "line": i,
                                 "evidence": "与原文连续重合 %d 字｜%s" % (common, line[:60]),
                                 "note": "DP-06：概述句／叙述者评价须转一场戏、一次剪切或直接删，"
                                         "禁止逐字念成旁白"})
    elif narr_lines:
        findings.append({"code": "GA-10", "level": "INFO", "line": 0,
                         "evidence": "本稿有 %d 行旁白，但未提供 --source 原文切片" % len(narr_lines),
                         "note": "DP-06 逐字直搬检查已跳过，需人工核或补 --source（不判杀）"})

    # ---- GA-11 A/B 同一旁白逐字相同 ----
    for txt, fs in (cross or {}).items():
        if Path(path).name in fs:
            findings.append({"code": "GA-11", "level": "FAIL", "line": 0,
                             "evidence": "同一旁白出现在 %s｜%s"
                                         % ("、".join(sorted(set(fs))), txt[:50]),
                             "note": "DP-07：事实层一致靠共用事实台账，不靠共用解说词"})

    # ---- GA-12 稿件形态门：只查「有没有戏」，不查「有没有违规」 ----
    # 独立于 enforce_dialogue：空稿/占位稿无论是否挂载 DP 模块都不予验收。
    shape = draft_shape(text)
    stats["shape"] = shape
    stats["scenes"] = shape["scenes"]
    if not cfg.get("skip_shape_gate", False) and not shape["ok"]:
        findings.append({"code": "GA-12", "level": "FAIL", "line": 0,
                         "evidence": "形态不达标：%s｜场次标记 %d｜人物对白句 %d｜"
                                     "演练占位标记 %s（不设字数下限）"
                                     % ("；".join(shape["issues"]), shape["scenes"],
                                        shape["dialogue_sentences"],
                                        "是" if shape["dry_mark"] else "否"),
                         "note": "只判形态不判质量：占位/空稿不得进入验收、不得写「验收通过」；"
                                 "补正文后复跑。本项与内容违规分开陈述，不替 GA-01~11 判好坏。"
                                 "确需兼容存量格式时设 config.skip_shape_gate=true（只报数不判杀）"})

    # ---- 锚点文件存在性（不解析语义，只做证据绑定） ----
    if anchors_text is not None and not cfg.get("skip_anchor_check", False):
        if len(CJK.findall(anchors_text)) < 30:
            findings.append({"code": "GA-02", "level": "FAIL", "line": 0,
                             "evidence": "锚点文件内容不足 30 汉字", "note": "人设逐场核对缺证据源"})

    return findings, stats


def write_report(out, results):
    lines = ["# 闸门A 脚本化硬指标报告（GA-01~12）", "",
             "> 由 `scripts/check_gate_a.py` 生成。数值为脚本计数，禁止模型自报。",
             "> 正文口径：首场 → 文末登记块之前；登记块引用被删原句不计入（DP-08）。",
             "> GA-12 是**稿件形态门**（只判有没有戏，不判好坏、不设字数下限）；"
             "不达标写「不予验收」，不等于内容违规。", ""]
    total_fail = total_info = 0
    for r in results:
        s = r["stats"]
        lines += ["## %s" % Path(s["file"]).name, "",
                  "| 指标 | 数值 |", "|---|---|",
                  "| 台词轮次 | %d |" % s["turns"],
                  "| 正文汉字数 | %d |" % s["cjk_chars"],
                  "| 正文行数 | %d |" % s["lines"],
                  "| 系统相关行 | %d |" % s["system_lines"],
                  "| 对白句数 | %d |" % s["dialogue_sentences"],
                  "| 短节奏句（<8 字，登记例外） | %d |" % s["dialogue_short"],
                  "| 超长句（>15 字，判杀分子） | %d ／ %.0f%% |" %
                  (s["dialogue_long"], s["dialogue_long_ratio"] * 100),
                  "| 8-15 字区间外合计 | %d ／ %.0f%% |" %
                  (s["dialogue_outside"], s["dialogue_outside_ratio"] * 100),
                  "| 最长单句汉字数 | %d |" % s["dialogue_max_chars"],
                  "| 旁白行数 | %d |" % s["narration_lines"],
                  "| 稿件形态（GA-12） | %s |" %
                  ("达标" if s.get("shape", {}).get("ok", True) else
                   "不达标：" + "；".join(s.get("shape", {}).get("issues", []))),
                  "| 场次标记数（宽松识别） | %d |" % s.get("scenes", 0), ""]
        if not r["findings"]:
            lines += ["无告警。", ""]
        for f in r["findings"]:
            total_fail += f["level"] == "FAIL"
            total_info += f["level"] == "INFO"
            lines += ["- **%s %s**｜行 %s｜%s｜%s" %
                      (f["level"], f["code"], f["line"], f["evidence"], f["note"])]
        lines.append("")
    lines += ["---", "", "**合计**：FAIL %d ／ INFO %d ／ 文件 %d" %
              (total_fail, total_info, len(results)),
              "", "任一 FAIL → 该版本判杀并记死因；INFO 需人工确认后写入体检报告。",
              "",               "GA-09~11 挂载 `modules/process/dialogue-pass.md` 时为硬门；",
              "未挂载时 `enforce_dialogue=false` 只报数，避免误杀存量稿。",
              "GA-12 默认启用（与模块挂载无关）；`skip_shape_gate=true` 时只报数不判杀。", ""]
    Path(out).write_text("\n".join(lines), encoding="utf-8")
    return total_fail


def selftest():
    sample = Path("_ga_selftest.md")
    sample.write_text(
        "宁清和：报尺寸。\n宁清禾：我那件蓝衬衫呢。\n"
        "他很愤怒。\n系统每月十块零花按时到账，自动结算。\n"
        "她瞳孔骤缩，眼底闪过一丝冷笑。\n", encoding="utf-8")
    cfg = {"turns_min": 1, "turns_max": 3,
           "system_rules": ["仓储费一毛一天"],
           "term_aliases": {"孙倩": "孙红梅"}}
    anchor = ("人物小传锚点档案内容：宁清和、谢知予、张公安、青年甲、青年乙，"
              "吹牛暴富系统五米内触发，国营饭店手表下乡，中文内容用于通过锚点检查长度校验")
    try:
        f, s = check_one(sample, cfg, anchor)
        codes = {x["code"] for x in f if x["level"] == "FAIL"}
        assert s["turns"] == 2, s
        assert "GA-02" in codes, codes
        assert "GA-03" in codes, codes
        assert "GA-04" in codes, codes
        print("[PASS] selftest：轮次计数 / 人名混用 / 新增条款 / 情绪词 四项均检出")
        f2, _ = check_one(sample, dict(cfg, name_whitelist=["宁清和", "宁清禾"]), anchor)
        assert not any(x["code"] == "GA-02" and x["level"] == "FAIL"
                       and "人名疑似混用" in x["evidence"] for x in f2), f2
        assert not any("锚点文件内容不足" in x["evidence"] for x in f), f
        assert any(x["code"] == "GA-02" and x["level"] == "INFO" for x in f2), f2
        print("[PASS] selftest：name_whitelist 确认的双角色降级 INFO、不再误杀")
        d = Path("_ga_selftest_dir")
        d.mkdir(exist_ok=True)
        (d / "ep001_A_v1.md").write_text("宁清和：测试。", encoding="utf-8")
        (d / "01_体检报告.md").write_text("FAIL GA-04", encoding="utf-8")
        (d / "纲源索引.md").write_text("x", encoding="utf-8")
        (d / "闸门A.md").write_text(
            "# 闸门A 脚本化硬指标报告\n\n> 由 `scripts/check_gate_a.py` 生成\n\n"
            "**结论：未通过**\n", encoding="utf-8")
        (d / "03_覆盖验收_E10-12.md").write_text("# 按纲改编覆盖验收报告\n", encoding="utf-8")
        assert [x.name for x in draft_files(d)] == ["ep001_A_v1.md"], list(draft_files(d))
        print("[PASS] selftest：报告/索引/无编号报告名/03_ 前缀验收报告均不进入初稿扫描")

        # ---- GA-09~11 ----
        orig = "李承泽当天就把领导辞了，再给老板一个滚蛋的机会。"
        ga = d / "ep001_A_v1.md"
        gb = d / "ep001_B_v1.md"
        narr = "旁白：「当天他把领导辞了，再给老板一个滚蛋的机会。」"
        ga.write_text("【场1｜办公室】\n宁清和：你在教我做事。\n" + narr +
                      "\n---\n## 改编登记\n原旁白：当天他把领导辞了…\n", encoding="utf-8")
        gb.write_text("【场1｜办公室】\n宁清和：我不伺候了。\n" + narr + "\n", encoding="utf-8")
        cross = cross_file_narration([str(ga), str(gb)])
        cfg2 = {"enforce_dialogue": True, "dialogue_chars_min": 8,
                "dialogue_chars_max": 15, "dialogue_max_ratio": 0.20}
        fa, sa = check_one(ga, cfg2, anchor, cross, orig)
        ca = {x["code"] for x in fa}
        assert "GA-10" in ca, fa                      # 逐字直搬
        assert "GA-11" in ca, fa                      # A/B 同旁白
        assert sa["narration_lines"] == 1, sa         # 登记块引用不计入正文
        assert all("登记" not in x["evidence"] for x in fa if x["code"] == "GA-10"), fa
        # 删旁白 → GA-10/11 零命中
        clean = d / "ep001_C_v1.md"
        clean.write_text("【场1｜办公室】\n宁清和：你在教我做事。\n（工牌往桌上一拍。）\n",
                         encoding="utf-8")
        fc, _ = check_one(clean, cfg2, anchor, {}, orig)
        assert not any(x["code"] in ("GA-10", "GA-11") for x in fc), fc
        # GA-09 占比判：大量超长句才判杀，短节奏句不误杀
        longs = "\n".join("宁清和：%s。" % ("这事情说起来话就很长了而且还得从头讲一遍" * 1)
                          for _ in range(5))
        gl = d / "ep001_D_v1.md"
        gl.write_text("【场1｜办公室】\n" + longs + "\n", encoding="utf-8")
        fl, sl = check_one(gl, cfg2, anchor, {}, "")
        assert any(x["code"] == "GA-09" and x["level"] == "FAIL" for x in fl), fl
        assert sl["dialogue_outside_ratio"] == 1.0, sl
        # 未启用 enforce_dialogue 时只报数不判杀
        f0, _ = check_one(gl, {}, anchor, {}, "")
        assert not any(x["code"] == "GA-09" and x["level"] == "FAIL" for x in f0), f0
        # 纯短节奏句不得被 8-15 字口径误杀（短剧「滚。」「我不！」合法）
        gs = d / "ep001_E_v1.md"
        gs.write_text("【场1｜办公室】\n" + "\n".join(
            "宁清和：%s。" % t for t in ["滚", "我不", "走开", "没门", "别过来",
                                    "你等着", "老子不干了", "少废话"]) + "\n", encoding="utf-8")
        fs, ss = check_one(gs, cfg2, anchor, {}, "")
        assert ss["dialogue_short"] == 8 and ss["dialogue_long"] == 0, ss
        assert not any(x["code"] == "GA-09" and x["level"] == "FAIL" for x in fs), fs
        print("[PASS] selftest：GA-09 超长句占比判 / 短句不误杀 / GA-10 直搬 / GA-11 同旁白 / 正文截断 / 未启用不误杀")

        # ---- GA-12 稿件形态门 ----
        dry_text = ("> ⚠ DRY-RUN 占位，非真实初稿；删除本行前禁止进入闸门A。\n"
                    "> 版本：ep010_A_v1 · 引擎：glm-5.3-flash（批量档）\n\n"
                    "（演练未调用 API，本文件无正文，不得进入闸门A。）\n")
        shp = d / "ep001_F_v1.md"
        shp.write_text(dry_text, encoding="utf-8")
        ff, sf = check_one(shp, cfg2, anchor, {}, "")
        assert not sf["shape"]["ok"] and len(sf["shape"]["issues"]) == 3, sf["shape"]
        assert any(x["code"] == "GA-12" and x["level"] == "FAIL" for x in ff), ff
        assert "不设字数下限" in next(x["evidence"] for x in ff if x["code"] == "GA-12"), ff
        # 六档位真稿用「1-1　日　外」，格式不同不得误判成没戏
        alt = d / "ep001_G_v1.md"
        alt.write_text("1-1　日　外　国营饭店门口\n青年甲：瞧见没？\n", encoding="utf-8")
        fg, sg = check_one(alt, cfg2, anchor, {}, "")
        assert sg["shape"]["ok"] and sg["shape"]["scenes"] == 1, sg["shape"]
        assert not any(x["code"] == "GA-12" for x in fg), fg
        # 不设字数下限：一场一句两字台词也算达标
        tiny = d / "ep001_H_v1.md"
        tiny.write_text("【场1｜门口】\n甲：滚。\n", encoding="utf-8")
        assert check_one(tiny, cfg2, anchor, {}, "")[1]["shape"]["ok"]
        # 显式关闭时只报数不判杀，但数值仍留痕
        fskip, sskip = check_one(shp, dict(cfg2, skip_shape_gate=True), anchor, {}, "")
        assert not any(x["code"] == "GA-12" for x in fskip), fskip
        assert sskip["shape"]["dry_mark"] and not sskip["shape"]["ok"], sskip["shape"]
        print("[PASS] selftest：GA-12 DRY 占位判不予验收 / 异格式真稿不误杀 / "
              "不设字数下限 / skip_shape_gate 只报数")
        return 0
    finally:
        sample.unlink(missing_ok=True)
        d2 = Path("_ga_selftest_dir")
        if d2.exists():
            for f in d2.iterdir():
                f.unlink()
            d2.rmdir()


def main():
    ap = argparse.ArgumentParser(description="闸门A 脚本化硬指标核对 GA-01~12")
    ap.add_argument("--draft", help="初稿文件或目录（.md/.txt）")
    ap.add_argument("--anchors", help="人物小传/术语表 md，作为人设核对证据源")
    ap.add_argument("--config", help="gate_a_config.json，未提供时仅报数不判杀")
    ap.add_argument("--source", help="本集原文切片（GA-10 逐字直搬比对用）")
    ap.add_argument("--source-dir", help="按 epNNN 命名的原文切片目录")
    ap.add_argument("--out", help="Markdown 报告输出路径")
    ap.add_argument("--json", dest="json_out", help="同时输出 JSON 结果")
    ap.add_argument("--init-config", help="生成配置模板并退出")
    ap.add_argument("--selftest", action="store_true", help="内置自检")
    a = ap.parse_args()

    if a.selftest:
        return selftest()
    if a.init_config:
        tpl = {
            "_说明": "按本剧填写；未提供的维度脚本只报数值不判杀，避免误杀。",
            "turns_min": 8, "turns_max": 12,
            "segment_chars_min": 80, "segment_chars_max": 150,
            "fixed_traits": ["特征1", "特征2", "特征3", "特征4", "特征5"],
            "require_all_traits": False,
            "name_whitelist": [], "name_aliases": {"旧名": "统一名"},
            "system_rules": ["吹牛触发", "五米内"],
            "term_aliases": {"旧写法": "统一写法"},
            "enforce_dialogue": False,
            "dialogue_chars_min": 8, "dialogue_chars_max": 15,
            "dialogue_max_ratio": 0.20,
            "lift_min": 8,
            "skip_shape_gate": False,
            "_DP说明": "挂载 modules/process/dialogue-pass.md 时把 enforce_dialogue 置 true；"
                       "dialogue_max_ratio 是「>15 字超长句」占比上限（<8 字短节奏句登记例外、"
                       "不计入判杀分子）；GA-10 需 --source 原文切片；GA-11 自动跨文件比对。",
            "_GA12说明": "GA-12 稿件形态门默认启用（与模块挂载无关）：演练占位标记／人物对白句为 0／"
                        "场次标记为 0 任一命中即不予验收；只量形态、不设字数下限、不判语义。"
                        "兼容存量异格式稿时可置 true，脚本仍报数但不判杀。",
        }
        Path(a.init_config).write_text(json.dumps(tpl, ensure_ascii=False, indent=2), encoding="utf-8")
        print("[OK] 配置模板已生成：%s" % a.init_config)
        return 0
    if not a.draft:
        print("[ERROR] 需 --draft（或 --selftest / --init-config）", file=sys.stderr)
        return 2

    files = draft_files(a.draft)
    if not files:
        print("[ERROR] 未找到初稿文件：%s" % a.draft, file=sys.stderr)
        return 2
    cfg = load_config(a.config)
    anchors = Path(a.anchors).read_text(encoding="utf-8") if a.anchors and Path(a.anchors).exists() else None
    sources = load_sources(a.source, a.source_dir)
    cross = cross_file_narration([str(f) for f in files])
    results = []
    for f in files:
        findings, stats = check_one(f, cfg, anchors, cross, source_for(f, sources))
        results.append({"findings": findings, "stats": stats})
        n_fail = sum(x["level"] == "FAIL" for x in findings)
        print("[%s] %s｜轮次 %d｜区间外 %d/%d｜形态 %s｜FAIL %d" %
              ("杀" if n_fail else "过", f.name, stats["turns"],
               stats["dialogue_outside"], stats["dialogue_sentences"],
               "达标" if stats["shape"]["ok"] else "不达标", n_fail))
    total_fail = 0
    if a.out:
        total_fail = write_report(a.out, results)
        print("[OK] 报告：%s" % a.out)
    else:
        total_fail = sum(sum(x["level"] == "FAIL" for x in r["findings"]) for r in results)
    if a.json_out:
        Path(a.json_out).write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    return 1 if total_fail else 0


if __name__ == "__main__":
    sys.exit(main())
