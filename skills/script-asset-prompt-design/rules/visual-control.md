# 规则模块 — VIS 画面控制与统一性（怎么"不脏不碎"）

作用域：S4~S5 阶段的画面质量控制。编号前缀 VIS。

## VIS-01 连续性约束段（每个非首张提示词必备）

中文版标准文案骨架（按母题表填空）：

```
【连续性约束】
必须与【前一张场景名】属于同一地点。
保持相同森林地貌、树木种类、岩石材质、雾气质感和整体色调。
不要重新设计一个完全不同的【场景类型】。
```

英文版对应：

```
CONTINUITY CONSTRAINT:
This must be the exact same location as shot A.
Maintain the same forest terrain, tree species, rock materials, atmospheric mist and overall color palette.
Do not redesign the forest as a completely different environment.
```

- 首张不需要此段；组内第 N 张需声明与前一张（或全组）的连续关系。
- 允许写"渐变例外"：连续但环境随深入逐渐更古老/荒凉/异常——变化必须写成渐进过程，不是跳变（SPC-07）。

## VIS-02 画面控制段（每张必备，源自用户实测反馈）

这是防止"高光过碎、画面脏花累"的系统级约束。中文版标准文案骨架：

```
【画面控制】
控制画面复杂度，避免细节过度堆叠。
保持大面积干净、通透、连续的【雾气/天空/暗部】区域。
非视觉中心区域简化处理，不刻意增加【树叶、石块、符文和纹理】。
细节只集中在【视觉主体与关键前景】。
整体清晰但柔和，避免强锐化、超高解析度、过度纹理化。
高光区域保持完整、柔和、连续，不产生大量碎片化亮点。
避免脏、碎、花、累的 AI 生成感。
不要过高饱和度，不要过强局部对比，不要 HDR 过曝效果。
```

英文版对应（大写起头强调）：

```
CONTROL VISUAL COMPLEXITY.
Avoid excessive detail accumulation.
Keep large areas of clean, open 【mist / dark forest】as visual breathing space.
Simplify non-focal areas instead of adding excessive 【leaves, stones, runes and textures】.
Concentrate detail only around 【the visual subject and key foreground】.
Keep the image clear but soft. Avoid aggressive sharpening, excessive micro-detail and over-resolved textures.
Highlights must remain broad, soft and continuous, without fragmented sparkling highlights.
Avoid dirty, noisy, cluttered or overly detailed AI-generated appearance.
Avoid excessive saturation, extreme local contrast and HDR overexposure.
```

核心原则三条：
1. **高光成面不成点**（broad, soft, continuous highlights — not thousands of tiny glowing details）；
2. **负空间是构图资产**（大片干净通透区域 = 视觉呼吸空间）；
3. **细节预算集中在焦点**（每张只允许一个细节密集区）。

## VIS-03 默认参数

- 画幅：**按管线 PP-S1**——P1=9:16 / P2=16:9 / P3=16:9 / P4=21:9（用户指定除外）。开工未定管线时先提问。
- 风格：**真人写实电影**（photorealistic / live-action），非动漫、非游戏CG、非概念插画。
- 色彩：低饱和、克制调色（restrained color grading）。
- 质感：subtle film grain + high dynamic range + soft cinematic contrast。

## VIS-04 正向描述原则（反馈转译）

- 用户的修正反馈必须**转译为正文本身的正向描述**，禁止把反馈原文（"不要消失""不是传送门""修正：…"）作为标注、注释或否定约束写进提示词。
- 例：反馈"高光过碎" → 正文写"高光区域保持完整、柔和、连续"，不写"不要碎片化高光"（负面清单兜底除外）。
- 需要避免的效果靠**直接描写正确动作/形态**落地，而不是靠否定词去拦。

## VIS-05 光线纪律（跨张检查）

- 全组统一环境光基调（如冷蓝灰夜景 + 柔和漫射）。
- 组内光线演进只允许两种合法变化：
  1. **强度渐变**（更暗/更亮，渐进而非跳变）；
  2. **新增光色必须绑定新叙事信息**（暗红光首次出现 = 悬念升级节点），且首现时"极微弱"。
- 禁止同一张内冷暖光五五开；主光唯一，辅助光"若有若无"。
- 每张提示词的光线描述必须同时包含：光源性质、色温、饱和度、光的动静态（流动/脉动/静止）。
