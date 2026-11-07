#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""S0 授权链阻断检查（SH-01/02）。

只核字段完整性、范围关键词与确认状态，**不判定法律效力**。未登记 / 字段缺失 /
状态非已确认 / 范围未覆盖短剧与漫剧 → 阻断（exit 1），S0 不得出稿。

用法:
  python scripts/check_authorization.py init-template pipeline/00_授权登记.md
  python scripts/check_authorization.py check --pipeline pipeline/ \
      [--registry <登记表>] [--out outputs/00_授权检查.md] [--json outputs/00_授权检查.json]
  python scripts/check_authorization.py selftest

登记表默认名 `00_授权登记.md`；自定义名（如 `00_授权登记表.md`）会自动发现，
不会被误判成「未登记」。检查报告类文件永不作为登记表候选。

退出码: 0=放行；1=阻断；2=输入错误。纯标准库。
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

REGISTRY_NAME = "00_授权登记.md"
# 自动发现：只认「像登记表」的文件，且显式排除检查报告/模板/备份类命名。
REGISTRY_ALIASES = ("授权登记", "授权表", "授权与净稿")
REGISTRY_NAME_EXCLUDE = ("检查", "报告", "模板", "示例", "样表", "备份", "副本",
                         "check", "report", "template", "sample", "bak")
REGISTRY_REPORT_MARKS = ("# S0 授权检查", "阻断项", "字段快照")

FIELDS = [
    ("work_title", "作品名", ["作品名", "作品", "书名", "IP 名称", "work_title"]),
    ("rights_holder", "权利方", ["权利方", "授权方", "版权方", "权利人", "rights_holder"]),
    ("grant_scope", "授权范围", ["授权范围", "权利范围", "改编范围", "grant_scope"]),
    ("distribution", "分发渠道", ["分发渠道", "发行渠道", "投放渠道", "distribution"]),
    ("term", "授权期限", ["授权期限", "有效期", "授权期", "term"]),
    ("evidence", "凭证", ["凭证", "合同编号", "授权文件", "evidence"]),
    ("confirmed_by", "确认人", ["确认人", "核对人", "confirmed_by"]),
    ("confirmed_at", "确认日期", ["确认日期", "核对日期", "confirmed_at"]),
    ("status", "状态", ["状态", "确认状态", "status"]),
]

PLACEHOLDERS = {"", "-", "—", "–", "待定", "待补", "未知", "不详", "TBD", "tbd",
                "___", "?", "？", "N/A", "n/a", "无", "暂无", "待确认", "（空）"}

SHORT_KEYS = ("短剧", "short", "微短剧")
COMIC_KEYS = ("漫剧", "动态漫", "comic")

TEMPLATE = """# S0 授权登记（SH-01）

> 本表须由人填写并确认；脚本只核字段完整性，不判法律效力。填完跑
> `python scripts/check_authorization.py check --pipeline pipeline/`。
> 未登记或字段不全 → S0 阻断，不出稿，只出提示。

| 字段 | 值 | 说明 |
|---|---|---|
| 作品名 | ___ | 必填，小说原名 |
| 权利方 | ___ | 必填，著作权人 / 授权主体 |
| 授权范围 | ___ | 必填，**须同时覆盖「短剧」与「漫剧／动态漫」改编权**及信息网络传播权 |
| 分发渠道 | ___ | 必填，列具体平台；不得写「待定」 |
| 授权期限 | ___ | 必填，起止日期或「永久」 |
| 凭证 | ___ | 必填，合同编号 / 扫描件路径 |
| 确认人 | ___ | 必填，由谁核过 |
| 确认日期 | ___ | 必填，YYYY-MM-DD |
| 状态 | ___ | 必填，只有「已确认」放行 |

## 备注（人读，不参与机检）

- 本表不替代合同审查；授权真实性、链条完整性、地域与期限由权利方／法务确认。
- 若只拿到「改编权」三个字而没写载体与渠道，视为未覆盖，判阻断。
"""


