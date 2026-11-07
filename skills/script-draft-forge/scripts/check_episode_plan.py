#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""分集规划三要素门（EP-01~06）：冲突 / 信息增量 / 尾钩缺一即杀。

只查字段是否齐备、集号是否连续、信息增量是否逐字重复，**不判语义、不判好不好看**。
三要素齐备率 <100% 时不得写「HK-09 通过」。

用法:
  python scripts/check_episode_plan.py init-template pipeline/01_分集规划表.md --episodes 10-12
  python scripts/check_episode_plan.py check --plan pipeline/01_分集规划表.md --episodes 10-12 \
      --out outputs/01_分集规划检查.md --json outputs/01_分集规划检查.json
  python scripts/check_episode_plan.py selftest

--episodes 两种口径：纯数字 N = **全剧集数**（要求 1..N 齐备）；区间/逗号
（如 10-12、10,11,12）= **中间批次**（只要求这批齐备，不要求 1..9）。不给则
只查表内集号是否连续。两种口径都写进报告，避免「只跑 3 集」被误判缺 1..9。

退出码: 0=通过；1=有 FAIL（该集判杀）；2=输入错误。纯标准库。
"""
import argparse
import io
import json
import re
import sys
import tempfile
from datetime import datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _text_util import cjk_only, longest_common  # noqa: E402

PLACEHOLDERS = {"", "-", "—", "–", "待定", "待补", "未知", "不详", "TBD", "tbd",
                "___", "?", "？", "N/A", "n/a", "无", "暂无", "（空）", "（待补）"}

HEADER_ALIASES = {
    "ep": ["集", "集号", "集数", "EP", "ep"],
    "event": ["本集核心事件", "核心事件", "主事件"],
    "conflict": ["明确冲突", "冲突", "本集冲突"],
    "gain": ["本集信息增量", "信息增量", "增量", "新增信息"],
    "hook": ["尾钩", "集尾钩子", "本集尾钩", "结尾钩子"],
    "source": ["出处", "原文出处", "依据", "回指"],
}

REQUIRED = [("event", "本集核心事件"), ("conflict", "明确冲突"),
            ("gain", "本集信息增量"), ("hook", "尾钩")]

SUBJECT_HINT = ("观众", "剧中人", "主角", "他", "她", "众人", "李承泽", "知道", "得知", "发现", "新知道", "才明白")

TEMPLATE_HEAD = """# 分集规划三要素表（EP-01）

> 可并入 `01_钩子预算表.md` 作为一节，也可单独成文件。表头列名不可改，集号须连续。
> 「本集信息增量」写**观众／剧中人本集新知道的事实**，不写钩子复述、不写「爽点升级」（EP-02/03）。
> 素材不足写 `___` 并进缺口清单，**禁止编造原文里没有的事件**。
> 验收：`check --plan <本文件> --episodes <集数>`；纯数字=全剧 1..N，
> `10-12`=只跑中间批次（不再要求 1..9 齐备），不给则只查表内集号连续。

## 逐集三要素表

