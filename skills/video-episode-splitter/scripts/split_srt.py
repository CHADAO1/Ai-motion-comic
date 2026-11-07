#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
split_srt.py — 把一整条时间线的「主 SRT」按集拆分，并让每集字幕各自从 00:00:00,000 起算

========= 使用步骤 =========
1. 在 Premiere 里把整部电影【整段】导出一次，同时导出【整条时间线】的 SRT，命名为 master.srt。
   —— 视频导出时「字幕(Captions)」里 Burn-in 选「无」，保证画面无字幕。
2. 打开 episodes.xlsx，在 start / end 两列填入每集的入点 / 出点（Premiere 时间码：HH:MM:SS:FF）；
   D 列「duration(自动)」会实时算出每集时长，方便你核对。
   —— 同时把 G1 单元格的「帧率 fps」填成你 PR 序列的帧率（如 25 / 24 / 30），脚本据此把 FF 换算成毫秒。
   —— 也可用 episodes.csv（同样填 HH:MM:SS:FF，并在运行时加 --fps 25）。
3. 运行：  python split_srt.py
   （可选：python split_srt.py --srt master.srt --csv episodes.xlsx --out srt_out）
   注：读取 .xlsx 需先 pip install openpyxl；只用 .csv 则无需额外依赖。

========= 脚本做了什么 =========
 a) 把【横跨切割点】的字幕按入/出点裁断，接缝处不丢字幕；
 b) 每集时间码减去该集入点，使字幕从 0 起算，与你按入/出点导出的视频对齐；
 c) 字幕中间的留白（无字幕区间）原样保留，不受影响；
 d) 仅取落在该集窗口内的字幕，自动跳过空行 / 占位符 / 格式错误行。
