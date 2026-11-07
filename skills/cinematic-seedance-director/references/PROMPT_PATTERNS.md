# Seedance Prompt Patterns & Structure

> The authoritative guide for constructing world-class Seedance 2.0 prompts.
> Every prompt follows a structural order — hit every section, don't skip, don't reorder.

---

## 1. Output Format

All output is **plain text prompt lists**, one prompt per scene/shot-group, formatted as:

```
[完整 Seedance 提示词——直接以【风格参考：…】开头，不写"场景X|标题 / 风格参考"两行题头]
[场景标题、镜头分析等信息留在提示词代码块之外]

[N]秒。[画幅]。

---
镜头分析：
[该镜头的镜头语言、构图、节奏分析，用于让创作者理解为什么这样设计]
```

> 注意：提示词正文**不含任何题头行**——包括 `场景 X | [标题]`、`段X | 标题（时长）`、`风格参考：[导演]` 独立行，以及任何 `═══` 分隔线块，这些一律不进入提示词。提示词代码块第一行直接是 `【风格参考：…】`（可带中文括号说明，如 `Deakins（对话）→ Khondji（吊坠特写）`），**代码块以 `[N]秒。[画幅]。` 收尾，结尾不追加任何分隔线或收尾符号**。场景标题、段落名、时长、镜头分析只留在代码块外作为交付说明。

---

## 2. Prompt Structural Order

Every Chinese Seedance 2.0 prompt follows this sequence:

1. **风格声明** (Style declaration)
2. **场景概述** (Scene overview)
3. **空间布局** (Spatial blocking — character positions, distances)
4. **镜头块** (Per-shot blocks `【镜头N】` for multi-shot, or single continuous block)
5. **表演指导** (Performance micro-beats)
6. **环境活动** (Background activity)
7. **对白规则** (Dialogue rules — if applicable)
8. **失败模式警告** (⚠️ failure-mode markers)
9. **收尾** (Duration + aspect ratio)

---

## 3. Section Details

### 3.1 风格声明 (Style Declaration)

Open with the selected cinematographic style. Select from [DIRECTOR_STYLES.md](DIRECTOR_STYLES.md):

```
【风格参考：Deakins】自然光源驱动，深暗阴影富有雕塑感，消饱和调色，仅一抹强调色。从暗侧拍摄。禁补光灯、禁反光板。
```

Or if blending styles:
```
【风格参考：Deakins → Doyle】前半段Deakins冷峻自然光，后半段过渡为Doyle色彩浸染手持暧昧。过渡点在角色情绪转变瞬间。
```

### 3.2 场景概述 (Scene Overview)

One to two sentences establishing what happens in this prompt:

```
【场景概述】[角色A]独自站在空旷的公寓客厅中央，面对墙上已不存在的照片痕迹。窗外城市灯火透过雨痕玻璃投射斑驳光影。角色从静止到情绪崩溃的完整弧线。
```

### 3.3 空间布局 (Spatial Blocking)

For any prompt with 2+ characters OR significant environmental interaction:

```
⚠️空间布局：
@image1（角色A）：站在画面中央偏左（房间西南角），面朝右侧窗户（东）。
@image2（角色B）：站在@image1右后方2米处（东偏北），身体半侧朝向@image1，被@image1的身体部分遮挡。
窗户：画面右侧（东墙），距@image1约3米，光源来自窗外城市灯火。
```
*本段换算基准：面向北时左=西、右=东、上=高空/画面上方、下=地面/画面下方、北=画面纵深方向（远）、南=画面近端方向（近）。*

Rules:
- Use precise distances in meters
- Note who faces which direction
- Note who occludes whom
- For solo-character scenes, note character's position relative to key environment features
- **双重方位参照（硬性，详见 SKILL.md §5.3）**: every positional statement must carry BOTH the screen-reference set (上下/左右/前后/中央, the primary set video AI can actually execute) AND the compass set (东南西北) — e.g. `站在画面中央偏左（房间西南角）`、`面朝北（画面纵深方向）`、`右墙（东）自动门`、`沿来路向南（画面近端方向）离去`. Never write a compass direction alone (`街道北端`) without its screen-frame counterpart (`街道北端远景中央=画面纵深最远端`), and never write a screen-frame direction alone without its compass counterpart. State the mapping once at the top of the block.

### 3.4 镜头块 (Shot Blocks)

