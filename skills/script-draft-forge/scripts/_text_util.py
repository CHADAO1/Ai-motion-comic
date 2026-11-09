# -*- coding: utf-8 -*-
"""闸门脚本共用文本工具（纯标准库，无第三方依赖）。

统一五件容易产生「同一份稿两种结论」的口径：
1. 正文边界：首场 → 文末登记块之前（登记块会引用被删原句，扫进去会自污染）。
2. 汉字归一：去掉标签、引号、标点后只留汉字，用于连续重合比对。
3. 旁白行与跨文件同旁白：两个脚本必须共用，否则 GA-11 与 G9 结论会打架。
4. 稿件形态（GA-12）：场次/人物对白/演练占位标记，两个验收入口必须共用。
5. 稿件文件识别：报告/索引/登记表不得被目录扫描当稿件（三个验收入口共用）。

GA-12 动机（2026-11-06 第10-12集回归实测）：12 份 DRY 占位稿（57-68 字、
0 场、0 句对白）被门禁全部判「验收通过」——门只查「有没有违规」，不查
「有没有戏」。形态门只量形态：不设字数下限、不判语义、不判好不好看。
"""
import io
import os
import re
from pathlib import Path

CJK_RE = re.compile(r"[\u4e00-\u9fff]")
SPLIT_RE = re.compile(r"[。！？!?；;…]+|\n")
SPEAKER_RE = re.compile(
    r"^\s*[-•*#> ]*(?P<name>[^：:「」\"']{1,16})[：:]\s*(?P<body>.+)$")
# 非人物标签：不算「对白句」，但仍是旁白检查的对象
NON_DIALOGUE_LABELS = {
    "旁白", "字幕", "画外音", "花字", "OS", "VO", "旁白VO", "系统",
}
BODY_END_MARKERS = ("## 改编登记", "## 对白调整登记", "## v3 复查处置登记",
                    "## 处置登记", "## 版本差异说明")


# ---------- 稿件文件识别（防报告自扫污染，三入口共用） ----------
# 动机（2026-11-06 第10-12集回归实测）：把 `闸门A.md` 写进 outputs/ 后，
# 下一轮 --draft outputs/ 会把报告本身当稿件扫进去（「轮次 2 / FAIL 2」），
# 结论被自己污染。旧规则只排 00_/01_ 前缀与「报告/索引」，漏了 03_、
# 「闸门A.md」这类。文件名 + 首部标题双层判定，宁可漏收
# 一份可疑文件，也不要把报告算进验收分母。
REPORT_NAME_PREFIX = re.compile(r"^\d{2}[-_]")
REPORT_NAME_WORDS = (
    "报告", "索引", "检查", "验收", "覆盖", "规划", "登记", "体检", "统计",
    "汇总", "摘要", "说明", "清单", "模板", "自检", "留痕", "台账", "快照",
    "readme", "manifest", "config", "report", "gate", "check", "audit",
    "index", "template", "selftest", "lint",
)
REPORT_TITLE_RE = re.compile(
    r"^#{1,2}[^\n]*(?:报告|检查|验收|覆盖|索引|登记|规划|体检|清单|"
    r"留痕|快照|自检|净稿|闸门|分集规划门)")
REPORT_GENERATED_RE = re.compile(r"由\s*`?scripts/[^\s`]+`?\s*生成")


def is_draft_candidate(path):
    """这个文件能不能当稿件进验收目录扫描？显式单文件传参不受本函数限制。"""
    p = Path(path)
    if p.suffix.lower() not in (".md", ".txt"):
        return False
    low = p.name.lower()
    if REPORT_NAME_PREFIX.match(p.name):
        return False
    if any(w in low for w in REPORT_NAME_WORDS):
        return False
    try:
        with io.open(p, encoding="utf-8", errors="replace") as fh:
            head = fh.read(1200)
    except OSError:
        return True
    first = "\n".join(head.splitlines()[:3])
    if REPORT_TITLE_RE.search(first):
        return False
    if REPORT_GENERATED_RE.search(head) and any(
            k in head for k in ("结论", "FAIL", "齐备率", "阻断项")):
        return False
    return True


