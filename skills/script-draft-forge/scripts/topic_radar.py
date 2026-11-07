#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""题材探测雷达（MS-01~06 的可执行补位）。

诚实定位：这是「带采集日期的本地快照 + 强制时效闸门」，不是实时榜单 API。
实时部分由 MS-01 联网检索完成；本脚本负责沉淀、复核提醒与禁止引用过期数据。

子命令：
  query   --topic 穿越 [--platform 红果]   题材×平台速查表（MS-02）
  check                                   全库时效体检（>90 天需复核 / >180 天过期）
  refresh --input new.json                 导入新快照，旧条目标 [过期] 保留
  selftest                                 内置自检

纯标准库，无第三方依赖。
"""
import argparse
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
DEFAULT = ROOT / "reference" / "topic-snapshot.json"


def parse_date(s):
    s = (s or "").strip()
    if re.fullmatch(r"\d{4}-\d{2}", s):
        s += "-01"
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except ValueError:
        return None


def today(at=None):
    return parse_date(at) if at else date.today()


def age_of(entry, at):
    d = parse_date(entry.get("collected_at"))
    if not d:
        return None
    return (at - d).days


def status_of(entry, meta, at):
    age = age_of(entry, at)
    if age is None:
        return "无日期", None
    if entry.get("status") == "[过期]":
        return "[过期]", age
    if age > meta.get("expire_days", 180):
        return "过期", age
    if age > meta.get("freshness_days", 90):
        return "需复核", age
    return "新鲜", age


def load(path):
    p = Path(path)
    data = json.loads(p.read_text(encoding="utf-8"))
    return data.get("meta", {}), data.get("entries", []), data, p


def as_table(entries, meta, at):
    out = ["| 题材 | 平台 | 近期供给量 | 热度信号 | 稀缺判定 | 依据 + 采集日期 | 时效 |",
           "|---|---|---|---|---|---|---|"]
    for e in entries:
        st, age = status_of(e, meta, at)
        src = "%s（%s）" % (e.get("source", "-"), e.get("collected_at", "无日期"))
        out.append("| %s | %s | %s | %s | %s | %s | %s%s |" %
                   (e.get("topic", "-"), e.get("platform", "-"), e.get("supply", "-"),
                    e.get("heat", "-"), e.get("scarcity", "证据不足"), src, st,
                    "" if age is None else "（%d 天）" % age))
    return "\n".join(out)


def disclaimer(meta, at):
    fresh, expire = meta.get("freshness_days", 90), meta.get("expire_days", 180)
    return ("> ⚠ 数据种类：%s。快照日期 %s，时效口径 新鲜≤%d 天 / 需复核 %d-%d 天 / 过期>%d 天。"
            "\n> 本快照**不是实时数据**：做市场判断前必须按 MS-01 联网复核，并在报告写「数据采集日期：%s｜来源：___」。" %
            (meta.get("data_kind", "本地快照"), at.isoformat(),
             fresh, fresh, expire, expire, at.isoformat()))


def cmd_query(a):
    meta, entries, _, _ = load(a.snapshot)
    at = today(a.at_date)
    hits = [e for e in entries
            if a.topic in (e.get("topic", "") + e.get("supply", "") + e.get("note", ""))
            and (not a.platform or a.platform in e.get("platform", "") or e.get("platform") == "全平台")]
    if not hits:
        print("未命中。本快照只覆盖已沉淀题材；按 MS-01 联网检索补充，不要拍脑袋判稀缺。")
        print(disclaimer(meta, at))
        return 0
    print("## 题材速查表（MS-02）\n")
    print(as_table(hits, meta, at))
    print()
    for e in hits:
        if e.get("note"):
            print("- **%s**：%s" % (e.get("topic"), e["note"]))
    print()
    print(disclaimer(meta, at))
    over = [e for e in hits if status_of(e, meta, at)[0] in ("过期", "[过期]", "无日期")]
    if over:
        print("\n[FAIL] %d 条依据已过期/无日期，禁止用于稀缺判定：%s" %
              (len(over), ", ".join(e.get("id", "?") for e in over)))
        return 1
    return 0


def cmd_check(a):
    meta, entries, _, _ = load(a.snapshot)
    at = today(a.at_date)
    buckets = {"新鲜": [], "需复核": [], "过期": [], "[过期]": [], "无日期": []}
    for e in entries:
        st, age = status_of(e, meta, at)
        buckets.setdefault(st, []).append((e, age))
    print("## 题材快照时效体检｜%s｜共 %d 条" % (at.isoformat(), len(entries)))
    for k in ("新鲜", "需复核", "过期", "[过期]", "无日期"):
        print("- %s：%d 条" % (k, len(buckets.get(k, []))))
    for k in ("需复核", "过期", "无日期"):
        for e, age in buckets.get(k, []):
            print("   %s %s / %s｜采集 %s｜%s 天" %
                  (k, e.get("id", "?"), e.get("topic", "?"), e.get("collected_at", "-"),
                   age if age is not None else "?"))
    print("\n" + disclaimer(meta, at))
    expired = buckets.get("过期", []) + buckets.get("[过期]", []) + buckets.get("无日期", [])
    if expired:
        print("\n[FAIL] 存在过期/无日期数据，按 MS-05 不得据此判稀缺；请跑 refresh 导入复核后的新快照。")
        return 1
    if buckets.get("需复核"):
        print("\n[WARN] 有数据超过 %d 天，按 MS-05 需联网复核后才可引用。" % meta.get("freshness_days", 90))
    return 0


def next_id(entries):
    nums = [int(m.group(1)) for e in entries
            for m in [re.search(r"MS-D(\d+)", e.get("id", ""))] if m]
    return "MS-D%03d" % (max(nums, default=0) + 1)


def cmd_refresh(a):
    meta, entries, data, path = load(a.snapshot)
    incoming = json.loads(Path(a.input).read_text(encoding="utf-8"))
    new = incoming.get("entries", incoming if isinstance(incoming, list) else [])
    if not new:
        print("[ERROR] 新快照无 entries", file=sys.stderr)
        return 2
    at = today(a.at_date)
    for item in new:
        key_id, key_topic = item.get("id"), item.get("topic")
        old = next((e for e in entries if e.get("id") == key_id or
                    (e.get("topic") == key_topic and e.get("platform") == item.get("platform"))), None)
        if old:
            old["status"] = "[过期]"
            old["superseded_at"] = at.isoformat()
            old["superseded_by"] = item.get("collected_at", "新快照")
        item["id"] = next_id(entries)
        item.setdefault("collected_at", at.isoformat())
        item.setdefault("source", "MS-01 联网复核（导入时未注明来源，需补）")
        entries.append(item)
    data["entries"] = entries
    data.setdefault("meta", {})["last_refresh"] = at.isoformat()
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print("[OK] 导入 %d 条，旧同题材条目标 [过期] 保留；当前共 %d 条。" % (len(new), len(entries)))
    print("       按 MS-06：新条目必须带 collected_at 与 source，无来源者已在 source 标注待补。")
    return 0


def cmd_selftest():
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "snap.json"
        snap = {
            "meta": {"data_kind": "selftest", "freshness_days": 90, "expire_days": 180},
            "entries": [
                {"id": "MS-D001", "platform": "红果", "topic": "逆袭", "supply": "215",
                 "heat": "高", "scarcity": "饱和", "source": "测试", "collected_at": "2026-11-02"},
                {"id": "MS-D002", "platform": "抖音", "topic": "都市日常", "supply": "672亿",
                 "heat": "高", "scarcity": "常温", "source": "测试", "collected_at": "2025-01-01"},
            ],
        }
        p.write_text(json.dumps(snap, ensure_ascii=False, indent=2), encoding="utf-8")
        a = argparse.Namespace(snapshot=str(p), at_date="2026-11-04", topic="逆袭", platform="红果", input=None)
        assert cmd_query(a) == 0
        a.topic, a.platform = "都市日常", "抖音"
        assert cmd_query(a) == 1, "过期数据必须被拦下"
        assert cmd_check(a) == 1, "全库体检必须报过期"
        inc = Path(td) / "new.json"
        inc.write_text(json.dumps({"entries": [{"topic": "都市日常", "platform": "抖音",
                                                "supply": "新数据", "heat": "高", "scarcity": "常温",
                                                "source": "MS-01 复核", "collected_at": "2026-11-04"}]},
                                 ensure_ascii=False), encoding="utf-8")
        a.input = str(inc)
        assert cmd_refresh(a) == 0
        _, entries, _, _ = load(str(p))
        assert len(entries) == 3 and entries[1].get("status") == "[过期]"
        assert entries[2]["id"] == "MS-D003"
    print("[PASS] selftest：速查 / 过期拦截 / 时效体检 / 刷新保留旧条目 全通过")
    return 0


def main():
    ap = argparse.ArgumentParser(description="题材探测雷达（本地快照 + 时效闸门）")
    ap.add_argument("--snapshot", default=str(DEFAULT))
    ap.add_argument("--at-date", help="模拟判定日期 YYYY-MM-DD，便于测试")
    sub = ap.add_subparsers(dest="cmd")
    q = sub.add_parser("query"); q.add_argument("--topic", required=True); q.add_argument("--platform")
    sub.add_parser("check")
    r = sub.add_parser("refresh"); r.add_argument("--input", required=True)
    sub.add_parser("selftest")
    a = ap.parse_args()
    if a.cmd == "query": return cmd_query(a)
    if a.cmd == "check": return cmd_check(a)
    if a.cmd == "refresh": return cmd_refresh(a)
    if a.cmd == "selftest": return cmd_selftest()
    ap.print_help(); return 2


if __name__ == "__main__":
    sys.exit(main())
