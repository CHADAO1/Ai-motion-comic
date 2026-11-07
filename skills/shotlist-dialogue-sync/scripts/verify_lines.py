# -*- coding: utf-8 -*-
"""校验分镜提示词的台词行：纯英文 / OS第一人称 / 旁白第三人称 / 无重复。"""
import io, os, re

from paths import WORK, OUT, OUTDIR, DRY, EP_MAX, TITLE, COMPARE_PREFIX, load_role_map, compare_file, compare_bundle, compare_legacy, bundle_file
CN = re.compile(r"[\u4e00-\u9fff]")
FP = re.compile(r"\b(I|I'm|I'd|I'll|I've|me|my|mine|myself|we|we're|we'd|we've|us|our|ours)\b", re.I)
LAB = re.compile(r"^(?P<lab>[-•*#\s]*)(?P<name>[^：]{1,24})[：:](?P<body>.+)$")

cn_left, os_nofp, nb_fp, dup = [], [], [], []
n_line = 0
for ep in range(1, EP_MAX + 1):
    d = os.path.join(DRY, "第%d集" % ep)
    for fn in sorted(os.listdir(d), key=lambda x: (len(x), x)):
        if not fn.endswith(".txt") or "英文台词" in fn:
            continue
        prev = None
        for i, raw in enumerate(io.open(os.path.join(d, fn), encoding="utf-8").read().splitlines()):
            s = raw.strip()
            m = LAB.match(s)
            if not m:
                continue
            name = re.sub(r"^[-•*#\s]+", "", m.group("name")).strip()
            if not re.search(r"(台词|旁白|OS|VO|屏幕文字|内心)", name):
                continue
            body = m.group("body").strip()
            q = re.search(r'"([^"]*)"', body)
            inner = q.group(1) if q else ""
            tail = body[q.end():] if q else ""
            n_line += 1
            tag = "%d集 %s:%d" % (ep, fn, i + 1)
            if CN.search(inner) or "中英" in name:
                cn_left.append("%s | %s" % (tag, s[:110]))
            if "OS" in name.upper() and inner and not FP.search(inner):
                os_nofp.append("%s | %s | %s" % (tag, name, inner[:80]))
            if "旁白" in name and inner and FP.search(inner):
                nb_fp.append("%s | %s | %s" % (tag, name, inner[:80]))
            if prev == s:
                dup.append("%s | %s" % (tag, s[:110]))
            prev = s

print("台词行总数:", n_line)
print("引号内含中文 或 标签残留“中英”:", len(cn_left))
for x in cn_left[:20]:
    print("   ", x)
print("OS行英文缺第一人称:", len(os_nofp))
for x in os_nofp[:20]:
    print("   ", x)
print("旁白行英文含第一人称:", len(nb_fp))
for x in nb_fp[:20]:
    print("   ", x)
print("相邻重复行:", len(dup))
for x in dup[:20]:
    print("   ", x)