#### Single-Shot Prompt (no internal cuts)
```
单镜头（one-shot，无剪辑）。

机位：35mm广角，全景。缓慢推进至中近景，速度0.5mm/秒感觉。
构图：三分法，角色位于左侧三分线，右侧负空间占据画面2/3。窗外光源在右侧制造侧逆光（contre-jour），角色正面落在阴影中。
景深：F2.8，中景深，角色面部锐利，背景窗户光斑化为散景。
拍摄角度：平视微仰（3度），赋予角色微妙的尊严感。
摄影机运动：缓推——从全景以不可察觉的速度逼近。手持呼吸感（organic handheld breathing），镜头随角色胸腔呼吸微幅起伏。
```

#### Multi-Shot Prompt (internal cuts)
```
⚠️本段共3个镜头（参考节奏，非强制）。允许在不改变剧情走向、对白内容与人物形象的前提下，根据实际生成效果灵活拆分、合并或替换镜头。特别地——当某句台词过长、或画面内容过于呆板缺乏变化时，鼓励自行增补反应镜、特写或过渡镜，让节奏更自然；若某个镜头不合理，可直接用更合适的机位与构图替代。硬性限制只有一条：总时长不得超过本段标注的时长，且不得删改台词与系统面板文字。

【镜头1】
机位：50mm标准，F2.0中浅景深，中景。固定镜头。
构图：框中框——通过走廊门框拍摄@image1，角色在纵深尽头。门框占据画面两侧1/4形成自然遮挡。
动作：@image1背对镜头站在窗前，双臂下垂，肩胛骨微微起伏。静止5秒后，右肩微转——身体开始转向镜头。
⚠️约5秒后硬切至镜头2——无过渡、无淡出。

【镜头2】（紧接镜头1硬切）
机位：85mm中长焦，F1.8浅景深，特写。
构图：正面紧凑特写，角色面部占画面70%。左侧微留负空间引导视线。
摄影机运动：呼吸手持——镜头随角色呼吸节奏（4秒吸/4秒呼）微幅浮动。
动作：@image1双眼直视镜头方向。瞳孔微缩——认出了什么。嘴唇微启又闭合。喉结上下移动一次。
⚠️约4秒后硬切至镜头3。

【镜头3】
机位：24mm超广角，F8深景深，大远景。缓慢后拉。
构图：对称构图，角色居中，两侧走廊墙壁形成消失点透视。角色在环境中极度渺小。
摄影机运动：缓拉——从中景缓慢后退至大远景，速度匀速不减速。
动作：@image1身体微微前倾，像要迈步但停住了。双肩缓缓下沉——一种认输的姿态。画面缓慢拉远，角色缩入环境的阴影中。
```

#### Each shot block must include:
- **机位** — focal length + aperture + shot type + camera type (handheld/static/dolly)
- **构图** — composition rule (三分法/对称/框中框/引导线/负空间/前景遮挡/纵深调度) + subject placement + background description
- **景深** — aperture + depth type + what's sharp / what's blurred
- **拍摄角度** — eye level / low angle / high angle / Dutch tilt (with degree if specific)
- **摄影机运动** — movement type + speed + direction + emotion sync (see SHOT_LANGUAGE.md)
- **动作** — step-by-step character action with numbered beats (① ② ③) for arcs
- **微表演细节** — physical micro-events (see §3.5 below)
- **起始表情（硬性）** — each character's first on-screen shot in the segment must explicitly state their starting expression, derived from their current emotional state (not a neutral default face). Write it into the 动作/微表演 line as concrete micro-events (眉/眼/嘴角/呼吸), e.g. 好奇: 眉梢微抬、目光追视、嘴角自然放松. 远景站桩角色至少给情绪基调.

### 3.5 表演指导 (Performance Direction)

This is the cinematographer's core creative output. Direct emotion as physical micro-events — NEVER generic labels.

**起始表情先行（硬性）**: 写表演弧线前，先按角色当下处境确定起始表情并写进其首镜的微表演行（眉/眼/嘴角/呼吸的具体微事件，见下方目录），例如 6-2 塞拉初逛空间站街道 → 好奇/惊叹。禁止让角色首镜保持中性脸。

#### Anti-Pattern (FORBIDDEN)
```
❌ 角色看起来很悲伤。
```