def parse_registry(text):
    """解析 `| 字段 | 值 |` 两列/三列表；返回 {key: value}。"""
    found = {}
    aliases = {a.lower(): key for key, _, alts in FIELDS for a in alts}
    for line in text.splitlines():
        s = line.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if len(cells) < 2:
            continue
        k = cells[0].strip().strip("*").lower()
        v = cells[1].strip()
        if k in aliases and not re.fullmatch(r"[-: ]+", k):
            key = aliases[k]
            if key not in found or found[key] in PLACEHOLDERS:
                found[key] = v
    return found


def has_any(text, keys):
    low = text.lower()
    return any(k.lower() in low for k in keys)


def check_one(text, registry_path):
    data = parse_registry(text)
    fails, infos = [], []
    for key, label, _ in FIELDS:
        v = data.get(key, "")
        if v.strip() in PLACEHOLDERS:
            fails.append("[SH-01] 缺字段：%s（%s）" % (label, key))
    scope = data.get("grant_scope", "")
    if scope and scope.strip() not in PLACEHOLDERS:
        if not has_any(scope, SHORT_KEYS):
            fails.append("[SH-02] 授权范围未覆盖「短剧」：%s" % scope[:60])
        if not has_any(scope, COMIC_KEYS):
            fails.append("[SH-02] 授权范围未覆盖「漫剧／动态漫」：%s" % scope[:60])
        if scope.strip() in ("改编权", " IP 改编权"):
            fails.append("[SH-02] 只写「改编权」不写载体与渠道，视为未覆盖")
    status = data.get("status", "")
    if status and status.strip() not in PLACEHOLDERS and "已确认" not in status:
        fails.append("[SH-01] 状态非「已确认」：%s" % status)
    dist = data.get("distribution", "")
    if dist and dist.strip() not in PLACEHOLDERS:
        if len(dist) < 2:
            infos.append("[SH-02] 分发渠道过短，请列具体平台：%s" % dist)
    return {
        "registry": str(registry_path),
        "checked_at": datetime.now().isoformat(timespec="seconds"),
        "fields_found": len([1 for k, _, _ in FIELDS
                             if data.get(k, "").strip() not in PLACEHOLDERS]),
        "fields_required": len(FIELDS),
        "values": {k: data.get(k, "") for k, _, _ in FIELDS},
        "fails": fails,
        "infos": infos,
        "verdict": "放行（字段齐全；法律效力待权利方确认）" if not fails else "阻断",
    }


def discover_registry(pipeline, registry=None):
    """找登记表：显式指定 > 默认名 > 目录内自动发现。

    返回 (路径或 None, 候选路径列表, 发现方式)。多候选时按「字段完整度降序」
    选一份并在报告里登记候选清单 —— 但**不因此判定授权真实有效**（SH-02 边界不变）。
    """
    if registry:
        p = Path(registry)
        return (p if p.is_file() else None), [], "显式 --registry 指定"
    pl = Path(pipeline)
    default = pl / REGISTRY_NAME
    if default.is_file():
        return default, [], "默认文件名"
    cands = []
    if pl.is_dir():
        for p in sorted(pl.glob("*.md")):
            name = p.name
            if any(x.lower() in name.lower() for x in REGISTRY_NAME_EXCLUDE):
                continue
            if not any(x in name for x in REGISTRY_ALIASES):
                continue
            try:
                txt = p.read_text(encoding="utf-8")
            except OSError:
                continue
            if any(m in txt[:400] for m in REGISTRY_REPORT_MARKS):
                continue
            if "| 授权范围 |" not in txt and "# S0 授权登记" not in txt[:200]:
                continue
            cands.append((p, txt))
    if not cands:
        return None, [], "未发现"
    scored = sorted(cands, key=lambda it: (
        -check_one(it[1], it[0])["fields_found"], it[0].name))
    return scored[0][0], [str(x[0]) for x in scored], \
        "自动发现（候选 %d 份，取字段最全者）" % len(scored)


