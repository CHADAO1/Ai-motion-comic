# -*- coding: utf-8 -*-
"""统一 40 个单集整合文档的头部口径说明。"""
import io, os

from paths import WORK, OUT, OUTDIR, DRY, EP_MAX, TITLE, COMPARE_PREFIX, load_role_map, compare_file, compare_bundle, compare_legacy, bundle_file
n = 0
for ep in range(1, EP_MAX + 1):
    p = os.path.join(OUT, "第%d集_整合文档_全段提示词.md" % ep)
    s = io.open(p, encoding="utf-8").read()
    o = s
    s = s.replace("英文台词 + 中英对照", "纯英文台词")
    s = s.replace("（v2.0）", "（v2.1）")
    s = s.replace("版本：v2.0 ｜", "版本：v2.1 ｜")
    if s != o:
        io.open(p, "w", encoding="utf-8").write(s)
        n += 1
print("更新头部:", n)

# 复核
for ep in (1, 5, 40):
    p = os.path.join(OUT, "第%d集_整合文档_全段提示词.md" % ep)
    s = io.open(p, encoding="utf-8").read()
    bad = [l for l in s.splitlines()[:9] if "中英对照" in l or "v2.0" in l]
    print("第%d集 头部残留:" % ep, bad)