def iter_draft_files(draft):
    """目录 → 只收稿件；单文件 → 直接返回（尊重显式指定，故意验报告也允许）。"""
    p = Path(draft)
    if p.is_dir():
        return sorted(f for f in p.rglob("*")
                      if f.is_file() and is_draft_candidate(f))
    return [p] if p.exists() else []


def cjk_only(s):
    """归一成纯汉字串（去标签、引号、标点、空白、英数）。"""
    return "".join(CJK_RE.findall(s or ""))


def longest_common(a, b):
    """最长公共连续子串长度。稿本行很短，O(n*m) 足够。"""
    best = 0
    prev = [0] * (len(b) + 1)
    for i in range(1, len(a) + 1):
        cur = [0] * (len(b) + 1)
        for j in range(1, len(b) + 1):
            if a[i - 1] == b[j - 1]:
                cur[j] = prev[j - 1] + 1
                if cur[j] > best:
                    best = cur[j]
        prev = cur
    return best


def body_lines(raw):
    """正文 = 首场 → 文末登记块之前。

    没有场标记的文件（如测试稿、散文稿）返回全文，保持向后兼容。
    """
    lines = raw.splitlines()
    i = 0
    while i < len(lines) and not lines[i].strip().startswith("【场"):
        i += 1
    if i == len(lines):
        return lines
    j = len(lines)
    for k in range(i, len(lines)):
        s = lines[k].strip()
        if s == "---" or s.startswith(BODY_END_MARKERS):
            j = k
            break
    return lines[i:j]


def narration_lines(raw):
    return [l.strip() for l in body_lines(raw) if l.strip().startswith("旁白：")]


def cross_file_narration(paths):
    """跨文件同一旁白逐字相同 → {旁白全文: [文件名, ...]}。"""
    seen = {}
    for p in paths:
        try:
            for line in narration_lines(io.open(p, encoding="utf-8").read()):
                seen.setdefault(line, []).append(os.path.basename(p))
        except OSError:
            pass
    return {t: f for t, f in seen.items() if len(set(f)) > 1}


def dialogue_sentences(lines):
    """提取人物台词并切成句。返回 [(行号, 说话人, 句子)]。

    排除旁白/字幕/花字等非人物标签；括号内动作提示不计入汉字数。
    """
    out = []
    for i, line in enumerate(lines, 1):
        strip = line.strip()
        # 动作行／场景行一律不算台词；括号内「特写：」这类冒号会被误认成说话人
        if strip.startswith(("（", "(", "【", "△", "※", ">")):
            continue
        m = SPEAKER_RE.match(line)
        if not m:
            continue
        name = m.group("name").strip()
        if name in NON_DIALOGUE_LABELS or name.startswith("【"):
            continue
        if re.search(r"[。！？，、；…]", name):
            continue
        body = re.sub(r"[（(][^）)]*[）)]", "", m.group("body"))
        body = re.sub(r"\[[^\]]*\]", "", body)
        for s in SPLIT_RE.split(body):
            s = re.sub(r"^[「」\"'\s]+|[「」\"'\s]+$", "", s)
            if cjk_only(s):
                out.append((i, name, s))
    return out


def sentence_len(s):
    """句子的汉字数（不含标点、括号动作、角色名）。"""
    return len(cjk_only(s))


# ---------- 稿件形态门（GA-12 / check_adapt 形态项） ----------
# 场次格式跨产线并不统一：v3/Mode3 用「【场1｜…】」，六档位调度真稿用
# 「1-1　日　外　国营饭店门口」，也有「## 场1」「第1场」。只认一种格式会把
# 「格式不同」误判成「没有戏」，故用宽松口径，且两个验收入口共用本函数。
SCENE_PATTERNS = (
    re.compile(r"^\s*【\s*场(?:景)?\s*\d+"),
    re.compile(r"^\s*#{1,4}\s*场\s*\d+"),
    re.compile(r"^\s*第\s*\d+\s*场"),
    re.compile(r"^\s*场\s*\d+\s*[｜|：:】]"),
    re.compile(r"^\s*\d+\s*[-－—]\s*\d+(?:[\s　]|$)"),
)
# 演练占位行常写在首场之前，body_lines 有场标记时会截掉，故必须查全文。
# 只收高置信标记，不用泛化的「演练/占位」二字，避免误杀正文里的说明。
DRY_MARK_RE = re.compile(
    r"DRY[-_\s]?(?:RUN|MARK)|演练未调用|本文件无正文|"
    r"占位[，,]?非真实初稿|非真实初稿[，,]?删除本行", re.I)


