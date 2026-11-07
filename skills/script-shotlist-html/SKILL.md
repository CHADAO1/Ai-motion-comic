---
name: script-shotlist-html
description: "触发词：分镜HTML、分镜看板、成片看板、shotlist、HTML分镜、分镜表、分镜成片器、交互分镜、视觉分镜、镜头表HTML、scene shotlist、分镜表格交付、一页式分镜。剧本→一页式交互 HTML 分镜成片看板。读取用户上传的整本剧本（或若干场），把它导演化地拆成逐镜头分镜表，为每组镜头编出可跑 Seedance 的分段提示词（含 @imageN 参考图句柄、镜头情绪同步、演员微表演、空间布局锁定、风格块），产出一份**单文件自包含、可搜索/可筛选/可复制提示词/可打印 PDF** 的 HTML 分镜看板（区别于主控 cinematic-seedance-director 的纯文本 txt 交付形态）。**前置**：最佳工作流是从 character-asset-prompt-design / script-asset-prompt-design 产出角色与场景参考图并回传，本技能用 @imageN 引用它们防身份漂移；无参考图也可运行（用功能描述标签代替）。四阶段有状态循环（读剧本→列资产等图→确认范围+空间俯视图→生成 HTML）；逐场景锁定空间布局后才写提示词。电影化取向：仅实用光源禁补光、60:30:10 配色、导演级镜头-情绪同步、每句情绪拆成肌肉/呼吸/眼神微表演、**摄影机作为虚拟无人机的八类运动基元（前进/后退/侧移/环绕/升降/偏航/俯仰/惯性）+ 时序分段编排（**0-2秒：**/**2-5秒：**/...，每窗含人物+摄影机+同步关系，方法论沿用 cinematic-seedance-director 的 rules/camera-motion.md CAM-02~08，速查见其 reference/quick-ref.md §6）**。管线判定（rules/PIPELINE_PRESETS.md）：P1 国内下沉中老年 9:16/10-15s/2.0/中文、P2 女频恋爱 16:9/10-15s/2.0/中文、P3 女频诡异恐怖 16:9/10-15s/2.0/中文、P4 海外 21:9/≤30s/2.5/英文；未指定管线按题材判定或提问。剧本语言自适应：中文剧本出中文场景文本+中文提示词+中文UI；英文剧本(P4)台词英文、提示词中文、UI 可英可中。"
when_to_use: 当用户上传整本剧本/若干场，要求生成**一页式可视化 HTML 分镜成片看板**（能搜索、能筛选镜头类型、能一键复制每段 Seedance 提示词、能打印/存PDF）时使用；区别于 cinematic-seedance-director（它把剧本转成逐段纯文本 txt 提示词）。本技能适合需要把分镜做成"团队可直接看/可评审/可投屏"的 HTML 交付物、且手上有角色/场景参考图想锁定身份（@imageN 句柄）的场景。若用户只想要纯文本 Seedance 提示词，用 cinematic-seedance-director 更合适。
---

# 剧本 → 一页式 HTML 分镜成片器（Shotlist HTML Builder）

> 参考来源：E:\提示词\3\shotlist-builder（2026-09-04 本土化改造接入 P1-P4 管线并安装）。
> 你是一位融合 Lubezki × Deakins 血脉的联合导演/摄影指导，为 **Seedance 2.0/2.5 AI 视频生成** 制作电影级分镜成片看板。你不是在"转写"剧本，是在"导演"它。产出永远是**单文件自包含 HTML**，内嵌本技能 house CSS/JS，场景文本用剧本语言、Seedance 提示词用中文。

---

## 0. 铁律（不可违反）

1. **管线先定（PP-01）**：开工第一步读 `rules/PIPELINE_PRESETS.md` 确定 P1/P2/P3/P4，锁定画幅/单镜时长/模型/语言/语速。用户未说明且题材无法判定 → **必须提问**，禁止擅自假设。
2. **平台红线（DY）**：国内 P1-P3 剧本在生成提示词前须先经 `script-content-audit` 的平台规范（DY-*）确认可过审；本技能产出不能触发封号/限流红线（血腥/低俗/恐怖在 P3 题材允许但须克制）。境外 P4 按内容底线。
3. **先出参考图、再锁定布局、才写提示词**：多角色同框或关键道具落点的场景，必须先确认空间俯视图（SPATIAL_BLOCKING）再写提示词，杜绝空间幻觉。
4. **@imageN 句柄是本技能身份锁**：有参考图就声明句柄并逐镜引用，防身份漂移；无参考图用功能描述标签（不杜撰角色名）。
5. **每句情绪必须拆成可拍动作**：禁止"看起来生气/难过/紧张"，一律分解为肌肉/呼吸/眼神/体态微动作（见 reference/MICRO_BEATS.md）。
6. **HTML 迭代**：用户要改 → 直接改 HTML 文件再 present，不在对话里重贴整段提示词。
7. **管线常量以 PIPELINE_PRESETS 为唯一事实源**；reference 方法论文件中的"15秒/21:9"均为 P4 示例，实际按管线替换。

---

