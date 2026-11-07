# -*- coding: utf-8 -*-
"""发布分镜：把 _shot_dry 写回 outputs/第N集/，并重建单集/全剧整合文档。"""
import io, os, re, shutil
from paths import WORK, OUT, OUTDIR, DRY, EP_MAX, TITLE, bundle_file

def read(p):
    return io.open(p, encoding="utf-8").read()

def head_of(path, fallback):
    """取原整合文档的头部（到第一个 --- 之后），并补上纯英文台词口径说明"""
    head = fallback
    if os.path.exists(path):
        t = read(path)
        m = re.search(r"^(.*?\n---\n)", t, re.S)
        if m:
            head = m.group(1)
    note = "> 台词为纯英文（中文已剥离，避免视频模型读出中文）；旁白第三人称叙述，角色内心独白（OS）第一人称。\n"
    head = head.replace("（v2.0）", "（v2.1）")
    if "纯英文" not in head:
        head = head.replace("\n---\n", "\n" + note + "\n---\n", 1)
    return head

def files_sorted(d):
    return sorted([f for f in os.listdir(d) if f.endswith(".txt") and "英文台词" not in f],
                  key=lambda x: (len(x), x))

# ---- 1. 写回分文件 ----
written = 0
for ep in range(1, EP_MAX + 1):
    src = os.path.join(DRY, "第%d集" % ep)
    dst = os.path.join(OUTDIR, "第%d集" % ep)
    for fn in files_sorted(src):
        shutil.copyfile(os.path.join(src, fn), os.path.join(dst, fn))
        written += 1

# ---- 2. 单集整合文档 ----
for ep in range(1, EP_MAX + 1):
    src = os.path.join(DRY, "第%d集" % ep)
    dstp = os.path.join(OUTDIR, "第%d集_整合文档_全段提示词.md" % ep)
    fb = ("# 《%s》第 %d 集 · 分镜提示词整合文档（v2.1）\n\n"
          "> P4 海外管线 ｜ 21:9 ｜ Seedance 2.5 ｜ 纯英文台词（欧洲本土口音）｜ 单段 ≤30s\n"
          "> 结构：前缀 → 场景概述 → 逐镜头 → 色调基准 → 特定场景优化 → 后缀\n"
          "> 台词为纯英文（中文已剥离，避免视频模型读出中文）；旁白第三人称叙述，角色内心独白（OS）第一人称。\n\n---\n" % (TITLE, ep))
    head = head_of(dstp, fb)
    parts = [head, "\n"]
    for fn in files_sorted(src):
        parts.append(read(os.path.join(src, fn)).rstrip() + "\n")
        parts.append("\n---\n\n")
    io.open(dstp, "w", encoding="utf-8").write("".join(parts))

# ---- 3. 全剧整合文档 ----
bundle = [
    "# 《%s》全剧 %d 集 分镜提示词 · 整合文档" % (TITLE, EP_MAX),
    "",
    "> 本文件为全剧唯一入口，覆盖第 1-%d 集所有分镜提示词，按集顺序排列，从上往下复制即可。" % EP_MAX,
    "> 口径：P4 海外管线（21:9 / 单镜头 ≤30s / Seedance 2.5 / 纯英文台词）。",
    "> 格式：v2.1（前缀 → 场景概述 → 逐镜头 → 特定场景优化 → 后缀）。",
    "> 台词：纯英文（中文已剥离，避免视频模型读出中文）；旁白第三人称叙述，角色内心独白（OS）第一人称。",
    "",
    "---",
    "",
]
for ep in range(1, EP_MAX + 1):
    bundle.append("\n# 第 %d 集\n" % ep)
    src = os.path.join(DRY, "第%d集" % ep)
    for fn in files_sorted(src):
        bundle.append(read(os.path.join(src, fn)).rstrip() + "\n")
    bundle.append("\n---\n")
io.open(os.path.join(OUTDIR, bundle_file()), "w", encoding="utf-8").write(
    "\n".join(bundle))

print("分文件写回:", written)
print("单集整合文档: %d" % EP_MAX)
print("全剧整合文档: ok")
