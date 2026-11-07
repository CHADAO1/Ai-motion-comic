#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify_integrated.py — INT-01 一致性校验：整合文档 ⇄ 分文件

用途
    交付时生成的"整合文档"（一文件看全）必须与分文件一字不差。本脚本做机器校验，
    替代"我检查过了"这类空泛结论（preflight 使用原则第 2 条）。

用法
    python verify_integrated.py --integrated <整合文档.md> --sources <分文件目录> [--ext .txt] [--json]

判定
    - 从整合文档里抽出所有 ``` 代码块（= 各段提示词正文 + 空间基准等辅助块）
    - 从分文件目录里的所有提示词文件抽出所有 ``` 代码块
    - 逐块在"分文件全部块拼接文本"里找子串（归一化：去每行尾空格、去空行）
    - 全部命中 → ALL_MATCH（exit 0）
    - 有未命中 → HAS_DIFF（exit 1），打印未命中块的首行与"缺失行"前若干条，
      供人工判定是「整合文档漂移」还是「该块是按交付需要改造过的（如对话段删镜）」

退出码
    0 = ALL_MATCH    1 = HAS_DIFF    2 = 用法/文件错误
"""
import argparse
import json
import os
import re
import sys

FENCE = re.compile(r"```[a-zA-Z0-9_-]*\n(.*?)```", re.S)


def blocks(path):
    with open(path, encoding="utf-8") as f:
        return FENCE.findall(f.read())


def norm(s):
    lines = [l.rstrip() for l in s.strip().splitlines()]
    return "\n".join(l for l in lines if l.strip() != "")


def collect_sources(folder, exts, exclude=None):
    ex_abs = os.path.abspath(exclude) if exclude else None
    files = [
        os.path.join(folder, n)
        for n in sorted(os.listdir(folder))
        if os.path.isfile(os.path.join(folder, n))
        and any(n.lower().endswith(e) for e in exts)
        and not n.startswith("~")
        and os.path.abspath(os.path.join(folder, n)) != ex_abs
    ]
    out = []
    for p in files:
        for b in blocks(p):
            n = norm(b)
            if n:
                out.append((os.path.basename(p), n))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--integrated", required=True, help="整合文档路径（.md）")
    ap.add_argument("--sources", required=True, help="分文件所在目录")
    ap.add_argument("--ext", default=".txt,.md",
                    help="分文件扩展名，逗号分隔，默认 .txt,.md（.md 用于把衔接表里的空间基准块也纳入比对）")
    ap.add_argument("--json", action="store_true", help="以 JSON 输出结果")
    ap.add_argument("--skip", default="", help="声明式例外：要跳过的整合文档代码块序号，逗号分隔（如 2,5）。"
                                             "用于「该块按交付需要改造过、不与任何分文件逐字相同」的情形"
                                             "（典型：对话段删镜头/改时长）。跳过项会在结果里单独列出，"
                                             "禁止用它掩盖真实漂移——漂移应当去改文件，不是加 --skip。")
    a = ap.parse_args()

    skips = {int(x) for x in a.skip.replace("，", ",").split(",") if x.strip().isdigit()}

    exts = [e.strip().lower() for e in a.ext.split(",") if e.strip()]
    if not exts:
        exts = [".txt"]

    if not os.path.isfile(a.integrated):
        print(f"ERROR: 整合文档不存在: {a.integrated}")
        return 2
    if not os.path.isdir(a.sources):
        print(f"ERROR: 分文件目录不存在: {a.sources}")
        return 2

    src = collect_sources(a.sources, exts, exclude=a.integrated)
    if not src:
        print(f"ERROR: 分文件目录里没找到 {exts} 提示词文件: {a.sources}")
        return 2

    blob = "\n".join(n for _, n in src)
    src_lines = set()
    for _, n in src:
        src_lines.update(n.splitlines())

    results = []
    for i, b in enumerate(blocks(a.integrated), 1):
        nb = norm(b)
        if not nb:
            continue
        head = nb.splitlines()[0][:60]
        hit = nb in blob
        item = {"index": i, "head": head, "chars": len(nb), "match": hit,
                "skipped": i in skips}
        if not hit and i not in skips:
            item["missing_lines"] = [l[:110] for l in nb.splitlines() if l not in src_lines][:8]
        results.append(item)

    ok = all(r["match"] or r["skipped"] for r in results)
    if a.json:
        print(json.dumps({"result": "ALL_MATCH" if ok else "HAS_DIFF",
                          "declared_skips": sorted(skips),
                          "sources": [n for n, _ in src],
                          "blocks": results}, ensure_ascii=False, indent=2))
    else:
        print(f"分文件代码块: {len(src)} 个（来自 {len(set(n for n, _ in src))} 个文件）")
        print(f"整合文档代码块: {len(results)} 个" + (f"；声明例外 {sorted(skips)}" if skips else ""))
        print("")
        for r in results:
            tag = "SKIP" if r["skipped"] else ("OK  " if r["match"] else "FAIL")
            print(f"{tag}  #{r['index']:<3} {r['chars']:>5} chars  {r['head']}")
            for m in r.get("missing_lines", []):
                print("        - " + m)
        print("")
        print("ALL_MATCH" if ok else "HAS_DIFF")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