def render(result):
    L = ["# S0 授权检查（SH-01/02）", "",
         "> 检查对象：`%s`" % result["registry"],
         "> 发现方式：%s" % result.get("registry_source", "-"),
         "> 时间：%s" % result["checked_at"], "",
         "**结论：%s**" % result["verdict"], "",
         "字段完整度：%d / %d" % (result["fields_found"], result["fields_required"]), "",
         "## 阻断项", ""]
    L += ["- %s" % x for x in result["fails"]] or ["- 无"]
    L += ["", "## 提示项", ""]
    L += ["- %s" % x for x in result["infos"]] or ["- 无"]
    L += ["", "## 字段快照", "", "| 字段 | 值 |", "|---|---|"]
    L += ["| %s | %s |" % (label, (result["values"].get(key) or "（空）").replace("|", "／"))
          for key, label, _ in FIELDS]
    L += ["", "> **边界（SH-02，不得省略）**：本检查只核字段是否齐全、范围关键词是否覆盖、"
          "是否有人确认，**不判定授权是否真实有效**。授权真实性、链条完整性、地域与期限"
          "由权利方／法务确认；模型不得写「授权合规」结论。字段齐全不等于已完成环节 1。", ""]
    return "\n".join(L)


def run_check(pipeline, registry, out, json_out):
    p, candidates, how = discover_registry(pipeline, registry)
    if p is None:
        pl = Path(pipeline)
        seen = [x.name for x in sorted(pl.glob("*.md"))[:8]] if pl.is_dir() else []
        msg = ("[SH-01] 未找到授权登记表，S0 阻断（先跑 init-template 并由人填写；"
               "自定义名可用 --registry 显式指定）")
        result = {
            "registry": str(registry or (pl / REGISTRY_NAME)),
            "registry_source": how,
            "candidates": candidates,
            "checked_at": datetime.now().isoformat(timespec="seconds"),
            "fields_found": 0, "fields_required": len(FIELDS),
            "values": {k: "" for k, _, _ in FIELDS},
            "fails": [msg],
            "infos": (["> 目录内 .md 文件：%s" % "、".join(seen)] if seen else []) +
                     ["> 自动发现只认含「授权登记／授权表」且非检查报告/模板的文件名。"],
            "verdict": "阻断",
        }
    else:
        result = check_one(p.read_text(encoding="utf-8"), p)
        result["registry_source"] = how
        result["candidates"] = candidates
        if len(candidates) > 1:
            result["infos"].append(
                "[SH-01] 发现 %d 份授权登记表候选，本次以 `%s`（字段最全）为准；"
                "请人工确认唯一来源并清理重复表：%s" %
                (len(candidates), p.name, "、".join(Path(x).name for x in candidates)))
    text = render(result)
    if out:
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        Path(out).write_text(text, encoding="utf-8")
    if json_out:
        Path(json_out).parent.mkdir(parents=True, exist_ok=True)
        Path(json_out).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print("[%s] 授权检查：%s（字段 %d/%d）" %
          ("PASS" if not result["fails"] else "BLOCK", result["verdict"],
           result["fields_found"], result["fields_required"]))
    for x in result["fails"]:
        print("   ", x)
    return 1 if result["fails"] else 0


