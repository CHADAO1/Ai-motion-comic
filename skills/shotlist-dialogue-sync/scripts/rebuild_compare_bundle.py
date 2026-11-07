# -*- coding: utf-8 -*-
"""重建全剧台词中英对照整合文件，并同步旧名副本。"""
import io, os
from paths import OUT, EP_MAX, TITLE, COMPARE_PREFIX, compare_file, compare_bundle, compare_legacy

head = [
    "《%s》%s · 全%d集整合版" % (TITLE, COMPARE_PREFIX, EP_MAX),
    "（台词为纯英文提示词口径 ｜ 供配音 / 字幕剪辑）",
    "（旁白为第三人称叙述；角色内心独白 OS 保留第一人称）",
    "",
    "",
]
sep = "=" * 60

parts = list(head)
for ep in range(1, EP_MAX + 1):
    p = os.path.join(OUT, compare_file(ep))
    parts.append(sep)
    parts.append(io.open(p, encoding="utf-8").read().rstrip())
    parts.append("")

body = "\n".join(parts) + "\n"
dst1 = os.path.join(OUT, compare_bundle())
dst2 = os.path.join(OUT, compare_legacy())
io.open(dst1, "w", encoding="utf-8").write(body)
io.open(dst2, "w", encoding="utf-8").write(body)
print("整合版:", len(body), "字节")
print("集数分隔:", body.count(sep))
t = io.open(dst1, encoding="utf-8").read()
print("首条预览:", t[:60].replace("\n", " "))