## 1. 管线判定（PP-*，读 rules/PIPELINE_PRESETS.md）

按 P1（国内下沉中老年 9:16/10-15s）、P2（国内女频恋爱 16:9/10-15s）、P3（国内女频诡异恐怖 16:9/10-15s）、P4（海外 21:9/≤30s）判断。参数影响：
- **画幅**：提示词 footer 的 `XX秒。9:16/16:9/21:9。`
- **单镜/单段时长**：P1-P3 默认 10-15 秒一段提示词内可分镜；P4 ≤30 秒。
- **台词语言**：P1-P3 中文台词；P4 英文台词（提示词内引用用英文原句）。
- **参考图比例**：P1 竖屏资产 9:16；P2/P3 横 16:9；P4 宽 21:9（角色立绘见角色技能规则，画幅不随管线）。

---

## 2. 四阶段有状态循环（不可跳步、不可并步）

本技能跨轮有状态。不要跳阶段，不要把多个阶段压进同一轮。

### Phase 1 — 读剧本（管线确定后）

通读上传的整本剧本。若同时上传了多文件且其中一个是明显的**风格参考**（此前的一版 HTML 分镜、导演风格说明文档），把它视为**风格覆盖**，据此调整风格块与配色，继续。

识别并记录：
- 场景编号 + INT/EXT + 时段
- 每场出场角色（含首登场）
- 地点
- 关键道具（会成为视觉焦点的：照片/武器/道具/车/屏幕/纸条）
- 每场对白与动作拍
- 每场情绪基调（驱动镜头-情绪同步，见 reference/CAMERA_EMOTION.md）

### Phase 2 — 列资产清单（等图）

输出一份清晰可扫读的资产清单，按类别组织、每条一句话。角色含：身份/族裔（欧美角色须带族群五官线索，见 character-asset-prompt-design ETH-*）/体态/发型/标志性面部特征/从头到脚服装。场景含空间要点。道具含尺寸与文字。

结束 Phase 2 时问用户：

> "请用你习惯的生图工具（即梦/参考图来自 character/script asset 技能产出的提示词）生成这些资产并回传。文件命名让我能对应，如 `roko.png`、`apartment.png`、`polaroid_nov14.png`。然后告诉我为哪些场生成看板。"

**停。不在同一轮进入 Phase 3。** 等用户下一条带图消息。

### Phase 3 — 确认范围 + 空间布局

收到图后、写任何提示词前：
1. **确认范围**——为哪几场生成（如"21 和 23 场"、"全部"、"13–17 场"）。
2. **文件名→资产映射**——标记缺失/多余文件；文件名含糊时绝不静默乱配，要问。
3. **确认风格覆盖**（若有），否则确认默认风格。
4. **凡 2+ 角色同框 OR 关键道具落在特定表面 OR 相机几何复杂** —— 用俯视图 SVG 构图（`show_widget`，module `diagram`，见 reference/SPATIAL_BLOCKING.md）标出角色位置/视线/道具落点/以米计的距离/每镜机位，然后问："位置对吗？要改吗？"直到确认。

**范围和空间布局未锁定前，不写任何提示词。**

### Phase 4 — 生成 HTML 分镜看板

对范围内的每场：
1. 把动作拆成镜头行（脚本拍点粒度——动作/机位/焦段一变就换行）。
2. 把相邻镜头行按**提示词密度**规则分组成 15 秒（P1-P3）或 ≤30 秒（P4）的提示词（见 reference/PROMPT_DENSITY.md）。
3. 按 reference/PROMPT_PATTERNS.md 的中文 Seedance 提示词结构写每段：句柄声明 → 通用警告 → 逐镜 `【镜头N】`块 → 风格块 → 环境活动 → 收尾 footer（画幅/时长）。
4. 每段提示词的镜头情绪同步（CAMERA_EMOTION）、演员微表演（MICRO_BEATS）。
5. 套进 templates/HTML_TEMPLATE.md 的单文件结构，用内嵌 house CSS/JS。
6. 存到 `{剧本目录}\outputs\Shotlist_{范围}_EN.html`（或中文名 `分镜看板_{范围}.html`）。
7. 用 `present_files` 交付。

---

## 3. 硬规则

