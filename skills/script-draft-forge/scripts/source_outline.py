#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""按纲改编：小说原文 + 编剧大纲/细纲 → 生成包 + 覆盖验收（SO-01~08 / GA-06~08）。

动机：原来的 Mode 1 只接收"素材"（一段简介/对标/想法），遇到「整本小说 + 编剧已经
写好的细纲」时有两个真问题：①全文塞进上下文必然爆窗，且模型会自己改结构；
②细纲逐条有没有落地，靠模型自报等于没查。本脚本把可计算的部分收回来：
原文入库切片、细纲编号化、生成包按集打包、覆盖/忠实/新增事件核对。

用法：
  # N0-N2：原文 + 纲入库，产出索引/解析报告/每集生成包
  python scripts/source_outline.py ingest --source <原文> --outline <细纲> --outline <大纲> --pipeline <dir>

  # S1/S2 建档完成后刷新生成包（不带 --source/--outline，读已有 JSON）
  python scripts/source_outline.py refresh --pipeline <dir>

  # 净稿（SH-03~06）：默认启用内置词表，逐条登记；项目专属规则可追加
  python scripts/source_outline.py ingest --source <原文> --outline <细纲> --pipeline <dir> \
      --exclude-patterns '^广告' --exclude-patterns '本站' --clean-config <自定义规则.json>
  # 关闭清洗 --no-clean；整段剔除番外/作者附言 --apply-sections

  # N4：初稿覆盖验收
  python scripts/source_outline.py check --draft <初稿文件或目录> --pipeline <dir> \
      --out outputs/01_体检报告_纲源.md

  # 生成细纲/大纲模板；内置自检
  python scripts/source_outline.py init-template <dir>
  python scripts/source_outline.py selftest

退出码：0=无 FAIL；1=有 FAIL（该版本判杀）；2=输入错误。
纯标准库，无第三方依赖。

诚实边界（写进报告，不许隐去）：
  - 锚点命中只证明"词出现了"，不证明语义覆盖；逐条语义判定仍由闸门A带行号证据完成。
  - 人名/术语是**候选**，不是事实；无锚点条目一律标"待人工核对"，不自动判过。
  - 章节自动分配是**推定**，细纲里写显式引用才作准。
  - 脚本不判断新增事件是否合法，只列证据，定性由用户/闸门A决定。
  - 净稿清洗只删整行高置信噪声；**乱码行与板块头默认只标记不删**（SH-05/06）。
    删除逐条登记到 00_净稿报告.md，行号为**清洗前原文件行号**，与索引表（净稿行号）分属两套口径。
    授权登记/阻断模块已于 2026-11-09 剥离删除，本脚本不再处理授权；读取原文做分析不等于出稿。
