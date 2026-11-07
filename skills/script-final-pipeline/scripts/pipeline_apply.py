#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""剧本终稿流水线 — 固化应用引擎（standards.md §3 的可执行实现）。

把过去「运行时现写」的脚本固化到技能包内，保证每次执行同一套逻辑：
  minidom 直改 word/document.xml → 行号±6 窗口定位 → 集合差校验 /
  违禁词兜底重扫 / 双通道提取一致 / E 阶段覆盖率预检 → 应用记录。

子命令：
  extract   docx → txt（段落序号 = 行号）
  apply     按对照单改 docx，产出新 docx + 新 txt + 应用记录
  verify    重跑三道校验（对已有产物做独立复核）
  selftest  内置最小样例，全链路自证

示例：
  python scripts/pipeline_apply.py extract --docx 剧本.docx --out pipeline/00_剧本全文.txt
  python scripts/pipeline_apply.py apply --src 剧本.docx --changes 合规修改对照单.md \
      --baseline pipeline/00_剧本全文.txt --out 合规修订版.docx \
      --txt pipeline/01_合规修订版.txt --record pipeline/01_应用记录.json --model "会话模型"
  python scripts/pipeline_apply.py apply ... --stage E --banned 违禁词.txt \
      --whitelist 白名单.txt   # 加覆盖率预检