#### Correct Pattern
```
⚠️微表演细节：
- ① 双肩缓缓下沉，像有什么重物从肩膀上卸下
- ② 眼睑微垂，瞳孔缓慢从[方向]收回至正面
- ③ 一次深长的吸气——胸腔起伏可见——然后缓慢从鼻腔呼出
- ④ 咬肌缓慢收缩，颧骨处可见肌肉绷紧——他在忍住什么
- ⑤ 双手在身侧缓慢握拳又松开，指节泛白后恢复血色
- ⑥ 眼眶逐渐湿润——不是流泪，是泪水积聚使眼球开始泛光
- ⑦ 嘴唇微启，停在要说什么的位置，最终闭合
```

#### Emotion Decomposition Catalog

| Generic Emotion | Decompose Into Physical Micro-Events |
|-----------------|--------------------------------------|
| 悲伤 (sadness) | 双肩下沉, 眼睑微垂, 呼吸深长不规则, 咬肌绷紧, 指节泛白, 眼眶湿润泛光, 嘴唇微启又闭合 |
| 愤怒 (anger) | 颞肌鼓起, 鼻翼扩张, 呼吸急促从鼻腔, 双拳紧握, 下颌前推, 颈部血管可见, 眼睛收窄凝视 |
| 恐惧 (fear) | 瞳孔放大, 呼吸浅而快, 肩膀上提内收, 手指微颤, 肤色泛白, 嘴唇干燥舔唇, 后退半步 |
| 震惊 (shock) | 全身僵直, 瞳孔骤缩后放大, 呼吸暂停, 嘴微张, 手中动作停止, 颈部血管可见 |
| 焦虑 (anxiety) | 目光频繁移位, 手指无意识搓捻, 咬唇, 重心在双脚间转移, 吞咽频繁, 肩膀紧绷 |
| 喜悦 (joy) | 眼角细纹收紧, 嘴角先于一秒微扬, 颧肌上推, 呼吸轻快, 肩膀上提放松, 身体重心前移 |
| 压抑 (suppressed) | 表面平静但颞肌鼓起, 呼吸刻意放缓, 指甲掐入掌心, 颈部肌肉可见绷紧, 吞咽频率增加 |

### 3.6 环境活动 (Background Activity)

For populated scenes — forbid empty backgrounds:
```
环境活动：背景中3-5名工作人员持续活动——两人并排讨论文件，一人弯腰核对设备屏幕，一人在通道间快速走动。银色机械臂全程持续低速运动。远处有人打开门带进一束走廊光。
```

For quiet/empty scenes — describe the absence:
```
完全寂静——禁背景音乐、禁画外人声。仅环境SFX：远处城市低频嗡鸣、暖气管轻响、雨打窗玻璃的细密白噪音。
```

### 3.7 对白规则 (Dialogue Rules)

When dialogue is present:
```
⚠️对白规则：
- 严格朝向[角色X]说（视线和声音方向明确指向X）。
- 一句台词 = 一个镜头——台词严格只出现在该角色的镜头内。
- 台词前的微节拍：角色先深吸一口气→目光锁定对方→开口。
- 台词引用原文英文："[exact dialogue line]"
```

### 3.8 失败模式警告 (⚠️ Markers)

Anticipate what Seedance will get wrong. Use ⚠️ for important, ⚠️⚠️⚠️ for critical.

#### Standard Forbidden Block (include in every prompt)
```
禁3D渲染。禁游戏引擎质感。禁CG过场。
禁正面光、禁侧面补光、禁反光板、禁柔光箱。
禁可见光束（god rays）。禁光学畸变。禁鱼眼。
禁漂浮道具。禁身份漂移。禁抖动（呼吸手持除外）。
禁音乐（除非场景明确需要）。禁字幕。
```

#### Common Failure Modes & Counters

| Failure Mode | Counter |
|--------------|---------|
| 身份漂移 (identity drift across cuts) | `连续性：角色、道具、环境每个镜头完全一致。禁身份漂移。` |
| 角色服装混淆 (wardrobe contamination) | Re-state each character's exact wardrobe in every shot block |
| 光溢 (light spill on skin) | `禁止[色]色溢打在人物皮肤和服装上` |
| 广角畸变 (wide-angle distortion) | `禁桶形畸变、禁枕形畸变、禁鱼眼效果` |
| 多余镜头 (spurious cuts) | `⚠️本视频严格只有N个镜头——禁止添加额外镜头。` |
| 焦点漂移 (focus drift) | `焦平面严格锁定在[对象]——禁rack focus、禁autofocus跳变` |
| 道具悬浮 (floating props) | `禁漂浮道具——[道具]必须有支撑或手持` |
| 空背景 (empty background) | Explicit background activity callout |
| 手部混乱 (hand chaos) | Specify exact finger count and action |
| 比例失真 (scale mismatch) | Restate heights and distances per shot |