"""
import argparse
import csv
import hashlib
import html
import io
import json
import re
import sys
import tempfile
import xml.etree.ElementTree as ET
import zipfile
from collections import Counter
from datetime import datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _text_util import iter_draft_files  # noqa: E402  稿件文件识别（与闸门A 同口径）

W_NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
S_NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"

SOURCE_EXT = {".txt", ".md", ".markdown", ".docx"}
OUTLINE_EXT = {".txt", ".md", ".markdown", ".docx", ".csv", ".tsv", ".xlsx"}
DEFAULT_CLEAN_RULES = Path(__file__).resolve().parent.parent / "reference" / "source_clean.rules.json"
CJK = re.compile(r"[\u4e00-\u9fff]")
CN_DIGITS = {"零": 0, "〇": 0, "一": 1, "二": 2, "两": 2, "三": 3, "四": 4,
             "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}

# 默认章节标题：第N章/回/节/卷/部/篇/集、Chapter N。可用 --chapter-pattern 覆盖。
CHAPTER_RE = re.compile(
    r"^[ \t]*(?:"
    r"第\s*[0-9零〇一二三四五六七八九十百千两]{1,10}\s*[章回节卷部篇集][^\n]{0,60}"
    r"|(?:Chapter|CHAPTER|CH)\s*\d{1,4}[^\n]{0,60}"
    r")\s*$"
)
EP_HEAD_RE = re.compile(
    r"^\s*#{0,6}\s*[-*•]?\s*"
    r"(?:第\s*(?P<cn>[0-9零〇一二三四五六七八九十百千两]{1,10})\s*集"
    r"|(?:EP|Ep|ep)[ _\-]?(?P<num>\d{1,4})"
    r"|(?:集|集号)\s*[:：]?\s*(?P<n2>\d{1,4}))"
    r"\s*[|｜:：\-—]?\s*(?P<title>.*)$"
)
BEAT_RE = re.compile(r"^\s*(?:[-*•●]|[(（]?\d{1,2}[)）.、]|①|②|③|④|⑤|⑥|⑦|⑧|⑨)\s*(?P<body>.+)$")
_NUM = r"[0-9零〇一二三四五六七八九十百千两]{1,10}"
# 「集/回/节」必须带 原文/原著/对应/章节/出处 前缀，否则 "## 第3集" 的集号会被误当章节引用；
# 「章」可裸写（小说细纲常写「第1-3章」）；CHnnn 为脚本生成的章节 ID 直引。
REF_RE = re.compile(
    r"(?:原文|原著|对应|章节|出处)\s*[:：]?\s*第\s*(?P<a1>" + _NUM +
    r")\s*(?:[-–~～至到]\s*(?P<b1>" + _NUM + r"))?\s*[章回节集卷篇]"
    r"|第\s*(?P<a2>" + _NUM + r")\s*(?:[-–~～至到]\s*(?P<b2>" + _NUM + r"))?\s*章"
    r"|@?CH(?P<a3>\d{3,4})\s*(?:[-–~～至到]\s*@?CH?(?P<b3>\d{3,4}))?"
)
SPEAKER_RE = re.compile(r"^\s*[-•*#> ]*(?P<name>[^：:「」\"']{1,16})[：:]\s*(?P<body>.+)$")
QUOTE_RE = re.compile(r"[《「『]([^》」』]{2,14})[》」』]")
EVENT_RE = re.compile(
    r"(?:死(?:了|亡|去)|杀了|杀害|自尽|结婚|离婚|怀孕|生了(?:个|了)?孩子|穿越|重生|"
    r"失忆|毁容|破产|入狱|出狱|出国|回国|身世(?:揭|暴|曝)露|真实身份|认亲|断绝关系|"
    r"系统(?:升级|绑定|激活|更新|惩罚)|金手指(?:升级|消失|变更)|觉醒|结拜|拜师|"
    r"签(?:了)?(?:合同|协议)|(?:继承|夺得|丢失)(?:了)?(?:遗产|家产|职位|名额))"
)
NAME_STOP = set("的了在是我你他她它们就都也又把被这那一不说问道答和与或中上下里外时后前来去看听见想知能会要没很太更好最再只还却又已将其此其之个些多少怎么为什么因为所以但是如果虽然即便于对从向给拿把让使被比及其诸凡")


# ---------------------------------------------------------------------------- 基础工具

def cn2int(s):
    s = (s or "").strip()
    if s.isdigit():
        return int(s)
    if not s:
        return None
    total, num = 0, 0
    for ch in s:
        if ch in CN_DIGITS:
            num = CN_DIGITS[ch]
        elif ch == "十":
            total += (num or 1) * 10
            num = 0
        elif ch == "百":
            total += (num or 1) * 100
            num = 0
        elif ch == "千":
            total += (num or 1) * 1000
            num = 0
        else:
            return None
    return total + num


def read_bytes_text(p):
    b = Path(p).read_bytes()
    for enc in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            return b.decode(enc)
        except UnicodeDecodeError:
            continue
    return b.decode("utf-8", errors="replace")


def clean_xml_dump(text):
    """处理从 docx 复制出来、只残留 <w:t> 片段的 .txt（实测常见）。"""
    if "<w:t" not in text and "<w:p" not in text:
        return text
    out = []
    for raw in text.splitlines():
        if "<w:t" in raw:
            m = re.search(r"<w:t[^>]*>(.*)$", raw)
            s = html.unescape(m.group(1)) if m else ""
            out.append(re.sub(r"<[^>]+>", "", s).rstrip())
        elif "<w:" in raw or re.match(r"\s*</?w:", raw):
            out.append("")
        else:
            out.append(html.unescape(raw))
    return "\n".join(out)


# ---------------------------------------------------------------------------- 净稿 N0（SH-03~06）

def load_clean_rules(path=None, extra_patterns=None):
    """加载默认词表；--exclude-patterns 追加项目专属整行规则。无规则文件返回 None。"""
    p = Path(path) if path else DEFAULT_CLEAN_RULES
    if not p.exists():
        return None
    rules = json.loads(p.read_text(encoding="utf-8"))
    for i, pat in enumerate(extra_patterns or [], 1):
        try:
            re.compile(pat)
        except re.error as e:
            raise ValueError("--exclude-patterns 第 %d 条正则无效：%s（%s）" % (i, pat, e))
        rules.setdefault("exclude_line_patterns", []).append(
            {"id": "USER-%02d" % i, "pattern": pat, "reason": "项目追加规则（--exclude-patterns）"})
    return rules


def load_clean_document(p, rules, apply_sections=False):
    """返回 (清洗后文本, 删除登记, 标记登记)。原文件只读不改；乱码/板块头默认只标记。"""
    text, _ = load_document(p)
    if not rules:
        return text, [], []
    d = rules.get("defaults", {})
    max_line = d.get("max_noise_line_chars", 60)
    min_garbled = d.get("min_garbled_line_chars", 12)
    min_cjk = d.get("min_cjk_ratio", 0.2)
    gar = rules.get("garbled", {})
    removed, flags = [], []
    kept = []
    section = None
    for ln, raw in enumerate(text.splitlines(), 1):
        s = raw.strip()
        # 板块切片在下一个章节标题处结束（默认不启用切片）
        if section is not None and (CHAPTER_RE.match(raw) or re.match(r"^\s*#{1,4}\s*第", raw)):
            section = None
        for r in rules.get("section_head_patterns", []):
            if re.search(r["pattern"], raw):
                flags.append({"file": p, "line": ln, "text": raw[:120],
                              "rule": r["id"], "kind": "section", "reason": r.get("reason", "")})
                if apply_sections:
                    section = r
                break
        if section is not None:
            removed.append({"file": p, "line": ln, "text": raw[:120],
                            "rule": section["id"] + "/整段", "reason": "板块整段剔除（--apply-sections）"})
            continue
        hit = None
        if d.get("apply_line_removal", True) and s and len(s) <= max_line:
            for r in rules.get("exclude_line_patterns", []):
                if re.search(r["pattern"], raw):
                    hit = r
                    break
        if hit:
            removed.append({"file": p, "line": ln, "text": raw[:120],
                            "rule": hit["id"], "reason": hit.get("reason", "")})
            continue
        if len(s) >= min_garbled:
            cjk_ratio = len(CJK.findall(s)) / len(s)
            bad = (any(x in raw for x in gar.get("replacement_chars", []))
                   or any(x in raw for x in gar.get("html_residue", []))
                   or any(x in raw for x in gar.get("control_chars", [])))
            if bad or cjk_ratio < min_cjk:
                flags.append({"file": p, "line": ln, "text": raw[:120],
                              "rule": "SH-G01", "kind": "garbled",
                              "reason": "疑似转码脏行/非汉字占比 %.2f，待人工确认（不自动删）" % cjk_ratio})
        kept.append(raw)
    clean = "\n".join(kept)
    # 安全上限：删得过多说明规则写宽了，整体降级为只标记不删除
    removed_chars = sum(len(x["text"]) for x in removed)
    # 比例上限只对长文有意义：短文本里两三条广告行就能超 5%，会让净稿完全失效。
    # 故取「比例上限」与「绝对下限 200 字符」的较大值。
    limit = max(d.get("max_removed_ratio", 0.05) * len(text),
                d.get("min_removed_chars_floor", 200))
    if removed and removed_chars > limit:
        flags.append({"file": p, "line": 0, "text": "删除 %d 字符 / 原文 %d 字符，超过上限 %d 字符（比例 %.0f%% 或绝对下限）" %
                      (removed_chars, len(text), limit, d.get("max_removed_ratio", 0.05) * 100),
                      "rule": "SH-06", "kind": "downgraded",
                      "reason": "整体降级：本次不删除任何行，原文本原样入库"})
        for x in removed:
            flags.append({"file": p, "line": x["line"], "text": x["text"],
                          "rule": x["rule"], "kind": "downgraded", "reason": x["reason"]})
        return text, [], flags
    return clean, removed, flags


def write_clean_report(pipeline, removed, flags, sources, plain, rules):
    """SH-03：删除逐条登记；原文件 sha1；两套行号口径说明。"""
    L = ["# N0 净稿报告（SH-03~06）", "",
         "> 由 `scripts/source_outline.py ingest` 生成。**原文件只读不改**；"
         "`原文纯文本.txt` 是清洗后唯一入上下文的原文基准。", "",
         "## 口径（重要）", "",
         "- 下表「原始行号」= **清洗前源文件的行号**；`10_原文索引.md` 的行号 = "
         "**净稿拼接后的行号**。两者分属两套体系，不要混用。",
         "- 乱码行与板块头默认**只标记不删**（SH-05/06）；删除项须逐条可回退。", "",
         "## 删除登记（%d 条）" % len(removed), ""]
    if removed:
        L += ["| 源文件 | 原始行号 | 规则 | 原句 | 理由 |", "|---|---|---|---|---|"]
        L += ["| %s | %d | %s | %s | %s |" %
              (Path(x["file"]).name, x["line"], x["rule"],
               (x["text"] or "").replace("|", "／"), x["reason"]) for x in removed]
    else:
        L.append("（无删除；原文按原样入库）")
    L += ["", "## 待人工确认（%d 条，脚本不自动处理）" % len(flags), ""]
    if flags:
        L += ["| 源文件 | 原始行号 | 类别 | 规则 | 原句 | 说明 |", "|---|---|---|---|---|---|"]
        L += ["| %s | %d | %s | %s | %s | %s |" %
              (Path(x["file"]).name, x["line"], x["kind"], x["rule"],
               (x["text"] or "").replace("|", "／"), x["reason"]) for x in flags]
    else:
        L.append("（无标记）")
    L += ["", "## 源文件与校验", "", "| 源文件 | 原文件 sha1 |", "|---|---|"]
    L += ["| %s | %s |" % (Path(f).name, hashlib.sha1(Path(f).read_bytes()).hexdigest()[:12])
          for f in sources]
    L += ["", "- 净稿字符数：%d；净稿 sha1：%s" %
          (len(plain), hashlib.sha1(plain.encode("utf-8")).hexdigest()[:12]),
          "- 规则版本：%s；来源：`%s`" % (rules.get("version", "?"), DEFAULT_CLEAN_RULES.name
                                       if rules else "（未启用）"),
          "- `--apply-sections`（番外/作者附言整段剔除）默认关闭；如需开启，"
          "删掉的每段仍会逐行进上表。", ""]
    (pipeline / "00_净稿报告.md").write_text("\n".join(L), encoding="utf-8")


def read_docx(p):
    with zipfile.ZipFile(p) as z:
        xml = z.read("word/document.xml")
    root = ET.fromstring(xml)
    out = []
    for para in root.iter(W_NS + "p"):
        s = "".join(t.text or "" for t in para.iter(W_NS + "t"))
        out.append(s)
    return "\n".join(out)


def read_xlsx_rows(p):
    with zipfile.ZipFile(p) as z:
        shared = []
        if "xl/sharedStrings.xml" in z.namelist():
            root = ET.fromstring(z.read("xl/sharedStrings.xml"))
            for si in root.iter(S_NS + "si"):
                shared.append("".join(t.text or "" for t in si.iter(S_NS + "t")))
        sheet = next((n for n in z.namelist()
                      if re.match(r"xl/worksheets/sheet\d+\.xml$", n)), None)
        if not sheet:
            return []
        root = ET.fromstring(z.read(sheet))
        rows = []
        for row in root.iter(S_NS + "row"):
            cells = {}
            for c in row.iter(S_NS + "c"):
                ref = c.get("r", "")
                col = re.match(r"[A-Z]+", ref).group(0) if ref else ""
                ctype = c.get("t")
                if ctype == "inlineStr":
                    val = "".join(t.text or "" for t in c.iter(S_NS + "t"))
                else:
                    node = c.find(S_NS + "v")
                    val = node.text if node is not None and node.text else ""
                    if ctype == "s" and val:
                        val = shared[int(val)]
                cells[col] = val.strip()
            if cells:
                rows.append(cells)
    grid = []
    for cells in rows:
        cols = sorted(cells, key=lambda x: (len(x), x))
        mx = max((col_idx(c) for c in cols), default=0)
        line = [""] * (mx + 1)
        for c, v in cells.items():
            line[col_idx(c)] = v
        grid.append(line)
    return grid


def col_idx(letters):
    n = 0
    for ch in letters:
        n = n * 26 + (ord(ch.upper()) - 64)
    return n - 1


def read_csv_rows(p):
    text = read_bytes_text(p)
    delim = "\t" if Path(p).suffix.lower() in (".tsv",) else (
        "\t" if "\t" in text.splitlines()[0] and "," not in text.splitlines()[0] else ",")
    return [list(r) for r in csv.reader(io.StringIO(text), delimiter=delim)]


def load_document(p):
    """返回 (文本, 表格行 or None)。"""
    suf = Path(p).suffix.lower()
    if suf == ".docx":
        return read_docx(p), None
    if suf == ".xlsx":
        return "", read_xlsx_rows(p)
    if suf in (".csv", ".tsv"):
        return "", read_csv_rows(p)
    return clean_xml_dump(read_bytes_text(p)), None


def expand(paths, exts):
    out = []
    for raw in paths or []:
        p = Path(raw)
        if p.is_dir():
            out += sorted([str(x) for x in p.rglob("*")
                           if x.is_file() and x.suffix.lower() in exts])
        elif p.is_file():
            out.append(str(p))
        else:
            raise FileNotFoundError("找不到输入：%s" % p)
    return out


def dedup(seq):
    seen, out = set(), []
    for x in seq:
        x = (x or "").strip()
        if x and x not in seen:
            seen.add(x)
            out.append(x)
    return out


def content_words(text, limit=10):
    """从一句话里取可作锚点的实词片段（不追求准确，只用于漏项预警）。"""
    chunks = re.split(r"[^\u4e00-\u9fff]+", text)
    words = [c for c in chunks if 2 <= len(c) <= 12]
    words = [w for w in words if not all(ch in NAME_STOP for ch in w)]
    return dedup(sorted(words, key=len, reverse=True))[:limit]


# ---------------------------------------------------------------------------- 原文入库 N0

def split_chapters(text, pattern=None):
    rx = re.compile(pattern) if pattern else CHAPTER_RE
    lines = text.splitlines()
    heads = []
    for i, line in enumerate(lines):
        if line.strip() and rx.match(line):
            heads.append((i, line.strip()))
    chapters = []
    if not heads:
        heads = [(0, "（全文，未检测到章节标题）")]
    for k, (ln, title) in enumerate(heads):
        end_ln = heads[k + 1][0] if k + 1 < len(heads) else len(lines)
        body = "\n".join(lines[ln:end_ln])
        m = re.search(r"第\s*([0-9零〇一二三四五六七八九十百千两]{1,10})\s*[章回节卷部篇集]", title)
        no = cn2int(m.group(1)) if m else k + 1
        chapters.append({"id": "CH%03d" % (no or k + 1), "no": no or k + 1,
                         "title": title[:80], "line_start": ln + 1, "line_end": end_ln,
                         "text": body})
    # 计算字符偏移（相对拼接后的纯文本）
    pos, buf = 0, []
    for ch in chapters:
        body = ch.pop("text")
        ch["start"] = pos
        ch["end"] = pos + len(body)
        ch["chars"] = len(body)
        buf.append(body)
        pos += len(body) + 1
    return chapters, "\n".join(buf)


def extract_candidates(text):
    """人名/术语候选：只做频次与出处，不下事实结论。"""
    names = Counter()
    for ln, line in enumerate(text.splitlines(), 1):
        for m in re.finditer(
                r"(?:^|[ \t（(「【,，。；;])([\u4e00-\u9fff]{2,4})(?=[：:]|\s*(?:说|道|问|答|喊|应|笑|点头|摇头|转身|抬手|皱眉))",
                line):
            n = m.group(1)
            if any(ch in NAME_STOP for ch in n) or n in ("人物", "场景", "内容", "备注"):
                continue
            names[n] += 1
        for m in re.finditer(r"(?:人物|出场|男主|女主|主角)\s*[:：]\s*([^\n｜|]{2,80})", line):
            for n in re.findall(r"[\u4e00-\u9fff]{2,4}", m.group(1)):
                if not any(ch in NAME_STOP for ch in n):
                    names[n] += 1
    name_list = [{"name": n, "count": c} for n, c in names.most_common(80) if c >= 2]
    terms = Counter()
    for m in QUOTE_RE.finditer(text):
        terms[m.group(1)] += 1
    for m in re.finditer(r"[\u4e00-\u9fff]{1,6}(?:系统|空间|金手指|大队|公社|知青|票证|抚恤金|名额|等级|任务|奖励|规则)", text):
        t = m.group(0)
        if 2 <= len(t) <= 10:
            terms[t] += 1
    term_list = [{"term": t, "count": c} for t, c in terms.most_common(60) if c >= 2]
    return name_list, term_list


def build_source_index(source_files, pipeline, chapter_pattern,
                       clean_rules=None, apply_sections=False):
    docs = [load_clean_document(f, clean_rules, apply_sections) for f in source_files]
    removed = [x for d in docs for x in d[1]]
    flags = [x for d in docs for x in d[2]]
    chapters, plain = split_chapters("\n".join(d[0] for d in docs), chapter_pattern)
    name_list, term_list = extract_candidates(plain)
    idx = {
        "generated": datetime.now().isoformat(timespec="seconds"),
        "novel_title": Path(source_files[0]).stem if len(source_files) == 1 else "（多文件合并）",
        "sources": [{"path": f, "chars": len(d[0]),
                     "sha1": hashlib.sha1(Path(f).read_bytes()).hexdigest()[:12]}
                    for f, d in zip(source_files, docs)],
        "chapter_pattern": chapter_pattern or "默认（第N章/回/节/卷/部/篇/集、Chapter N）",
        "chapters": chapters,
        "name_candidates": name_list,
        "term_candidates": term_list,
        "total_chars": len(plain),
        "cleaning": {
            "enabled": bool(clean_rules),
            "removed": len(removed), "flagged": len(flags),
            "apply_sections": bool(apply_sections),
            "clean_sha1": hashlib.sha1(plain.encode("utf-8")).hexdigest()[:12],
            "report": "00_净稿报告.md",
            "line_number_note": "索引表行号基于净稿；删除/标记登记的行号基于清洗前源文件",
        },
    }
    write_clean_report(pipeline, removed, flags, source_files, plain, clean_rules or {})
    (pipeline / "原文纯文本.txt").write_text(plain, encoding="utf-8")
    (pipeline / "source-index.json").write_text(
        json.dumps(idx, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = ["# 原文索引（N0 入库）", "",
             "> 由 `scripts/source_outline.py ingest` 生成。人名/术语为**候选**，不是事实。",
             "> 切片依据：%s" % idx["chapter_pattern"], "",
             "| 章节ID | 章号 | 标题 | 起始行 | 结束行 | 字数 |", "|---|---|---|---|---|---|"]
    for c in chapters:
        lines.append("| %s | %s | %s | %s | %s | %s |" %
                     (c["id"], c["no"], c["title"].replace("|", "／"),
                      c["line_start"], c["line_end"], c["chars"]))
    lines += ["", "合计：%d 章 / %d 字符" % (len(chapters), len(plain)), "",
              "## 人名候选（频次 ≥2，供 S2 人物小传取证）", "",
              "| 候选 | 频次 |", "|---|---|"]
    lines += ["| %s | %d |" % (x["name"], x["count"]) for x in name_list] or ["| （无） | |"]
    lines += ["", "## 术语候选（书名号/领域后缀，频次 ≥2）", "",
              "| 候选 | 频次 |", "|---|---|"]
    lines += ["| %s | %d |" % (x["term"], x["count"]) for x in term_list] or ["| （无） | |"]
    lines += ["", "> 候选仅供 S0 五维拆解与 DR-04 术语表取证，必须回原文核对后才算既定事实。", "",
              "## 净稿（SH-03~06）", "",
              "- 清洗启用：%s；删除 %d 行；待人工确认 %d 行；板块整段剔除：%s" %
              ("是" if clean_rules else "否（--no-clean 或无规则文件）",
               len(removed), len(flags), "开启" if apply_sections else "关闭"),
              "- 本表行号基于**净稿**；逐条删除登记与原文件行号见 `00_净稿报告.md`，两套口径不要混用。",
              "- 乱码行、番外/作者附言板块头默认只标记不自动删（SH-05/06）。", ""]
    (pipeline / "10_原文索引.md").write_text("\n".join(lines), encoding="utf-8")
    return idx


# ---------------------------------------------------------------------------- 纲解析 N1

SECTION_MARK = [
    (re.compile(r"细纲|逐场|分场|beat\s*sheet|scene\s*outline", re.I), "fine"),
    (re.compile(r"大纲|分集梗概|故事梗概|story\s*outline", re.I), "outline"),
]


def split_sections(text):
    """按标题行把一份文件切成 大纲 / 细纲 / 未分类 三段。"""
    parts = {"outline": [], "fine": [], "unknown": []}
    cur = "unknown"
    for line in text.splitlines():
        if re.match(r"^\s*#{0,6}\s*\S", line) and len(line.strip()) <= 60:
            hit = None
            for rx, kind in SECTION_MARK:
                if rx.search(line):
                    hit = kind
                    break
            if hit:
                cur = hit
                continue
        parts[cur].append(line)
    return {k: "\n".join(v) for k, v in parts.items()}


def clean_beat_text(s):
    """去掉行尾的标签段，只留事件本身供生成/展示；原始 text 仍保留作证据。"""
    return re.split(r"[｜|]\s*(?:人物|出场|锚点|钩子|原文|原著|章节|可选|必留|必保)",
                    s)[0].strip(" ｜|；;")


def parse_tags(s):
    must = not bool(re.search(r"(?:可选|可删|备选|参考)", s))
    refs = []
    for m in REF_RE.finditer(s):
        a = m.group("a1") or m.group("a2") or m.group("a3")
        b = m.group("b1") or m.group("b2") or m.group("b3")
        x = cn2int(a)
        y = cn2int(b) if b else x
        if x:
            refs.append((x, y or x))
    hook = re.search(r"钩子\s*[:：]\s*([^｜|;；，,)\]]{1,30})", s)
    chars = re.search(r"(?:人物|出场)\s*[:：]\s*([^｜|;；]{1,60})", s)
    anchors = re.search(r"锚点\s*[:：]\s*([^｜;；\n]{1,120})", s)
    return {
        "must_keep": must,
        "chapter_refs": refs,
        "hook": hook.group(1).strip(" |") if hook else None,
        "characters": dedup(re.findall(r"[\u4e00-\u9fff]{2,4}", chars.group(1))) if chars else [],
        "explicit_anchors": [x.strip() for x in anchors.group(1).split("|")] if anchors else [],
    }


def beats_from_text(text, kind, warnings, source_name):
    eps = []
    cur = None
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        m = EP_HEAD_RE.match(line)
        if m and len(line) <= 120:
            n = (cn2int(m.group("cn")) if m.group("cn") else
                 int(m.group("num") or m.group("n2")))
            title = (m.group("title") or "").strip()
            cur = {"ep": n, "title": title, "chapter_ref": title or None,
                   "hook": None, "beats": []}
            eps.append(cur)
            t = parse_tags(title)
            cur["hook"] = t["hook"]
            cur["chapter_refs"] = t["chapter_refs"]
            continue
        if cur is None:
            if kind == "outline":
                cur = {"ep": 1, "title": "（未标注集号）", "chapter_ref": None,
                       "hook": None, "beats": [], "chapter_refs": []}
                eps.append(cur)
            else:
                warnings.append("%s：出现在任何集号之前的正文被忽略 → %s" % (source_name, line[:40]))
                continue
        b = BEAT_RE.match(line)
        body = b.group("body").strip() if b else line
        body = re.sub(r"^\s*\[?(?:EP\d{3}-)?B?\d{1,2}\]?\s*[.、]?\s*", "", body) if b else body
        if not body:
            continue
        seq = len(cur["beats"]) + 1
        t = parse_tags(body)
        if kind == "outline" and not b and cur["beats"]:
            cur["beats"][-1]["text"] += " " + body
            cur["beats"][-1]["text_clean"] = clean_beat_text(cur["beats"][-1]["text"])
            continue
        cur["beats"].append({
            "id": "EP%03d-B%02d" % (cur["ep"], seq),
            "seq": seq,
            "text": body,
            "text_clean": clean_beat_text(body),
            "must_keep": t["must_keep"] if kind == "fine" else False,
            "hook": t["hook"],
            "characters": t["characters"],
            "explicit_anchors": t["explicit_anchors"],
            "chapter_refs": t["chapter_refs"],
            "origin": kind,
        })
    return eps


def beats_from_table(grid, source_name, warnings):
    if not grid:
        return []
    header = None
    for i, row in enumerate(grid[:8]):
        cells = [str(x).strip() for x in row]
        if any(re.search(r"集|episode|EP", c, re.I) for c in cells) and \
           any(re.search(r"场|内容|情节|细纲|事件|beat|content|scene", c, re.I) for c in cells):
            header = (i, cells)
            break
    if not header:
        warnings.append("%s：表格未识别到表头（需含 集号 与 内容/场次 列），按每行一集处理" % source_name)
        header = (0, [str(x) for x in grid[0]])
    hi, cols = header

    def col(keys):
        for i, c in enumerate(cols):
            if any(k in c for k in keys):
                return i
        return None

    c_ep = col(["集号", "集", "episode", "EP"])
    c_scene = col(["场次", "场", "scene"])
    c_body = col(["内容", "情节", "细纲", "事件", "beat", "content", "正文"])
    c_ref = col(["原文", "章节", "chapter"])
    c_hook = col(["钩子", "hook"])
    c_chars = col(["人物", "出场", "角色"])
    c_anchor = col(["锚点", "anchor"])
    if c_ep is None or c_body is None:
        warnings.append("%s：表格缺「集号」或「内容」列，跳过该文件" % source_name)
        return []
    eps = {}
    for row in grid[hi + 1:]:
        cell = lambda i: (str(row[i]).strip() if i is not None and i < len(row) else "")
        raw_ep = cell(c_ep)
        m = re.search(r"\d{1,4}", raw_ep)
        if not m:
            continue
        ep = int(m.group(0))
        body = cell(c_body)
        if not body:
            continue
        e = eps.setdefault(ep, {"ep": ep, "title": "", "chapter_ref": None,
                                "hook": None, "beats": [], "chapter_refs": []})
        if c_scene is not None and cell(c_scene):
            e["title"] = e["title"] or ("%s" % cell(c_scene))
        if c_hook is not None and cell(c_hook):
            e["hook"] = cell(c_hook)
        refs = parse_tags(cell(c_ref)).get("chapter_refs", []) if c_ref is not None else []
        e["chapter_refs"] = dedup([str(x) for x in e["chapter_refs"]] + [str(x) for x in refs])
        seq = len(e["beats"]) + 1
        e["beats"].append({
            "id": "EP%03d-B%02d" % (ep, seq), "seq": seq, "text": body,
            "text_clean": clean_beat_text(body),
            "must_keep": True, "hook": None,
            "characters": dedup(re.findall(r"[\u4e00-\u9fff]{2,4}", cell(c_chars))) if c_chars is not None else [],
            "explicit_anchors": [x.strip() for x in cell(c_anchor).split("|")] if c_anchor is not None else [],
            "chapter_refs": refs, "origin": "fine",
        })
    return [eps[k] for k in sorted(eps)]


def build_outline(outline_files, idx, pipeline):
    warnings = []
    outline_eps, fine_eps = [], []
    for f in outline_files:
        text, grid = load_document(f)
        if grid is not None:
            got = beats_from_table(grid, Path(f).name, warnings)
            fine_eps += got
            continue
        parts = split_sections(text)
        if parts["outline"].strip():
            outline_eps += beats_from_text(parts["outline"], "outline", warnings, Path(f).name)
        if parts["fine"].strip():
            fine_eps += beats_from_text(parts["fine"], "fine", warnings, Path(f).name)
        if not parts["outline"].strip() and not parts["fine"].strip():
            got = beats_from_text(text, "fine", warnings, Path(f).name)
            if got:
                fine_eps += got
                warnings.append("%s：未检测到「大纲/细纲」分节标题，整份按细纲解析" % Path(f).name)

    # 只给大纲、没给细纲：把大纲逐集条目升格为必留事件，结构锁定降级为「事件锁定」
    if not fine_eps and outline_eps:
        fine_eps = outline_eps
        for e in fine_eps:
            for b in e["beats"]:
                b["must_keep"] = True
                b["origin"] = "outline→fine"
        warnings.append("未提供细纲：已把大纲逐集条目当作必留事件（事件锁定，不做逐场结构锁定）")

    # 合并同集细纲
    by_ep = {}
    for e in fine_eps:
        cur = by_ep.setdefault(e["ep"], {"ep": e["ep"], "title": e["title"],
                                          "hook": e["hook"], "beats": [],
                                          "chapter_refs": list(e.get("chapter_refs") or [])})
        if e["title"] and not cur["title"]:
            cur["title"] = e["title"]
        if e["hook"] and not cur["hook"]:
            cur["hook"] = e["hook"]
        cur["chapter_refs"] += [str(x) for x in (e.get("chapter_refs") or [])]
        cur["beats"] += e["beats"]
    episodes = [by_ep[k] for k in sorted(by_ep)]
    for e in episodes:
        for i, b in enumerate(e["beats"], 1):
            b["seq"] = i
            b["id"] = "EP%03d-B%02d" % (e["ep"], i)

    # 大纲级一致性
    o_eps = sorted({e["ep"] for e in outline_eps})
    f_eps = sorted(by_ep)
    if o_eps and f_eps:
        missing = [x for x in o_eps if x not in f_eps]
        extra = [x for x in f_eps if x not in o_eps]
        if missing:
            warnings.append("大纲有但细纲缺集：%s" % missing)
        if extra:
            warnings.append("细纲有但大纲未列集：%s" % extra)
    if f_eps:
        gaps = [n for n in range(min(f_eps), max(f_eps) + 1) if n not in f_eps]
        if gaps:
            warnings.append("细纲集号不连续：缺 %s" % gaps)
    if not episodes:
        warnings.append("未解析到任何细纲条目 → 请检查集号标题格式，或用 init-template 生成模板")

    chapter_ids = [c["id"] for c in idx["chapters"]]
    chapter_nos = [c["no"] for c in idx["chapters"]]
    name_cands = [x["name"] for x in idx.get("name_candidates", [])]
    term_cands = [x["term"] for x in idx.get("term_candidates", [])]
    plain = (pipeline / "原文纯文本.txt").read_text(encoding="utf-8") \
        if (pipeline / "原文纯文本.txt").exists() else ""

    # ---- 章节绑定：显式引用优先；无引用的集在左右显式引用之间插值，全无引用才按篇幅均分 ----
    n_ch, n_ep = len(chapter_nos), len(episodes)
    chset = {c["id"]: c for c in idx["chapters"]}
    explicit = {}
    for pos, e in enumerate(episodes):
        refs = []
        for r in e.get("chapter_refs") or []:
            nums = [int(x) for x in re.findall(r"\d+", str(r))[:2]]
            if nums:
                a, z = nums[0], (nums[1] if len(nums) > 1 else nums[0])
                if z >= a:
                    refs.extend(range(a, z + 1))
        for b in e["beats"]:
            for a, z in b.get("chapter_refs") or []:
                if z >= a:
                    refs.extend(range(a, z + 1))
        refs = sorted(set(refs))
        if refs:
            e["chapters"] = ["CH%03d" % n for n in refs if n in chapter_nos]
            e["chapter_basis"] = "显式引用"
            explicit[pos] = (min(refs), max(refs))
            bad = [n for n in refs if n not in chapter_nos]
            if bad:
                warnings.append("第%d集引用了不存在的章号 %s（原文共 %d 章）" % (e["ep"], bad, n_ch))
        else:
            e["chapters"] = []
            e["chapter_basis"] = None
    if n_ch and n_ep:
        lo_all, hi_all = min(chapter_nos), max(chapter_nos)
        if not explicit:
            warnings.append("细纲全无原文章节引用：全剧按篇幅**推定**分配，必须人工确认（SO-02）")
        runs, cur = [], []
        for p in range(n_ep):
            if p in explicit:
                if cur:
                    runs.append(cur)
                    cur = []
            else:
                cur.append(p)
        if cur:
            runs.append(cur)
        for run in runs:
            prev = max((p for p in explicit if p < run[0]), default=None)
            nxt = min((p for p in explicit if p > run[-1]), default=None)
            lo = (explicit[prev][1] + 1) if prev is not None else lo_all
            hi = (explicit[nxt][0] - 1) if nxt is not None else hi_all
            if lo > hi:
                lo = hi = (explicit[prev][1] if prev is not None else
                           (explicit[nxt][0] if nxt is not None else lo_all))
            span = max(1, hi - lo + 1)
            for k, p in enumerate(run):
                a = lo + round(k * span / len(run))
                z = max(a, lo + round((k + 1) * span / len(run)) - 1)
                picks = [n for n in chapter_nos if a <= n <= z]
                if not picks:
                    picks = [min(chapter_nos, key=lambda n: abs(n - a))]
                episodes[p]["chapters"] = ["CH%03d" % n for n in picks]
                episodes[p]["chapter_basis"] = "推定分配"
                warnings.append("第%d集未写原文章节引用，按邻居插值**推定**分配 %s（请人工确认）" %
                                (episodes[p]["ep"], ",".join(episodes[p]["chapters"])))

    for e in episodes:
        if not e["chapters"]:
            e["chapter_basis"] = "无原文"
        e["chapter_refs"] = dedup([str(x) for x in e.get("chapter_refs") or []])

        # 锚点 + 原文依据
        slice_text = "\n".join(plain[chset[c]["start"]:chset[c]["end"]]
                              for c in e["chapters"] if c in chset)
        for b in e["beats"]:
            body = b.get("text_clean") or b["text"]
            anc = list(b.get("explicit_anchors") or [])
            anc += [n for n in name_cands if n in body][:8]
            anc += [t for t in term_cands if t in body][:6]
            anc += [m.group(1) for m in QUOTE_RE.finditer(body)]
            anc += list(b.get("characters") or [])
            b["anchors"] = dedup(anc)[:12]
            probes = b["anchors"] or content_words(body)
            b["source_support"] = ("有锚点命中" if any(x in slice_text for x in probes)
                                   else "未在原文切片中找到锚点")
            if b["source_support"] != "有锚点命中":
                warnings.append("%s：细纲条目在原文切片中未找到依据（可能是编剧新增/改写，需用户确认）" % b["id"])

    data = {
        "generated": datetime.now().isoformat(timespec="seconds"),
        "files": [str(f) for f in outline_files],
        "outline_episodes": [{"ep": e["ep"], "title": e["title"],
                              "summary": " ".join((b.get("text_clean") or b["text"])
                                                  for b in e["beats"])[:200]}
                             for e in outline_eps],
        "episodes": episodes,
        "warnings": warnings,
        "chapter_count": n_ch,
        "episode_count": len(episodes),
    }
    (pipeline / "outline.json").write_text(json.dumps(data, ensure_ascii=False, indent=2),
                                           encoding="utf-8")
    lines = ["# 纲解析报告（N1）", "",
             "> 由 `scripts/source_outline.py ingest` 生成。结构以细纲为准，事实以原文为准（SO-01）。", "",
             "| 项 | 值 |", "|---|---|",
             "| 大纲集数 | %d |" % len(outline_eps),
             "| 细纲集数 | %d |" % len(episodes),
             "| 细纲条目总数 | %d |" % sum(len(e["beats"]) for e in episodes),
             "| 原文章节数 | %d |" % n_ch, "",
             "## 逐集", "",
             "| 集 | 标题 | 条目数 | 原文切片 | 依据 |", "|---|---|---|---|---|"]
    for e in episodes:
        lines.append("| %d | %s | %d | %s | %s |" %
                     (e["ep"], (e["title"] or "-").replace("|", "／")[:40], len(e["beats"]),
                      ",".join(e["chapters"]) or "-", e["chapter_basis"]))
    lines += ["", "## 细纲条目（编号即覆盖验收键）", ""]
    for e in episodes:
        lines += ["### 第%d集 %s" % (e["ep"], e["title"] or ""), "",
                  "| 编号 | 必留 | 内容 | 锚点 | 原文依据 |", "|---|---|---|---|---|"]
        for b in e["beats"]:
            lines.append("| %s | %s | %s | %s | %s |" %
                         (b["id"], "是" if b["must_keep"] else "否",
                          (b.get("text_clean") or b["text"]).replace("|", "／")[:90],
                          "、".join(b["anchors"]) or "（无，待人工核对）", b["source_support"]))
        lines.append("")
    lines += ["## 告警（%d 条）" % len(warnings), ""]
    lines += ["- %s" % w for w in warnings] or ["- 无"]
    lines += ["", "> **推定分配、无锚点条目、无原文依据条目** 必须在 S5 挑稿决策点清单里逐条列出（SO-05/06）。", ""]
    (pipeline / "12_纲解析报告.md").write_text("\n".join(lines), encoding="utf-8")
    return data


# ---------------------------------------------------------------------------- 生成包 N2

def find_pipeline_file(pipeline, patterns):
    for pat in patterns:
        got = sorted(pipeline.glob(pat))
        if got:
            return got[0]
    return None


def episode_plan_rows(lines):
    """抽取《逐集三要素表》的逐集行（EP-07：生成期必须看得到信息增量）。"""
    out, in_table = {}, False
    for l in lines:
        s = l.strip()
        if not s.startswith("|"):
            in_table = False
            continue
        if "本集信息增量" in s:
            in_table = True
            continue
        if not in_table or re.fullmatch(r"[\s|:-]+", s):
            continue
        m = re.match(r"\|\s*(\d+)\s*\|", s)
        if m:
            out.setdefault(int(m.group(1)), []).append(s[:400])
    return out


PLAN_EMPTY_CELLS = ("", "-", "—", "–", "___", "待定", "待补", "（空）", "（待补）")


def episode_plan_hooks(lines):
    """从《逐集三要素表》抽「尾钩」列 → {集号: 尾钩文本}。

    三要素表单独成文件时（模板允许），钩子预算行不再写「S1 尚未产出」，
    而是明确标注「尾钩取自三要素表」，避免同一份信息在两个块里一处有、一处空。
    """
    out, hook_col = {}, None
    for l in lines:
        s = l.strip()
        if not s.startswith("|"):
            continue
        cs = [c.strip() for c in s.strip("|").split("|")]
        if "本集信息增量" in s:
            hook_col = next((i for i, c in enumerate(cs) if "尾钩" in c), None)
            continue
        if hook_col is None or re.fullmatch(r"[\s|:-]+", s):
            continue
        m = re.match(r"\d+", cs[0]) if cs else None
        if not m or hook_col >= len(cs):
            continue
        val = cs[hook_col].strip()
        if val in PLAN_EMPTY_CELLS:
            continue
        out.setdefault(int(m.group(0)), val[:200])
    return out


def build_packets(data, idx, pipeline, max_chars):
    outdir = pipeline / "packets"
    outdir.mkdir(parents=True, exist_ok=True)
    plain_path = pipeline / "原文纯文本.txt"
    plain = plain_path.read_text(encoding="utf-8") if plain_path.exists() else ""
    chset = {c["id"]: c for c in idx["chapters"]}
    anchor_file = find_pipeline_file(pipeline, ["02_人物小传*.md"])
    term_file = find_pipeline_file(pipeline, ["03_术语表*.md"])
    budget_file = find_pipeline_file(pipeline, ["01_钩子预算表*.md"])
    plan_file = find_pipeline_file(pipeline, ["01_分集规划表*.md", "01_钩子预算表*.md"])
    brief_file = find_pipeline_file(pipeline, ["00_需求与体检*.md"])
    anchors = anchor_file.read_text(encoding="utf-8")[:6000] if anchor_file else "（S2 尚未建档：先跑 S2 再 refresh）"
    terms = term_file.read_text(encoding="utf-8")[:3000] if term_file else "（S2 尚未建档：先跑 S2 再 refresh）"
    budget_all = budget_file.read_text(encoding="utf-8").splitlines() if budget_file else []
    plan_all = plan_file.read_text(encoding="utf-8").splitlines() if plan_file else []
    plan_map = episode_plan_rows(plan_all)
    plan_hooks = episode_plan_hooks(plan_all)
    brief = brief_file.read_text(encoding="utf-8")[:2500] if brief_file else "（S0 尚未登记）"
    prev_titles = []
    for e in data["episodes"]:
        ep = e["ep"]
        lines = ["# 第%d集 生成包（结构锁定 · Mode 3）" % ep, "",
                 "> 由 `scripts/source_outline.py` 生成。本包是**唯一可入上下文的原文范围**（SO-02/08）。",
                 "> 结构以细纲为准，事实以原文为准；不得改动细纲事件顺序、不得新增大纲外大事件（SO-01/03）。", "",
                 "## 一、需求与预算", "", brief[:1200], ""]
        ep_pat = re.compile(r"(第\s*0*%d\s*集|EP0*%d\b|^\|?\s*0*%d\s*\|)" % (ep, ep, ep))
        hit = [l for l in budget_all if ep_pat.search(l)][:12]
        plan_hit = plan_map.get(ep, [])
        if hit:
            budget_note = "（来源：《%s》）" % budget_file.name
            budget_rows = hit
        elif plan_hit:
            budget_note = ("（《01_钩子预算表》未命中本集行：本集尾钩取自《%s》「尾钩」列，"
                           "与下方三要素行同源）" %
                           (plan_file.name if plan_file else "逐集三要素表"))
            budget_rows = ["尾钩：%s" % (plan_hooks.get(ep) or "（尾钩列未填，需补）")]
        else:
            budget_note = ""
            budget_rows = ["（S1 尚未产出本集预算行，且未建《逐集三要素表》：先跑 S1 再 refresh）"]
        lines += ["**本集钩子预算行**（S1 产物，未命中则标注待补）%s：" % budget_note, ""]
        lines += ["```"] + budget_rows + ["```", ""]
        lines += ["**本集三要素行**（EP-07：核心事件／明确冲突／信息增量／尾钩／出处）：", ""]
        lines += ["```"] + (plan_hit or ["（未建《逐集三要素表》：跑 check_episode_plan.py init-template 补齐，"
                                        "S4 合并门会判 FAIL）"]) + ["```", ""]
        lines += ["## 二、本集细纲（逐条必须落地，编号用于覆盖验收）", ""]
        for b in e["beats"]:
            lines.append("- **%s**%s %s｜锚点：%s" %
                         (b["id"], "[必留]" if b["must_keep"] else "[可选]",
                          b.get("text_clean") or b["text"],
                          "、".join(b["anchors"]) or "（无，需人工核对）"))
        lines += ["", "## 三、原文切片（%s｜%s）" % (",".join(e["chapters"]) or "无", e["chapter_basis"]), ""]
        slice_text = "\n".join(plain[chset[c]["start"]:chset[c]["end"]]
                              for c in e["chapters"] if c in chset)
        if not slice_text:
            lines.append("（无对应原文切片，需人工补）")
        else:
            truncated = len(slice_text) > max_chars
            lines.append("```text")
            lines.append(slice_text[:max_chars])
            lines.append("```")
            if truncated:
                lines += ["", "> ⚠ **切片已截断**：原 %d 字符，注入前 %d 字符。禁止把全文另塞进上下文；"
                          "需要更多内容请细纲写显式章节引用并分批，或调大 `--packet-max-chars`。" %
                          (len(slice_text), max_chars)]
        lines += ["", "## 四、一致性锚点（DR-01 四件套，既定事实不得改动）", "",
                  "### 人物小传 + 金手指卡", "", anchors, "",
                  "### 术语表", "", terms, "",
                  "### 前情提要（前序集细纲摘要，滚动生成时以 pipeline 前情卡为准）", ""]
        lines += ["- 第%d集：%s" % (x, t) for x, t in prev_titles[-10:]] or ["- （首集为空）"]
        lines += ["", "## 五、覆盖清单（生成后由 `check` 逐条核对，禁止模型自报）", ""]
        lines += ["- [ ] %s %s" % (b["id"], (b.get("text_clean") or b["text"])[:50])
                  for b in e["beats"]]
        lines += ["", "> 生成时按 `workflows/source-outline-draft.md` N3：版本数默认 2，"
                  "差异化只在呈现层（切入点/场面调度/台词密度/卡点切法），**不改事件结构**。", ""]
        (outdir / ("ep%03d.md" % ep)).write_text("\n".join(lines), encoding="utf-8")
        prev_titles.append((ep, "；".join((b.get("text_clean") or b["text"])[:24]
                                         for b in e["beats"][:3])))
    return outdir, len(data["episodes"])


# ---------------------------------------------------------------------------- 覆盖验收 N4

def draft_files(draft):
    """只扫稿件；报告/索引/登记表不得进入覆盖验收（与 check_gate_a.py 同口径）。"""
    return iter_draft_files(draft)


def check_one(path, ep_data, idx, config):
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    findings = []
    beats = ep_data["beats"] if ep_data else []
    name_set = {x["name"] for x in idx.get("name_candidates", [])}
    name_set |= set(config.get("name_whitelist", []))
    for e in (config.get("outline_characters") or []):
        name_set.add(e)

    # GA-06 细纲覆盖
    covered = 0
    for b in beats:
        if not b.get("must_keep"):
            continue
        body = b.get("text_clean") or b["text"]
        anchors = [a for a in b.get("anchors", []) if a]
        if not anchors:
            anchors = content_words(body, 6)
            note = "细纲未给锚点，脚本用内容词做漏项预警；需人工逐条语义核对"
        else:
            note = "锚点命中只证明词出现，不证明语义覆盖"
        hits = [(i, a) for i, line in enumerate(lines, 1) for a in anchors if a in line]
        if not hits:
            findings.append({"code": "GA-06", "level": "FAIL",
                             "line": 0, "evidence": "%s 未命中任何锚点（%s）｜%s" %
                             (b["id"], "、".join(anchors[:5]) or "无", body[:50]),
                             "note": note})
        else:
            covered += 1
    must_n = len([b for b in beats if b.get("must_keep")])
    stats = {"file": str(path), "ep": ep_data["ep"] if ep_data else None,
             "beats": must_n, "covered": covered,
             "coverage": (covered / must_n) if must_n else None,
             "cjk_chars": len(CJK.findall(text)), "lines": len(lines)}

    # GA-07 原文忠实（人名/说话人）
    speakers = []
    for i, line in enumerate(lines, 1):
        m = SPEAKER_RE.match(line)
        if m and len(m.group("name").strip()) <= 12:
            n = re.sub(r"[（(].*?[)）]", "", m.group("name")).strip()
            n = re.sub(r"(OS|VO|画外|旁白)$", "", n).strip()
            if 2 <= len(n) <= 4 and CJK.fullmatch(n):
                speakers.append((i, n))
    unknown = sorted({n for _, n in speakers if n not in name_set})
    if unknown:
        first = next((i for i, n in speakers if n in unknown), 0)
        findings.append({"code": "GA-07", "level": "INFO", "line": first,
                         "evidence": "原文候选表外的说话人：%s" % "、".join(unknown[:12]),
                         "note": "可能是原文已有但未被候选表捕获，也可能是新增角色/异写；须回原文核对（DR-02/04）"})
    if not name_set:
        findings.append({"code": "GA-07", "level": "INFO", "line": 0,
                         "evidence": "原文入库未抽出人名候选",
                         "note": "人名核对退化为 INFO，需人工逐场核对"})

    # GA-08 大纲外新增大事件（只列证据，不定性）
    beat_anchors = dedup([a for b in beats for a in b.get("anchors", [])])
    for i, line in enumerate(lines, 1):
        m = EVENT_RE.search(line)
        if not m:
            continue
        if any(a and a in line for a in beat_anchors):
            continue
        findings.append({"code": "GA-08", "level": "INFO", "line": i,
                         "evidence": "疑似新增事件「%s」｜%s" % (m.group(0), line.strip()[:70]),
                         "note": "该行不命中本集任何细纲锚点；是否属细纲/大纲外新增事件由人工判定（SO-05）"})
    return findings, stats


def write_check_report(out, results, warnings):
    lines = ["# 按纲改编覆盖验收报告（GA-06~08）", "",
             "> 由 `scripts/source_outline.py check` 生成。数值为脚本计数，**禁止模型自报覆盖**。", "",
             "> 诚实边界：锚点命中 ≠ 语义覆盖；无锚点条目、推定章节、原文外人名一律标 INFO 交人工。", "",
             "| 文件 | 集 | 必留条目 | 命中 | 覆盖率 | 汉字数 | FAIL |", "|---|---|---|---|---|---|---|"]
    total_fail = total_info = 0
    for r in results:
        s = r["stats"]
        n_fail = sum(f["level"] == "FAIL" for f in r["findings"])
        n_info = sum(f["level"] == "INFO" for f in r["findings"])
        total_fail += n_fail
        total_info += n_info
        rate = "-" if s["coverage"] is None else "%.0f%%" % (s["coverage"] * 100)
        lines.append("| %s | %s | %d | %d | %s | %d | %d |" %
                     (Path(s["file"]).name, s["ep"] or "-", s["beats"], s["covered"],
                      rate, s["cjk_chars"], n_fail))
    lines += ["", "## 逐条证据", ""]
    for r in results:
        lines += ["### %s" % Path(r["stats"]["file"]).name, ""]
        if not r["findings"]:
            lines += ["无告警。", ""]
        for f in r["findings"]:
            lines.append("- **%s %s**｜行 %s｜%s｜%s" %
                         (f["level"], f["code"], f["line"], f["evidence"], f["note"]))
        lines.append("")
    if warnings:
        lines += ["## 来自纲解析的告警（沿用）", ""] + ["- %s" % w for w in warnings] + [""]
    lines += ["---", "", "**合计**：FAIL %d ／ INFO %d ／ 文件 %d" %
              (total_fail, total_info, len(results)), "",
              "任一 **GA-06 FAIL**（必留细纲条目未落地）→ 该版本判杀并记死因；"
              "INFO 逐条进 S5 挑稿决策点清单，不得静默忽略。", ""]
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text("\n".join(lines), encoding="utf-8")
    return total_fail


def run_check(draft, pipeline, out, json_out, fail_on_unverified=False):
    op = pipeline / "outline.json"
    ip = pipeline / "source-index.json"
    if not op.exists() or not ip.exists():
        print("[ERROR] 缺 outline.json / source-index.json，请先跑 ingest", file=sys.stderr)
        return 2
    data = json.loads(op.read_text(encoding="utf-8"))
    idx = json.loads(ip.read_text(encoding="utf-8"))
    cfg_path = pipeline / "gate_a_config.json"
    config = json.loads(cfg_path.read_text(encoding="utf-8")) if cfg_path.exists() else {}
    # 细纲「人物：」标签里的人名是原文候选表的补充证据（仍不改事实结论）
    config["outline_characters"] = dedup(
        [c for e in data["episodes"] for b in e["beats"] for c in b.get("characters", [])])
    ep_map = {e["ep"]: e for e in data["episodes"]}
    files = draft_files(draft)
    if not files:
        print("[ERROR] 未找到初稿文件：%s" % draft, file=sys.stderr)
        return 2
    results = []
    for f in files:
        m = re.search(r"ep(\d{3,4})", f.name, re.I)
        ep = int(m.group(1)) if m else None
        findings, stats = check_one(f, ep_map.get(ep), idx, config)
        if ep is None:
            findings.append({"code": "GA-06", "level": "INFO", "line": 0,
                             "evidence": "文件名无法解析集号（需 epNNN_*.md）",
                             "note": "无法绑定细纲，人工核对"})
        elif ep not in ep_map:
            stats["ep"] = ep
            findings.append({"code": "GA-06", "level": "FAIL", "line": 0,
                             "evidence": "第%d集无细纲条目" % ep,
                             "note": "细纲未覆盖本集，禁止擅自出稿（SO-04）"})
        if fail_on_unverified:
            pass
        results.append({"findings": findings, "stats": stats})
        n_fail = sum(x["level"] == "FAIL" for x in findings)
        print("[%s] %s｜必留 %d／命中 %d｜FAIL %d" %
              ("杀" if n_fail else "过", f.name, stats["beats"], stats["covered"], n_fail))
    total_fail = write_check_report(out, results, data.get("warnings", [])) if out else \
        sum(sum(x["level"] == "FAIL" for x in r["findings"]) for r in results)
    if out:
        print("[OK] 报告：%s" % out)
    if json_out:
        Path(json_out).write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    return 1 if total_fail else 0


# ---------------------------------------------------------------------------- 命令

def cmd_ingest(args):
    pipeline = Path(args.pipeline)
    pipeline.mkdir(parents=True, exist_ok=True)
    src = expand(args.source, SOURCE_EXT)
    out = expand(args.outline, OUTLINE_EXT)
    if not src and not out:
        print("[ERROR] 首次 ingest 需 --source 与 --outline；仅刷新生成包请用 refresh", file=sys.stderr)
        return 2
    clean_rules = None
    if not getattr(args, "no_clean", False):
        try:
            clean_rules = load_clean_rules(getattr(args, "clean_config", None),
                                          getattr(args, "exclude_patterns", None))
        except ValueError as e:
            print("[ERROR] %s" % e, file=sys.stderr)
            return 2
    apply_sections = bool(getattr(args, "apply_sections", False))
    if src:
        idx = build_source_index(src, pipeline, args.chapter_pattern,
                                 clean_rules, apply_sections)
        c = idx["cleaning"]
        print("[OK] 原文入库：%d 文件 / %d 章 / %d 字符 / 人名候选 %d" %
              (len(src), len(idx["chapters"]), idx["total_chars"], len(idx["name_candidates"])))
        print("[OK] 净稿：启用=%s｜删除 %d 行｜待人工确认 %d 行｜报告 00_净稿报告.md" %
              ("是" if clean_rules else "否", c["removed"], c["flagged"]))
    else:
        ip = pipeline / "source-index.json"
        if not ip.exists():
            print("[ERROR] 缺 source-index.json，请带 --source", file=sys.stderr)
            return 2
        idx = json.loads(ip.read_text(encoding="utf-8"))
    if out:
        data = build_outline(out, idx, pipeline)
        print("[OK] 纲解析：%d 集 / %d 条目 / 告警 %d 条" %
              (data["episode_count"], sum(len(e["beats"]) for e in data["episodes"]),
               len(data["warnings"])))
    else:
        op = pipeline / "outline.json"
        if not op.exists():
            print("[ERROR] 缺 outline.json，请带 --outline", file=sys.stderr)
            return 2
        data = json.loads(op.read_text(encoding="utf-8"))
    d, n = build_packets(data, idx, pipeline, args.packet_max_chars)
    print("[OK] 生成包：%s（%d 集，单集原文上限 %d 字符）" % (d, n, args.packet_max_chars))
    ipath = pipeline / "ingest-manifest.json"
    ipath.write_text(json.dumps({
        "generated": datetime.now().isoformat(timespec="seconds"),
        "sources": src, "outlines": out,
        "packet_max_chars": args.packet_max_chars,
        "chapter_pattern": args.chapter_pattern,
        "cleaning": idx.get("cleaning", {}),
        "note": "S1/S2 完成后跑 refresh 重打生成包；原文/纲变更需重新 ingest",
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


def cmd_refresh(args):
    pipeline = Path(args.pipeline)
    man = pipeline / "ingest-manifest.json"
    if man.exists():
        m = json.loads(man.read_text(encoding="utf-8"))
        args.packet_max_chars = m.get("packet_max_chars", args.packet_max_chars)
    return finish_refresh(pipeline, args.packet_max_chars)


def finish_refresh(pipeline, max_chars):
    op, ip = pipeline / "outline.json", pipeline / "source-index.json"
    if not op.exists() or not ip.exists():
        print("[ERROR] 缺 outline.json / source-index.json，请先跑 ingest", file=sys.stderr)
        return 2
    data = json.loads(op.read_text(encoding="utf-8"))
    idx = json.loads(ip.read_text(encoding="utf-8"))
    d, n = build_packets(data, idx, pipeline, max_chars)
    print("[OK] 生成包已刷新：%s（%d 集）" % (d, n))
    return 0


TEMPLATE_FINE = """# 细纲

