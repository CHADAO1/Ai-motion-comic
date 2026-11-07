---
name: html-report-layout
description: 数据密集型 HTML 报表（服装表、资产总表、核对表、审核报告）的排版规范与渲染自检。把"不好看"的长表格改成可读、可控、可交付的版面，并用 headless Chrome 截图验证真实渲染效果。
when_to_use: 用户说「排版不好看」「表格太挤」「重新排一下」「这表格没法看」；或你要生成/修改任何行数 >20、列数 ≥5 的 HTML 长表格交付物（服装表、资产总表、场次对照表、核对表、审核报告、缺口清单）时，主动加载。
agent_created: true
---

# HTML 长表格 · 排版规范与自检

## 核心判断：排版不好看，九成是这三个问题

在动手改样式之前，先按这个顺序排查。改样式救不了结构性问题。

| 优先级 | 症状 | 真因 |
|---|---|---|
| 1 | 表格横向溢出容器、出现滚动条 | `white-space:nowrap` 撞上了长内容（最典型：`场次串 1-1｜1-2｜1-3｜…`） |
| 2 | 某列挤成一条、另一列空一半 | `table-layout:auto` 下浏览器按内容分配，nowrap 列吃掉宽度 |
| 3 | 数字前后矛盾 | 改了总数忘了改分项（"56 条"改了，"连续 33｜单独 12"没改） |

**先修这三条，再谈视觉。** 反过来做，等于给歪墙上刷漆。

---

## 一、CSS 基线（浅色主题，可直接复用）

```css
:root{
  --bg:#f5f6f8; --card:#ffffff;
  --ink:#17171c; --ink2:#4b4b55; --ink3:#86868f;
  --line:#e7e7ec; --line2:#d9d9e0;
  --mono:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;
  font-size:14px;line-height:1.7;-webkit-font-smoothing:antialiased;font-variant-numeric:tabular-nums}
.wrap{max-width:1180px;margin:0 auto;padding:36px 22px 88px}

/* 表格：吸顶表头 + 斑马纹 + 圆角 */
.tb{width:100%;border-collapse:separate;border-spacing:0;background:var(--card);
  border:1px solid var(--line);border-radius:13px;overflow:hidden;font-size:13px}
.tb thead th{position:sticky;top:0;z-index:3;background:#fafafb;text-align:left;font-weight:600;
  color:var(--ink2);padding:10px 11px;border-bottom:1px solid var(--line2);white-space:nowrap;font-size:12.5px}
.tb td{padding:9px 11px;border-bottom:1px solid #f1f1f4;vertical-align:top;word-break:break-word;line-height:1.7}
.tb tbody tr:nth-child(even){background:#fcfcfd}
.tb tbody tr:hover{background:#f6f9fd}
.tb tbody tr:last-child td{border-bottom:none}
.tb .mono{font-family:var(--mono);font-size:12px;color:var(--ink2)}   /* 注意：不含 nowrap */
.tb .c{text-align:center;white-space:nowrap}
.tb tbody td:first-child{font-weight:600;color:var(--ink);white-space:nowrap}

/* 分组行 */
.seg td{background:#f3f6fa !important;font-size:12.5px;font-weight:600;color:var(--ink2);
  padding:9px 13px !important;border-bottom:1px solid var(--line2) !important;position:relative}
.seg td:before{content:"";position:absolute;left:0;top:0;bottom:0;width:3px;background:#c3d0e6}

/* 场次 chip —— 根治长串溢出 */
.epc{line-height:1.85}
.ep{display:inline-block;font-family:var(--mono);font-size:11px;line-height:1.55;color:#3f4b5b;
  background:#f1f4f8;border:1px solid #e3e8ef;border-radius:5px;padding:0 5px;
  margin:0 4px 4px 0;white-space:nowrap}

/* 锁列宽 */
.tb-ch,.tb-sup,.tb-eps{table-layout:fixed}
```

**关键**：`.mono` 只负责字体，`white-space:nowrap` 单独给 `.c` 和 `thead th`。这两件事混在一起是溢出的头号来源。

---

## 二、长串 chip 化（最高收益的一步）

