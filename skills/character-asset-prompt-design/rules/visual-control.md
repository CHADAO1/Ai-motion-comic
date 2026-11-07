# 规则模块 — CVC 画面控制与身份稳定（怎么"不脏不碎、脸不漂"）

作用域：S4~S5 阶段。编号前缀 CVC。

## CVC-01 身份锚定段（每个变体必备）

中文骨架：

```
【身份锚定】
@{角色名}原始外观
面部、发型、发色、瞳色、肤色与体型与参考图完全一致，不做任何改变。
[{2~3 个最关键锚 token 复述}]
```

英文骨架：

```
IDENTITY LOCK:
@{角色名}原始外观
The face, hairstyle, hair color, eye color, skin tone and body build must remain exactly identical to the reference image, with no alterations.
[{key anchor tokens restated}]
```

- `@…` 行为 **CAP-12 参考图占位标识**（唯一允许入块的 @ 内容）：用户生成时把该行替换为对应参考图；英文版同样保留中文占位，便于用户定位。
- 有符号的角色，印记行前再加 `@{符号名}` 占位（CAP-12）。

- 核心原则：**身份交给参考图，不重述**。全脸重述=重新解释=漂移入口；只复述最关键锚 token 作保险。
- 锚token复述控制在 2~3 个：发色、瞳色、标志性印记优先（这三项最容易被模型顺手改掉）。

## CVC-02 画面控制段（原始外观完整版 / 变体简化版）

**原始外观**中文骨架：

```
【画面控制】
皮肤与布料的高光保持完整、柔和、连续，呈大面积柔光而不是碎亮点。
背景保持干净、通透的中性暗色，作为负空间。
细节预算集中在面部与服装关键结构，其余区域简化。
避免塑料皮肤、过度磨皮、网红滤镜感。
避免强锐化、超高解析度、过高饱和度、过强局部对比。
避免脏、碎、花、累的AI生成感。
```

英文版（大写起头，逐句对应）：

```
CONTROL VISUAL COMPLEXITY.
Highlights on skin and fabric must remain broad, soft and continuous, never fragmented sparkling points.
Keep the background clean, open and neutrally dark as negative space.
Concentrate the detail budget on the face and key garment structure; simplify everything else.
Avoid plastic skin, over-smoothing and influencer filter look.
Avoid aggressive sharpening, excessive resolution, excessive saturation and extreme local contrast.
Avoid dirty, noisy, cluttered or overly detailed AI-generated appearance.
```

**变体**用三句简化版：
1. 变更项（血迹/新装/尘土）的高光成面，不出碎亮点；
2. 未变更区域保持参考图的皮肤与布料质感，不新增纹理细节；
3. 整体饱和度与锐度与参考图一致。

## CVC-03 默认参数与角色统一构图基准

- 画幅：**9:16 竖幅**（角色资产固定值，2026-08-29 用户拍板——全身像应竖长；2026-09-03 复核：**不随管线变化**，理由见 `PIPELINE_PRESETS.md` PP-C1）。注意区分：**场景资产画幅按管线**（P1=9:16 / P2/P3=16:9 / P4=21:9）由场景技能 `script-asset-prompt-design` 管，**视频画幅按管线**由 `cinematic-seedance-director` 管——角色立绘是身份参考图，一律 9:16，勿沿用场景/视频画幅。
- **风格调性按管线（PP-C2）**：P1 下沉中老年→生活化真实、保留皮肤纹理、朴素服装、低饱和暖调；P2 女频恋爱→都市质感、清透柔和、重可代入感；P3 女频诡异恐怖→日常便装、冷调、惊恐变体必备、无血腥；P4 海外→沿用本文件原有默认。
- **构图基准（全角色统一，原始外观与全部变体恒定）**：
  1. **全身像**：头顶/脚下少量留白便于裁切；
  2. **居中笔直站立**：正面朝向镜头，身体不侧转、不倚靠；
  3. **双手自然下垂**，贴于身体两侧；
  4. **双手无手持物**：不持任何道具（剧情道具如符牌一律"藏袖/不在画面中露出"处理）；
  5. **平面柔光**：均匀柔和、无戏剧性单侧光与强投影；
  6. **浅灰色背景**：干净平面浅灰，作大面积负空间。
