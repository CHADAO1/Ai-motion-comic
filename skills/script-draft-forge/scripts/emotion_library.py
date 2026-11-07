#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""情绪转折点库（EH-03/05/06 的可执行补位）。

诚实定位：SaaS 的 3000+ 是真实项目数据壁垒，本技能不伪造。这里给的是
「编号化 + 带出处 + 可增长」的库骨架：每轮闸门A 过关版自动入库、历史项目批量导入，
规模随项目累积。`stats` 永远公开当前真实条数与来源构成。

子命令：
  verify                     字段/编号/强度差/去重校验
  stats                       规模与来源构成（含距 3000 的差距）
  query --genre 年代/穿越      EH-04 生成注入用，取同题材最近 N 条
  append --json '{...}'        入库单条（闸门A 过关版）
  import --file history.jsonl  批量导入去重（.jsonl / .csv）
  selftest                     内置自检

纯标准库，无第三方依赖。
"""
import argparse
import csv
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
DEFAULT = ROOT / "reference" / "emotion-turns.jsonl"
TARGET = 3000
REQUIRED = ["scene", "trigger", "transition", "intensity_delta", "source_type", "source", "date"]
ALLOWED_TYPES = {"闸门A实测", "对标拆解", "方法论派生", "实测错误案例", "项目导入"}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def norm(s):
    return re.sub(r"[\s，。！？、…—「」\"'（）()【】:：;,.!?\-]+", "", s or "")


def load(path):
    p = Path(path)
    if not p.exists():
        return []
    rows = []
    for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as e:
            raise SystemExit("[ERROR] %s 第 %d 行不是合法 JSON：%s" % (p, i, e))
    return rows


def save(path, rows):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")


def dedup_key(r):
    return hashlib.md5((norm(r.get("trigger")) + "|" + norm(r.get("transition"))).encode("utf-8")).hexdigest()


def next_id(rows):
    nums = [int(m.group(1)) for r in rows for m in [re.search(r"ET-(\d+)", r.get("id", ""))] if m]
    return "ET-%04d" % (max(nums, default=0) + 1)


def validate(rows):
    errs, seen_ids, seen_keys = [], set(), {}
    for i, r in enumerate(rows, 1):
        rid = r.get("id", "?")
        if rid in seen_ids:
            errs.append("第%d条 %s：编号重复" % (i, rid))
        seen_ids.add(rid)
        for k in REQUIRED:
            if not str(r.get(k, "")).strip() and r.get(k) != 0:
                errs.append("第%d条 %s：缺字段 %s" % (i, rid, k))
        d = r.get("date", "")
        if d and not DATE_RE.match(str(d)):
            errs.append("第%d条 %s：日期格式须 YYYY-MM-DD（%s）" % (i, rid, d))
        try:
            delta = int(r.get("intensity_delta"))
            if not -5 <= delta <= 5:
                errs.append("第%d条 %s：强度差 %d 超出 -5~5" % (i, rid, delta))
        except (TypeError, ValueError):
            errs.append("第%d条 %s：强度差非整数" % (i, rid))
        if r.get("source_type") and r["source_type"] not in ALLOWED_TYPES:
            errs.append("第%d条 %s：来源类型 %s 不在白名单" % (i, rid, r["source_type"]))
        k = dedup_key(r)
        if k in seen_keys:
            errs.append("第%d条 %s：与 %s 触发+转换重复" % (i, rid, seen_keys[k]))
        seen_keys[k] = rid
    return errs


def prepare(raw, rows, default_type="项目导入"):
    r = dict(raw)
    r.setdefault("source_type", default_type)
    r.setdefault("date", __import__("datetime").date.today().isoformat())
    r.setdefault("source", "未注明（导入时必须补）")
    r["id"] = next_id(rows)
    r.setdefault("note", "")
    return r


def cmd_verify(a):
    rows = load(a.library)
    errs = validate(rows)
    print("## 情绪转折点库校验｜共 %d 条" % len(rows))
    if errs:
        for e in errs[:20]:
            print("[FAIL] " + e)
        print("[FAIL] 合计 %d 处问题" % len(errs))
        return 1
    print("[PASS] 字段 / 编号 / 强度差 / 来源类型 / 去重 全通过")
    return 0


def cmd_stats(a):
    rows = load(a.library)
    print("## 情绪转折点库规模｜%d 条｜目标 %d 条（差 %d）" %
          (len(rows), TARGET, max(0, TARGET - len(rows))))
    print("\n按来源类型：")
    for k, v in Counter(r.get("source_type", "未标") for r in rows).most_common():
        print("  %-12s %3d" % (k, v))
    print("\n按题材：")
    for k, v in Counter(r.get("genre", "未标") for r in rows).most_common():
        print("  %-16s %3d" % (k, v))
    real = sum(1 for r in rows if r.get("source_type") in ("闸门A实测", "对标拆解", "项目导入"))
    print("\n实测/对标/项目导入 %d 条｜方法论派生 %d 条｜错误案例 %d 条" %
          (real, sum(1 for r in rows if r.get("source_type") == "方法论派生"),
           sum(1 for r in rows if r.get("source_type") == "实测错误案例")))
    print("\n> 诚实声明：SaaS 的 3000+ 来自真实项目数据积累。本库只收录可指回出处的条目，")
    print("> 派生条目明确标注「方法论派生」，错误案例标注「实测错误案例」，不混入实测数。")
    print("> 增长路径：每轮闸门A 过关版 `append` + 历史项目 `import`，不做凭空批量造数。")
    return 0


def cmd_query(a):
    rows = load(a.library)
    hits = [r for r in rows if a.genre in r.get("genre", "") and
            r.get("source_type") != "实测错误案例"]
    hits = hits[-a.limit:][::-1]
    print("## EH-04 注入样例｜题材 %s｜最近 %d 条" % (a.genre, len(hits)))
    for r in hits:
        print("- %s｜%s｜%s → %s｜强度差 %s｜%s" %
              (r["id"], r.get("scene", ""), r.get("trigger", ""), r.get("transition", ""),
               r.get("intensity_delta"), r.get("source", "")))
    if not hits:
        print("（库空或无同题材条目：EH-04 跳过，不阻塞生成）")
    return 0


def cmd_append(a):
    rows = load(a.library)
    raw = json.loads(a.json) if a.json else json.loads(Path(a.file).read_text(encoding="utf-8"))
    r = prepare(raw, rows, a.source_type)
    if dedup_key(r) in {dedup_key(x) for x in rows}:
        print("[SKIP] 触发+转换已存在，不重复入库")
        return 0
    errs = validate(rows + [r])
    if errs:
        print("[FAIL] 入库校验未过：%s" % errs[:3], file=sys.stderr)
        return 1
    rows.append(r)
    save(a.library, rows)
    print("[OK] %s 已入库｜当前 %d 条｜来源类型 %s" % (r["id"], len(rows), r["source_type"]))
    return 0


def cmd_import(a):
    rows = load(a.library)
    p = Path(a.file)
    raws = []
    if p.suffix.lower() == ".csv":
        with p.open(encoding="utf-8-sig") as f:
            raws = [dict(x) for x in csv.DictReader(f)]
    else:
        raws = [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]
    keys = {dedup_key(x) for x in rows}
    added = skipped = 0
    for raw in raws:
        r = prepare(raw, rows, a.source_type)
        k = dedup_key(r)
        if k in keys:
            skipped += 1
            continue
        keys.add(k)
        rows.append(r)
        added += 1
    errs = validate(rows)
    if errs:
        print("[FAIL] 导入后校验未过，未写盘：%s" % errs[:5], file=sys.stderr)
        return 1
    save(a.library, rows)
    print("[OK] 导入 %d 条，跳过重复 %d 条｜当前 %d 条" % (added, skipped, len(rows)))
    return 0


def cmd_selftest():
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "lib.jsonl"
        good = {"genre": "测试", "scene": "S1", "trigger": "被当众揭穿", "transition": "得意→羞愤",
                "intensity_delta": 3, "source_type": "闸门A实测", "source": "selftest", "date": "2026-11-04"}
        save(p, [dict(good, id="ET-0001")])
        a = argparse.Namespace(library=str(p), genre="测试", limit=3, json=None, file=None, source_type="项目导入")
        assert cmd_verify(a) == 0
        a.json = json.dumps(dict(good, trigger="另一触发", transition="另一转换"), ensure_ascii=False)
        assert cmd_append(a) == 0
        assert len(load(p)) == 2
        a.json = json.dumps(dict(good, trigger="另一触发", transition="另一转换"), ensure_ascii=False)
        assert cmd_append(a) == 0 and len(load(p)) == 2, "去重必须生效"
        inc = Path(td) / "in.jsonl"
        inc.write_text(json.dumps(dict(good, trigger="批量A", transition="转换A"), ensure_ascii=False) + "\n" +
                       json.dumps(dict(good, trigger="批量B", transition="转换B"), ensure_ascii=False) + "\n",
                       encoding="utf-8")
        a.file = str(inc)
        assert cmd_import(a) == 0 and len(load(p)) == 4
        # 故意破坏一条：强度差越界
        broken = load(p)
        broken[0]["intensity_delta"] = 99
        save(p, broken)
        assert cmd_verify(a) == 1
        assert cmd_stats(a) == 0
        assert cmd_query(a) == 0
    print("[PASS] selftest：校验 / 入库 / 去重 / 批量导入 / 坏数据拦截 / 统计 / 查询 全通过")
    return 0


def main():
    ap = argparse.ArgumentParser(description="情绪转折点库（编号化、带出处、可增长）")
    ap.add_argument("--library", default=str(DEFAULT))
    sub = ap.add_subparsers(dest="cmd")
    sub.add_parser("verify")
    sub.add_parser("stats")
    q = sub.add_parser("query"); q.add_argument("--genre", required=True); q.add_argument("--limit", type=int, default=3)
    x = sub.add_parser("append"); x.add_argument("--json"); x.add_argument("--file")
    x.add_argument("--source-type", default="项目导入")
    y = sub.add_parser("import"); y.add_argument("--file", required=True)
    y.add_argument("--source-type", default="项目导入")
    sub.add_parser("selftest")
    a = ap.parse_args()
    if a.cmd == "verify": return cmd_verify(a)
    if a.cmd == "stats": return cmd_stats(a)
    if a.cmd == "query": return cmd_query(a)
    if a.cmd == "append": return cmd_append(a)
    if a.cmd == "import": return cmd_import(a)
    if a.cmd == "selftest": return cmd_selftest()
    ap.print_help(); return 2


if __name__ == "__main__":
    sys.exit(main())