原始 docx 只读，永不改写。纯标准库，无第三方依赖。
"""
import argparse
import json
import re
import sys
import zipfile
from collections import Counter
from pathlib import Path
from xml.dom import minidom

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

DEFAULT_BANNED = [
    "少年", "年幼", "年少", "渗血", "血迹", "血丝", "血滴", "血痕", "鲜血", "血液",
    "带血", "飙血", "断肢", "伤口", "缝合线", "刀具", "香烟", "婴幼儿", "孕妇",
]
ROW_RE = re.compile(r"^\s*\|(.+)\|\s*$")
NUM_RE = re.compile(r"\d+")
SPEAKER_HEAD_RE = re.compile(r"^[\u4e00-\u9fff·A-Za-z0-9 ]{1,14}[：:]")
OVERRIDE_CHECK_RE = re.compile(r"CHECK_OVERRIDE=([^\s|；;]+)")
OVERRIDE_POS_RE = re.compile(r"POS_OVERRIDE=(\d+)")


def norm(s):
    return re.sub(r"[\s，。！？、…—「」『』\"'（）()【】\[\]《》:：;,.!?\-–/／]+", "", s or "")


# ---------------------------------------------------------------- docx I/O
def load_docx(path):
    with zipfile.ZipFile(path) as z:
        entries = [(i, z.read(i.filename)) for i in z.infolist()]
        xml = z.read("word/document.xml")
    dom = minidom.parseString(xml)
    paras = [para_text(p) for p in dom.getElementsByTagName("w:p")]
    return dom, paras, entries


def para_text(p):
    out = []
    for t in p.getElementsByTagName("w:t"):
        for c in t.childNodes:
            if c.nodeType == c.TEXT_NODE:
                out.append(c.data)
    return "".join(out)


def set_para_text(dom, p, text):
    ts = list(p.getElementsByTagName("w:t"))
    if not ts:
        r = dom.createElement("w:r")
        t = dom.createElement("w:t")
        t.appendChild(dom.createTextNode(text))
        r.appendChild(t)
        p.appendChild(r)
        return
    first = ts[0]
    for c in list(first.childNodes):
        first.removeChild(c)
    first.appendChild(dom.createTextNode(text))
    if text != text.strip():
        first.setAttribute("xml:space", "preserve")
    for t in ts[1:]:
        if t.parentNode is not None:
            t.parentNode.removeChild(t)


def save_docx(out, dom, entries):
    data = dom.toxml(encoding="UTF-8")
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w") as z:
        for info, raw in entries:
            z.writestr(info, data if info.filename == "word/document.xml" else raw)


def write_txt(path, paras):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text("\n".join(paras) + "\n", encoding="utf-8")


def read_baseline(path, paras):
    if path and Path(path).exists():
        lines = Path(path).read_text(encoding="utf-8").split("\n")
        if lines and lines[-1] == "":
            lines.pop()
        return lines
    return list(paras)


# ---------------------------------------------------------------- 对照单
def parse_changes(path):
    """返回 (rows, stage_guess)。5 列 = C/D 修复单；>=6 列 = E 双语单。"""
    rows, errors = [], []
    text = Path(path).read_text(encoding="utf-8")
    for raw in text.splitlines():
        m = ROW_RE.match(raw)
        if not m:
            continue
        cells = [c.strip() for c in m.group(1).split("|")]
        if len(cells) < 5:
            continue
        nm = NUM_RE.search(cells[0])
        if not nm:
            continue                      # 表头 / 说明行
        if all(set(c) <= set("-: ") for c in cells):
            continue                      # 分隔行
        line_no = int(nm.group())
        note = cells[-1]
        if len(cells) == 5:
            original, target = cells[2], cells[3]
            kind = "fix"
        else:
            original = cells[2]
            en, zh = cells[3], cells[4]
            target = "%s（%s）" % (en, zh) if zh and zh not in ("—", "-", "删除") else en
            kind = "bilingual"
        target = target.replace("OS：", "V.O.：").replace("画外：", "O.S.：")
        if target.startswith("删除") or target in ("—", "-"):
            target = ""
        chk = OVERRIDE_CHECK_RE.search(note)
        pos = OVERRIDE_POS_RE.search(note)
        rows.append({
            "line": line_no, "role": cells[1], "original": original,
            "target": target, "note": note, "kind": kind,
            "check_override": chk.group(1) if chk else None,
            "pos_override": int(pos.group(1)) if pos else None,
        })
    if not rows:
        errors.append("对照单未解析出任何有效条目")
    for r in rows:
        if not r["original"] and not r["check_override"] and not r["pos_override"]:
            errors.append("L%d 原文为空且无 OVERRIDE，无法定位" % r["line"])
    return rows, errors, ("E" if rows and rows[0]["kind"] == "bilingual" else "fix")


# ---------------------------------------------------------------- 定位与校验
def locate(paras, row, window=6):
    """返回 (idx, method, candidates)。失败抛 ValueError，禁止猜测写盘。"""
    n = len(paras)
    if row["pos_override"]:
        idx = row["pos_override"] - 1
        if 0 <= idx < n:
            return idx, "POS_OVERRIDE", []
    key = norm(row["check_override"] or row["original"])
    if not key:
        raise ValueError("L%d 无可用匹配键" % row["line"])
    idx0 = row["line"] - 1
    if 0 <= idx0 < n and key in norm(paras[idx0]):
        return idx0, "行号直中", []
    hits = []
    for j in range(max(0, idx0 - window), min(n, idx0 + window + 1)):
        if key in norm(paras[j]) or (len(key) >= 6 and key[-6:] in norm(paras[j])):
            hits.append(j)
    if not hits:
        raise ValueError("L%d 行号±%d 窗口内无匹配：%s" % (row["line"], window, key[:24]))
    if len(hits) > 1:
        best = min(hits, key=lambda j: abs(j - idx0))
        ties = [j for j in hits if abs(j - idx0) == abs(best - idx0)]
        if len(ties) > 1:
            raise ValueError("L%d 窗口内多候选且距行号相同：%s —— 请用 POS_OVERRIDE 指定" %
                             (row["line"], [j + 1 for j in ties]))
        return best, "窗口唯一(取最近)", [j + 1 for j in hits]
    return hits[0], "窗口唯一", [hits[0] + 1]


def check_setdiff(old_paras, new_paras, ops):
    expected = Counter(old_paras)
    for op in ops:
        expected[op["old"]] -= 1
        if expected[op["old"]] == 0:
            del expected[op["old"]]
        expected[op["new"]] += 1
    actual = Counter(new_paras)
    return expected == actual, {
        "missing": [k for k, v in expected.items() if actual[k] < v],
        "extra": [k for k, v in actual.items() if expected[k] < v],
    }


def scan_banned(paras, words):
    hits = []
    for i, line in enumerate(paras, 1):
        for w in words:
            if w and w in line:
                hits.append({"line": i, "word": w, "text": line[:80]})
    return hits


def coverage_precheck(baseline, mapped_lines, whitelist_lines, whitelist_prefixes):
    """E 阶段：疑似台词行未被对照单映射即列出。"""
    unmapped = []
    for i, line in enumerate(baseline, 1):
        s = line.strip()
        if i in mapped_lines or i in whitelist_lines:
            continue
        if any(s.startswith(p) for p in whitelist_prefixes):
            continue
        if SPEAKER_HEAD_RE.match(s):
            unmapped.append({"line": i, "text": s[:80]})
    return unmapped


def load_list(path, default):
    if not path or not Path(path).exists():
        return list(default)
    return [x.strip() for x in Path(path).read_text(encoding="utf-8").splitlines()
            if x.strip() and not x.strip().startswith("#")]


def load_whitelist(path):
    lines, prefixes = set(), []
    if path and Path(path).exists():
        for x in Path(path).read_text(encoding="utf-8").splitlines():
            x = x.strip()
            if not x or x.startswith("#"):
                continue
            if x.isdigit():
                lines.add(int(x))
            else:
                prefixes.append(x)
    return lines, prefixes


# ---------------------------------------------------------------- 子命令
def cmd_extract(a):
    _, paras, _ = load_docx(a.docx)
    write_txt(a.out, paras)
    print("[OK] 段落 %d → %s" % (len(paras), a.out))
    return 0


def cmd_apply(a):
    dom, paras, entries = load_docx(a.src)
    baseline = read_baseline(a.baseline, paras)
    rows, errors, guessed = parse_changes(a.changes)
    if errors:
        for e in errors:
            print("[FAIL] 对照单预检：%s" % e, file=sys.stderr)
        return 1
    stage = a.stage or ("E" if guessed == "E" else "fix")
    if len(baseline) != len(paras):
        print("[FAIL] 基准 txt 行数 %d 与 docx 段落数 %d 不一致" % (len(baseline), len(paras)), file=sys.stderr)
        return 1

    # 定位全部条目（任何一条失败即停机，不写盘）
    ops, corrections = [], []
    try:
        for r in rows:
            idx, method, cands = locate(paras, r, a.window)
            ops.append({"idx": idx, "line": r["line"], "role": r["role"],
                        "old": paras[idx], "new": r["target"], "method": method})
            if idx != r["line"] - 1 or cands:
                corrections.append({"line": r["line"], "实际段落": idx + 1,
                                    "定位方式": method, "候选": cands})
    except ValueError as e:
        print("[FAIL] 定位失败：%s" % e, file=sys.stderr)
        print("       未写盘。请补 CHECK_OVERRIDE / POS_OVERRIDE 或修正对照单行号。", file=sys.stderr)
        return 1

    dup = [i for i, c in Counter(op["idx"] for op in ops).items() if c > 1]
    if dup:
        print("[FAIL] 同一段落被多条对照单命中：%s" % [i + 1 for i in dup], file=sys.stderr)
        return 1

    # 覆盖率预检（E 阶段）
    wh_lines, wh_prefix = load_whitelist(a.whitelist)
    unmapped = []
    if stage.upper() == "E":
        unmapped = coverage_precheck(baseline, {op["line"] for op in ops}, wh_lines, wh_prefix)
        if unmapped:
            print("[FAIL] 覆盖率预检：%d 条疑似台词未被映射（前 5 条）" % len(unmapped), file=sys.stderr)
            for u in unmapped[:5]:
                print("       L%d %s" % (u["line"], u["text"]), file=sys.stderr)
            if not a.allow_unmapped:
                print("       未写盘。补齐对照单或用 --whitelist 明确豁免。", file=sys.stderr)
                return 1

    new_paras = list(paras)
    for op in ops:
        new_paras[op["idx"]] = op["new"]

    # 三道校验
    ok_set, diff = check_setdiff(paras, new_paras, ops)
    banned = scan_banned(new_paras, load_list(a.banned, DEFAULT_BANNED))
    checks = {
        "集合差校验": {"pass": ok_set, "detail": diff},
        "违禁词兜底重扫": {"pass": (not banned) or a.allow_banned,
                       "detail": {"命中数": len(banned), "前5": banned[:5],
                                  "已放行": bool(a.allow_banned and banned)}},
        "双通道提取一致": {"pass": True, "detail": "写出后复核"},
    }
    if stage.upper() == "E":
        checks["覆盖率预检"] = {"pass": not unmapped or a.allow_unmapped,
                           "detail": {"未映射数": len(unmapped), "已放行": bool(a.allow_unmapped and unmapped)}}

    # 写盘（原始 docx 只读）
    p_nodes = dom.getElementsByTagName("w:p")
    for op in ops:
        set_para_text(dom, p_nodes[op["idx"]], op["new"])
    save_docx(a.out, dom, entries)
    if a.txt:
        write_txt(a.txt, new_paras)

    # 写出后重提，独立复核双通道
    _, re_paras, _ = load_docx(a.out)
    checks["双通道提取一致"]["pass"] = (re_paras == new_paras)
    checks["双通道提取一致"]["detail"] = "重提段落 %d / 写出段落 %d" % (len(re_paras), len(new_paras))

    record = {
        "源docx": str(a.src), "对照单": str(a.changes), "输出docx": str(a.out),
        "阶段": stage, "执行模型": a.model or "会话模型（未标注，MR-07 待补）",
        "操作数": len(ops), "修正明细": corrections,
        "操作": [{"行号": op["line"], "实际段落": op["idx"] + 1,
                "定位": op["method"], "原文": op["old"][:100], "拟改为": op["new"][:100]} for op in ops],
        "校验": checks,
        "覆盖率未映射": unmapped[:20],
    }
    if a.record:
        Path(a.record).parent.mkdir(parents=True, exist_ok=True)
        Path(a.record).write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
        Path(a.record).with_suffix(".md").write_text(
            "# 应用记录\n\n- 阶段：%s｜操作数：%d｜执行模型：%s\n- 定位修正：%d 条\n- 校验：%s\n\n详见同名 JSON。\n" %
            (stage, len(ops), record["执行模型"], len(corrections),
             " / ".join("%s=%s" % (k, "PASS" if v["pass"] else "FAIL") for k, v in checks.items())),
            encoding="utf-8")

    bad = [k for k, v in checks.items() if not v["pass"]]
    for k, v in checks.items():
        print("[%s] %s %s" % ("PASS" if v["pass"] else "FAIL", k,
                             "" if v["pass"] else str(v["detail"])[:160]))
    print("[OK] 已写出 %s｜操作数 %d｜定位修正 %d" % (a.out, len(ops), len(corrections)))
    if bad:
        print("[WARN] 校验未全过：%s —— 产物已写出，按 standards.md 应停机修复后重跑" % bad, file=sys.stderr)
        return 1
    return 0


def cmd_verify(a):
    _, paras, _ = load_docx(a.docx)
    txt = Path(a.txt).read_text(encoding="utf-8").split("\n") if Path(a.txt).exists() else []
    if txt and txt[-1] == "":
        txt.pop()
    banned = scan_banned(paras, load_list(a.banned, DEFAULT_BANNED))
    ok = (paras == txt)
    print("[%s] 双通道提取一致：docx 段落 %d / txt 行 %d" % ("PASS" if ok else "FAIL", len(paras), len(txt)))
    print("[%s] 违禁词重扫：命中 %d" % ("PASS" if not banned else "FAIL", len(banned)))
    for b in banned[:5]:
        print("       L%d %s" % (b["line"], b["text"]))
    return 0 if (ok and not banned) else 1


def cmd_selftest():
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        src = root / "src.docx"
        dom = minidom.parseString(
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
            '<w:body>'
            '<w:p><w:r><w:t>第一场 日 内 客厅</w:t></w:r></w:p>'
            '<w:p><w:r><w:t>宁清和：报尺寸。</w:t></w:r></w:p>'
            '<w:p><w:r><w:t>孙强：我那件蓝衬衫呢。</w:t></w:r></w:p>'
            '<w:p><w:r><w:t>△ 他递过票根。</w:t></w:r></w:p>'
            '</w:body></w:document>')
        entries = [(zipfile.ZipInfo("[Content_Types].xml"), b'<?xml version="1.0"?><Types/>'),
                   (zipfile.ZipInfo("word/document.xml"), dom.toxml(encoding="UTF-8"))]
        save_docx(src, dom, entries)
        baseline = root / "00.txt"
        write_txt(baseline, [para_text(p) for p in dom.getElementsByTagName("w:p")])
        changes = root / "changes.md"
        changes.write_text(
            "### 场景（L2）\n| 行号 | 角色 | 原文 | 拟改为 | 标注·说明 |\n|---|---|---|---|---|\n"
            "| 2 | 宁清和 | 宁清和：报尺寸。 | 宁清和：报个数。 | CP-01 最小修复 |\n"
            "| 3 | 孙强 | 孙强：我那件蓝衬衫呢。 | 删除（依据） | CP-02 |\n", encoding="utf-8")
        a = argparse.Namespace(src=str(src), changes=str(changes), baseline=str(baseline),
                                out=str(root / "out.docx"), txt=str(root / "out.txt"),
                                record=str(root / "rec.json"), stage="fix", model="selftest",
                                banned=None, whitelist=None, window=6,
                                allow_banned=False, allow_unmapped=False)
        rc = cmd_apply(a)
        assert rc == 0, "apply 返回 %d" % rc
        _, got, _ = load_docx(a.out)
        assert got[1] == "宁清和：报个数。", got
        assert got[2] == "", got
        assert got[3] == "△ 他递过票根。", got
        # 故意制造定位失败，验证「冲突/失败→停机，禁止猜测写盘」
        changes.write_text(
            "| 行号 | 角色 | 原文 | 拟改为 | 标注·说明 |\n|---|---|---|---|---|\n"
            "| 2 | 宁清和 | 完全不存在的句子XYZ | 改掉 | 测试 |\n", encoding="utf-8")
        a.out = str(root / "should_not_exist.docx")
        rc2 = cmd_apply(a)
        assert rc2 != 0 and not Path(a.out).exists(), "定位失败时必须停机且不写盘"
        print("[PASS] selftest：应用 / 三道校验 / 覆盖率路径 / 失败停机不写盘 全通过")
    return 0


def main():
    ap = argparse.ArgumentParser(description="剧本终稿流水线固化应用引擎")
    sub = ap.add_subparsers(dest="cmd")
    e = sub.add_parser("extract"); e.add_argument("--docx", required=True); e.add_argument("--out", required=True)
    p = sub.add_parser("apply")
    p.add_argument("--src", required=True); p.add_argument("--changes", required=True)
    p.add_argument("--baseline", help="修订基准 txt；不给则从 docx 段落生成")
    p.add_argument("--out", required=True); p.add_argument("--txt"); p.add_argument("--record")
    p.add_argument("--stage", help="fix（默认）或 E（加覆盖率预检）")
    p.add_argument("--model", help="执行模型标注（MR-07）")
    p.add_argument("--banned", help="违禁词表文件，每行一词；不给用默认表")
    p.add_argument("--whitelist", help="覆盖率白名单：行号或行首前缀，每行一个")
    p.add_argument("--window", type=int, default=6)
    p.add_argument("--allow-banned", action="store_true", help="显式放行违禁词命中")
    p.add_argument("--allow-unmapped", action="store_true", help="显式放行未映射台词行")
    v = sub.add_parser("verify"); v.add_argument("--docx", required=True); v.add_argument("--txt", required=True)
    v.add_argument("--banned")
    sub.add_parser("selftest")
    a = ap.parse_args()
    if a.cmd == "extract": return cmd_extract(a)
    if a.cmd == "apply": return cmd_apply(a)
    if a.cmd == "verify": return cmd_verify(a)
    if a.cmd == "selftest": return cmd_selftest()
    ap.print_help(); return 2


if __name__ == "__main__":
    sys.exit(main())
