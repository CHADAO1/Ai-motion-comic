# -*- coding: utf-8 -*-
"""资产图库 → 全量缩略拼图（contact sheet）

用途：资产回填核对时，把整个成品图目录（可能几十上百张 2~5MB 原图）
缩成若干张「4 列 x 4 行」拼图，一次读入即可看清**全部**图的服装款式、
颜色与年龄，context 消耗约为逐张开原图的 1/10。

用法：
    python make_contact_sheet.py <图目录> <输出目录> [--cols 4] [--rows 4]
                                [--cell 300x420] [--quality 88]

随后直接 Read 输出的 sheet*.jpg 即可；有疑问的图再单独放大复核。
"""
import os
import sys
import argparse

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    sys.exit("需要 Pillow：pip install pillow")

FONT_CANDIDATES = [
    r"C:\Windows\Fonts\msyh.ttc",      # 微软雅黑（中文首选）
    r"C:\Windows\Fonts\simhei.ttf",
    r"C:\Windows\Fonts\simsun.ttc",
    "/System/Library/Fonts/PingFang.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
]
EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


def pick_font(size):
    """路径含中文时必须显式指定字体，否则中文全变方块。"""
    for p in FONT_CANDIDATES:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("out")
    ap.add_argument("--cols", type=int, default=4)
    ap.add_argument("--rows", type=int, default=4)
    ap.add_argument("--cell", default="300x420")
    ap.add_argument("--quality", type=int, default=88)
    a = ap.parse_args()

    cw, ch = (int(x) for x in a.cell.lower().split("x"))
    lh = 46  # 标签区高度

    files = sorted(f for f in os.listdir(a.src)
                   if os.path.splitext(f)[1].lower() in EXTS)
    if not files:
        sys.exit("目录里没有图片：%s" % a.src)
    os.makedirs(a.out, exist_ok=True)

    fname = pick_font(18)
    ftitle = pick_font(26)
    per = a.cols * a.rows
    pages = [files[i:i + per] for i in range(0, len(files), per)]

    for gi, grp in enumerate(pages, 1):
        W, H = a.cols * cw, a.rows * (ch + lh) + 60
        sheet = Image.new("RGB", (W, H), (245, 245, 247))
        d = ImageDraw.Draw(sheet)
        d.text((14, 16), "%s  (%d 张 / 共 %d 张)  第 %d/%d 页"
               % (os.path.basename(a.src.rstrip("\\/")), len(files), len(files), gi, len(pages)),
               font=ftitle, fill=(20, 20, 20))
        for k, fn in enumerate(grp):
            r, c = divmod(k, a.cols)
            x, y = c * cw, 60 + r * (ch + lh)
            try:
                im = Image.open(os.path.join(a.src, fn)).convert("RGB")
                im.thumbnail((cw - 12, ch - 12), Image.LANCZOS)
                sheet.paste(im, (x + (cw - im.width) // 2, y + (ch - im.height) // 2))
            except Exception as e:
                d.text((x + 10, y + 10), "ERR " + str(e)[:30], font=fname, fill=(200, 0, 0))
            d.rectangle([x, y, x + cw - 1, y + ch + lh - 1], outline=(200, 200, 205))
            d.text((x + 8, y + ch + 6), fn[:34], font=fname, fill=(30, 30, 30))
            d.text((x + 8, y + ch + 24), "#%d" % (k + 1), font=fname, fill=(150, 150, 150))
        p = os.path.join(a.out, "sheet%d.jpg" % gi)
        sheet.save(p, quality=a.quality)
        print(p, sheet.size)
    print("共 %d 页 / %d 张图" % (len(pages), len(files)))


if __name__ == "__main__":
    main()
