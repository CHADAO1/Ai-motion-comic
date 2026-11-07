#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
docx -> 纯文本（保留段落分隔），用于两版剧本对比前的全文提取。

用法：
    python extract_docx.py <输入.docx> [输出.txt]
    python extract_docx.py <a.docx> <b.docx> [--outdir DIR]   # 多文件，自动命名

说明：
  - 只读，不修改源文件。
  - 走 word/document.xml 直接解析；这是 tencent-local-office-edit 的
    doc_resolve_document_structure（text_preview 上限 200 字节）取不到长段时的兜底路径。
  - 段落分隔 <w:p>，制表 <w:tab/> -> \\t，软换行 <w:br/> -> \\n。
"""
import sys, os, re, zipfile


def docx_text(path):
    with zipfile.ZipFile(path) as z:
        xml = z.read('word/document.xml').decode('utf-8', 'replace')
    paras = re.findall(r'<w:p\b.*?</w:p>|<w:p\b[^>]*/>', xml, re.S)
    out = []
    for p in paras:
        p = p.replace('<w:tab/>', '\t').replace('<w:br/>', '\n')
        runs = re.findall(r'<w:t(?:\s[^>]*)?>(.*?)</w:t>', p, re.S)
        txt = ''.join(runs)
        for a, b in (('&amp;', '&'), ('&lt;', '<'), ('&gt;', '>'),
                     ('&quot;', '"'), ('&apos;', "'")):
            txt = txt.replace(a, b)
        out.append(txt.strip())
    return out


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    outdir = '.'
    if '--outdir' in sys.argv:
        outdir = sys.argv[sys.argv.index('--outdir') + 1]
        args = [a for a in args if a != outdir]
    if not args:
        print(__doc__)
        return 1

    files = [a for a in args if a.lower().endswith(('.docx', '.docm', '.dotx'))]
    explicit_out = args[-1] if (len(args) == 2 and not args[-1].lower().endswith(('.docx', '.docm', '.dotx'))) else None

    os.makedirs(outdir, exist_ok=True)
    for i, f in enumerate(files):
        if not os.path.exists(f):
            print('MISSING  %s' % f)
            continue
        t = docx_text(f)
        if explicit_out and len(files) == 1:
            out = explicit_out
        else:
            stem = os.path.splitext(os.path.basename(f))[0]
            out = os.path.join(outdir, stem + '.txt')
        with open(out, 'w', encoding='utf-8') as fh:
            fh.write('\n'.join(t))
        ne = sum(1 for x in t if x)
        print('%-52s 段落%5d 非空%5d 总字%7d 最长%4d -> %s'
              % (os.path.basename(f)[:50], len(t), ne,
                 sum(len(x) for x in t), max(len(x) for x in t), out))
    return 0


if __name__ == '__main__':
    sys.exit(main())