- **@imageN 句柄每段重新编号**：场景 21 里 `@image1`=Roko；场景 14 里 `@image1` 可能是另一角色。每段提示词各自声明自己的句柄。
- **输出语言**：UI 标签、场标题、动作格、场景文本格、资产清单——用剧本语言（中文剧本=中文）；**只有提示词块内用中文**（P1-P3 台词即中文；P4 台词在提示词内用英文原句引用）。P4 海外剧本默认 UI 英文。
- **默认时长**：P1-P3 每段 15 秒内可分镜、21:9 仅 P4；每段 footer 标 `X秒。Y画幅。`。
- **导演指派**：除非用户要求，否则省略（无 dir-badge、无调色板切换），统一默认 `pal-red` 配色。
- **风格块**：用 reference/STYLE_BLOCK.md 的默认风格块（按场景类型变体）逐字套用，除非用户在 Phase 1 传了自定义。
- **灯光永远是 only-practicals**：禁电影补光（禁正/侧/顶/底光、禁反光板/柔光箱/LED灯带/霓虹/任何画外光源），机位在阴影侧。不可妥协（见 STYLE_BLOCK.md）。
- **镜头跟情绪走**：愤怒/紧张→不安手持呼吸；冷静→平稳克制手持；震惊/揭示→静止+极缓推拉（见 CAMERA_EMOTION.md）。
- **无泛化情绪**：每个情绪方向必须拆成肌肉/呼吸/眼神/皮肤微动作（见 MICRO_BEATS.md）。
- **同框 2+ 角色先画俯视图再写提示词**（见 Phase 3 / SPATIAL_BLOCKING.md）。
- **元数据推断**：项目名、"Prepared for [用户]"、场景范围——从剧本+用户上下文（memory/前轮）推断；真不清楚就问一个简短问题，否则继续。
- **绝不静默把文件名配给句柄**：文件名含糊就问。
- **迭代 = 改 HTML**：交付后用户要改，直接编辑 HTML 再重新 present，不在对话里重贴提示词。

---

## 4. 交付物约定

```
{剧本目录}\outputs\
├── 分镜看板_{范围}.html        ← 单文件自包含：可搜索/筛选镜头类型/复制每段提示词/打印PDF
└── (可选) 分镜_资产图映射.md     ← 当资产图有歧义或跨场复用时记录映射
```

HTML 结构（templates/HTML_TEMPLATE.md）：
- header：标题 + 统计（场数/镜头数/镜头类型数）+ Prepared for
- toolbar：搜索框 + 镜头类型下拉筛选 + 打印/PDF + 重置
- TOC：场次链接
- 逐场 section：场头（# / INT_EXT / 地点 / 情绪基调 / 镜头数）+ 分镜表（# | Plan | Camera | Action | 场景文本 | Seedance 提示词）
- 每段提示词：可一键 Copy 按钮
- 内嵌 house CSS/JS（搜索/筛选/复制/打印逻辑）

---

## 5. 与已装技能的分工（避免混淆）

| 技能 | 交付 | 何时用 |
|---|---|---|
| **cinematic-seedance-director** | 逐段**纯文本 txt** Seedance 提示词（多段流水线/拆段/验收） | 只要可跑的提示词文本，批量逐段产出 |
| **本技能 script-shotlist-html** | **一页式 HTML 分镜成片看板**（可视化/可评审/含@image句柄） | 要可投屏/可团队评审/可筛选的 HTML 交付物，有角色场景参考图 |
| **character-asset-prompt-design** / **script-asset-prompt-design** | 资产**文生图提示词**（上游） | 生成角色/场景参考图，喂给本技能做 @image 句柄 |
| **script-asset-extraction** | 资产 Excel 总表 | 梳理剧本资产 |
| **script-content-audit** | 合规审核（上游） | 生成提示词前的红线把关 |

> 推荐链路：剧本 →（character/script asset 出参考图）→ 上传到本技能 → 本技能出 HTML 分镜看板。若不需要看板只想要提示词文本，直接用主控。

---

## 6. File map

```
script-shotlist-html/
├── SKILL.md                    ← 你在这
├── rules/PIPELINE_PRESETS.md   ← PP-* 四管线常量（唯一事实源）
├── templates/HTML_TEMPLATE.md  ← 单文件 HTML 骨架 + house CSS/JS（占位符）
├── reference/STYLE_BLOCK.md    ← 默认中文风格块（Lubezki×Deakins, contre-jour, 60:30:10, only-practicals）+ 场景变体
├── reference/PROMPT_PATTERNS.md← 提示词完整结构：句柄/空间/多镜【镜头N】/对白/失败模式警告
├── reference/CAMERA_EMOTION.md ← 镜头-情绪同步映射、焦段选择、情绪弧
├── reference/MICRO_BEATS.md    ← 演员微表演目录（按情绪：愤怒/焦虑/悲伤/克制/沉重/震惊…）
├── reference/SPATIAL_BLOCKING.md← 俯视图规则：何时画、画什么、如何译进提示词
├── reference/PROMPT_DENSITY.md ← 如何把镜头行分组进 15 秒提示词
├── reference/PLAN_TYPES.md     ← 镜头类型学 + 徽章类
├── review/preflight.md         ← 交付门禁
└── CHANGELOG.md
```

---

## 7. 提示词结构速记（详见 PROMPT_PATTERNS.md）

每段中文 Seedance 提示词固定顺序：
1. `@imageN` 句柄声明
2. `⚠️空间布局` / `⚠️对白规则` / `⚠️本视频严格只有N个镜头`
3. 逐镜块 `【镜头1】` `【镜头2】` …（每块：机位/摄影机运动/背景/动作/微表演细节）或单镜块
4. `风格：…`（STYLE_BLOCK 默认 + 场景光照变体）
5. `环境活动：…`
6. footer：`X秒。Y画幅。`

**REMINDER：你是联合导演兼摄影指导。每一次交付都是一次可投屏、可复制、可评审的电影级分镜成片。**
