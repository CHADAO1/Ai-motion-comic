# -*- coding: utf-8 -*-
"""语义门禁 G1–G9（通用版 · 只读）

把「改编规范」里写了但闸门A 量不到的语义问题收回来：叙述腔进台词、
不可见内心、破第四面墙、新增实体、规则剧透、说话人错配、关键动作漏项、
叙述腔直搬旁白、解说型旁白、A/B 同一旁白逐字相同。

与 `check_gate_a.py` 的分工：那边量机械项（轮次/字数/人名/术语/单句长度），
这边量语义形态。两个都过才可写「验收通过」，G8 逐句溯源仍需人工。

用法：
  python scripts/adapt_gate.py --files outputs/ep001_A_v1.md outputs/ep001_B_v1.md \
      --source pipeline/source/ep001.txt --config pipeline/adapt_gate_config.json \
      --out outputs/01_语义门禁.json
  python scripts/adapt_gate.py --glob "outputs/ep*_v1.md" --source-dir pipeline/source/ --out ...
  python scripts/adapt_gate.py --init-config pipeline/adapt_gate_config.json
  python scripts/adapt_gate.py --selftest

设计口径：**项目专属判据一律走配置，不写死在脚本里**。
G5/G6/G7/G9⑤ 未配置时跳过并给提示，不假装检查过；
G1/G2/G3/G4/G9①④ 用通用剧作法词表，跨项目直接可用。

纯标准库，无第三方依赖。
"""
import argparse
import glob
import io
import json
import os
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from _text_util import (body_lines, cjk_only, cross_file_narration,
                        longest_common)

# ---------- 通用判据（剧作法层面，跨项目适用） ----------
DEFAULT_NARRATION = (r"原主|谁让他|生性不羁|唯唯诺诺|这环境里|左右不敢得罪|"
                     r"性格还|受不得委屈|天生|素来|向来|众所周知")
DEFAULT_INVISIBLE = (r"心里|原以为|才明白|念头|盘算|第一个念头|越想|越嚼|"
                     r"在嘴里嚼|不敢想|压根没打算|暗自|心下")
DEFAULT_FOURTH_WALL = r"看屏幕|看客|观众|只有[^\n]{0,10}知道|看客已经知道|镜头外的"
DEFAULT_EXPOSITORY = (r"成了|变成|意味着|原来|其实|才知道|最大的|等着看|看笑话|"
                      r"要的是|这一头|那一头|根本|终究|从此|就此|比谁都|算盘|"
                      r"死局|下场|不是.{0,8}而是|落得一个|只落了")
NUM_TOKEN_RE = re.compile(r"[一二三四五六七八九十百千万\d]+[把个名口张条件匹石两版次天]")

LIFT_MIN = 8   # 旁白与原文连续汉字重合 ≥8 字 → 叙述腔直搬
DUP_MIN = 6    # 与紧邻已演行重合 ≥6 字 → 注水候选（仅提示）


class GateConfig:
    """项目专属判据容器。缺省即跳过对应门，绝不编造期望值。"""

    def __init__(self, data=None):
        d = data or {}
        self.narration = d.get("narration", DEFAULT_NARRATION)
        self.invisible = d.get("invisible", DEFAULT_INVISIBLE)
        self.fourth_wall = d.get("fourth_wall", DEFAULT_FOURTH_WALL)
        self.expository = d.get("expository", DEFAULT_EXPOSITORY)
        self.forbidden_new = d.get("forbidden_new", {})
        self.speaker_map = d.get("speaker_map", {})
        self.key_assertions = {str(k): v for k, v in d.get("key_assertions", {}).items()}
        self.unfounded = d.get("unfounded", [])
        self.system_spoiler = d.get("system_spoiler", {})
        self.lift_min = d.get("lift_min", LIFT_MIN)
        self.dup_min = d.get("dup_min", DUP_MIN)

    @classmethod
    def load(cls, path):
        if not path or not Path(path).exists():
            return cls()
        return cls(json.loads(Path(path).read_text(encoding="utf-8")))

    def unfounded_re(self):
        return re.compile("|".join(self.unfounded)) if self.unfounded else None