「覆盖集-场」这类列，内容形如 `26-1｜26-2｜31-2｜…｜44-1`（16 个场次）。原样是灾难，chip 化后自动换行排列，列宽立刻收敛。

```python
import re
EP = re.compile(r'<td class="mono">((?:\d+-\d+[a-z]?(?:b)?(?:\s*(?:前段|后段))?(?:｜))+'
                r'\d+-\d+[a-z]?(?:b)?(?:\s*(?:前段|后段))?)</td>')
def chip(m):
    parts = [p.strip() for p in m.group(1).split('｜') if p.strip()]
    return '<td class="epc">' + ''.join(f'<span class="ep">{p}</span>' for p in parts) + '</td>'
t, n = EP.subn(chip, t)
```

⚠️ 正则必须**至少匹配一个 `｜`**（即 2 个及以上场次），否则单值单元格也会被 chip 化，视觉噪音反而变大。

---

## 三、锁列宽：`colgroup` + `table-layout:fixed`

auto 布局永远调不准。给每个长表格配 `colgroup`，宽列给 `auto` 吃剩余，窄列写死。

```python
CG = ('<table class="tb tb-ch">\n'
      '<colgroup><col style="width:76px"><col style="width:140px"><col style="width:88px">'
      '<col style="width:198px"><col style="width:104px"><col><col style="width:132px"></colgroup>\n<thead>')
t = t.replace('<table class="tb">\n<thead><tr><th>编号</th><th>服装</th>', CG + '<tr><th>编号</th><th>服装</th>')
```

经验值（1180px 容器 / 7 列表）：
- 编号 76 ｜ 名称 140 ｜ badge 列 88 ｜ chip 列 198 ｜ 次要 monospace 列 104 ｜ 主文本 `auto` ｜ 资产名 132
- 逐集表（5 列）：集-场 76 ｜ 场景 108 ｜ 剧情 `auto` ｜ 绑定 chips 268 ｜ 标记 80

**窄列一定要验字宽**：`≠ 换装点`（约 62px）塞进 56px 列会挤字 → 给 80px。中文 1 字 ≈ 13px，别按字符数估。
**等宽字体字宽**：mono 11px ≈ 6.6px/字符，mono 10px ≈ 6px/字符。用这个算「列里能放几个 chip」。

### 3.1 chip 列宽必须 ≥ 2 个 chip 的宽度（易踩）

chip 列被压到只能放 1 个 chip 时，内容会**竖排**，行高翻倍，比溢出更难看。实测 `LOC-05-D`（8 字符）：
- 11px mono：53px + padding 10 + margin 4 = **67px/个** → 两列需 ≥150px
- 10px mono：48px + 10 + 4 = **62px/个** → 两列需 ≥144px

给 LOC 这类长编号 chip 单独降一档字号（`.ep.loc{font-size:10px}`）比加宽列更划算。列宽公式：
`列宽 = 单元格padding(20) + N × chip宽 + (N-1) × margin`，N 取 2 为底线。

---

## 四、一致性检查（改完必跑）

### 4.0 根治「数字矛盾」：数据驱动生成

统计卡与表格数对不上，根因是**手工同步两处**。正确做法：用一份 Python 数据结构（list of dict / JSON）作**唯一数据源**，MD 与 HTML 都由它渲染。

```python
CNT = {}
for p in PROPS: CNT[p['k']] = CNT.get(p['k'], 0) + 1
TOTAL = len(PROPS)
assert TOTAL == CNT['连续'] + CNT['单独'] + CNT['特殊']   # 结构上不可能对不上
```

再按分组、逐集表、链路、缺口等列表各自迭代渲染。改数据即改表，统计卡自动跟着走。
顺带用 `assert` 卡住不变量（条目数=分项和、分组行数合计=总数），比事后核对可靠。

### 4.1 检查脚本

```python
# 1) 实际条目数
ids = re.findall(r'<tr><td class="mono">([A-Z]{3}-\d+)</td>', t)
# 2) 分项统计（只在总表区域统计，避免把缺口表算进去）
seg = t[t.find('二</span>服装总表'):t.find('三</span>逐集')]
from collections import Counter
c = Counter(re.findall(r'<span class="bd bd-(cont|solo|spec)">([^<]+)</span>', seg))
# 3) 统计卡里的数字必须等于 1) 和 2)
```

