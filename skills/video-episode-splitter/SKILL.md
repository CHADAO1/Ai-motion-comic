---
name: video-episode-splitter
description: "视频分集/整片切集/分集切片/一部整片切成多集/切视频出集/字幕烧录版/无字幕版/独立字幕/分集字幕归零/字幕从0起算/字幕错位/字幕不显示/第2集起字幕偏移/SRT归零重算/整条时间线SRT套分集画面/一集一文件/episode split/split video by episode。整片按分集表切成多集，每集同时产出「字幕烧录版」与「无字幕版+独立字幕」：切点精确到帧，字幕按入点减去、每集从 00:00:00 重算，与画面天然对齐。专治「整条时间线 SRT 套到分集画面上第 2 集起字幕整体偏移/不显示」。"
when_to_use: 当用户要把一部整片（电影、长视频、合稿成片）按分集入出点表切成多集，或需要同时间产出「字幕烧录进画面的成片」与「干净画面 + 该集独立字幕」两套时使用；也用于用户反馈「字幕明明有却拖进去不显示 / 第2集开始字幕整体往后偏 / SRT 时间轴对不上分集画面」这类症状。典型输入：一个整片视频 + 一份 HH:MM:SS:FF 的分集入出点表（xlsx/csv）+ 一条整时间线的 SRT。
---

# 视频分集 — 整片按分集表切成多集（烧录版 + 无字幕版）

把一部整片按分集表切成多集，每集同时产出「字幕烧录版」与「无字幕版 + 该集独立字幕」。切点精确到帧；字幕按入点归零重算，与画面天然对齐。

**本文件只做调度与用法说明**，算法在 `scripts/`，完整图文说明在 `assets/使用说明.md`。

## 0. 铁律

1. **先拆字幕、再切视频。** 顺序不可颠倒 —— `split_video.py` 要读 `split_srt.py` 产出的字幕目录。
2. **SRT 必须是「整条时间线」那一份。** 不要用剪辑软件逐集导出的 SRT（每集带绝对时间码，套到分集画面上会整体偏移）——这是本技能存在的唯一理由。
3. **帧率必须填对。** `episodes.xlsx` 的 `G1` 格 ＝ 序列真实帧率（24/25/30…）。填错只会让切点差 ≤1 帧（肉眼不可见），但口径要对。
4. **烧录字幕必须重编码。** 成品约占源片 1~2 倍大小，先确认磁盘余量。
5. **字幕样式用像素级参数**（`--sub-size` / `--sub-margin-v`），不要依赖 ffmpeg 默认值。1080p 实测标定：字号 `52` ≈ 可见字高 43px、距底 `44`px。

## 1. 环境预检（每次先跑）

```bash
# ffmpeg（脚本会自动定位，这里只是确认可用）
"$FFMPEG" -version | head -1

# openpyxl（读 .xlsx 用；只用 CSV 可跳过）
python -c "import openpyxl; print('openpyxl', openpyxl.__version__)"
```

| 项 | 状态 |
|---|---|
| ffmpeg | 由 `$FFMPEG` 环境变量或 PATH 定位（本机未预装，需自备 ffmpeg / ffprobe） |
| openpyxl | 见下方安装 |

