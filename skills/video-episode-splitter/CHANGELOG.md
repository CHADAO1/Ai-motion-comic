# CHANGELOG — video-episode-splitter

## 0.1.0 — 2026-10-09

**导入来源**：`E:\letsvpn\视频分集工具包\`（原目录完整保留，作为回滚基准）

### 导入时的改动（仅 1 处代码修复，其余原样）

- **修复 `scripts/split_video.py`：相对路径必然失败**
  - **症状**：按 `assets/使用说明.md` 的示例传相对路径（`--video "整片.mp4"`），
    ffmpeg 报 `Error opening input file 整片.mp4` / `Error opening output burned\01.mp4`。
  - **根因**：脚本为绕开 `subtitles` 滤镜对中文/冒号路径的限制，把 ffmpeg 的 `cwd`
    切到内部 ASCII 临时目录（`tempfile.mkdtemp(prefix='subsplit_')`）。因此所有传给
    ffmpeg 的**相对路径**都相对那个临时目录解析，必然找不到。
  - **修复**：在 `parse_args()` 之后，把 `--video / --table / --srt-dir / --out-burned /
    --out-clean / --ref` 全部 `os.path.abspath()` 绝对化。输出路径由
    `os.path.join(绝对目录, 'NN.mp4')` 自然得到绝对路径，无需二次改动。
  - **验证**：修复前后各跑一次端到端冒烟测试（3 秒测试视频 + 2 集分集表 + 跨切点字幕），
    修复前 `rc=1`，修复后相对路径 `rc=0`，产出 `burned/01.mp4`、`clean_srt/01.mp4` +
    `01.mp4.srt`，且跨切点字幕正确裁断、每集时间轴从 `00:00:00,000` 归零。

### 未改动（原样导入）

- `scripts/split_srt.py`、`scripts/make_template.py` — 二者不经 ffmpeg、不切 cwd，相对路径行为正常。
- `assets/episodes.xlsx`、`assets/使用说明.md`、`requirements.txt` — 原样。

### 环境部署（本机）

- ffmpeg（gyan.dev essentials build 9.0.2）由 `$FFMPEG` 环境变量或 PATH 定位；
  **未**塞进技能目录（避免 210MB 随包分发）。2026-11-07 已装到 `C:\ffmpeg\bin\`
  并加入用户 PATH，脚本自动识别。
- `openpyxl 3.1.5` 装进本机 Python 环境。

## 0.2.0 — 2026-10-09

**来源**：《女巫与狼王》(HDM029) 海外版 40 集分切实战暴露的两个问题。

### 改动 1｜`scripts/split_srt.py` — 全角标点导致整集被静默跳过

- **症状**：`狼王分集.xlsx` 第 1 集 `B2` 单元格是 `00：00：00：00`（**全角冒号**，中文输入法默认），
  其余行是半角。运行后第 1 集被 `[跳过]`，且**不报错**，极易漏集。
- **根因**：`parse_tc()` 用 `tc.count(':')` 和 `tc.split(':')` 判断/切分，全角 `：` 不匹配 `:`，
  于是落到最后一个 `raise ValueError`，被上层 `cell_to_ms → None` 吞掉。
- **修复**：`parse_tc()` 入口先把 `：，．－` 及全角空格归一化为半角，再解析。
- **验证**：`parse_tc('00：00：00：00', 24)` → `0`；`parse_tc('00：02：30：01', 24)` → `150042 ms`。

### 改动 2｜`scripts/split_video.py` — 支持自定义输出命名

- **背景**：默认输出 `01.mp4 / 02.mp4`，但交付惯例常要求带剧名与集号（如 `女巫与狼王ep001.mp4`）。
  40 集 × 2 版共 120 个文件，跑完再批量改名既慢又易错。
- **修复**：新增 `--name-format`，用 `{ep}` 占位（Python `str.format` 语法），默认 `{ep:02d}.mp4`。
  独立字幕版的同名 `.srt` 由视频名自动追加 `.srt` 得到。
- **用法**：`--name-format "女巫与狼王ep{ep:03d}.mp4"` → `女巫与狼王ep001.mp4` + `女巫与狼王ep001.mp4.srt`

### 实战口径记录（非代码，供复用）

- **分集表 fps 以「PR 序列真实帧率」为准，不要盲信 `G1`。**
  《女巫与狼王》模板 `G1=25` 是未改的默认值；用历史单集时长反查，**29 集命中 24fps、0 集命中 25fps**
  （第 1 集误差 0.000），确认序列实为 24fps。25→24 的误差约 `帧号 × 0.001667 s`，单点 ≤0.04s，
  但**集数多、切点累加**，口径必须用 `--fps 24` 显式覆盖。
- **源片帧率 ≠ 序列帧率**：成片可能是 30fps 导出，但时间码语义仍是 24fps。切点按**秒**落刀，
  与源帧率无关，故 `--fps` 只用于解析时间码，输出帧率默认保持源帧率。

