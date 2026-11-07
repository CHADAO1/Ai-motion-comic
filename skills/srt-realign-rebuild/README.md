# srt-realign-rebuild

字幕对齐重建工具：把 B 语言字幕整轨挂到 A 语言字幕（基准轨）的时间轴上，做到一条对一条、时间轴逐字节一致。

## 何时用

- 用户说「中文字幕要和英文字幕意思对上，时间轴也要完全一致」
- 两轨字幕条数/时间点对不上，需要统一
- 已有译文，需要换到另一条时间轴上
- 用户说「字幕里不能出现标点符号」「标点的要断成两条」→ 走 MODE 3 去标点拆条

## 快速用法

```bash
# 1) 先判定两轨是否只是平移关系
python scripts/rebuild_srt.py check --base en.srt --target 现有中文.srt

# 2) 准备译文映射 zh_map.json：{"1": "第一条译文", "2": "第二条译文", ...}
#    键 = 基准轨的 1-based 条号；缺键/多键脚本会直接报错终止

# 3) 合轨
python scripts/rebuild_srt.py build --base en.srt --map zh_map.json --out 交付.srt \
    --newline crlf --bom none

# 4) 锚点抽查（防整块错位）
python scripts/rebuild_srt.py anchor --base en.srt --target 交付.srt --lines 1,151,300,1760

# 5) MODE 3：去标点拆条（前提：两轨已逐条对齐）
python scripts/strip_punct_split.py --base en.srt --target 交付.srt \
    --out 交付_无标点.srt --newline crlf --bom none
```

## 四条硬规则

1. 基准轨几条，交付就几条；基准轨时间轴是什么，交付就是什么。
2. 译文用 `{条号: 译文}` 显式字典承载，**不要**用文件排序/分块顺序隐式表达行号。
3. 交付前必须给出数值证据：条数相等、时间轴不一致 = 0、序号连续、起始时间单调递增。
4. 去标点拆条会**改变条数**，与规则 1 冲突 —— 动手前必须先跟用户确认时间口径（默认推荐「拆条但父窗口边界零漂移」）。

## 依赖

纯标准库（Python 3.8+），无需安装。