> 复制本文件按集填。集号标题必须独占一行；每条以 - 开头即一个「必留细纲条目」。
> 行内可写标签：原文第3-5章 / 钩子：身份揭露 / 人物：宁清和、谢知予 / 锚点：宁清和|手表
> 写「可选」的条目不参与覆盖判杀；不写则全部必留。

## 第1集｜落水获救｜原文第1章｜钩子：身份揭露
- 宁清和落水，谢知予把他救上岸｜人物：宁清和、谢知予｜锚点：宁清和|谢知予|落水
- 宁清和醒来，意识到自己穿越｜锚点：醒来|穿越
- （可选）河边围观群众议论，用于补气氛

## 第2集｜系统首触发｜原文第2章｜钩子：金手指揭示
- 青年甲在国营饭店炫耀新手表｜锚点：青年甲|新手表
- 系统触发，宁清和得到同款手表｜锚点：系统|手表
"""

TEMPLATE_OUTLINE = """# 大纲

> 全剧/分集骨架，一句话到三句话一集。只写事件，不写台词。
> 大纲与细纲可以放同一份文件（用 # 大纲 / # 细纲 分节），也可以分两个文件都传给 --outline。

## 第1集
宁清和穿越落水被救，摸清原主处境，继母已替他报了下乡名额。