"""

import os
import re
import csv
import argparse
import sys
import datetime as _dt

try:
    import openpyxl
    _HAS_OXL = True
except ImportError:
    _HAS_OXL = False

# ---------- 时间码解析 ----------
# 支持三种格式（均返回毫秒）：
#   1) SRT 毫秒   : HH:MM:SS,mmm  或  HH:MM:SS.mmm
#   2) PR 时间码   : HH:MM:SS:FF  （FF 为帧，需 fps 才能换算成毫秒）
#   3) 简易秒      : HH:MM:SS
def parse_tc(tc, fps=25):
    # [修复] 归一化全角标点：中文输入法下极易把时间码打成全角冒号/逗号（如 00：00：00：00），
    # 会导致该行解析失败、整集被静默跳过。此前《狼王分集.xlsx》第 1 集即因全角冒号丢失。
    tc = (tc.replace('：', ':').replace('，', ',').replace('．', '.')
            .replace('－', '-').replace('\u3000', ' ').strip())
    # SRT 毫秒格式（含逗号，或「2 段冒号 + 点号」）
    if ',' in tc or ('.' in tc and tc.count(':') == 2):
        t = tc.replace('.', ',')
        h, m, s, ms = (int(x) for x in re.split('[:,]', t))
        return (h * 3600 + m * 60 + s) * 1000 + ms
    # PR 时间码 HH:MM:SS:FF
    if tc.count(':') == 3:
        h, m, s, f = (int(x) for x in tc.split(':'))
        return (h * 3600 + m * 60 + s) * 1000 + round(f / fps * 1000)
    # 简易 HH:MM:SS
    if tc.count(':') == 2:
        h, m, s = (int(x) for x in tc.split(':'))
        return (h * 3600 + m * 60 + s) * 1000
    raise ValueError("无法识别的时间码格式（应为 HH:MM:SS,mmm 或 HH:MM:SS:FF）")

def fmt_tc(ms):
    ms = max(0, int(ms))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1_000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

# ---------- Excel 单元格值 → 毫秒（兼容 字符串 / datetime / 小数时间） ----------
def cell_to_ms(val, fps=25):
    if val is None:
        return None
    if isinstance(val, str):
        v = val.strip()
        if v == '':
            return None
        try:
            return parse_tc(v, fps)
        except ValueError:
            return None
    if isinstance(val, _dt.datetime):
        val = val.time()
    if isinstance(val, _dt.time):
        ms = val.microsecond // 1000
        return (val.hour * 3600 + val.minute * 60 + val.second) * 1000 + ms
    if isinstance(val, float):               # Excel 时间小数（一天的分数）
        return int(round(val * 86_400 * 1000))
    return None

# ---------- 读取分集表（csv 或 xlsx 通用） ----------
def read_table(path):
    rows = []
    if path.lower().endswith('.xlsx'):
        if not _HAS_OXL:
            sys.exit("✗ 读取 .xlsx 需要 openpyxl，请先运行：pip install openpyxl")
        wb = openpyxl.load_workbook(path, data_only=True)
        ws = wb.active
        for r in ws.iter_rows(min_row=2, values_only=True):
            ep = r[0] if len(r) > 0 else None
            st = r[1] if len(r) > 1 else None
            en = r[2] if len(r) > 2 else None
            rows.append((ep, st, en))
    else:
        with open(path, encoding='utf-8-sig', newline='') as f:
            for row in csv.DictReader(f):
                rows.append((row.get('episode'), row.get('start'), row.get('end')))
    return rows

# ---------- 从 xlsx 的 G1 读帧率 ----------
def read_fps_from_xlsx(path):
    if not _HAS_OXL:
        return None
    try:
        wb = openpyxl.load_workbook(path, data_only=True)
        ws = wb.active
        v = ws['G1'].value
        if isinstance(v, (int, float)) and v > 0:
            return float(v)
    except Exception:
        pass
    return None

# ---------- 读取主 SRT ----------
def read_srt(path):
    with open(path, encoding='utf-8-sig') as f:
        raw = f.read().strip()
    subs = []
    for block in raw.split('\n\n'):
        lines = [l for l in block.split('\n') if l.strip() != '']
        if not lines:
            continue
        ti = next((i for i, l in enumerate(lines) if '-->' in l), None)
        if ti is None:
            continue
        parts = re.split(r'\s*-->\s*', lines[ti])
        if len(parts) != 2:
            continue
        try:
            s = parse_tc(parts[0])
            e = parse_tc(parts[1])
        except ValueError:
            continue
        text = '\n'.join(lines[ti + 1:])
        subs.append([s, e, text])
    subs.sort(key=lambda x: x[0])
    return subs

# ---------- 切分单集（裁断跨边界字幕） ----------
def split_episode(subs, start_ms, end_ms):
    out = []
    for s, e, txt in subs:
        if e <= start_ms or s >= end_ms:      # 完全在区间外
            continue
        ns = max(s, start_ms) - start_ms       # 跨入点：把前面部分裁掉
        ne = min(e, end_ms) - start_ms         # 跨出点：把后面部分裁掉
        if ne > ns:
            out.append((ns, ne, txt))
    return out

# ---------- 主流程 ----------
def main():
    ap = argparse.ArgumentParser(description="按集拆分主 SRT 并归零时间码")
    ap.add_argument('--srt', default='master.srt', help='整条时间线的主字幕文件')
    ap.add_argument('--csv', default='episodes.xlsx', help='分集入/出点清单（.xlsx 或 .csv）')
    ap.add_argument('--out', default='srt_out', help='输出目录')
    ap.add_argument('--fps', type=float, default=None,
                    help='序列帧率，用于解析 HH:MM:SS:FF 时间码（默认读 xlsx 的 G1，仍无则 25）')
    args = ap.parse_args()

    if not os.path.exists(args.srt):
        sys.exit(f"✗ 找不到主字幕文件：{args.srt}\n  请先导出整条时间线的 SRT。")
    if not os.path.exists(args.csv):
        sys.exit(f"✗ 找不到分集表：{args.csv}")

    subs = read_srt(args.srt)
    print(f"已读取主字幕：{len(subs)} 条")

    # 确定帧率：命令行 > xlsx 的 G1 > 默认 25
    fps = args.fps
    if fps is None and args.csv.lower().endswith('.xlsx'):
        fps = read_fps_from_xlsx(args.csv)
    fps = fps or 25
    print(f"帧率 fps = {fps}（HH:MM:SS:FF 的 FF 按此换算成毫秒）")

    os.makedirs(args.out, exist_ok=True)

    total = 0
    for ep_raw, st_raw, en_raw in read_table(args.csv):
        ep = str(ep_raw).strip() if ep_raw is not None else ''
        st = str(st_raw).strip() if st_raw is not None else ''
        en = str(en_raw).strip() if en_raw is not None else ''

        if not ep or not st or not en:
            print(f"  [跳过] 第 {ep or '?'} 集：缺少入点/出点，请填写后重跑")
            continue
        if re.search(r'[A-Za-z]', st) or re.search(r'[A-Za-z]', en):  # 含字母 → 仍是占位符
            print(f"  [跳过] 第 {ep} 集：时间码还是占位符，请填入真实时间")
            continue
        try:
            epn = int(ep)
            s0 = cell_to_ms(st_raw, fps)    # 直接传原始值（字符串 / datetime / 小数均可）
            e0 = cell_to_ms(en_raw, fps)
            if s0 is None or e0 is None:
                raise ValueError("时间码无法解析")
        except ValueError:
            print(f"  [跳过] 第 {ep} 集：时间码格式有误（{st} / {en}）")
            continue
        if e0 <= s0:
            print(f"  [跳过] 第 {ep} 集：出点必须晚于入点")
            continue

        blocks = split_episode(subs, s0, e0)
        dur = fmt_tc(e0 - s0)
        fn = os.path.join(args.out, f"episode_{epn:02d}.srt")
        with open(fn, 'w', encoding='utf-8') as w:
            body = '\n\n'.join(
                f"{i + 1}\n{fmt_tc(s)} --> {fmt_tc(e)}\n{t}"
                for i, (s, e, t) in enumerate(blocks)
            )
            w.write(body + ('\n' if body else ''))
        print(f"  [生成] episode_{epn:02d}.srt  -> {len(blocks)} 条字幕（时长 {dur}）")
        total += 1

    print(f"\n完成：共生成 {total} 个分集 SRT，输出目录 {args.out}/")

if __name__ == '__main__':
    main()