- 理由：立绘是后续所有变体的参考图根与角色身份基准——统一构图让 I2I 编辑时的环境/姿态串扰最小，也让跨角色并排对照成为可能。剧情姿态（如"双手交叠身前"）属表演层，在视频提示词阶段叠加，不进角色资产。
- 风格：**真人写实电影**（photorealistic / live-action portrait），非动漫、非游戏CG、非概念插画。
- 色彩：低饱和、克制调色、subtle film grain、soft cinematic contrast（皮肤与布料质感层面仍保留电影质感）。
- 变体默认与参考图**同构图**（居中直立、双手下垂、浅灰背景），便于对照与编辑；保持段显式声明。

## CVC-04 正向描述原则（反馈转译）

同场景技能：用户的修正反馈必须**转译为正文本身的正向描述**，禁止把反馈原文（"脸变了""不要磨皮""修正：…"）作为标注、注释或否定约束写进提示词（负面清单兜底除外）。

- 例：反馈"脸漂了" → 正文写"面部特征与参考图完全一致"（锚定段强化），不写"不要漂"。
- 例：反馈"皮肤太假" → 正文写"带真实毛孔与轻微风霜感的皮肤"，不写"不要假皮肤"。

## CVC-05 编辑漂移防护（I2I 特有）

图生图/图片编辑最大的风险不是画不出变更，而是**变更之外的东西被顺手改掉**：

1. 变更段**只写变更项**；未提及 = 保持参考图原样，并在保持段显式声明。
2. 禁止在变体中引入参考图没有的装饰/配饰/背景元素（变更段明确要求除外）。
3. **一个变体只承载一类变更**（CHR-06 一型）；确需复合变更时逐项分列、逐项量化，禁止揉成一句。
4. 变更程度用递进词序（`轻微 > 明显 > 彻底`），对应剧情强度，防止"小伤画成重残"。
5. 负面清单必须含编辑漂移层（CAP-07 第4层），作为最后兜底。

## CVC-06 比例与真人感强化 token 库（原始外观必插；变体简化）

**为什么**：T2I 生成角色最常见两类翻车——① 头身比/四肢比例失真（尤其全身像）；② 皮肤衣料"AI 塑料感"。以下 token 为用户实测有效的纠偏词，经整合优化后**分插进原始外观 T2I 的对应段**（勿整块堆在结尾）。

**中文 token（按插入位置分派）**：

| 目标 | token（可按语感微调，语义不变） | 插入位置（CAP-01 段号） |
|---|---|---|
| 比例 | 全身构图，头身比例合理协调，接近时装模特的身形比例，身材高挑修长，四肢与躯干比例自然 | ③ 身份锚总述 |
| 真人感·皮肤 | 真实细腻的皮肤纹理，带自然毛孔与皮下光影，是真实存在的人的皮肤质感 | ④ 面部 |
| 真人感·服饰 | 衣料垂坠真实，衣摆自然下垂，袖口与下摆边缘干净利落无毛边；饰品与金属配件结构精细、比例自然合理 | ⑥ 服装层 |
| 细节 | 高清细节集中于面部五官、皮肤质感与服装关键结构，细节精致耐看 | ⑧ 背景与光 或 ⑨ 摄影术语前 |

**English token（逐项对应）**：

| 目标 | token |
|---|---|
| 比例 | full-body composition, correct and harmonious head-to-body proportions, close to a fashion model's figure, tall slender build with natural limb-to-torso ratios |
| 真人感·皮肤 | fine realistic skin texture with natural pores and subsurface light, the skin of a real living person |
| 真人感·服饰 | realistic fabric drape, hems falling naturally, clean crisp edges at cuffs and hem with no fraying; finely structured, naturally proportioned jewelry and metal fittings |
| 细节 | high-definition detail concentrated on facial features, skin texture and key garment structure, refined without clutter |

**变体（I2I）简化版**：比例与站姿已由参考图锁定，强化 token 退化为保持段一行：
`头身比例与全身构图（居中直立、双手自然下垂、无手持物、浅灰背景）保持参考图原样。`
英文：`Head-to-body proportions and full-body composition (centered upright stance, arms relaxed at sides, empty hands, light-gray background) remain exactly as the reference image.`

**例外声明**：**无毛边/边缘干净**是默认要求；当变体的变更段显式声明破损（战损撕裂、起毛、烧灼痕）时，以变更段为准，且破损只出现在声明的位置——其余边缘仍保持干净。
