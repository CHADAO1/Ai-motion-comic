#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_template.py — 生成分集表模板 episodes.xlsx（带时长自动计算）

用法：
  python make_template.py                      # 生成 40 集模板 episodes.xlsx
  python make_template.py --rows 34 --out 满月囚笼_分集表.xlsx

表结构：
  A=episode  B=start  C=end  D=duration(自动)
  G1 = 帧率 fps（split_srt.py 会读这里）
  你只需要填 B/C 两列（Premiere 时间码 HH:MM:SS:FF），D 列自动出时长。
"""

import argparse
import os

import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.workbook.properties import CalcProperties


HEADERS = ['episode', 'start', 'end', 'duration(自动)']
DUR_FORMULA = (
    '=IF(OR(B{r}="",C{r}=""),"",IFERROR(TEXT(('
    '(LEFT(C{r},2)*3600+MID(C{r},4,2)*60+MID(C{r},7,2)+MID(C{r},10,2)/$G$1)'
    '-(LEFT(B{r},2)*3600+MID(B{r},4,2)*60+MID(B{r},7,2)+MID(B{r},10,2)/$G$1)'
    ')/86400,"hh:mm:ss"),"—"))'
)


def build(path, rows=40, fps=25):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = '分集表'

    head_fill = PatternFill('solid', fgColor='2F3B52')
    head_font = Font(color='FFFFFF', bold=True, size=11)
    thin = Side(style='thin', color='C9CDD4')
    border = Border(left=thin, right=thin, top=thin, bottom=thin)

    for i, h in enumerate(HEADERS, start=1):
        c = ws.cell(1, i, h)
        c.fill = head_fill
        c.font = head_font
        c.alignment = Alignment(horizontal='center', vertical='center')
        c.border = border

    # 帧率格子（split_srt.py / split_video.py 读 G1）
    ws['F1'] = '帧率fps →'
    ws['F1'].font = Font(color='1D2129', size=10)
    ws['F1'].alignment = Alignment(horizontal='right', vertical='center')
    ws['G1'] = fps
    ws['G1'].font = Font(bold=True, color='D4380D', size=11)
    ws['G1'].alignment = Alignment(horizontal='center', vertical='center')
    ws['G1'].fill = PatternFill('solid', fgColor='FFF1E6')
    ws['G1'].border = border

    ws['I1'] = 'B/C 列填 PR 时间码 HH:MM:SS:FF（时:分:秒:帧）；D 列自动算时长'
    ws['I1'].font = Font(color='86909C', size=9, italic=True)
    ws['I1'].alignment = Alignment(horizontal='left', vertical='center')

    for n in range(1, rows + 1):
        r = n + 1
        ws.cell(r, 1, n).alignment = Alignment(horizontal='center')
        b = ws.cell(r, 2)
        c = ws.cell(r, 3)
        b.number_format = '@'          # 文本格式，防 Excel 吞掉四段冒号
        c.number_format = '@'
        b.alignment = Alignment(horizontal='center')
        c.alignment = Alignment(horizontal='center')
        d = ws.cell(r, 4, DUR_FORMULA.format(r=r))
        d.alignment = Alignment(horizontal='center')
        d.font = Font(color='0E7A0D')
        for col in range(1, 5):
            ws.cell(r, col).border = border

    # 表头行外，数据区加浅色斑马纹，方便看行
    for r in range(2, rows + 2):
        if r % 2 == 0:
            for col in range(1, 5):
                ws.cell(r, col).fill = PatternFill('solid', fgColor='F7F8FA')

    ws.column_dimensions['A'].width = 9
    ws.column_dimensions['B'].width = 15
    ws.column_dimensions['C'].width = 15
    ws.column_dimensions['D'].width = 15
    ws.column_dimensions['E'].width = 2
    ws.column_dimensions['F'].width = 11
    ws.column_dimensions['G'].width = 8
    ws.column_dimensions['H'].width = 2
    ws.column_dimensions['I'].width = 62

    ws.freeze_panes = 'A2'
    wb.calculation = CalcProperties(fullCalcOnLoad=True)
    wb.save(path)
    return path


def main():
    ap = argparse.ArgumentParser(description='生成分集表模板 episodes.xlsx')
    ap.add_argument('--rows', type=int, default=40, help='集数（默认 40）')
    ap.add_argument('--fps', type=float, default=25, help='帧率（默认 25）')
    ap.add_argument('--out', default='episodes.xlsx', help='输出文件名')
    args = ap.parse_args()
    p = build(args.out, args.rows, args.fps)
    print('已生成 %s（%d 集，帧率 %s）' % (os.path.abspath(p), args.rows, args.fps))
    print('请打开它，在 B/C 两列填入每集入/出点（HH:MM:SS:FF），并确认 G1 帧率。')


if __name__ == '__main__':
    main()