### 3.9 收尾 (Closing Footer)

```
[N]秒。[画幅]。
```

**按管线取值（PP-01，禁止沿用出厂默认）**：

| 管线 | 模型 | 尾行示例 |
|---|---|---|
| P1 国内下沉中老年 | 2.0 | `[12]秒。9:16。` |
| P2 国内女频恋爱 | 2.0 | `[12]秒。16:9。` |
| P3 国内女频诡异恐怖 | 2.0 | `[12]秒。16:9。` |
| P4 海外 | 2.5 | `[30]秒。21:9。` |

- 秒数填该段实际估算值（P1-P3 落在 12–15 秒区间，PP-01）。
- 用户指定其他画幅/时长时用指定值，并在 manifest 记录。

---

## 4. Complete Example Prompt

```
【风格参考：Deakins】自然光源驱动——窗外城市灯火投射方向性硬光，阴影深邃富有雕塑感。消饱和调性，仅保留一抹琥珀色。从暗侧拍摄。禁补光灯、禁反光板。

【场景概述】角色A独自站在安全屋窗前，面对窗外雨夜城市。从静止凝望到情绪逐渐崩溃的完整弧线——从控制到失控，15秒内完成从压抑到释放的过渡。

⚠️空间布局：
@image1（角色A）：站在画面中央偏左三分线，面朝右侧窗户。距窗户约1.5米。
窗户：画面右侧，大面积玻璃，雨水沿玻璃流下形成扭曲光影投射在角色面部。

单镜头（one-shot，无剪辑）。

机位：50mm标准镜头，F2.0中浅景深，中景起步缓推至特写。
构图：三分法，角色位于左侧三分线，右侧2/3为窗户和城市灯火负空间。窗框在画面右侧形成框中框效果。
景深：F2.0，角色面部锐利，窗户雨水和城市灯火化为光斑散景。
拍摄角度：平视微仰2度——赋予角色在脆弱中的尊严。
摄影机运动：缓推——从全身中景以0.5mm/秒感觉缓慢逼近面部。呼吸手持——镜头随角色胸腔呼吸（4秒吸/4秒呼）微幅浮动。

⚠️微表演细节（角色A从控制到失控的7拍弧线）：
- ① 静止凝望窗外——双肩平正，呼吸均匀可控
- ② 双肩缓缓下沉——像有什么重物从肩膀卸下
- ③ 一次深长吸气，胸腔明显起伏——然后极缓慢从鼻腔呼出
- ④ 咬肌缓慢收缩，颧骨处可见肌肉绷紧——他在忍住什么
- ⑤ 眼眶逐渐湿润——泪水积聚使眼球开始泛光，但未流下
- ⑥ 嘴唇微启——停在要说什么的位置——最终闭合
- ⑦ 双肩微微一颤——像被无形的力击中——然后彻底放松下来，认输

环境活动：窗外雨夜城市——远处车灯缓慢移动形成流动光斑。室内完全寂静——禁背景音乐。仅SFX：雨打窗玻璃的细密白噪音、远处城市低频嗡鸣。

禁3D渲染。禁游戏引擎质感。禁CG过场。
禁正面光、禁侧面补光、禁反光板、禁柔光箱。
禁可见光束（god rays）。禁光学畸变。禁鱼眼。
禁漂浮道具。禁身份漂移。禁抖动（呼吸手持除外）。
禁音乐。禁字幕。

[12]秒。9:16。

---
镜头分析：
• 镜头语言：50mm标准镜头+缓推——50mm是最接近人眼自然透视的焦距，缓推在15秒内从全身到特写完成空间压缩，让观众从"观看"角色到"进入"角色内心。
• 构图设计：三分法+框中窗框——角色在左1/3，负空间在右2/3，窗框形成框中框暗示角色被困在某种内在空间中。窗光从右侧投射形成侧逆光，角色正面落入阴影——Deakins式的"从暗侧拍摄"。
• 节奏把控：慢燃弧线——7拍微表演从①静止到⑦认输，呼吸节奏（4秒吸/呼）与镜头缓推同步。15秒无剪辑，让观众无法逃避角色的情绪累积。
```

---

## 5. Multi-Shot Example (3 cuts)