"""


def parse_episode_spec(s):
    """集数口径解析。

    None/空 → None（只查表内集号连续）；纯数字或 int → int（全剧口径 1..N）；
    "10-12" / "10,11,12" → list（中间批次口径，只要求这批齐备）。
    """
    if s is None or (isinstance(s, str) and not s.strip()):
        return None
    if isinstance(s, int):
        return s
    s = str(s).strip()
    if re.fullmatch(r"\d+", s):
        return int(s)
    nums = []
    for part in s.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            if not (a.strip().isdigit() and b.strip().isdigit()):
                raise ValueError("集数区间格式错误：%s（示例 10-12）" % part)
            lo, hi = int(a), int(b)
            if lo < 1 or hi < lo:
                raise ValueError("集数区间须为 1<=起点<=终点：%s" % part)
            nums += list(range(lo, hi + 1))
        elif part.isdigit():
            nums.append(int(part))
        else:
            raise ValueError("集数只能是数字、区间或逗号列表：%s" % part)
    if not nums:
        raise ValueError("集数口径为空")
    return sorted(set(nums))


def make_template(episodes):
    nums = list(range(1, episodes + 1)) if isinstance(episodes, int) else sorted(episodes)
    if not nums:
        nums = [1]
    L = [TEMPLATE_HEAD.rstrip(), "",
         "| 集 | 本集核心事件 | 明确冲突 | 本集信息增量 | 尾钩 | 出处 |",
         "|---|---|---|---|---|---|"]
    L += ["| %d | ___ | ___ | ___ | ___ | ___ |" % i for i in nums]
    L += ["", "> 齐备率 <100% 时不得写「HK-09 通过」（EP-06）。逐句语义仍由闸门A 人工判。", ""]
    return "\n".join(L)


def cells(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def is_separator(line):
    return bool(re.fullmatch(r"[\s|:-]+", line.strip()))


def parse_table(text):
    """定位含「本集信息增量」的表头，返回 (列名映射, 行列表)。"""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if not line.strip().startswith("|") or "信息增量" not in line:
            continue
        head = cells(line)
        colmap = {}
        for key, aliases in HEADER_ALIASES.items():
            for j, h in enumerate(head):
                if h in aliases or any(a in h for a in aliases if len(a) >= 3):
                    colmap.setdefault(key, j)
        rows = []
        for raw in lines[i + 1:]:
            if not raw.strip().startswith("|"):
                break
            if is_separator(raw):
                continue
            cs = cells(raw)
            ep_m = re.search(r"\d+", cs[colmap.get("ep", 0)]) if cs else None
            if not ep_m:
                continue
            row = {"ep": int(ep_m.group(0))}
            for key in HEADER_ALIASES:
                if key == "ep":
                    continue
                j = colmap.get(key)
                row[key] = cs[j] if j is not None and j < len(cs) else ""
            rows.append(row)
        return colmap, rows
    return {}, []


def empty_value(v):
    """出处列可为 CH001 / L12 这类非汉字引用，只查空与占位，不查汉字数。"""
    return (v or "").strip() in PLACEHOLDERS


def missing(v):
    """三要素必须是中文事实句，汉字数 <2 视为未填。"""
    s = (v or "").strip()
    return s in PLACEHOLDERS or len(cjk_only(s)) < 2


def scope_of(expected_eps):
    """把集数口径写成人读的一句话，报告与 JSON 都带，避免两种口径混用。"""
    if expected_eps is None or expected_eps == "":
        return "连续性口径（未指定集数，只查表内集号连续）"
    if isinstance(expected_eps, int):
        return "全剧口径 1..%d（要求 1..%d 齐备）" % (expected_eps, expected_eps)
    xs = sorted(int(x) for x in expected_eps)
    return "批次口径 %s（只要求这批齐备）" % ",".join(map(str, xs))


def check(text, expected_eps=None, lift_min=8):
    colmap, rows = parse_table(text)
    fails, infos = [], []
    scope = scope_of(expected_eps)
    if not colmap or not rows:
        return {
            "expected_eps": expected_eps, "episode_scope": scope,
            "rows": [], "colmap": colmap,
            "fails": ["[EP-01] 未找到《逐集三要素表》或表为空；先跑 init-template，"
                      "表头须含「本集信息增量」"],
            "infos": [], "complete": 0, "total": 0, "ratio": 0.0,
            "verdict": "未通过",
        }
    eps = [r["ep"] for r in rows]
    if len(set(eps)) != len(eps):
        fails.append("[EP-01] 集号重复：%s" % sorted(set(e for e in eps if eps.count(e) > 1)))
    if expected_eps:
        want = (set(range(1, expected_eps + 1)) if isinstance(expected_eps, int)
                else set(int(x) for x in expected_eps))
        lack = sorted(want - set(eps))
        extra = sorted(set(eps) - want)
        if lack:
            fails.append("[EP-01] 缺集：%s（%s）" % (lack, scope))
        if extra:
            fails.append("[EP-01] 超出需求集数：%s（%s）" % (extra, scope))
    elif eps and eps != list(range(min(eps), max(eps) + 1)):
        fails.append("[EP-01] 集号不连续：%s" % eps)

    complete = 0
    for r in rows:
        lack = [label for key, label in REQUIRED if missing(r.get(key))]
        if lack:
            fails.append("[EP-02] 第%d集缺三要素字段：%s" % (r["ep"], "／".join(lack)))
        else:
            complete += 1
        if empty_value(r.get("source")):
            infos.append("[EP-05] 第%d集缺出处，待人工回原文核对（不自动判杀）" % r["ep"])
        gain = (r.get("gain") or "").strip()
        if gain and gain not in PLACEHOLDERS:
            if not any(w in gain for w in SUBJECT_HINT):
                infos.append("[EP-03] 第%d集信息增量未写清「谁知道」：%s" % (r["ep"], gain[:40]))
            for other in ("event", "hook"):
                v = (r.get(other) or "").strip()
                if v and v not in PLACEHOLDERS and longest_common(cjk_only(gain), cjk_only(v)) >= lift_min:
                    infos.append("[EP-03] 第%d集信息增量与%s连续重合 ≥%d 字，疑似复述：%s" %
                                 (r["ep"], other, lift_min, gain[:40]))
                    break
    ordered = [r for r in sorted(rows, key=lambda x: x["ep"])]
    for a, b in zip(ordered, ordered[1:]):
        ga, gb = (a.get("gain") or "").strip(), (b.get("gain") or "").strip()
        if ga and ga not in PLACEHOLDERS and ga == gb:
            fails.append("[EP-04] 第%d/%d集信息增量逐字相同，等于后一集没有增量" %
                         (a["ep"], b["ep"]))

    total = len(rows)
    ratio = complete / total if total else 0.0
    if ratio < 1.0:
        infos.append("[EP-06] 齐备率 %.0f%% < 100%%，不得写「HK-09 通过」" % (ratio * 100))
    return {
        "expected_eps": expected_eps, "episode_scope": scope,
        "rows": rows, "colmap": colmap,
        "fails": fails, "infos": infos, "complete": complete, "total": total,
        "ratio": round(ratio, 3), "verdict": "通过" if not fails else "未通过",
    }


def render(result, plan_path):
    L = ["# S4 分集规划门（EP-01~06）", "",
         "> 检查对象：`%s`" % plan_path,
         "> 集数口径：%s" % result.get("episode_scope", scope_of(result.get("expected_eps"))),
         "> 时间：%s" % datetime.now().isoformat(timespec="seconds"), "",
         "**结论：%s**" % result["verdict"], "",
         "三要素齐备率：**%d / %d（%.0f%%）**" %
         (result["complete"], result["total"], result["ratio"] * 100), "",
         "| 集 | 本集核心事件 | 明确冲突 | 本集信息增量 | 尾钩 | 出处 | 齐备 |",
         "|---|---|---|---|---|---|---|"]
    for r in sorted(result["rows"], key=lambda x: x["ep"]):
        ok = not any(missing(r.get(k)) for k, _ in REQUIRED)
        L.append("| %d | %s | %s | %s | %s | %s | %s |" %
                 (r["ep"], *(("" + (r.get(k) or "（空）")).replace("|", "／")
                             for k in ("event", "conflict", "gain", "hook", "source")),
                  "✅" if ok else "❌"))
    L += ["", "## FAIL（缺一即杀）", ""]
    L += ["- %s" % x for x in result["fails"]] or ["- 无"]
    L += ["", "## INFO（人工判定，脚本不定性）", ""]
    L += ["- %s" % x for x in result["infos"]] or ["- 无"]
    L += ["", "> **边界**：脚本只查字段齐备、集号连续、逐字重复与明显复述候选，"
          "**不判语义、不判「这一集好不好看」**；出处缺失不代表已核对。"
          "三要素逐句语义与冲突是否成立仍由闸门A 带证据判定（EP-06）。", ""]
    return "\n".join(L)


def run_check(plan, episodes, out, json_out, lift_min):
    try:
        spec = parse_episode_spec(episodes)
    except ValueError as e:
        print("[ERROR] --episodes：%s" % e, file=sys.stderr)
        return 2
    p = Path(plan)
    result = check(p.read_text(encoding="utf-8") if p.exists() else "", spec, lift_min)
    if not p.exists():
        result["fails"].insert(0, "[EP-01] 规划表文件不存在：%s" % p)
        result["verdict"] = "未通过"
    text = render(result, p)
    if out:
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        Path(out).write_text(text, encoding="utf-8")
    if json_out:
        Path(json_out).parent.mkdir(parents=True, exist_ok=True)
        Path(json_out).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print("[%s] 分集规划门：%s｜齐备 %d/%d｜FAIL %d｜INFO %d" %
          ("PASS" if not result["fails"] else "FAIL", result["verdict"],
           result["complete"], result["total"], len(result["fails"]), len(result["infos"])))
    for x in result["fails"][:8]:
        print("   ", x)
    return 1 if result["fails"] else 0


def selftest():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        tpl = make_template(3)
        assert len(parse_table(tpl)[1]) == 3
        r0 = check(tpl, 3)
        assert r0["fails"] and r0["ratio"] == 0.0, r0
        print("[PASS] 全占位模板判 FAIL（缺三要素）")

        good = tpl
        good = good.replace("| 1 | ___ | ___ | ___ | ___ | ___ |",
                            "| 1 | 主角落水获救 | 主角要查案、府衙压卷宗不给 | 观众新知道：凶手是谢风 | 卷宗翻开停在半句 | CH001 |")
        good = good.replace("| 2 | ___ | ___ | ___ | ___ | ___ |",
                            "| 2 | 主角强闯府衙 | 主角要抓人、知府拿祖制挡 | 剧中人新知道：皇子身份可免死 | 知府抄刀半句未完 | CH003 |")
        good = good.replace("| 3 | ___ | ___ | ___ | ___ | ___ |",
                            "| 3 | 刺客夜入王府 | 主角求死、刺客不肯下手 | 观众新知道：母妃留了玉佩 | 玉佩露出一角就切 | CH005 |")
        r1 = check(good, 3)
        assert not r1["fails"] and r1["ratio"] == 1.0, r1["fails"]
        print("[PASS] 齐备 3 集通过，齐备率 100%")

        r2 = check(good.replace("| 3 | 刺客夜入王府", "| 4 | 刺客夜入王府"), 3)
        assert any("缺集" in x or "超出" in x for x in r2["fails"]), r2["fails"]
        dup = good.replace("| 剧中人新知道：皇子身份可免死 |", "| 观众新知道：凶手是谢风 |")
        r3 = check(dup, 3)
        assert any("逐字相同" in x for x in r3["fails"]), r3["fails"]
        print("[PASS] 缺集 / 相邻集增量逐字相同 均判 FAIL")

        echo = good.replace("| 1 | 主角落水获救 |", "| 1 | 主角落水获救后摸清处境 |")
        echo = echo.replace("| 观众新知道：凶手是谢风 |", "| 主角落水获救后摸清处境，凶手是谢风 |")
        r4 = check(echo, 3)
        assert any("疑似复述" in x for x in r4["infos"]), r4["infos"]
        assert not any("缺出处" in x for x in r4["infos"]), "CH001 等非汉字出处不应误判为空"
        print("[PASS] 增量复述核心事件给 INFO 候选（不判杀）")

        pl = root / "plan.md"
        pl.write_text(good, encoding="utf-8")
        assert run_check(pl, 3, str(root / "r.md"), str(root / "r.json"), 8) == 0
        assert json.loads((root / "r.json").read_text(encoding="utf-8"))["ratio"] == 1.0
        assert "不判语义" in (root / "r.md").read_text(encoding="utf-8")
        assert run_check(root / "missing.md", 3, None, None, 8) == 1
        print("[PASS] CLI 报告/JSON 落盘、边界声明在位、缺文件判 FAIL")

        # 中间批次口径：只跑 10-12 集，不该再被要求 1..9 齐备
        spec = parse_episode_spec("10-12")
        assert spec == [10, 11, 12] and parse_episode_spec("10,11,12") == spec
        assert parse_episode_spec("3") == 3 and parse_episode_spec(None) is None
        tplb = make_template(spec)
        assert "| 10 | ___ |" in tplb and "| 12 | ___ |" in tplb and "| 1 | ___ |" not in tplb
        assert len(parse_table(tplb)[1]) == 3
        batch = tplb
        rows = [
            (10, "主角抵达江宁", "主角要查案、府衙压卷宗不给", "观众新知道：卷宗被人抽走", "卷宗翻开停在半句", "CH010"),
            (11, "主角夜探衙库", "主角要证据、知府拿祖制挡", "剧中人新知道：皇子身份可免死", "知府抄刀半句未完", "CH011"),
            (12, "刺客夜入王府", "主角求死、刺客不肯下手", "观众新知道：母妃留了玉佩", "玉佩露出一角就切", "CH012"),
        ]
        for n, ev, cf, gain, hook, src in rows:
            batch = batch.replace("| %d | ___ | ___ | ___ | ___ | ___ |" % n,
                                  "| %d | %s | %s | %s | %s | %s |" %
                                  (n, ev, cf, gain, hook, src))
        rb = check(batch, spec)
        assert not rb["fails"] and rb["ratio"] == 1.0, rb["fails"]
        assert "批次口径" in rb["episode_scope"], rb["episode_scope"]
        assert any("缺集" in x for x in check(batch, 12)["fails"]), "全剧 12 集口径仍应判缺 1..9"
        assert not check(batch, None)["fails"], "不给 --episodes 时只查连续性"
        plb = root / "batch.md"
        plb.write_text(batch, encoding="utf-8")
        assert run_check(plb, "10-12", str(root / "rb.md"), str(root / "rb.json"), 8) == 0
        assert "批次口径" in (root / "rb.md").read_text(encoding="utf-8")
        assert json.loads((root / "rb.json").read_text(encoding="utf-8"))["expected_eps"] == [10, 11, 12]
        assert run_check(plb, 12, None, None, 8) == 1, "全剧口径该批仍应 FAIL"
        assert run_check(plb, "abc", None, None, 8) == 2, "非法集数串应报输入错误"
        print("[PASS] 中间批次口径：10-12 放行 / 全剧 12 集仍判缺 / 口径写进报告与 JSON / 非法串报 2")
        print("[PASS] selftest 全部通过")
    return 0


def main():
    ap = argparse.ArgumentParser(description="分集规划三要素门 EP-01~06")
    sub = ap.add_subparsers(dest="cmd")
    it = sub.add_parser("init-template", help="生成逐集三要素表模板")
    it.add_argument("path")
    it.add_argument("--episodes", default="8",
                    help="集数：8=全剧 1..8；10-12=中间批次；默认 8")
    ck = sub.add_parser("check", help="检查三要素齐备率，缺一即杀")
    ck.add_argument("--plan", required=True, help="01_钩子预算表.md 或 01_分集规划表.md")
    ck.add_argument("--episodes",
                    help="集数口径：纯数字=全剧 1..N；10-12/10,11,12=中间批次；不给=只查连续性")
    ck.add_argument("--out", help="Markdown 报告路径")
    ck.add_argument("--json", dest="json_out", help="JSON 结果路径")
    ck.add_argument("--lift-min", type=int, default=8, help="复述候选连续重合字数，默认 8")
    sub.add_parser("selftest", help="内置自检")
    a = ap.parse_args()
    if a.cmd == "init-template":
        try:
            spec = parse_episode_spec(a.episodes)
        except ValueError as e:
            print("[ERROR] --episodes：%s" % e, file=sys.stderr)
            return 2
        p = Path(a.path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(make_template(spec if spec is not None else 8), encoding="utf-8")
        print("[OK] 三要素表模板（%s）：%s" % (scope_of(spec), p))
        return 0
    if a.cmd == "check":
        return run_check(a.plan, a.episodes, a.out, a.json_out, a.lift_min)
    if a.cmd == "selftest":
        return selftest()
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
