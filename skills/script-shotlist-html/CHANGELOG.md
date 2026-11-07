# CHANGELOG — script-shotlist-html

> 约定：每条变更独立成条（回滚单元），格式 `[版本] 日期 变更标题` + 动机/变更点/影响文件。新条目加在最上面。

## [1.0.0] 2026-09-04 本土化改造安装：剧本→一页式 HTML 分镜成片器

**动机**：用户提供 E:\提示词\3\shotlist-builder（海外团队脚本，硬编码 15s/21:9/Seedance2.0、英文 UI、缺 P1-P4 国内管线、HTML 模板引用了不在包内的 "house template"）。用户要求"按管线规范本土化改造并安装成可用技能"。

**变更点**：
- 全新 `SKILL.md`：定位为"剧本→一页式交互 HTML 分镜看板"交付形态（与主控 cinematic-seedance-director 的纯文本 txt 互补）；接入 P1-P4 管线判定（读 rules/PIPELINE_PRESETS.md）；剧本语言自适应（中文剧本=中文UI+中文提示词；P4英文=英文UI+台词英文）；四阶段有状态循环保留；写明与已装技能分工与推荐链路。
- 新增 `rules/PIPELINE_PRESETS.md`（PP-01~05）：四管线常量唯一事实源，与主控同一套数值（P1 9:16/P2 16:9/P3 16:9/P4 21:9 等）。
- `templates/HTML_TEMPLATE.md` **重写**：把原"引用 house template"的占位骨架升级为**可直接使用的单文件内嵌 CSS/JS 模板**（深/浅主题自适应、搜索/镜头类型筛选/一键复制提示词/打印PDF），UI 中文化。
- reference 从 E:\提示词\3\shotlist-builder\reference 移植 7 个方法论文件（STYLE_BLOCK / PROMPT_PATTERNS / CAMERA_EMOTION / MICRO_BEATS / SPATIAL_BLOCKING / PROMPT_DENSITY / PLAN_TYPES），并在 STYLE_BLOCK/PROMPT_PATTERNS/PROMPT_DENSITY/CAMERA_EMOTION 顶部注入"管线接入"横幅。
- 新增 `review/preflight.md` 交付门禁（结构完整性/提示词质量/空间布局/交付四组核查项）。

**影响文件**：SKILL.md、rules/PIPELINE_PRESETS.md、templates/HTML_TEMPLATE.md、reference/*（7个，4个加管线横幅）、review/preflight.md、本文件。

**与 2/seedance-director 的决策**：子目录2 弃用归档（不安装），理由见 `outputs/技能对比_子目录2_vs_已装主控.md`。