# ---------- 原文切片 ----------
def source_numbers(src):
    """原文出现过的数字+量词组合，用于 G4 新增数字候选比对。"""
    return set(NUM_TOKEN_RE.findall(src))


def load_sources(source=None, source_dir=None):
    """返回 {集号(int) 或 None: 原文文本}。

    --source 单文件 → {None: text}（所有稿共用）
    --source-dir 目录 → 按文件名里的 epNNN 匹配集号，无集号文件作默认兜底
    """
    out = {}
    if source:
        for p in ([source] if isinstance(source, str) else source):
            if Path(p).is_file():
                out[None] = io.open(p, encoding="utf-8", errors="ignore").read()
    if source_dir and Path(source_dir).is_dir():
        for p in sorted(Path(source_dir).glob("*")):
            if not p.is_file() or p.suffix.lower() not in (".txt", ".md"):
                continue
            m = re.search(r"ep(\d{3})", p.name, re.I)
            key = int(m.group(1)) if m else None
            out[key] = io.open(p, encoding="utf-8", errors="ignore").read()
    return out


def ep_of(path):
    m = re.search(r"ep(\d{3})", os.path.basename(path), re.I)
    return int(m.group(1)) if m else None


def source_for(path, sources):
    ep = ep_of(path)
    return sources.get(ep, sources.get(None, ""))


# ---------- G9 ----------
def g9_narration(lines, src_text, cfg):
    """① 逐字直搬 ② 注水候选 ④ 解说型旁白 ⑤ 无据概念。"""
    src_cjk = cjk_only(src_text)
    ex_re = re.compile(cfg.expository) if cfg.expository else None
    un_re = cfg.unfounded_re()
    fails, notes = [], []
    for i, l in enumerate(lines):
        strip = l.strip()
        # ⑤ 无据概念：旁白／台词／字幕任何形态都判
        if un_re and un_re.search(strip):
            fails.append("[无据概念] 命中勘误已判「无原文依据、用户未拍板」的概念，"
                         "不得入事实层：%s" % strip[:70])
        if not strip.startswith("旁白："):
            continue
        q = cjk_only(l.split("：", 1)[-1])
        if len(q) < cfg.lift_min:
            continue
        common = longest_common(q, src_cjk)
        if src_cjk and common >= cfg.lift_min:
            fails.append("[叙述腔直搬] 与原文连续重合 %d 字（概述句／叙述者评价须转成"
                         "一场戏、一次剪切或直接删，禁止逐字念成旁白）：%s"
                         % (common, strip[:70]))
        elif ex_re and ex_re.search(strip):
            fails.append("[解说型旁白] 叙述者替观众总结／点破，非可见画面（须转成可见行为、"
                         "对手戏或一次剪切；禁止提前讲破）：%s" % strip[:70])
        near = cjk_only("".join(lines[max(0, i - 3):i]))
        if near and longest_common(q, near) >= cfg.dup_min:
            notes.append("G9 注水候选（与紧邻已演行重合 ≥%d 字，需人工确认）：%s"
                         % (cfg.dup_min, strip[:60]))
    return fails, notes


