#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""字幕对齐重建工具。

用法：
  build  把 base.srt 的时间轴 + zh_map.json 的译文合成新字幕
  check  校验 target.srt 是否与 base.srt 逐条对齐（条数/时间轴/序号/单调性）
  anchor 按指定行号打印 base 原文 ↔ target 译文（人工抽查对齐）

zh_map.json 约定：{"1": "译文", "2": "译文", ...}，键=base 的 1-based 条号。
缺键/多键直接报错终止，不静默补位。
"""
import argparse
import json
import os
import re
import sys


# ---------- SRT 解析 ----------

def read_text(path):
    """按二进制读，显式剥离 BOM 并统计行尾真实情况。"""
    raw = open(path, 'rb').read()
    bom = raw.startswith(b'\xef\xbb\xbf')
    if bom:
        raw = raw[3:]
    txt = raw.decode('utf-8')
    crlf = raw.count(b'\r\n')
    lone_lf = raw.count(b'\n') - crlf
    return txt, bom, crlf, lone_lf


def parse_srt(path):
    """返回 [(序号原文, 时间轴, 文本)]，文本多行用空格连接。"""
    txt, _, _, _ = read_text(path)
    norm = txt.replace('\r\n', '\n').replace('\r', '\n')
    blocks = [b for b in re.split(r'\n\s*\n', norm.strip()) if b.strip()]
    out = []
    for b in blocks:
        ls = b.split('\n')
        ti = [i for i, l in enumerate(ls) if '-->' in l]
        if not ti:
            continue
        k = ti[0]
        idx = ' '.join(ls[:k]).strip()
        tl = ls[k].strip()
        body = ' '.join(x.strip() for x in ls[k + 1:] if x.strip()).strip()
        out.append((idx, tl, body))
    return out


def mono(tl):
    """把时间轴起始时间转毫秒，用于单调性比较。"""
    s = tl.split('-->')[0].strip()
    h, m, rest = s.split(':')
    sec, ms = rest.replace('.', ',').split(',')
    return int(h) * 3600000 + int(m) * 60000 + int(sec) * 1000 + int(ms)


# ---------- build ----------

def cmd_build(a):
    base = parse_srt(a.base)
    with open(a.map, encoding='utf-8') as f:
        zh = json.load(f)
    zh = {int(k): v for k, v in zh.items()}

    n = len(base)
    missing = [i for i in range(1, n + 1) if i not in zh]
    extra = [i for i in zh if i < 1 or i > n]
    if missing or extra:
        print('❌ 译文映射与基准轨条号不匹配，终止。')
        print('   基准轨条数:', n)
        print('   缺键(%d):' % len(missing), missing[:60])
        print('   越界键(%d):' % len(extra), sorted(extra)[:60])
        sys.exit(2)

    out = []
    for i, (_, tl, _) in enumerate(base, 1):
        out.append('%d\n%s\n%s\n' % (i, tl, zh[i].strip()))

    nl = '\r\n' if a.newline == 'crlf' else '\n'
    # 先按 \n 拼装，再统一替换行尾——直接 join('\r\n') 会留下内部裸 \n（历史踩坑）
    text = '\n'.join(out).replace('\n', nl)
    if a.bom == 'utf8':
        data = b'\xef\xbb\xbf' + text.encode('utf-8')
    else:
        data = text.encode('utf-8')
    with open(a.out, 'wb') as f:
        f.write(data)

    print('✅ 已生成:', a.out)
    print('   条数:', n, '| 行尾:', a.newline, '| BOM:', a.bom, '| 字节:', len(data))
    check(a.base, a.out)


# ---------- check ----------

def check(base_path, target_path):
    base = parse_srt(base_path)
    tgt = parse_srt(target_path)
    print('--- 四道校验 ---')
    print('① 条数: base=%d target=%d  一致=%s' % (len(base), len(tgt), len(base) == len(tgt)))

    if len(base) != len(tgt):
        print('   ⚠ 条数不等，后续校验按较短一侧进行')
    n = min(len(base), len(tgt))
    diff = [(i + 1, base[i][1], tgt[i][1]) for i in range(n) if base[i][1] != tgt[i][1]]
    print('② 时间轴逐条一致: 不一致 %d / %d' % (len(diff), n))
    for d in diff[:5]:
        print('     ', d)

    nums = []
    ok_num = True
    for x in tgt:
        try:
            nums.append(int(x[0]))
        except ValueError:
            ok_num = False
    print('③ 序号连续 1..N: %s' % (ok_num and nums == list(range(1, len(tgt) + 1))))

    ms = [mono(t) for _, t, _ in tgt]
    mono_ok = all(ms[i] < ms[i + 1] for i in range(len(ms) - 1))
    print('④ 起始时间单调递增: %s' % mono_ok)

    words = set()
    for _, _, b in tgt:
        words |= set(re.findall(r'[A-Za-z]{2,}', b))
    print('   目标轨残留英文词:', sorted(words) or '无')

    _, bom, crlf, lone = read_text(target_path)
    print('   编码/行尾: BOM=%s | CRLF=%d | 裸LF=%d  %s'
          % (bom, crlf, lone, '(行尾混合，建议 --newline 统一)' if lone else ''))
    print('   首条:', tgt[0][2] if tgt else '')
    print('   末条:', tgt[-1][2] if tgt else '')
    return len(base) == len(tgt) and not diff and mono_ok and not lone


def cmd_check(a):
    check(a.base, a.target)


# ---------- anchor ----------

def cmd_anchor(a):
    base = parse_srt(a.base)
    tgt = parse_srt(a.target)
    lines = [int(x) for x in re.split(r'[,\s]+', a.lines) if x.strip()]
    for i in lines:
        be = base[i - 1][2] if 1 <= i <= len(base) else '(越界)'
        zh = tgt[i - 1][2] if 1 <= i <= len(tgt) else '(越界)'
        tl_ok = (base[i - 1][1] == tgt[i - 1][1]) if 1 <= i <= min(len(base), len(tgt)) else False
        print('%5d  BASE: %s' % (i, be[:70]))
        print('       TGT : %s   [时间轴一致: %s]' % (zh[:70], tl_ok))


def main():
    p = argparse.ArgumentParser(description='字幕对齐重建工具')
    sub = p.add_subparsers(dest='cmd', required=True)

    b = sub.add_parser('build', help='按基准轨时间轴合成新字幕')
    b.add_argument('--base', required=True)
    b.add_argument('--map', required=True)
    b.add_argument('--out', required=True)
    b.add_argument('--newline', choices=['crlf', 'lf'], default='crlf')
    b.add_argument('--bom', choices=['none', 'utf8'], default='none')
    b.set_defaults(func=cmd_build)

    c = sub.add_parser('check', help='校验目标稿与基准轨逐条对齐')
    c.add_argument('--base', required=True)
    c.add_argument('--target', required=True)
    c.set_defaults(func=cmd_check)

    n = sub.add_parser('anchor', help='按行号抽查对齐')
    n.add_argument('--base', required=True)
    n.add_argument('--target', required=True)
    n.add_argument('--lines', required=True, help='如 1,150,151,1760')
    n.set_defaults(func=cmd_anchor)

    a = p.parse_args()
    a.func(a)


if __name__ == '__main__':
    main()