def scene_count(lines):
    """场次标记数（宽松识别，多种产线格式）。"""
    return sum(1 for l in lines if any(p.search(l) for p in SCENE_PATTERNS))


def draft_shape(raw):
    """稿件形态：演练占位 / 无人物对白 / 无场次 → 不予验收。

    只量形态，不设字数下限、不判语义、不判质量。ok=False 时 issues 列出全部原因，
    便于区分「形态不达标」与「内容违规」（两者不是一回事，不得混写成判杀理由）。
    """
    lines = body_lines(raw)
    dry = bool(DRY_MARK_RE.search(raw))
    scenes = scene_count(lines)
    dial = len(dialogue_sentences(lines))
    issues = []
    if dry:
        issues.append("含演练/占位标记（DRY-RUN）")
    if dial == 0:
        issues.append("人物对白句为 0")
    if scenes == 0:
        issues.append("场次标记为 0")
    return {
        "ok": not issues,
        "issues": issues,
        "dry_mark": dry,
        "scenes": scenes,
        "dialogue_sentences": dial,
    }


def selftest():
    dry = ("> ⚠ DRY-RUN 占位，非真实初稿；删除本行前禁止进入闸门A。\n"
           "> 版本：ep010_A_v1 · 引擎：glm-5.3-flash（批量档）\n\n"
           "（演练未调用 API，本文件无正文，不得进入闸门A。）\n")
    s = draft_shape(dry)
    assert not s["ok"] and len(s["issues"]) == 3, s
    assert s["dry_mark"] and s["scenes"] == 0 and s["dialogue_sentences"] == 0, s
    # 三种真稿场次格式都算「有戏」
    for scene_line in ("【场1｜现代办公室｜反讽】", "## 场1｜府衙",
                       "1-1　日　外　国营饭店门口", "第1场 客栈"):
        good = "%s\n李承泽：滚。\n" % scene_line
        g = draft_shape(good)
        assert g["ok"] and g["scenes"] == 1 and g["dialogue_sentences"] == 1, (scene_line, g)
    # 不设字数下限：一句话两字、一场也算达标
    assert draft_shape("【场1｜门口】\n甲：滚。\n")["ok"]
    # 无场次标记仍判不达标；有场次但零对白也判不达标
    assert not draft_shape("甲：滚。\n")["ok"]
    assert not draft_shape("【场1｜门口】\n（他把门推开。）\n")["ok"]
    print("[PASS] _text_util selftest：DRY 占位三条件同判 / 四种场次格式 / "
          "不设字数下限 / 零对白与零场次判不达标")

    import tempfile
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        (d / "ep001_A_v1.md").write_text("【场1｜门口】\n甲：滚。\n", encoding="utf-8")
        (d / "第10集.md").write_text("【场1｜门口】\n甲：滚。\n", encoding="utf-8")
        (d / "闸门A.md").write_text(
            "# 闸门A 脚本化硬指标报告\n\n> 由 `scripts/check_gate_a.py` 生成\n\n"
            "**结论：未通过**\n", encoding="utf-8")
        (d / "03_覆盖验收_E10-12.md").write_text("# 按纲改编覆盖验收报告\n", encoding="utf-8")
        (d / "01_分集规划检查.md").write_text("# S4 分集规划门\n", encoding="utf-8")
        got = [x.name for x in iter_draft_files(d)]
        assert got == ["ep001_A_v1.md", "第10集.md"], got
        assert [x.name for x in iter_draft_files(d / "闸门A.md")] == ["闸门A.md"], \
            "显式单文件传参应被尊重"
    print("[PASS] _text_util selftest：闸门A/覆盖验收/规划报告不入扫描 / "
          "无编号前缀的报告名也被排除 / 显式单文件不受限 / 非标准稿件名不误杀")
    return 0


if __name__ == "__main__":
    raise SystemExit(selftest())