```
【风格参考：Fincher → Richardson】前半段Fincher精密对称冷峻，后半段过渡为Richardson低角度激进高反差。过渡点在角色转身瞬间。

【场景概述】角色A在天桥上被角色B追上。从冷静对话到突然冲突爆发的15秒。

⚠️空间布局：
@image1（角色A）：站在天桥中央，面朝镜头方向。
@image2（角色B）：从画面深处走来，距@image1约5米逐渐逼近至2米。

⚠️本段共3个镜头（参考节奏，非强制）。允许在不改变剧情走向、对白内容与人物形象的前提下，根据实际生成效果灵活拆分、合并或替换镜头。特别地——当某句台词过长、或画面内容过于呆板缺乏变化时，鼓励自行增补反应镜、特写或过渡镜，让节奏更自然；若某个镜头不合理，可直接用更合适的机位与构图替代。硬性限制只有一条：总时长不得超过本段标注的时长，且不得删改台词与系统面板文字。

【镜头1】（Fincher风格）
机位：35mm广角，F4中景深，全景。固定镜头。
构图：对称构图——天桥两侧栏杆形成完美对称消失点，@image1居中。背景城市灯火在纵深尽头。
拍摄角度：平视。
动作：@image1双手插在口袋中，静止背对镜头。远处@image2的身影从纵深走来，脚步声回响。⚠️约5秒后@image2走到距@image1两米处停下——硬切至镜头2。

【镜头2】（过渡镜头）
机位：50mm标准，F2.8中景深，中近景双人镜头。
构图：过肩镜头——从@image2的肩膀后方拍摄@image1正面。@image2的肩背在前景左侧虚化。
摄影机运动：微幅手持呼吸——随两人对话呼吸节奏浮动。
动作：@image1转身面对@image2——这个转身动作是风格过渡点。@image2开口说话时，@image1的眼神从平静变为凝视。
⚠️约5秒后@image1抬手——硬切至镜头3。

【镜头3】（Richardson风格）
机位：24mm超广角，F2.8，中景。极低角度仰拍。
构图：低角度仰拍——角色在天桥夜空背景下显得高大而压迫。天花板（天空）可见。
摄影机运动：激进手持——画面随冲击力度晃动。
动作：@image1一把推开@image2的肩膀——冲击力让两人都后退半步。@image2撞上栏杆。@image1的手停在空中——意识到自己做了什么。
⚠️约5秒。

环境活动：天桥下偶尔有车灯扫过形成光带。远处行人快速经过不回头。夜风可见@image1的外套下摆微动。

禁3D渲染。禁游戏引擎质感。
禁正面光、禁补光、禁反光板、禁柔光箱。
禁可见光束。禁光学畸变。禁鱼眼。
禁身份漂移——两人服装每个镜头完全一致。
禁漂浮道具。禁音乐。禁字幕。

[12]秒。9:16。

---
镜头分析：
• 镜头语言：35mm→50mm→24mm——焦距从环境全景压缩到对话中景再跳到广角冲击，焦距变化本身是叙事工具。固定→呼吸手持→激进手持的运动递进映射情绪失控。
• 构图设计：Fincher对称→过肩→Richardson低角度仰拍——从秩序到冲突的构图叙事。框中天桥栏杆消失点在前半段制造Fincher式压迫感，最后镜头的仰拍赋予暴力以神话尺度。
• 节奏把控：脉冲式——5秒/5秒/5秒等长镜头，但情绪强度递增。对话用中近景平稳呼吸，冲突用广角激进手持——同一时长内信息密度从低到高。最后5秒的静默（手停在空中）是Fincher式的"沉默比暴力更有力"。
```

---

## 6. Prompt Length Guidelines

- **Simple insert / detail shot:** 100-200 Chinese characters
- **Standard single-shot prompt:** 300-600 characters
- **Complex reaction shot with 5+ micro-beats:** 600-1000 characters
- **Multi-shot prompt (3+ cuts) with full blocking:** 800-2000+ characters

Do NOT truncate to be neat. Complex emotional scenes NEED the length because directing performance requires specificity. A vague prompt produces a vague video.

---

## 7. Tone & Voice

Write as a world-class cinematographer who has worked with Deakins, Lubezki, and Fincher. Think in shadows, lenses, and controlled physical reality. Write blocking notes with the muscularity of someone who has actually held a Steadicam.

**FORBIDDEN:** Generic AI-video prose ("a beautiful cinematic shot of...")
**REQUIRED:** Concrete physical specifics ("角色距窗1.5米，重心在左脚，右手垂在身侧握着照片，指节泛白")

The difference between amateur and professional cinematography prompts is specificity. Every number, every muscle, every light source, every meter of distance matters.
