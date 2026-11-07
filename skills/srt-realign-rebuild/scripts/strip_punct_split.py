#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
字幕去标点拆条（MODE 3）

以基准轨（base）的时间窗为唯一权威，把目标轨（target）每条文本按标点切成多条：
  - 标点本身丢弃（书名号 《》 默认保留）
  - 拆出的首条起点 == 基准条起点；末条终点 == 基准条终点  → 父窗口边界零漂移
  - 窗口内按字数比例分配时长，单条最低 --min-ms
  - 若父窗口给不出 --min-seg-ms/段 → 不拆，标点直接去掉、保留单卡（防闪卡）

用法:
  python strip_punct_split.py --base en.srt --target zh.srt --out zh_nopunct.srt \
      --newline crlf --bom none
"""
import argparse
import os
import re

# 断句并丢弃的标点
SPLIT_CHARS = '，。！？、；：,.!?;:…—－“”‘’（）()[]{}「」【】'
# 只删除、不拆分（间隔号：拆开会把「芬里斯·康尼克」劈成两张卡）
DROP_ONLY = '·•‧・'
# 保留（书名号等专用标记）
KEEP_CHARS = '《》'

PUNCT_RE = re.compile('[' + re.escape(SPLIT_CHARS) + ']+')
DROP_RE = re.compile('[' + re.escape(DROP_ONLY) + ']')
BAD_RE = re.compile(
    r'[^\w\s\u4e00-\u9fff' + re.escape(KEEP_CHARS) + r']', re.UNICODE)


def to_ms(s):
    h, m, rest = s.strip().split(':')
    sec, ms = rest.split(',')
    return int(h) * 3600000 + int(m) * 60000 + int(sec) * 1000 + int(ms)


def fmt(ms):
    ms = int(round(ms))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return '%02d:%02d:%02d,%03d' % (h, m, s, ms)


def parse(path):
    raw = open(path, 'rb').read()
    bom = raw[:3] == b'\xef\xbb\xbf'
    crlf = b'\r\n' in raw
    txt = raw.decode('utf-8-sig').replace('\r\n', '\n')
    out = []
    for b in re.split(r'\n\s*\n', txt.strip()):
        if not b.strip():
            continue
        ls = b.split('\n')
        try:
            k = [j for j, l in enumerate(ls) if '-->' in l][0]
        except IndexError:
            continue
        s, e = [x.strip() for x in ls[k].split('-->')]
        out.append((to_ms(s), to_ms(e), ' '.join(ls[k + 1:]).strip()))
    return out, bom, crlf


def split_text(t):
    t = DROP_RE.sub('', t)
    parts = [p.strip() for p in PUNCT_RE.split(t)]
    return [p for p in parts if p]


def alloc(dur, weights, min_ms):
    """按 weights 比例分配 dur 毫秒，带单条最低时长下限（水位填充）"""
    n = len(weights)
    if n == 1:
        return [float(dur)]
    floor = min(min_ms, dur / n)
    res = [0.0] * n
    fixed = set()
    while True:
        free = [i for i in range(n) if i not in fixed]
        if not free:
            break
        remaining = dur - sum(res[i] for i in fixed)
        if len(free) == 1:
            res[free[0]] = remaining
            break
        w = sum(weights[i] for i in free)
        viol = [i for i in free if remaining * weights[i] / w < floor - 1e-9]
        if not viol:
            for i in free:
                res[i] = remaining * weights[i] / w
            break
        for i in viol:
            fixed.add(i)
            res[i] = floor
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--base', required=True, help='基准轨 SRT（时间权威）')
    ap.add_argument('--target', required=True, help='待处理的目标轨 SRT')
    ap.add_argument('--out', required=True)
    ap.add_argument('--min-ms', type=int, default=700, help='拆条单条最低时长')
    ap.add_argument('--min-seg-ms', type=int, default=300,
                    help='父窗口低于「段数×该值」时退回单卡')
    ap.add_argument('--newline', choices=['crlf', 'lf'], default=None,
                    help='默认跟随基准轨')
    ap.add_argument('--bom', choices=['utf8', 'none'], default=None,
                    help='默认跟随基准轨')
    ap.add_argument('--quiet', action='store_true')
    a = ap.parse_args()

    base, b_bom, b_crlf = parse(a.base)
    tgt, _, _ = parse(a.target)
    nl_mode = a.newline or ('crlf' if b_crlf else 'lf')
    bom_mode = a.bom or ('utf8' if b_bom else 'none')

    if len(base) != len(tgt):
        raise SystemExit('❌ 条数不一致：基准 %d / 目标 %d。请先用 MODE 1 整轨重建，'
                         '再做去标点拆条。' % (len(base), len(tgt)))

    cues = []
    split_cnt = 0
    merged_back = []
    for idx, ((es, ee, _), (zs, ze, zt)) in enumerate(zip(base, tgt), 1):
        if es != zs or ee != ze:
            raise SystemExit('❌ 第 %d 条时间窗不一致（基准 %s-%s / 目标 %s-%s）。'
                             '去标点拆条的前提是两轨已逐条对齐。'
                             % (idx, fmt(es), fmt(ee), fmt(zs), fmt(ze)))
        segs = split_text(zt) or [zt.strip()]
        if len(segs) == 1:
            cues.append((es, ee, segs[0], idx))
            continue
        if (ee - es) < len(segs) * a.min_seg_ms:
            merged = ''.join(segs)
            cues.append((es, ee, merged, idx))
            merged_back.append((idx, ee - es, zt, merged))
            continue
        split_cnt += 1
        durs = alloc(ee - es, [len(x) for x in segs], a.min_ms)
        cur = es
        for i, (seg, d) in enumerate(zip(segs, durs)):
            st = cur
            en = ee if i == len(segs) - 1 else cur + d
            st_i, en_i = int(round(st)), int(round(en))
            if en_i <= st_i:
                en_i = st_i + 1
            cues.append((st_i, en_i, seg, idx))
            cur = en
        assert cues[-1][1] == ee, '末条终点漂移'

    nl = '\r\n' if nl_mode == 'crlf' else '\n'
    body = nl.join('%d%s%s --> %s%s%s%s' % (i, nl, fmt(s), fmt(e), nl, t, nl)
                   for i, (s, e, t, _) in enumerate(cues, 1))
    data = body.encode('utf-8')
    if bom_mode == 'utf8':
        data = b'\xef\xbb\xbf' + data
    with open(a.out, 'wb') as f:
        f.write(data)

    # ---- 自检 ----
    bad_b = sum(1 for pi, (es, ee, _) in enumerate(base, 1)
                if (lambda g: not g or g[0][0] != es or g[-1][1] != ee)(
                    [c for c in cues if c[3] == pi]))
    allt = ''.join(c[2] for c in cues)
    leftover = sorted(set(BAD_RE.findall(allt)))
    mono = all(cues[i][1] <= cues[i + 1][0] for i in range(len(cues) - 1))
    empty = [i + 1 for i, c in enumerate(cues) if not c[2].strip()]
    ok = (not leftover) and mono and bad_b == 0 and not empty

    if not a.quiet:
        print('基准条数        :', len(base))
        print('拆条父条数      :', split_cnt)
        print('窗口过紧未拆    :', len(merged_back))
        for idx, d, o, m in merged_back:
            print('   未拆 #%d (%dms): %s -> %s' % (idx, d, o, m))
        print('输出总条数      :', len(cues))
        print('输出字节        :', len(data))
        print('行尾 / BOM      :', nl_mode, '/', bom_mode)
        print('残留标点        :', leftover or '无')
        print('空文本          :', empty or '0')
        print('父窗口边界漂移  :', bad_b)
        print('时间轴不重叠    :', mono)
        print('书名号保留条数  :', sum(1 for c in cues if '《' in c[2]))
        durs = [c[1] - c[0] for c in cues]
        print('单条时长 min/中位/max : %d / %d / %d ms'
              % (min(durs), sorted(durs)[len(durs) // 2], max(durs)))
        print('自检结果        :', '✅ 全绿' if ok else '❌ 有问题，请检查')
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
