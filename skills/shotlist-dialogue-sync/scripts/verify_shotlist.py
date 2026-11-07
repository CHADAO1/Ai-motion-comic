# -*- coding: utf-8 -*-
"""校验 dry 分镜：按"中文流"检查剧本条目全覆盖 + 重复。"""
import re, io, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import match_shotlist as M

from paths import WORK, OUT, OUTDIR, DRY, EP_MAX, TITLE, COMPARE_PREFIX, load_role_map, compare_file, compare_bundle, compare_legacy, bundle_file

def norm(s):
    return re.sub(r"[\s\"'“”‘’，。！？、…—\-–/／,.!?;:：（）()【】]+", "", s or "")

def cn_stream(txt):
    """抽取所有台词行里第一个引号内的中文，按序拼接"""
    parts = []
    for l in txt.splitlines():
        s = l.strip()
        if not re.search(r"(台词|旁白|OS|VO|屏幕文字|内心)", s):
            continue
        for m in re.finditer(r'"([^"]*)"', s):
            v = m.group(1)
            if re.search(r"[\u4e00-\u9fff]", v):
                parts.append(v)
                break
    return norm("".join(parts))

tot_miss, tot_dup = 0, 0
lines = []
for ep in range(1, EP_MAX + 1):
    d = os.path.join(DRY, "第%d集" % ep)
    txt = ""
    for fn in sorted(os.listdir(d), key=lambda x: (len(x), x)):
        txt += io.open(os.path.join(d, fn), encoding="utf-8").read() + "\n"
    stream = cn_stream(txt)
    ents = M.entries[ep]
    miss = [e for e in ents if norm(e["cn"]) not in stream]
    dup = []
    for e in ents:
        n = norm(e["cn"])
        if n and len(n) > 6 and stream.count(n) > 1:
            dup.append(e)
    tot_miss += len(miss); tot_dup += len(dup)
    if miss or dup:
        lines.append("=== 第%d集 | 条目%d | 缺%d 重复%d" % (ep, len(ents), len(miss), len(dup)))
        for e in miss[:10]:
            lines.append("   [缺] %s %s: %s" % (e["scene"], e["speaker"], e["cn"][:50]))
        for e in dup[:6]:
            lines.append("   [重] %s: %s" % (e["speaker"], e["cn"][:50]))
io.open(os.path.join(WORK, "_shot_verify.txt"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
print("缺条目合计 %d | 重复条目合计 %d" % (tot_miss, tot_dup))
