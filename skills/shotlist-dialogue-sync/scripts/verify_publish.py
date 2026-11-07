# -*- coding: utf-8 -*-
"""校验发布结果：分文件一致性 + 整合文档头部与内容。"""
import io, os

from paths import WORK, OUT, OUTDIR, DRY, EP_MAX, TITLE, COMPARE_PREFIX, load_role_map, compare_file, compare_bundle, compare_legacy, bundle_file

bad = tot = 0
for ep in range(1, EP_MAX + 1):
    d = os.path.join(DRY, "第%d集" % ep)
    o = os.path.join(OUT, "第%d集" % ep)
    for fn in os.listdir(d):
        if not fn.endswith(".txt") or "英文台词" in fn:
            continue
        tot += 1
        a = io.open(os.path.join(d, fn), encoding="utf-8").read()
        b = io.open(os.path.join(o, fn), encoding="utf-8").read()
        if a != b:
            bad += 1
            print("DIFF", ep, fn)
print("分文件对比: %d  不一致: %d" % (tot, bad))

for name in ["第1集_整合文档_全段提示词.md", "第5集_整合文档_全段提示词.md",
             "第%d集_整合文档_全段提示词.md" % EP_MAX, bundle_file()]:
    p = os.path.join(OUT, name)
    s = io.open(p, encoding="utf-8").read()
    cn_q = 0
    for i, l in enumerate(s.splitlines()):
        if "：" not in l:
            continue
        lab = l.strip().split("：", 1)[0]
        if not any(k in lab for k in ("台词", "旁白", "OS", "VO", "屏幕文字")):
            continue
        import re
        q = re.search(r'"([^"]*)"', l)
        if q and re.search(r"[\u4e00-\u9fff]", q.group(1)):
            cn_q += 1
    print("%-38s %7d字节  台词行含中文引号: %d" % (name, len(s), cn_q))
    print("     头部:", s.splitlines()[0][:60], "|", s.splitlines()[2][:70] if len(s.splitlines()) > 2 else "")