# ---------- 主检查 ----------
def check(path, cfg, src_text="", cross=None, sources=None):
    """返回与项目版一致的结果结构，便于跨项目回归对比。"""
    raw = io.open(path, encoding="utf-8").read()
    lines = body_lines(raw)
    fails, notes = {}, []
    ep_no = ep_of(path)

    # G1 叙述腔进台词
    g1 = [l.strip() for l in lines
          if re.match(r"^\s*[^：:「」]{1,16}[：:]", l) and re.search(cfg.narration, l)]
    if g1:
        fails["G1"] = g1

    # G2 不可见内心
    g2 = [l.strip() for l in lines
          if (l.strip().startswith("（") or l.strip().startswith("旁白："))
          and re.search(cfg.invisible, l)]
    if g2:
        fails["G2"] = g2

    # G3 破第四面墙
    g3 = [l.strip() for l in lines if re.search(cfg.fourth_wall, l)]
    if g3:
        fails["G3"] = g3

    # G4 新增实体（配置禁用表 + 原文数字白名单候选）
    g4 = []
    for kw, why in cfg.forbidden_new.items():
        for l in lines:
            if kw in l:
                g4.append("[%s] %s → %s" % (kw, why, l.strip()[:80]))
                break
    nums = set()
    for l in lines:
        nums |= set(NUM_TOKEN_RE.findall(l))
    src_nums = source_numbers(src_text)
    unknown = sorted(n for n in nums if n not in src_nums
                     and not re.match(r"^[一二三四五六七八九十]+$", n))
    if unknown:
        notes.append("G4 数字候选需人工确认（原文未出现）：" + "、".join(unknown[:20]))
    if g4:
        fails["G4"] = g4

    # G5 规则剧透（项目配置驱动）
    sp = cfg.system_spoiler
    if sp.get("tag") and sp.get("spoiler") and sp.get("knot"):
        idx_sub = next((i for i, l in enumerate(lines)
                        if sp["tag"] in l and re.search(sp["spoiler"], l)), None)
        idx_knot = next((i for i, l in enumerate(lines) if re.search(sp["knot"], l)), None)
        if idx_sub is not None and idx_knot is not None and idx_sub < idx_knot:
            fails["G5"] = ["字幕第 %d 行先讲破规则，关键动作在第 %d 行（须在其后）"
                           % (idx_sub + 1, idx_knot + 1)]
        elif idx_sub is None and idx_knot is not None and sp.get("require", True):
            notes.append("G5：未出现该规则字幕，需人工确认是否漏了原文反转")
    else:
        notes.append("G5：未配置 system_spoiler（tag/spoiler/knot），该门跳过，需人工勾")

    # G6 说话人错配（项目配置驱动）
    g6 = []
    for quote, owner in cfg.speaker_map.items():
        for l in lines:
            if quote in l:
                m = re.match(r"^\s*([^：:「」]{1,16})[：:]", l)
                who = m.group(1).strip() if m else ""
                if who and owner not in who:
                    g6.append("应属『%s』，实挂『%s』：%s" % (owner, who, l.strip()[:80]))
                elif "不得挪到" in owner:
                    g6.append("跨集挪用（%s）：%s" % (owner, l.strip()[:80]))
                break
    if g6:
        fails["G6"] = g6
    if not cfg.speaker_map:
        notes.append("G6：未配置 speaker_map，该门跳过，需人工核说话人")

    # G7 关键动作断言（按集配置，未配置的集只提示人工勾，避免跨集误报）
    body = "\n".join(lines)
    assertions = cfg.key_assertions.get(str(ep_no)) if ep_no else None
    if assertions:
        g7 = []
        for item in assertions:
            name, need, bad, why = (list(item) + [None] * 4)[:4]
            if bad and re.search(bad, body):
                g7.append("[%s] 反向：%s" % (name, why))
            elif need and not re.search(need, body):
                g7.append("[%s] 缺失：%s" % (name, why))
        if g7:
            fails["G7"] = g7
    else:
        notes.append("G7：第 %s 集断言表未配置，需人工逐场勾关键动作，脚本不判" % ep_no)

    # G9
    if src_text == "" and sources:
        src_text = source_for(path, sources)
    g9, g9_notes = g9_narration(lines, src_text, cfg)
    for txt, fs in (cross or {}).items():
        if os.path.basename(path) in fs:
            g9.append("[A/B 同一旁白逐字相同] 出现在 %s（禁止用两版逐字抄同一段旁白"
                      "冒充事实层一致）：%s" % ("、".join(sorted(set(fs))), txt[:60]))
    if g9:
        fails["G9"] = g9
    notes.extend(g9_notes)

    notes.append("G8 逐句溯源率 / 决策日志：需人工核，脚本不判")
    if not src_text:
        notes.append("G9 未拿到原文切片，逐字直搬判定已跳过，只跑了解说型/注水/无据概念")

    hard = [g for g in ("G1", "G3", "G5", "G6") if g in fails]
    return {
        "file": os.path.basename(path),
        "hard_fail": hard,
        "fail_gates": list(fails),
        "gates": fails,
        "notes": notes,
        "verdict": "判杀" if hard else ("需登记后复核" if fails else "语义门禁通过（G8 仍待人工）"),
    }


