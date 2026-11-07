#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
extract_docx.py — 剧本正文提取器（.docx / .doc / .txt / .md → .txt）

为什么需要它：短剧投稿稿的正文藏在 Word 里，直接喂给模型会带上一堆
样式噪声。本脚本只做一件事——把正文抽成干净纯文本，且不改动原文件。

用法：
    python extract_docx.py <输入文件> [输出文件]

    python extract_docx.py 剧本.docx            # 输出 剧本.txt
    python extract_docx.py 剧本.doc             # Word97 也支持
    python extract_docx.py 剧本.txt out.txt     # 复制为纯文本

实现要点（三个格式三条路，踩过的坑都封在注释里）：
  · .docx = zip，解 word/document.xml，把 <w:p>/<w:br> 转成换行再去标签。
  · .doc  = OLE2 复合文档。**不要走 CLX piece table**——真实投稿稿的
    fcClx 经常指向异常的表，解析必崩。改用「WordDocument 流按 UTF-16LE
    解码 + CJK 连续段扫描」，对排版畸形的稿子容错性最好。
  · 段落边界不可靠时，用「连续 ≥2 个汉字的片段」作为行，噪声行自动丢弃。

只读输入，绝不写回原文件。
"""

import html
import os
import re
import struct
import sys
import zipfile

# 允许出现在正文里的字符（**反向**字符类：不在表内的字符一律视为噪声）。
# 注意这个 ^ 不能少——少了就变成「保留噪声、抹掉正文」，提取结果全空。
KEEP_RE = re.compile(
    r"[^一-鿿　-〿＀-￯0-9A-Za-z"
    r"“”‘’《》【】"
    r"，。！？；：（）、—…·"
    r"\r\n\t ]"
)


def extract_docx(path):
    with zipfile.ZipFile(path) as z:
        xml = z.read("word/document.xml").decode("utf-8", errors="ignore")
    # 段落/换行/制表 → 换行符，其余标签直接抹掉
    xml = re.sub(r"<w:p[ >][^>]*>|<w:p>", "\n", xml)
    xml = re.sub(r"<w:br[^>]*/>|<w:tab[^>]*/>", "\n", xml)
    return html.unescape(re.sub(r"<[^>]+>", "", xml))


def _cjk_runs(stream):
    """把 WordDocument 流按两种字节偏移解码，取 CJK 含量更高的一版。"""
    best = ([], 0)
    for shift in (0, 1):
        s = stream[shift:].decode("utf-16-le", errors="ignore")
        masked = KEEP_RE.sub("\x01", s)
        runs = []
        for r in re.split(r"[\x01\r\n]+", masked):
            r = r.strip()
            # 少于 2 个汉字的片段几乎都是二进制噪声或页眉页码残留
            if len(re.findall(r"[一-鿿]", r)) >= 2:
                runs.append(r)
        total = sum(len(r) for r in runs)
        if total > best[1]:
            best = (runs, total)
    return best[0]


def read_ole_stream(path, want="WordDocument"):
    """从 OLE2 复合文档（.doc）中取出指定流。

    自己实现而非依赖外部库：本机常常没有 catdoc / antiword / LibreOffice。
    只取正文所需的流，因此**不做 CLX piece table 解析**——真实投稿稿的
    fcClx 经常指向异常表位，解析必崩。改为定位到 WordDocument 流后，
    用「UTF-16LE 解码 + CJK 连续段扫描」提正文，对排版畸形的稿子容错最好。
    """
    d = open(path, "rb").read()
    if d[:8] != b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1":
        raise ValueError("不是 OLE2 复合文档（.doc）")
    ssz = 1 << struct.unpack_from("<H", d, 0x1E)[0]
    mssz = 1 << struct.unpack_from("<H", d, 0x20)[0]
    nfats = struct.unpack_from("<I", d, 0x2C)[0]
    dir_first = struct.unpack_from("<I", d, 0x30)[0]
    mini_cutoff = struct.unpack_from("<I", d, 0x38)[0]
    minifat_first = struct.unpack_from("<I", d, 0x3C)[0]
    nminifat = struct.unpack_from("<I", d, 0x40)[0]

    fat = []
    for i in range(nfats):
        fs = struct.unpack_from("<I", d, 0x4C + i * 4)[0]
        if fs == 0xFFFFFFFF:
            continue
        fat.append(fs)

    fat_table = []
    for fs in fat:
        fat_table += list(struct.unpack_from("<%dI" % (ssz // 4), d, 512 + fs * ssz))

    def read_chain(start):
        out, s, seen = b"", start, set()
        while s not in (0xFFFFFFFE, 0xFFFFFFFF) and s not in seen:
            seen.add(s)
            out += d[512 + s * ssz: 512 + (s + 1) * ssz]
            s = fat_table[s]
        return out

    dirdata = read_chain(dir_first)
    entries = []
    for i in range(len(dirdata) // 128):
        e = dirdata[i * 128:(i + 1) * 128]
        namelen = struct.unpack_from("<H", e, 0x40)[0]
        name = e[:max(0, namelen - 2)].decode("utf-16-le", errors="ignore")
        entries.append((name, e[0x42], struct.unpack_from("<I", e, 0x74)[0],
                        struct.unpack_from("<I", e, 0x78)[0]))

    streams = {}
    root = [e for e in entries if e[1] == 5]
    ministream = read_chain(root[0][2])[:root[0][3]] if root else b""
    minifat = []
    if minifat_first not in (0xFFFFFFFE, 0xFFFFFFFF):
        mdata = read_chain(minifat_first)
        minifat = list(struct.unpack_from("<%dI" % (len(mdata) // 4), mdata, 0))
    for name, etype, first, size in entries:
        if etype != 2 or (want and name != want):
            continue
        if size >= mini_cutoff:
            streams[name] = read_chain(first)[:size]
        else:
            buf, s = b"", first
            while s not in (0xFFFFFFFE, 0xFFFFFFFF):
                buf += ministream[s * mssz:(s + 1) * mssz]
                s = minifat[s] if s < len(minifat) else 0xFFFFFFFE
            streams[name] = buf[:size]
    return streams.get(want, b"")


def extract_doc(path):
    return "\n".join(_cjk_runs(read_ole_stream(path, "WordDocument")))


def extract_plain(path):
    for enc in ("utf-8", "utf-8-sig", "gb18030", "utf-16"):
        try:
            return open(path, encoding=enc).read()
        except (UnicodeDecodeError, UnicodeError):
            continue
    return open(path, encoding="utf-8", errors="ignore").read()


def extract(path):
    ext = os.path.splitext(path)[1].lower()
    if ext == ".docx":
        return extract_docx(path)
    if ext == ".doc":
        return extract_doc(path)
    return extract_plain(path)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    src = sys.argv[1]
    dst = sys.argv[2] if len(sys.argv) > 2 else os.path.splitext(src)[0] + ".txt"
    if not os.path.isfile(src):
        print("[FAIL] 文件不存在: %s" % src)
        sys.exit(1)
    try:
        text = extract(src)
    except Exception as e:  # noqa: BLE001 —— 解析失败要报原文，不能静默返回空
        print("[FAIL] 解析失败 %s: %s" % (src, e))
        sys.exit(1)
    lines = [l.strip() for l in text.splitlines()]
    body = "\n".join(l for l in lines if l)
    with open(dst, "w", encoding="utf-8") as f:
        f.write(body)
    print("[OK] %s -> %s  字符=%d  行=%d" % (src, dst, len(body), body.count("\n") + 1))
    if len(body) < 500:
        print("[WARN] 抽取正文过短（<500 字符），大概率解析失败，请改用 txt/md 或人工核对")


if __name__ == "__main__":
    main()