**ffmpeg 定位顺序（脚本内置，无需配置）**：`$FFMPEG` → PATH → `<技能目录>/../ffmpeg/bin/` → 各盘符 `X:\ffmpeg\bin\`。
**换机器部署**：把 `ffmpeg.exe` + `ffprobe.exe` 放进 PATH，或用 `$FFMPEG` 指向 ffmpeg 可执行文件即可。

**openpyxl 隔离安装**（勿污染全局环境）：

```bash
python -m pip install openpyxl
```

> 也可全程只用 CSV 分集表（`requirements.txt` 的依赖就不需要），但 CSV 运行时必须显式加 `--fps`。

## 2. 三步出片

### 第 1 步 · 在剪辑软件里导出

- 整片**整段导出一次**；导出设置里「字幕 Captions → Burn-in」选 **无**（保证画面干净）。
- 同时导出**整条时间线**的 SRT，命名 `master.srt`。

### 第 2 步 · 填分集表

- 打开 `assets/episodes.xlsx`（建议复制到工作目录再填）。
- 只填两列：`B` = `start`、`C` = `end`，格式 `时:分:秒:帧`，如 `00:22:30:00`。
- `D` 列 `duration(自动)` 实时算时长，用于核对。
- **`G1` 格填序列帧率**。
- 要空白模板：`python scripts/make_template.py --rows 40 --out episodes.xlsx`

### 第 3 步 · 跑两条命令

```bat
python scripts\split_srt.py   --srt master.srt --csv episodes.xlsx --out srt_out
python scripts\split_video.py --video "整片.mp4" --table episodes.xlsx --srt-dir srt_out
```

产出：

| 目录 | 内容 |
|---|---|
| `burned/` | 字幕烧录进画面：`01.mp4 02.mp4 …` |
| `clean_srt/` | 无字幕画面 + 每集独立字幕：`01.mp4` + `01.mp4.srt …` |

> 先试一集看效果：第二条命令加 `--episodes 1`；只打印计划不执行：加 `--dry-run`。

## 3. 参数速查

**split_srt.py（拆字幕）**

| 参数 | 说明 |
|---|---|
| `--srt` | 主字幕 `master.srt` |
| `--csv` | 分集表（`.xlsx` 或 `.csv`） |
| `--out` | 输出目录（默认 `srt_out`） |
| `--fps` | 帧率；不填则读 xlsx 的 `G1`，再不然按 25 |

**split_video.py（切视频）**

| 参数 | 说明 |
|---|---|
| `--video` `--table` `--srt-dir` | **必填**：整片 / 分集表 / 上一步的字幕目录 |
| `--episodes 1-3` | 只处理指定集（也可 `1,5,9`） |
| `--name-format` | 输出命名模板，`{ep}` 占位。默认 `{ep:02d}.mp4`；如 `"女巫与狼王ep{ep:03d}.mp4"`（独立字幕版自动追加同名 `.srt`） |
| `--ref "某集.mp4"` | 参考已有的一集导出，自动抄它的分辨率 / 码率 |
| `--width` `--height` | 直接指定输出分辨率（不填 ＝ 源分辨率） |
| `--encoder h264_nvenc` | 编码器；默认自动探测 N 卡硬件加速，没有则 CPU（libx264） |
| `--cq 16` | 质量（越小越清晰、越大越省空间） |
| `--sub-font Arial --sub-size 52 --sub-margin-v 44 --sub-outline 2` | 像素级字幕样式 |
| `--out-burned` `--out-clean` | 自定义输出目录名 |
| `--dry-run` | 只打印计划，不动文件 |

## 4. 常见坑

1. **第 2 集起字幕不显示 / 整体偏移** → 用了逐集导出的 SRT。必须换**整条时间线**那份重跑第 1 步。
2. **`G1` 帧率别盲信模板默认值** → 表里 `G1` 常是模板出厂默认（如 25）而没改。**用历史单集时长反查**验证：
   把某集实际时长与表里 `end-start` 在 24/25/30 三种 fps 下比对，命中哪一个一目了然。
   口径错了切点会偏（约 `帧号 × (1/fps1 − 1/fps2)` 秒），集数多时会累加。用 `--fps NN` 显式覆盖。
   **源片帧率 ≠ 序列帧率**：成片可能 30fps 导出、时间码却是 24fps 序列语义；切点按秒落刀，两者互不影响。
3. **某集被静默跳过** → 检查分集表该行时间码是不是**全角冒号** `：`（中文输入法易犯）。脚本已做归一化，但旧版本会漏集。
4. **找不到 ffmpeg** → 按 §1 的定位顺序放对位置，或设环境变量 `FFMPEG`。
5. **速度** → 有 NVIDIA 卡自动走 NVENC（实测约 1~2 分钟/集 × 2 份）；没有则回落 CPU，明显更慢。
6. **源片自带硬字幕 / 人名条** → 那是画面像素，两个版本都会带着，字幕后处理去不掉。
7. **跨集字幕** → 横跨切割点的字幕**自动裁断**，不会丢字；集内留白原样保留。
8. **路径** → 脚本会把 ffmpeg 的 `cwd` 切到纯 ASCII 临时目录（绕开字幕滤镜对中文路径的限制），
   `split_video.py` 已内部把全部参数 `abspath()` 绝对化，**传相对路径也可正常工作**。
   （导入时修过此处；原版传相对路径会必然报 `No such file or directory`，详见 CHANGELOG.md。）

## 5. File Map

```
video-episode-splitter/
├─ SKILL.md                  本文件（调度 + 用法）
├─ CHANGELOG.md              变更记录（导入时对 split_video.py 的路径修复）
├─ requirements.txt          openpyxl>=3.0
├─ assets/
│  ├─ episodes.xlsx          空白分集表模板（40 集，含时长公式）
│  └─ 使用说明.md             完整图文说明（面向人工操作）
└─ scripts/
   ├─ make_template.py       生成空白分集表
   ├─ split_srt.py           拆字幕（每集从 0 起算，跨边界自动裁断）
   └─ split_video.py         切视频（烧录版 + 无字幕版 + 独立字幕）
```