同时扫残留：
```python
re.findall(r'<td class="mono">[^<]*｜[^<]*</td>', t)   # 应为 0，否则 chip 化没做干净
```

---

## 五、渲染自检：headless Chrome 截图

**不要凭代码想象效果。** 排版必须眼见为实。

### 环境前提（本工作区）
- Bash 工具缺 coreutils（`ls`/`mkdir`/`head`/`tail`/`grep` 全废）→ **一律用 PowerShell 或内联 python（绝对路径）**
- 浏览器路径：`C:\Program Files\Google\Chrome\Application\chrome.exe`（Windows 也可查注册表 `HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe`）

### 首屏截图
```powershell
$chrome='C:\Program Files\Google\Chrome\Application\chrome.exe'
& $chrome --headless --disable-gpu --no-sandbox --hide-scrollbars --force-device-scale-factor=1 `
  --window-size=1440,2600 "--screenshot=$dst\top.png" "file:///C:/path/to/report.html"
```
⚠️ **参数用 `--headless`，不要写 `--headless=new`**——本机 Chrome 版本不认 `new`，会静默退化成"正在现有的浏览器会话中打开"，**PNG 一张都不生成、退出码仍是 0**（2026-09-23 实测踩坑）。判据：`$LASTEXITCODE` 后面必须再断言 `Test-Path` 输出文件并打印字节数。
⚠️ 含中文的路径先复制到英文临时目录再截；`file:///` URL 里用正斜杠。
⚠️ Chrome 会把 `--screenshot=...` 的成功信息打到 **stderr**，PowerShell 会当成 `NativeCommandError` 报红——那是误报，看结尾的 `bytes written to file` 与 `Test-Path` 结果即可，别去改命令。

### 整页分段法（页面超过一屏时）
headless 只截 viewport，不支持滚动。**负 margin 法**：复制一份 HTML，在 `</head>` 前注入偏移，逐段截。

```powershell
$base=[System.IO.File]::ReadAllText($src,[System.Text.UTF8Encoding]::new($false))
foreach($off in 0,2500,5000,7500,10000){
  $h = $base -replace '</head>', "<style>.wrap{margin-top:-${off}px}</style></head>"
  [System.IO.File]::WriteAllText((Join-Path $dst "s$off.html"), $h, [System.Text.UTF8Encoding]::new($false))
  & $chrome --headless --disable-gpu --no-sandbox --hide-scrollbars --window-size=1440,2400 `
    "--screenshot=$dst\s$off.png" "file:///C:/path/_shot/s$off.html"
}
```
（sticky 表头会吸在视口顶部，无碍观察。）

分段建议按页面结构定：顶部（header/统计卡/导航）、每张长表各一段、尾部（box + 附录）。

### 完成后
- 同步交付盘：`[System.IO.File]::Copy($s,$d,$true)` → **必须回读大小校验**（UNC 会静默失败）
- 清理截图临时目录

---

## 六、顺手加的加分项（成本低、观感提升明显）

- **锚点导航**：`h2` 加 `id`，顶部插 `<nav>` 跳转 chip。8 个章节的长文档必备。
- **统计卡**用左侧 3px 色条代替整块底色，`font-variant-numeric:tabular-nums` 对齐数字。
- **序号码**：`<span class="n">一</span>` 做成黑底圆角方块（24×24），比裸中文数字有质感。
- **空值统一 `—`**，不要留空白单元格。

---

## 七、交付前最后一遍

```
□ 无 td 因 nowrap 溢出（chip 化残留扫描 = 0）
□ 每张长表都有 colgroup + fixed
□ 统计卡数字 = 实际条目数（含分项相加）
□ 窄列无挤字（中文按 13px/字估宽）
□ 截图验证过至少 3 段（顶部 / 中间长表 / 尾部）
□ 已同步到交付盘并回读校验大小一致
□ 临时文件已清理
```