def write_report(out, cfg, sources, files, cross, rows):
    rep = {
        "config_lift_min": cfg.lift_min,
        "source_slices": sorted(str(k) for k in sources),
        "scanned": len(rows),
        "judged_kill": sum(1 for r in rows if r["verdict"] == "判杀"),
        "g9_hits": sum(1 for r in rows if "G9" in r["fail_gates"]),
        "cross_file_same_narration": len(cross),
        "rows": rows,
    }
    Path(out).write_text(json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")
    return rep


def selftest():
    import tempfile
    from _text_util import dialogue_sentences
    d = Path(tempfile.mkdtemp(prefix="adapt_gate_st_"))
    try:
        orig = "李承泽当天就把领导辞了，再给老板一个滚蛋的机会。"
        src = d / "ep001.txt"
        src.write_text(orig, encoding="utf-8")
        a = d / "ep001_A_v1.md"
        b = d / "ep001_B_v1.md"
        a.write_text("【场1｜办公室】\n李承泽：你在教我做事？\n"
                     "旁白：「当天他把领导辞了，再给老板一个滚蛋的机会。」\n"
                     "（他心里一亮。）\n---\n## 改编登记\n原旁白：当天他把领导辞了…\n",
                     encoding="utf-8")
        b.write_text("【场1｜办公室】\n领导：你……\n"
                     "旁白：「当天他把领导辞了，再给老板一个滚蛋的机会。」\n",
                     encoding="utf-8")
        cfg = GateConfig()
        sources = load_sources(str(src))
        cross = cross_file_narration([str(a), str(b)])
        ra = check(str(a), cfg, sources[None], cross)
        # 正文截断：登记块里的引用不得触发 G9
        assert not any("登记" in x for x in ra["gates"].get("G9", [])), ra
        assert any("叙述腔直搬" in x for x in ra["gates"].get("G9", [])), ra["gates"]
        assert any("A/B 同一旁白" in x for x in ra["gates"].get("G9", [])), ra["gates"]
        assert "G2" in ra["fail_gates"], ra["fail_gates"]          # 不可见内心
        assert len(cross) == 1, cross
        # 删掉旁白后应零命中
        clean = d / "ep001_C_v1.md"
        clean.write_text("【场1｜办公室】\n李承泽：你在教我做事？\n（工牌往桌上一拍。）\n",
                         encoding="utf-8")
        rc = check(str(clean), cfg, sources[None], {})
        assert "G9" not in rc["fail_gates"], rc["fail_gates"]
        # 项目专属门未配置时必须跳过且不误报
        assert any("G5：未配置" in x for x in rc["notes"]), rc["notes"]
        assert any("G7" in x for x in rc["notes"]), rc["notes"]
        # 配置驱动门可生效
        cfg2 = GateConfig({"forbidden_new": {"免死金牌": "无原文依据"},
                           "unfounded": ["免死金牌"],
                           "speaker_map": {"走，会会这软骨头": "王丰飘"}})
        wrong = d / "ep001_D_v1.md"
        wrong.write_text("【场1｜府衙】\n李承泽：走，会会这软骨头。\n"
                         "旁白：「皇子身份成了免死金牌。」\n", encoding="utf-8")
        rd = check(str(wrong), cfg2, sources[None], {})
        assert "G6" in rd["fail_gates"] and "G4" in rd["fail_gates"], rd["fail_gates"]
        assert any("无据概念" in x for x in rd["gates"].get("G9", [])), rd["gates"]
        # 通用工具：台词切句 + 动作括号里的冒号不得误判为说话人
        sents = dialogue_sentences(body_lines(io.open(a, encoding="utf-8").read()))
        assert len(sents) == 1 and sents[0][1] == "李承泽", sents
        probe = ["【场1｜办公室】", "（一声闷响。特写：键盘上一个巴掌印。）",
                 "李承泽：我不伺候了。"]
        probe_sents = dialogue_sentences(probe)
        assert len(probe_sents) == 1 and probe_sents[0][1] == "李承泽", probe_sents
        print("[PASS] selftest：正文截断 / 直搬 / 同旁白 / 不可见内心 / 配置门 / 台词切句 / 动作行排除 七组")
        return 0
    finally:
        for f in d.iterdir():
            f.unlink()
        d.rmdir()


def main():
    ap = argparse.ArgumentParser(description="语义门禁 G1-G9（通用版）")
    ap.add_argument("--files", nargs="*", help="稿件路径（可多个）")
    ap.add_argument("--glob", dest="glob_pat", help="稿件通配符，如 'outputs/ep*_v1.md'")
    ap.add_argument("--source", help="本集原文切片（单文件或目录）")
    ap.add_argument("--source-dir", help="按 epNNN 命名的原文切片目录")
    ap.add_argument("--config", help="项目判据 JSON（缺省时项目专属门跳过）")
    ap.add_argument("--out", help="JSON 报告输出路径")
    ap.add_argument("--init-config", help="生成配置模板并退出")
    ap.add_argument("--selftest", action="store_true", help="内置自检")
    a = ap.parse_args()

    if a.selftest:
        return selftest()
    if a.init_config:
        tpl = {
            "_说明": "只填本项目专属判据；未配置的门会跳过并给提示，脚本不编造期望值。",
            "forbidden_new": {"示例无据台词": "原文无此设定（人物/台词/数字/规则，禁）"},
            "speaker_map": {"示例台词": "应属的说话人"},
            "key_assertions": {
                "1": [["拔刀", "拔刀|刀出鞘|锵", "刀还没出鞘", "原文明写四人拔刀"],
                      ["关键动作", "必要词", "", "本集必留动作"]]
            },
            "unfounded": ["示例无据概念"],
            "system_spoiler": {"tag": "【系统｜字幕】", "spoiler": "自杀.{0,3}不算",
                               "knot": "打结|布条", "require": True},
            "lift_min": 8, "dup_min": 6,
        }
        Path(a.init_config).write_text(json.dumps(tpl, ensure_ascii=False, indent=2),
                                       encoding="utf-8")
        print("[OK] 配置模板已生成：%s" % a.init_config)
        return 0

    files = list(a.files or [])
    if a.glob_pat:
        files += sorted(glob.glob(a.glob_pat))
    if not files:
        print("[ERROR] 需 --files 或 --glob（或 --selftest / --init-config）", file=sys.stderr)
        return 2
    cfg = GateConfig.load(a.config)
    sources = load_sources(a.source, a.source_dir)
    cross = cross_file_narration(files)
    rows = [check(f, cfg, source_for(f, sources), cross, sources) for f in files]
    rep = {"scanned": len(rows), "rows": rows}
    if a.out:
        rep = write_report(a.out, cfg, sources, files, cross, rows)
        print("[OK] 报告：%s" % a.out)
    print("扫描 %d 版｜判杀 %d｜G9 命中 %d 版｜A/B 同旁白 %d 组｜原文切片 %d 份" %
          (len(rows), rep["judged_kill"], rep["g9_hits"],
           rep["cross_file_same_narration"], len(sources)))
    for r in rows:
        print("  %-24s %-18s %s" % (r["file"], r["verdict"],
                                    " ".join(r["fail_gates"]) or "—"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