## 第2集
吹牛暴富系统首次触发，宁清和决定靠听人吹牛攒物资下乡。
"""

TEMPLATE_CSV = """集号,场次,内容,原文范围,钩子,人物,锚点
1,1-1,宁清和落水被谢知予救起,第1章,身份揭露,宁清和|谢知予,宁清和|谢知予|落水
1,1-2,宁清和醒来意识到穿越,第1章,,宁清和,醒来|穿越
2,2-1,青年甲炫耀新手表,第2章,金手指揭示,青年甲,青年甲|新手表
2,2-2,系统触发宁清和得到手表,第2章,,宁清和,系统|手表
"""


def cmd_init_template(args):
    d = Path(args.dir)
    d.mkdir(parents=True, exist_ok=True)
    for name, body in (("细纲模板.md", TEMPLATE_FINE), ("大纲模板.md", TEMPLATE_OUTLINE),
                       ("细纲模板.csv", TEMPLATE_CSV)):
        (d / name).write_text(body, encoding="utf-8")
    print("[OK] 模板已生成于 %s" % d)
    print("    细纲模板.md / 大纲模板.md / 细纲模板.csv（也支持 .xlsx，列名同上）")
    return 0


def make_mini_docx(p, paragraphs):
    body = "".join("<w:p><w:r><w:t>%s</w:t></w:r></w:p>" % html.escape(x) for x in paragraphs)
    xml = '<?xml version="1.0" encoding="UTF-8"?><w:document xmlns:w="%s"><w:body>%s</w:body></w:document>' % (
        W_NS[1:-1], body)
    with zipfile.ZipFile(p, "w") as z:
        z.writestr("word/document.xml", xml)


def make_mini_xlsx(p, rows):
    strs, seen = [], {}
    for row in rows:
        for v in row:
            if v not in seen:
                seen[v] = len(strs)
                strs.append(v)
    ss = '<?xml version="1.0"?><sst xmlns="%s">%s</sst>' % (
        S_NS[1:-1], "".join('<si><t>%s</t></si>' % html.escape(s) for s in strs))
    sheet_rows = []
    for ri, row in enumerate(rows, 1):
        cells = []
        for ci, v in enumerate(row):
            col = chr(65 + ci)
            cells.append('<c r="%s%d" t="s"><v>%d</v></c>' % (col, ri, seen[v]))
        sheet_rows.append('<row r="%d">%s</row>' % (ri, "".join(cells)))
    sh = '<?xml version="1.0"?><worksheet xmlns="%s"><sheetData>%s</sheetData></worksheet>' % (
        S_NS[1:-1], "".join(sheet_rows))
    with zipfile.ZipFile(p, "w") as z:
        z.writestr("xl/sharedStrings.xml", ss)
        z.writestr("xl/worksheets/sheet1.xml", sh)


def selftest():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        pl = root / "pipeline"
        pl.mkdir()
        novel = root / "小说原文.md"
        novel.write_text(
            "第一章 落水\n"
            "宁清和沉进河里，浑黄的河水灌进鼻腔。谢知予跃入水中，把他托上岸。\n"
            "（未完待续，请点击下一页继续阅读）\n"
            "网站地图 | 版权归原作者所有\n"
            "本站所有小说为转载作品，所有章节均由网友上传，转载至本站只是为了宣传本书让更多读者欣赏。\n"
            "这一行是\ufffd乱码\ufffd锟斤拷测试用的一句很长很长的话啊啊啊啊啊啊啊\n"
            "番外一 旧事\n"
            "宁清和醒来，盯着自己枯瘦的手，半天没说出话。\n"
            "第二章 手表\n"
            "国营饭店门口，青年甲晃着腕上的新手表显摆。\n"
            "宁清和脑子里叮的一声，吹牛暴富系统触发，货架上多出一只同款手表。\n",
            encoding="utf-8")
        fine = root / "纲.md"
        fine.write_text(
            "# 大纲\n## 第1集\n落水获救，摸清处境。\n## 第2集\n系统首触发。\n"
            "# 细纲\n"
            "## 第1集｜落水获救｜原文第1章｜钩子：身份揭露\n"
            "- 宁清和落水，谢知予救他上岸｜人物：宁清和、谢知予｜锚点：宁清和|谢知予|落水\n"
            "- 宁清和醒来意识到穿越｜锚点：醒来|穿越\n"
            "## 第2集｜系统触发｜原文第2章\n"
            "- 青年甲炫耀新手表｜锚点：青年甲|新手表\n"
            "- 系统触发宁清和得到手表｜锚点：系统|手表\n",
            encoding="utf-8")
        # 二进制格式读取器
        dx, xs = root / "原文.docx", root / "细纲表.xlsx"
        make_mini_docx(dx, ["第一章 测试", "宁清和走了进来。"])
        make_mini_xlsx(xs, [["集号", "场次", "内容", "原文范围", "锚点"],
                            ["1", "1-1", "宁清和走进屋", "第1章", "宁清和|走进屋"]])
        assert "宁清和" in read_docx(dx), "docx 读取失败"
        rows = read_xlsx_rows(xs)
        assert rows[1][2] == "宁清和走进屋", "xlsx 读取失败：%s" % rows
        print("[PASS] docx / xlsx 读取器")

        class A:
            source, outline, pipeline = [str(novel)], [str(fine)], str(pl)
            chapter_pattern, packet_max_chars = None, 16000
        assert cmd_ingest(A()) == 0
        data = json.loads((pl / "outline.json").read_text(encoding="utf-8"))
        idx = json.loads((pl / "source-index.json").read_text(encoding="utf-8"))
        assert len(idx["chapters"]) == 2, idx["chapters"]
        assert data["episode_count"] == 2, data
        assert sum(len(e["beats"]) for e in data["episodes"]) == 4
        assert all(e["chapter_basis"] == "显式引用" for e in data["episodes"])
        assert (pl / "packets" / "ep001.md").exists()
        print("[PASS] ingest：章节切片 / 细纲编号 / 显式引用 / 生成包")

        # 净稿（SH-03~06）：整行噪声删除并登记，乱码/板块头只标记
        cl = idx["cleaning"]
        clean_text = (pl / "原文纯文本.txt").read_text(encoding="utf-8")
        clean_rep = (pl / "00_净稿报告.md").read_text(encoding="utf-8")
        assert cl["enabled"] and cl["removed"] == 3 and cl["flagged"] >= 2, cl
        assert "未完待续" not in clean_text and "网站地图" not in clean_text
        assert "本站所有小说为转载作品" not in clean_text, "SH-L06 应删转载站免责声明"
        assert "番外一" in clean_text and "锟斤拷" in clean_text, "板块头/乱码行默认不删"
        assert "SH-L01" in clean_rep and "原始行号" in clean_rep and "SH-S01" in clean_rep
        assert "SH-L06" in clean_rep, "SH-L06 删除须逐条登记规则 ID"
        assert "authorization" not in json.loads(
            (pl / "ingest-manifest.json").read_text(encoding="utf-8")), "授权字段应已剥离"
        print("[PASS] 净稿：删除 3 行并登记（含 SH-L06 转载站声明）/ 乱码与番外只标记 / 两套行号口径 / 授权字段已剥离")

        # --no-clean 与 --exclude-patterns 的向后兼容
        pl4 = root / "pipeline4"
        pl4.mkdir()

        class D:
            source, outline, pipeline = [str(novel)], [str(fine)], str(pl4)
            chapter_pattern, packet_max_chars = None, 16000
            no_clean = True
        assert cmd_ingest(D()) == 0
        assert "未完待续" in (pl4 / "原文纯文本.txt").read_text(encoding="utf-8")

        class E:
            source, outline, pipeline = [str(novel)], [str(fine)], str(pl4)
            chapter_pattern, packet_max_chars = None, 16000
            no_clean = False
            exclude_patterns = ["番外一 旧事"]
            clean_config, apply_sections = None, False
        assert cmd_ingest(E()) == 0
        assert "番外一" not in (pl4 / "原文纯文本.txt").read_text(encoding="utf-8")
        print("[PASS] --no-clean 原样入库 / --exclude-patterns 追加规则生效")

        # --apply-sections 整段剔除；删除超上限时整体降级为只标记
        class F:
            source, outline, pipeline = [str(novel)], [str(fine)], str(pl4)
            chapter_pattern, packet_max_chars = None, 16000
            no_clean, exclude_patterns, clean_config = False, [], None
            apply_sections = True
        assert cmd_ingest(F()) == 0
        assert "半天没说出话" not in (pl4 / "原文纯文本.txt").read_text(encoding="utf-8")

        cfg = root / "clean_zero.json"
        cfg.write_text(json.dumps({
            "defaults": {"apply_line_removal": True, "max_removed_ratio": 0,
                         "min_removed_chars_floor": 0, "max_noise_line_chars": 60,
                         "min_garbled_line_chars": 12, "min_cjk_ratio": 0.2},
            "exclude_line_patterns": [{"id": "TEST-01", "pattern": "未完待续", "reason": "自检"}],
            "section_head_patterns": [], "garbled": {},
        }, ensure_ascii=False), encoding="utf-8")

        class G:
            source, outline, pipeline = [str(novel)], [str(fine)], str(pl4)
            chapter_pattern, packet_max_chars = None, 16000
            no_clean, exclude_patterns = False, []
            clean_config, apply_sections = str(cfg), False
        assert cmd_ingest(G()) == 0
        assert "未完待续" in (pl4 / "原文纯文本.txt").read_text(encoding="utf-8"), "超上限应降级不删"
        assert "降级" in (pl4 / "00_净稿报告.md").read_text(encoding="utf-8")
        print("[PASS] --apply-sections 整段剔除 / 删除超上限整体降级为只标记")

        out = root / "outputs"
        out.mkdir()
        (out / "ep001_A_v1.md").write_text(
            "# 第1集 A版\n宁清和沉进河里。\n谢知予把他救上岸。\n"
            "宁清和醒来，意识到自己穿越了。\n", encoding="utf-8")
        (out / "ep002_A_v1.md").write_text(
            "# 第2集 A版\n青年甲晃着新手表。\n吹牛暴富系统触发，宁清和得到手表。\n", encoding="utf-8")
        (out / "ep002_B_v1.md").write_text(
            "# 第2集 B版\n宁清和在街上闲逛，什么也没发生。\n", encoding="utf-8")
        rep = out / "01_体检报告_纲源.md"
        js = out / "覆盖结果.json"
        rc = run_check(str(out), pl, str(rep), str(js))
        body = rep.read_text(encoding="utf-8")
        rs = json.loads(js.read_text(encoding="utf-8"))
        by_name = {Path(r["stats"]["file"]).name: r for r in rs}
        assert rc == 1, "缺条目的 B 版应判杀"
        assert "GA-06" in body and "ep002_B_v1" in body
        assert sum(f["level"] == "FAIL" for f in by_name["ep002_B_v1.md"]["findings"]) >= 2
        assert sum(f["level"] == "FAIL" for f in by_name["ep001_A_v1.md"]["findings"]) == 0
        assert by_name["ep001_A_v1.md"]["stats"]["covered"] == 2
        print("[PASS] check：缺细纲条目的版本被判 GA-06 FAIL，完整版本 2/2 覆盖，报告落盘")

        # 表格格式也能解析
        pl2 = root / "pipeline2"
        pl2.mkdir()

        class B:
            source, outline, pipeline = [str(dx)], [str(xs)], str(pl2)
            chapter_pattern, packet_max_chars = None, 16000
        assert cmd_ingest(B()) == 0
        d2 = json.loads((pl2 / "outline.json").read_text(encoding="utf-8"))
        assert d2["episode_count"] == 1 and len(d2["episodes"][0]["beats"]) == 1
        print("[PASS] 表格细纲（.xlsx）与 docx 原文端到端入库")

        # 只给大纲 + 邻居插值
        pl3 = root / "pipeline3"
        pl3.mkdir()
        outline_only = root / "只有大纲.md"
        outline_only.write_text(
            "# 大纲\n## 第1集｜原文第1章\n宁清和落水获救。\n## 第2集\n宁清和在国营饭店听人吹牛。\n",
            encoding="utf-8")

        class C:
            source, outline, pipeline = [str(novel)], [str(outline_only)], str(pl3)
            chapter_pattern, packet_max_chars = None, 16000
        assert cmd_ingest(C()) == 0
        d3 = json.loads((pl3 / "outline.json").read_text(encoding="utf-8"))
        assert d3["episode_count"] == 2
        assert all(b["must_keep"] for e in d3["episodes"] for b in e["beats"])
        assert d3["episodes"][0]["chapter_basis"] == "显式引用"
        assert d3["episodes"][1]["chapter_basis"] == "推定分配"
        assert any("大纲逐集条目" in w for w in d3["warnings"])
        print("[PASS] 只有大纲时升格为必留事件 + 邻居插值推定")

        # refresh 重打包
        (pl3 / "01_钩子预算表.md").write_text("| 集 | 钩子 |\n|---|---|\n| 1 | 身份揭露 |\n",
                                               encoding="utf-8")
        (pl3 / "01_分集规划表.md").write_text(
            "# 分集规划\n\n## 逐集三要素表\n\n"
            "| 集 | 本集核心事件 | 明确冲突 | 本集信息增量 | 尾钩 | 出处 |\n"
            "|---|---|---|---|---|---|\n"
            "| 1 | 落水获救 | 主角要活命、河水不给 | 观众新知道：穿越了 | 醒来停在半句 | CH001 |\n",
            encoding="utf-8")

        assert finish_refresh(pl3, 16000) == 0
        packet = (pl3 / "packets" / "ep001.md").read_text(encoding="utf-8")
        assert "身份揭露" in packet
        assert "观众新知道：穿越了" in packet, "EP-07 三要素行须注入生成包"
        print("[PASS] refresh：S1 建档后生成包注入预算行 + EP-07 三要素行")

        # 三要素表单独成文件、没有钩子预算表时，预算行不得再谎报「S1 尚未产出」
        (pl3 / "01_钩子预算表.md").unlink()
        assert finish_refresh(pl3, 16000) == 0
        packet2 = (pl3 / "packets" / "ep001.md").read_text(encoding="utf-8")
        assert "尾钩取自《01_分集规划表.md》" in packet2, packet2[:1200]
        assert "尾钩：醒来停在半句" in packet2, packet2[:1200]
        assert "S1 尚未产出本集预算行" not in packet2
        assert "观众新知道：穿越了" in packet2, "三要素行仍须保留"
        print("[PASS] 三要素单独成文件时：预算行标同源派生、不再谎报 S1 缺产物")
        print("[PASS] selftest 全部通过")
        return 0


def main():
    ap = argparse.ArgumentParser(description="按纲改编：入库 / 生成包 / 覆盖验收")
    sub = ap.add_subparsers(dest="cmd")

    ing = sub.add_parser("ingest", help="原文 + 大纲/细纲入库，产出索引、解析报告、生成包")
    ing.add_argument("--source", action="append", default=[], help="小说原文文件/目录，可重复")
    ing.add_argument("--outline", action="append", default=[], help="大纲或细纲文件/目录，可重复")
    ing.add_argument("--pipeline", required=True, help="项目 pipeline 目录")
    ing.add_argument("--chapter-pattern", help="自定义章节标题正则")
    ing.add_argument("--packet-max-chars", type=int, default=16000, help="单集原文切片上限字符数")
    ing.add_argument("--clean-config", help="自定义净稿规则 JSON（默认 reference/source_clean.rules.json）")
    ing.add_argument("--exclude-patterns", action="append", default=[],
                     help="追加整行剔除正则，可重复（项目专属广告/推广行）")
    ing.add_argument("--no-clean", action="store_true", help="关闭净稿清洗，原文原样入库")
    ing.add_argument("--apply-sections", action="store_true",
                     help="启用番外/作者附言整段剔除（默认只标记不删，SH-06）")

    ref = sub.add_parser("refresh", help="S1/S2 建档后重新打包生成包")
    ref.add_argument("--pipeline", required=True)
    ref.add_argument("--packet-max-chars", type=int, default=16000)

    chk = sub.add_parser("check", help="初稿覆盖验收 GA-06~08")
    chk.add_argument("--draft", required=True, help="初稿文件或 outputs 目录")
    chk.add_argument("--pipeline", required=True)
    chk.add_argument("--out", help="Markdown 报告路径")
    chk.add_argument("--json", dest="json_out", help="JSON 结果路径")

    tpl = sub.add_parser("init-template", help="生成细纲/大纲模板")
    tpl.add_argument("dir", help="模板输出目录")

    sub.add_parser("selftest", help="内置端到端自检")
    a = ap.parse_args()
    if a.cmd == "ingest":
        return cmd_ingest(a)
    if a.cmd == "refresh":
        return cmd_refresh(a)
    if a.cmd == "check":
        return run_check(a.draft, Path(a.pipeline), a.out, a.json_out)
    if a.cmd == "init-template":
        return cmd_init_template(a)
    if a.cmd == "selftest":
        return selftest()
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
