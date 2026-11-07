#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
两版剧本按集对齐 + 差异定位。

用法：
    python align_versions.py <旧版.txt> <新版.txt>
    python align_versions.py <旧版.txt> <新版.txt> --detail      # 逐集差异块明细
    python align_versions.py <旧版.txt> <新版.txt> --tab ADJ     # 指定偏移（默认自动探测 0..3）

核心：绝不做段落级整体 diff（删集会全局错位，产生上千条假差异）。
流程：按「集标记」切分 -> 逐集相似度求最优偏移 -> 只在改动区做逐行 diff。

集标记兼容：第X集 / 第X集（中文数字、阿拉伯数字、前导零、前后空白）
场次标记兼容：1-2 日 内 地点 / 2-3夜 内 地点（-、－、— 均可；日夜内外间可无空格）
"""
import sys, os, re, difflib

CN = {'零': 0, '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
      '六': 6, '七': 7, '八': 8, '九': 9, '十': 10}
EP = re.compile(r'^第\s*([一二三四五六七八九十百零\d]+)\s*集\s*$')
SC = re.compile(r'^(\d+)\s*[-－—]\s*(\d+)\s*')


def cn2int(s):
    if s.isdigit():
        return int(s)
    if s == '十':
        return 10
    if '十' in s:
        a, b = s.split('十')
        return CN.get(a, 1) * 10 + (CN.get(b, 0) if b else 0)
    return CN.get(s, 0)


def split_eps(lines):
    """-> [(集号, 起始行, 结束行, 行列表)]"""
    marks = [(i, cn2int(EP.match(s.strip()).group(1)))
             for i, s in enumerate(lines) if EP.match(s.strip())]
    out = []
    for j, (i, n) in enumerate(marks):
        e = marks[j + 1][0] if j + 1 < len(marks) else len(lines)
        out.append((n, i, e, lines[i:e]))
    return out


def sim(a, b):
    if not a or not b:
        return 0.0
    return difflib.SequenceMatcher(None, '\n'.join(a[3]), '\n'.join(b[3])).ratio()


def main():
    pos = [a for a in sys.argv[1:] if not a.startswith('--')]
    if len(pos) < 2:
        print(__doc__)
        return 1
    old = open(pos[0], encoding='utf-8').read().split('\n')
    new = open(pos[1], encoding='utf-8').read().split('\n')
    detail = '--detail' in sys.argv

    EO, EN = split_eps(old), split_eps(new)
    print('旧版：%d 集 / %d 段 / %d 字' % (len(EO), len(old), sum(len(x) for x in old)))
    print('新版：%d 集 / %d 段 / %d 字' % (len(EN), len(new), sum(len(x) for x in new)))
    print()

    # ── 自动探测最优偏移 ──
    if '--tab' in sys.argv:
        cands = [int(sys.argv[sys.argv.index('--tab') + 1])]
    else:
        # 必须含负值：新版比旧版「集数更多」时（如 47→49），
        # 结构是新第N集 ↔ 旧第N-d集，最优偏移为负。实测 47→49 的项目 d=-2，
        # 只扫 [0,3] 会把 47 集全部误判成「整集重写」。
        cands = list(range(-4, 4))
    best, best_score = 0, -1
    for d in cands:
        sc = [sim(next((x for x in EO if x[0] == n + d), None),
                  next((x for x in EN if x[0] == n), None))
              for n in range(1, len(EN) + 1)]
        m = sum(sc) / max(len(sc), 1)
        if m > best_score:
            best, best_score = d, m
    sgn = ('+%d' % best) if best >= 0 else ('%d' % best)
    print('★ 最优偏移：新版第 N 集 ↔ 旧版第 N%s 集（平均相似度 %.4f）' % (sgn, best_score))
    print()

    OD = {n: v for n, v in ((x[0], x) for x in EO)}
    print('%-6s %-10s %-9s %-9s %s' % ('新版', '对应旧版', '相似度', '差异块', '结论'))
    changed, identical = [], []
    for x in EN:
        n = x[0]
        o = OD.get(n + best)
        if not o:
            print('%-6d %-10s %-9s %-9s %s' % (n, '—', '—', '—', '旧版无对应'))
            changed.append((n, None))
            continue
        sm = sim(o, x)
        blocks = [op for op in difflib.SequenceMatcher(None, o[3], x[3]).get_opcodes()
                  if op[0] != 'equal']
        # 差异块只在「块内每一行都是集号/场号行」时才算编号变化；
        # 只要块里混进一行台词/动作，整块记为内容变化（否则会漏判改写）。
        tags = []
        for _, i1, i2, j1, j2 in blocks:
            body = [y for y in (o[3][i1:i2] + x[3][j1:j2]) if y.strip()]
            if body and all(EP.match(y.strip()) or SC.match(y.strip()) for y in body):
                tags.append('编号')
            else:
                tags.append('内容')
        if not tags:
            kind = '零差异'
        elif all(t == '编号' for t in tags):
            kind = '仅编号'
        else:
            kind = '内容+' if len(set(tags)) > 1 else '内容'
        # 内容零改动的判据只看「差异块是否全是编号行」，不设相似度阈值——
        # 集号/场号变化会把整集相似度压到 ~0.995，用 0.999 阈值会全部误判。
        if kind in ('仅编号', '零差异'):
            identical.append(n)
        else:
            changed.append((n, kind))
        print('%-6d %-10d %-9.4f %-9d %s'
              % (n, n + best, sm, len(blocks), kind))

    print()
    print('主体区（仅编号变化，内容零改动）：%d 集' % len(identical))
    if identical:
        print('   %s ... %s' % (identical[:5], identical[-3:]))
    print('改动区：%s' % [c[0] for c in changed if c[1]])
    print()

    if detail:
        print('=' * 76)
        print('改动区逐块明细')
        print('=' * 76)
        for n, _ in changed:
            if n is None:
                continue
            o = OD.get(n + best)
            x = next(y for y in EN if y[0] == n)
            if not o:
                print('\n--- 新版第%d集：旧版无对应（纯新增）---' % n)
                for y in x[3]:
                    print('  +[新] %s' % y[:110])
                continue
            if n in identical:
                continue
            print('\n--- 新第%d集 ↔ 旧第%d集（相似度 %.4f）---' % (n, n + best, sim(o, x)))
            for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, o[3], x[3]).get_opcodes():
                if tag == 'equal':
                    continue
                for y in o[3][i1:i2]:
                    print('  -[旧] %s' % y[:110])
                for y in x[3][j1:j2]:
                    print('  +[新] %s' % y[:110])
    return 0


if __name__ == '__main__':
    sys.exit(main())
