# -*- coding: utf-8 -*-
"""扫描分镜台词行里的中文说话人标签。"""
import io, os, re, collections

from paths import WORK, OUT, OUTDIR, DRY, EP_MAX, TITLE, COMPARE_PREFIX, load_role_map, compare_file, compare_bundle, compare_legacy, bundle_file
CN = re.compile(r"[\u4e00-\u9fff]")
c = collections.Counter()
samples = {}
for ep in range(1, EP_MAX + 1):
    d = os.path.join(DRY, "第%d集" % ep)
    for fn in sorted(os.listdir(d), key=lambda x: (len(x), x)):
        if not fn.endswith(".txt") or "英文台词" in fn:
            continue
        for i, raw in enumerate(io.open(os.path.join(d, fn), encoding="utf-8").read().splitlines()):
            s = raw.strip()
            m = re.match(r"^[-•*#\s]*(?P<name>[^：]{1,24})[：:](?P<body>.*)$", s)
            if not m:
                continue
            name = m.group("name").strip()
            if not re.search(r"(台词|旁白|OS|VO|屏幕文字|内心)", name):
                continue
            body = m.group("body")
            # 说话人 = 标签内 或 body 里 "——" 前
            sp = re.sub(r"^(台词|旁白|OS|VO|屏幕文字|内心)\s*", "", re.sub(r"^中英", "", name)).strip(" ：:—-")
            if not sp:
                mm = re.match(r"^(?P<sp>[^—\"]{1,16})[—-]{1,2}\s*\"", body.strip())
                if mm:
                    sp = mm.group("sp").strip()
            if sp and CN.search(sp):
                c[sp] += 1
                samples.setdefault(sp, "%d集 %s:%d" % (ep, fn, i + 1))
print("中文说话人标签种类:", len(c))
for k, v in c.most_common():
    print("   %-16s x%-3d  例: %s" % (k, v, samples[k]))
