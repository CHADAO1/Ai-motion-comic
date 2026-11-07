# -*- coding: utf-8 -*-
"""开工前核对生效配置，并做一次包内脱敏自检。

用法：python scripts/print_config.py
"""
import os
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import paths  # noqa: E402  未设环境变量时由 paths.py 明确报错退出

print("=== 生效配置 ===")
for k in ("SHOTLIST_WORK", "SHOTLIST_OUT", "SHOTLIST_EPISODES",
          "SHOTLIST_TITLE", "SHOTLIST_COMPARE_PREFIX", "SHOTLIST_ROLE_MAP"):
    print("  %-26s %s" % (k, os.environ.get(k, "(默认)")))
print("  WORK    = %s" % paths.WORK)
print("  OUT     = %s" % paths.OUT)
print("  DRY     = %s" % paths.DRY)
print("  EP_MAX  = %d" % paths.EP_MAX)
print("  对照文件= %s" % paths.compare_file(1))
print("  全剧整合= %s" % paths.bundle_file())
print("  WORK 存在: %s ｜ OUT 存在: %s" %
      (Path(paths.WORK).exists(), Path(paths.OUT).exists()))

# 脱敏自检：包内不得残留本机绝对路径、内网 IP、旧项目名
root = Path(__file__).resolve().parent.parent
pat = re.compile(r"192\.168\.|C:\\Users\\|CHM008|2026-09-14-21-29-23|别出声")
hits = []
for f in root.rglob("*"):
    if f.name == "print_config.py":
        continue  # 检测工具自身的正则字面量不算残留
    if f.is_file() and f.suffix.lower() in (".py", ".md"):
        try:
            t = f.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for i, line in enumerate(t.splitlines(), 1):
            if pat.search(line):
                hits.append("%s:%d %s" % (f.relative_to(root), i, line.strip()[:70]))
print("\n=== 脱敏自检 ===")
if hits:
    print("[FAIL] 残留 %d 处：" % len(hits))
    for h in hits[:20]:
        print("  " + h)
    sys.exit(1)
print("[PASS] 本机绝对路径 / 内网 IP / 旧项目名 命中数 = 0")