def selftest():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        good = TEMPLATE
        for label, value in [("作品名", "《测试小说》"), ("权利方", "某某文化"),
                             ("授权范围", "短剧、漫剧（动态漫）改编权及信息网络传播权"),
                             ("分发渠道", "抖音／红果／微信小程序"),
                             ("授权期限", "2026-01-01 至 2029-12-31"),
                             ("凭证", "合同 HT-001／扫描件 scan/ht001.pdf"),
                             ("确认人", "张三"), ("确认日期", "2026-11-06"),
                             ("状态", "已确认")]:
            good = good.replace("| %s | ___ |" % label, "| %s | %s |" % (label, value))
        r = check_one(good, root / REGISTRY_NAME)
        assert not r["fails"], r["fails"]
        print("[PASS] 完整登记表放行")
        assert check_one(TEMPLATE, root / REGISTRY_NAME)["fails"], "空表应阻断"
        r2 = check_one(good.replace("短剧、漫剧（动态漫）改编权及信息网络传播权", "短剧改编权"),
                       root / REGISTRY_NAME)
        assert any("漫剧" in x for x in r2["fails"]), r2["fails"]
        r3 = check_one(good.replace("| 状态 | 已确认 |", "| 状态 | 待确认 |"), root / REGISTRY_NAME)
        assert r3["fails"], "待确认应阻断"
        print("[PASS] 空表 / 范围缺漫剧 / 状态非已确认 均阻断")
        pl = root / "pipeline"
        pl.mkdir()
        assert run_check(pl, None, str(root / "r.md"), None) == 1, "缺文件应阻断"
        (pl / REGISTRY_NAME).write_text(good, encoding="utf-8")
        assert run_check(pl, None, str(root / "r2.md"), str(root / "r2.json")) == 0
        assert "不判定授权是否真实有效" in (root / "r2.md").read_text(encoding="utf-8")
        assert json.loads((root / "r2.json").read_text(encoding="utf-8"))["fields_found"] == 9
        print("[PASS] CLI 缺文件阻断 / 有表放行 / 报告与 JSON 落盘 / 边界声明在位")

        # 自定义文件名自动发现：填齐的 `00_授权登记表.md` 不该再判「未找到」
        pl2 = root / "pl_custom"
        pl2.mkdir()
        custom = pl2 / "00_授权登记表.md"
        custom.write_text(good, encoding="utf-8")
        # 同目录放一份字段快照齐全的「检查报告」，不得被当成登记表
        (pl2 / "00_授权检查.md").write_text(
            render(check_one(good, custom)), encoding="utf-8")
        assert run_check(pl2, None, str(root / "r3.md"), str(root / "r3.json")) == 0
        res3 = json.loads((root / "r3.json").read_text(encoding="utf-8"))
        assert res3["registry"].endswith("00_授权登记表.md"), res3["registry"]
        assert "自动发现" in res3["registry_source"], res3
        assert "不判定授权是否真实有效" in (root / "r3.md").read_text(encoding="utf-8")
        print("[PASS] 自定义文件名自动发现放行 / 检查报告不被误认 / 边界声明仍在")

        pl3 = root / "pl_custom_empty"
        pl3.mkdir()
        (pl3 / "00_授权登记表.md").write_text(TEMPLATE, encoding="utf-8")
        assert run_check(pl3, None, None, None) == 1, "空表即使自定义名也应阻断"
        pl4 = root / "pl_multi"
        pl4.mkdir()
        (pl4 / "授权登记_旧.md").write_text(TEMPLATE, encoding="utf-8")
        (pl4 / "授权登记表_新.md").write_text(good, encoding="utf-8")
        assert run_check(pl4, None, str(root / "r4.md"), str(root / "r4.json")) == 0
        res4 = json.loads((root / "r4.json").read_text(encoding="utf-8"))
        assert res4["registry"].endswith("授权登记表_新.md"), res4["registry"]
        assert any("候选" in x for x in res4["infos"]), res4["infos"]
        pl5 = root / "pl_none"
        pl5.mkdir()
        (pl5 / "随手记.md").write_text("x", encoding="utf-8")
        assert run_check(pl5, None, str(root / "r5.md"), None) == 1
        assert "随手记.md" in (root / "r5.md").read_text(encoding="utf-8")
        print("[PASS] 空表自定义名仍阻断 / 多候选取字段最全并登记 / 缺表列出目录清单")
        print("[PASS] selftest 全部通过")
    return 0


def main():
    ap = argparse.ArgumentParser(description="S0 授权链阻断检查（SH-01/02）")
    sub = ap.add_subparsers(dest="cmd")
    it = sub.add_parser("init-template", help="生成授权登记表模板")
    it.add_argument("path")
    ck = sub.add_parser("check", help="检查授权登记表，缺项即阻断")
    ck.add_argument("--pipeline", required=True)
    ck.add_argument("--registry", help="显式指定登记表路径（默认自动发现 <pipeline>/ 内授权登记表）")
    ck.add_argument("--out", help="Markdown 报告路径")
    ck.add_argument("--json", dest="json_out", help="JSON 结果路径")
    sub.add_parser("selftest", help="内置自检")
    a = ap.parse_args()
    if a.cmd == "init-template":
        p = Path(a.path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(TEMPLATE, encoding="utf-8")
        print("[OK] 授权登记表模板：%s" % p)
        return 0
    if a.cmd == "check":
        return run_check(a.pipeline, a.registry, a.out, a.json_out)
    if a.cmd == "selftest":
        return selftest()
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
