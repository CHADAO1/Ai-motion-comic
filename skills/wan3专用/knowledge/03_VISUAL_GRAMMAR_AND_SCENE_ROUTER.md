# 03 Visual Grammar And Scene Router

priority: high
scope: 画面结构、空间轴线、场景功能、构图、焦点路径、群众调度

## Wan3.0 画面结构优先

Wan3.0 更容易理解可见画面结构，而不是抽象导演词。提示词必须优先描述：

- screen-left / screen-right：画面左侧、右侧有什么，谁从哪边入画或离画。
- foreground / midground / background：前景、中景、后景各自承担什么信息。
- focus path：焦点从哪个主体变到哪个主体，为什么变。
- composition：中心构图、三分法、对称、负空间、遮挡构图、引导线。
- body mechanics：身体部位如何移动，手、脚、肩、头、眼睛、重心分别做什么。
- ending state：每段最后一帧停在哪个空间状态。

### 坐标词典

空间词必须附着到唯一参照系：

| 写法 | 唯一含义 | 禁止替代 |
| --- | --- | --- |
| `screen-left/right` | 当前摄影机画面左右 | 不等于场景东西方向，也不等于角色左右手 |
| `world-left/right` 或命名方向 | 场景平面图/路线方向 | 不随反拍改变 |
| `character's anatomical left/right` | 角色自身左右 | 角色转身后仍是同一身体侧 |
| `in front of/behind the character` | 相对角色身体朝向 | 不直接等于 foreground/background |
| `foreground/midground/background` | 相对当前摄影机的深度层 | 不等于人物面对/背对的方向 |
| `camera-facing/front view` | 摄影机看见人物正面 | 必须由摄影机位置和人物世界朝向共同成立 |

“左移、右移、前进、后退、回头、侧身、绕到后方”必须说明主体、参照物或世界路线，并在需要时补 `toward screen-left/right`、`toward/away from [命名对象]`。不要让模型自行决定参照系。

不要只写“紧张地倒车”。要写：

```text
screen-left metal pipe stays fixed in foreground, midground tractor handlebar moves backward from right to left, background worker's face is hidden by the frame edge; focus starts on the handlebar joint, rack focus to the two-finger gap between neck-height pipe and handlebar, ending with both objects locked in the same plane.
```

### 世界拓扑基础层与摄像机可见投影契约

世界拓扑是所有机位共用的基础坐标层，用于固定门窗、座位、行动轴、路线、主体间距和人物/道具世界状态；它不能因切镜而改变。视频模型的主要画面语言则是该拓扑在当前摄影机中的可见投影。每个 CUT 都执行一次单向编译：

```text
静默世界拓扑/动态状态 -> camera transform C(t): start/path/rotation/speed/end
-> frustum(t) cull -> occlusion(t) resolve -> camera-visible body/prop surfaces(t)
-> image-plane layout P(t) -> foreground/midground/background
-> screen-left/center/right + true background
```

- 新场景或尚未建立的空间系统，`CUT 1` 先把剧情所需的世界拓扑投影成可见建立镜头：可以是 WS/EWS，也可以是能证明主体、关键地标、朝向和间距的 POV/OTS/MS；首镜只证明当前叙事需要的关系，不要求把所有房间坐标塞进画框。（若已提供场景参考图，该世界拓扑/布局/陈设从参考图读取，不自行设计或脑补场景；见 SKILL.md「场景脑补禁令」。）
- `【运镜与时间轴】` 从camera和它实际看见的画框开始，不从人物世界坐标清单开始。世界锚点是基础连续性权威，但只有在建立空间、行动路线或轴线需要消歧时显性出现，并在同一句补出当前画面投影，例如“固定world-east座位在此反拍中投影到screen-left，camera看见人物三分之四正脸”。
- “两人面向黑板”“老师站在黑板前”“角色在门内侧”都只是世界事实。必须继续写camera位于哪里、朝哪里拍、因此看见两人的正面/背面/侧面，谁在screen-left/right，谁遮挡谁，人物身后真正可见什么。
- 画外人物不列入可见人物表。只有其画外声音、进入画框的手/影子/武器、投射光或运动来源影响本镜时，才写该可见/可听证据和来向。
- 改机位、反拍、人物转身或camera移动后，不沿用上一镜画面左右和可见面；从新的视锥与遮挡重新生成当前画框。移动镜头同时写起始可见集、运动中被遮挡/揭示的顺序和终点可见集。
- CUT 是一次连续 camera setup，不是固定机位的同义词。除非明确写 `locked-off camera`，否则按叙事需要选择 dolly/truck/pan/tilt/crane/orbit/handheld 等真实运动，并让 `C(t)` 持续更新视锥、遮挡、screen位置、主体大小、可见身体/道具面与focus；提示词写关键起点、运动路径/速度变化、遮挡/揭示节点和终点，不必逐帧枚举。

### 每CUT动态投影五点合同

每个CUT都用紧凑自然语言包含以下五点，不另起用户可见栏目：

1. **IN起点**：camera世界位置/高度/与主体距离、look direction、yaw/pitch/roll（有功能时）、焦段/景别；主体在世界与画面中的起始深度、screen位置、可见面和当前速度/动作相位。
2. **三维PATH**：camera的dolly/truck/boom/crane/orbit/handheld等物理路径、圆心或目标、横向/纵深/高度变化，以及 `accelerate -> cruise -> decelerate` 或受控through-speed；主体/道具另写自己的三维路线，不能与camera路径混写。
3. **深度跨越**：点名主体/道具何时从background进入midground/foreground，或反向离开；同步给出其相对camera的距离变化、遮挡关系和可见身体/道具面变化。
4. **投影演化**：写screen-left/center/right上的滑移方向、主体画框占比或景别的可见缩放、遮挡物及其覆盖峰值/解除点、focus变化；真实后景写近景快/远景慢的视差方向与幅度，若camera不位移则明确背景稳定、无camera parallax，不伪造视差。
5. **OUT制动/交棒点**：写camera在何种主体-背景关系上减速/稳定、终点画框、focus和主体动作相位。运动切镜可在该控制点保留明确速度向量、方向和screen轨迹交给下一CUT；“制动点”不等于每镜停死。

同一课堂关系的画面写法示例：

```text
不合格：男生在world-east、女生在world-west，两人面向world-north黑板。
合格：camera位于黑板前、眼睛高度朝教室后方拍35mm双人MS；两名学生分别落在screen-left与screen-right，camera看见二人正面和胸前课桌边，二人身后依次是后排同学与教室后墙；老师主观视线在两人之间切换。
```

## 画面结构编译顺序

每个 time beat 按以下顺序写：

1. 拓扑继承/建立：静默继承固定空间；若是未建立的新空间，本镜用可见地标和主体关系完成建立。
2. 摄影机动态态：camera IN起点、look direction、景别/焦段、三维运动路径/旋转/速度轮廓、OUT制动/交棒点；仅在确实固定时写 `locked-off camera` 与零长度路径。
3. 实际画框：前景/中景/后景跨越、screen-left/center/right滑移或缩放、遮挡峰值/解除点、人物身后的真实背景与视差。
4. 可见主体：只列当前入画的人、车、手脚、道具或动物，并写摄影机看见的身体/道具表面与当前任务。
5. 焦点：focus starts on A -> racks to B -> holds on C。
6. 构图：composition type and visual hierarchy。
7. 运镜：一个主要 camera movement；沿 `C(t)` 按揭示/遮挡顺序更新可见集、screen位置和可见面。
8. 动作：身体部位、路线、接触点、速度变化。
9. 结尾状态：最后一帧摄影机看见谁、位于画面何处，危险/信息是否清楚。

## 场景功能路由器

先判断 CUT 的戏剧功能，再决定可读时长、shot size 和 camera movement。

| 场景功能 | 默认画面策略 | 默认声音策略 |
| --- | --- | --- |
| 建立空间 | EWS/WS，清楚入口出口和危险线 | 环境声先行 |
| 角色识别 | CU/MCU，脸、服装、道具锚点 | 呼吸、衣料、轻动作声 |
| 信息揭示 | foreground occlusion / rack focus / tilt reveal | 声音先行或声音变窄 |
| 危险逼近 | fixed danger object + moving subject | 低频、机械声、短静默 |
| 反应确认 | reaction cut / held close-up | 呼吸中断、环境声抽离 |
| 动作冲突 | 中景到全景，路线和接触点清楚 | impact sound + debris/cloth/footstep |
| 尺度揭示 | `camera dollies backward`（焦段固定、主体缩小并显露环境尺度）/ `crane rise`（摄影机实体升高并扩大俯视范围） | 空间回声、低频扩张 |
| 音乐卡点 | marker-based motion accents | beat grid，不牺牲剧情可读性 |
| 产品/科普 | clean locked-off / macro insert | 清晰提示音、无混乱声层 |
| 漫画/动画 | pose clarity + exaggerated silhouette | 风格化动作音效 |

### 四主体以上首秒空间校准

当独立段的第一帧有4个及以上需要分别辨识、定位或跟踪任务的活跃主体，且人物关系、行动轴或任务组尚未在当前冷启动提示词中稳定建立时，允许使用“首秒全景校准”：

```text
CUT 1 开场约1秒，WS/EWS 已经同时收进全部必需主体和稳定地标；按 foreground/midground/background 与 screen-left/center/right 写清每个主体的位置、身体朝向、任务和主要关系线，让场景在进入对白或主动作前完成一次可读空间投影。
```

- “主体”指需要单独保持身份、位置或任务的角色、动物、怪物、车辆或关键运动体；按统一方向和任务行动的无名群众整体计为一个群体主体，具名领头人或独立反应者另计。
- 校准镜不是空 establishing shot。第一帧必须已有主体，可同时承载低幅走位、工作、戒备、环境运动或现场声，但不安排会被空间读取遮蔽的关键台词、接触、爆点或反转。
- 该规则是4主体以上空间高风险时的允许项，不是强制片头格式。3个及以下主体、空间已在当前段可靠建立、承接已验收动作需立即进入新机位，或时长不足时，直接使用最能服务剧情的景别。
- 同一空间完成校准后不在后续 CUT 重复一秒全景；换到新子空间、主体组大幅改变或既往生成已发生位置互换时才重新判断。

## 轴线与空间连续性

### 四层连续性模型

空间连续性和素材控制分成四层，不能混写：

1. **世界拓扑 World topology**：不随 CUT 或机位改变的墙、门、窗、道路、工位排数、座位、桌椅朝向、入口/出口、危险线和行动轴。
2. **动态世界状态 Dynamic world state**：角色和道具的世界位置、距离、朝向、高度、身体姿态、支撑点、动作相位、速度/惯性、握持/接触、装备、损伤和残余 VFX；它从已接受 OUT 继承，再由当前动作更新。
3. **摄影机连续性元数据 Camera continuity metadata**：上一镜摄影机终点、看向、轴线侧、焦段/景别、运动方向和速度阶段；它服务切镜理由、eyeline、动作/运动匹配和过轴判断，不默认成为下一镜摄影机。
4. **画面投影 Frame projection**：由当前 CUT 新指定的摄影机位置和看向方向决定的 screen-left/right、foreground/midground/background、人物正面/斜正面/背面、姿态可见性、遮挡和可见范围。前三层是基础推导数据，其中世界拓扑必须在新空间首镜投影出剧情相关关系；第四层是每个 `【运镜与时间轴】` CUT 的首要可见描述。

### 相邻 CUT/BEAT 空间差分证明门

连续交锋中不能只写正确的两个端点。每次从 `OUT N` 编译到 `IN N+1`，逐主体比较：`世界锚点/距离/高度或台阶级数/深度顺序/支撑点/身体朝向/握持与接触/动作相位/速度`。任何变化必须由以下之一证明：上一镜末端已开始且下一镜从同相位接收的可见位移；当前不间断画面中的完整移动路径与支撑检查点；明确的新camera重投影；或剧情允许且不处于连续交锋中的时间省略。连续攻击、闪避、追逐、摔落、缴械和一镜到底不得用时间省略补瞬移。

- camera保持行动轴同侧且双方没有在世界空间可见交叉时，人物的screen-left/right相对顺序不得翻转。换边必须显示谁从谁的哪一侧经过，或使用中性正轴、可见camera/人物穿轴、top-down轴线中立位，再按新机位重建投影。
- 台阶、平台、门柱、桌面、车辆、枝干等离散支点必须使用同一命名和层级口径。`第2级OUT -> 第1级IN`需要上一镜已起步或下一镜可见完成这一步；“柱旁/外侧/里面”改写为命名柱面、world方向和实际接触面。
- 画面遮挡可以隐藏局部动作细节，不能抹去改变世界位置、支撑、持械归属或接触拓扑所需的证据。若变化无法由当前镜头证明，调整路径、扩大景别、增加有动机的接力CUT，或保持原状态。

静态末尾帧可以作为观察证据，把直接可见的站位、朝向、姿态、支撑、握持/接触、损伤和残余状态更新到动态世界状态；单帧不能证明速度、惯性、画外动作或声音。它作为下一段 `@图片` 时仍只授权角色世界站位与相互距离，不能向画面投影层提供参数。下一段 `CUT 1` 必须以“解除旧画面投影控制”为理由 `hard cut/direct cut` 到新摄影机起点、看向、焦段和景别，并用世界站位、matched eyeline 或视觉重心承接，不虚构动作匹配或遮罩；角色身份从原角色参考/文字恢复，场景从原场景文字、已验收场景设定或原始场景图恢复，开场姿态/动作相位由动态世界状态和当前剧本用文字重锚，再由新机位重新计算人物角度、姿态可见性、遮挡、前中后景与 screen-left/right。

`background` 永远相对摄影机定义，不相对人物定义。人物面对某扇门，只说明门位于人物身体前方；门能否成为画面背景，取决于摄影机是否位于人物身后并朝门拍。摄影机改到门一侧反拍人物正面时，门通常位于摄影机后方或画外，人物的画面背景应变为其身体后方的工位、墙面或其他真实空间。

### 主体-道具-摄影机可见面

“人物朝向、脸朝向、目光、道具朝向”是四个相互关联但不能互相替代的方向。对手机/显示器/书页、枪械、刀剑、盾牌、门、容器开口等有明确正反面或功能方向的对象，每个相关 CUT 静默计算：

```text
人物身体前向与脸/目光 -> 道具握点和功能面/功能方向 -> 动作目标
-> 摄影机位置与look direction -> 摄影机实际看见的人物面和道具面 -> 遮挡关系
```

- 人物正面朝摄影机、手机位于人物与摄影机之间且屏幕朝人物时，摄影机应看见手机背壳/摄像头面；要看见屏幕，必须把摄影机移到人物肩后/侧后，或明确人物转腕把屏幕朝向摄影机。
- 射手位于摄影机与目标之间、身体朝目标开枪时，摄影机应看见射手背面/斜背面，枪口沿射线背离摄影机指向目标；只有摄影机明确位于目标一侧并沿射线反拍射手时，枪口才可能朝向摄影机。
- 脸或眼睛可以在合理颈部范围内偏离躯干，手腕也可以旋转道具；一旦使用这种例外，必须写清改变方向的身体部位、角度结果和新的可见面，不能只靠“看着/拿着/对着”让模型猜。
- camera、人物身体或道具任何一个发生转动/移位后，都重新计算人物正面/侧面/背面、道具正面/背面/侧面、功能方向、目标与遮挡；不能把上一 CUT 的可见面直接复制到新机位。
- 可见面字段只写当前frustum内可见的主体/道具，或方向直接影响画内动作的画外来源；纯画外人物只在世界状态账本保留朝向，不为完成审查而强塞入画框。
- `toward screen-left/right` 只说明二维画面位移，不自动表示人物绕竖轴转身。侧倒、横移或滑行后，除非明确写出torso/head/wrist yaw，摄影机仍看见原来的身体/道具面，只是它在画面中平移、倾斜或滚转。
- OUT分别更新三件事：主体新位置与可见面、方向性道具当前功能方向、目标当前是否仍位于该方向线上；再按新深度重叠核对遮挡扩大、收窄或解除，不能从“倒向一侧”直接推导转身、重新瞄准或遮挡消失。

每个复杂场景先建立静默连续性账本：

```text
世界锚点：后墙左侧门；三排工位；角色A在靠后第二排左位；角色A身体朝后墙。
动态尾态：角色A右脚承重、左手握住门把、躯干向门侧扭转；门打开三十度。
行动轴：角色A <-> 后墙门，或角色A <-> 对话角色B。
摄影机尾态：上一镜位于办公室前侧、50mm MS、沿轴线右侧缓慢横移到停止。
```

每个 CUT 再执行摄影机变换：

```text
继承世界拓扑与动态 OUT -> 读取上一镜摄影机尾态决定切镜/轴线策略 -> 指定新摄影机起点/所在侧与看向 -> 视锥裁切/遮挡 -> 人物正背侧面与道具可见面 -> 入镜固定物/真实后景 -> 前中后景 -> screen-left/right -> 视线与运动方向
```

上述链条是内部验算顺序。写给模型时从 `新camera + 画面实际包含什么` 开始，不把前端世界坐标推理原样输出。

办公室示例：

- 摄影机位于办公室前侧并朝后墙拍：角色A背对/斜背摄影机，后墙门可位于 background。
- 摄影机位于后墙一侧并朝办公室前侧反拍：角色A正面/斜正面，后墙门位于摄影机后方或画外，角色A背景是更靠办公室前侧的工位与同事。
- 摄影机位于角色A肩后：角色A肩背在 foreground，门可在 background；只有这个几何条件成立时才能写“角色面对的门位于背景”。

### 逐 CUT 画面可重建门

段落总表中的世界站位不能替代逐 CUT 声明。每个 CUT 都要用紧凑正向事实建立当前地点、画框和人物状态；多人、对白、门洞/门槛、相邻房间、人物依次入场、交接道具、正反拍或既往出现对象误配时，字段必须显式展开：

```text
地点/子空间与场景状态 -> 摄影机位置/看向/景别与视锥
-> 实际画框内容/真实后景 -> 逐个可见人物的画面位置/可见面/任务
-> 对白对象 -> 主变化、同步辅助变化、焦点与 OUT
```

1. **地点与场景状态**：每镜点名当前地点和具体子空间，例如“旧办公室后排靠门工位/雨夜”；写当前固定结构与动态环境状态，不用空泛场景名代替画面。
2. **摄影机与视锥**：写 camera position、look direction、axis side、lens/shot size，再列出当前视锥实际收进的人物。先以摄影机为主语确定“它看见谁/什么”；对前一 CUT 已活跃但本 CUT 不入镜的主体，只在确有误入风险时补最短裁切/遮挡原因。
3. **实际画框与真实后景**：按摄影机实际看到的顺序写 foreground/midground/background 与 screen-left/center/right。后景只能来自当前look direction内、位于可见人物身后的真实固定物和人群，不能因剧情重要自动出现门、走廊、工位或第三人。
4. **逐人可见状态**：只对当前frustum内的人物逐名写 depth plane、screen position、camera-visible body side、脸/目光方向、遮挡、道具接触和当前任务。方向性道具再写摄影机可见面、功能方向和目标。世界锚点留在台账；若必须出现，立即配对当前画面结果。
5. **人物任务与表演状态**：所有可见具名人物都有当前任务和一条可读表演基线；说话者、听者、第三人与后景人物可同步保持不同强度的动作/姿态，不把并存状态写成依次表演。
6. **对白归属**：有台词时写“角色A看着角色B并向角色B说”，同时写角色B视线或反应如何接收。可见第三人必须有独立位置、目光和低幅任务，不能占据角色A的视线终点。
7. **主变化与 OUT**：只设一个同等级剧情变化；地点、站位、姿态、场景状态和表演基线是支撑该变化的同步事实，不计为额外主变化。OUT 保留完成后的可见站位、朝向、接触、构图、焦点和环境状态。（站位脑补禁令：若提供了站位参考图，本条要求逐 CUT 声明的角色相对位置/朝向/间距/队形/分组一律以该图为准，不自行臆想或另编一套站位；只补写参考图未覆盖的时间维走位与动作相位。图锁的是世界站位，不锁摄影机——screen-left/right、人物正背面、前后景仍按当前新机位重新投影，禁止直接复制参考图画面左右/前后景。仅在无站位参考图时才自行设计站位。详见 SKILL.md「站位脑补禁令」、`knowledge/02` 末尾帧证据/控制分离路由第 7 条。）

简单单人 ECU/CU 可把字段自然合并成一段，不机械暴露字段名；但仍要点名地点/子空间、主体位置与可见部位、摄影机从哪边看、画框实际包含什么、真实后景、表演状态、当前动作对象和 OUT。

### 多轴分离与隐式对白配对

同一场景可同时存在多条轴，但不能把它们当成一条：

- **dialogue axis**：当前说话者与目标听者之间的线。
- **threshold/observation axis**：人物与门洞、窗、监视目标或相邻空间之间的线。
- **handoff/task axis**：人物与行李、文件、工具或交接对象之间的线。
- **movement axis**：人物或载具的世界路线。

相邻的正反打、过肩、reaction cut 和 matched eyeline 会让视频模型自动建立“谁对谁说”的配对。若角色A台词后切到角色C的近景，且角色C位于A的视线终点，即使文字声称A对角色B说，角色C仍会成为最强听者候选。按以下顺序修复：

1. 先用稳定世界锚点建立角色A与角色B的唯一对白轴，并让双方 reciprocal eyeline 清楚成立。
2. 把角色C放到对白摄影机后方、侧后方或明确的画外世界位置；若角色C仍入镜，给其非对白任务和不与A闭合的视线。
3. 需要三人同场时，先用可读的三人构图建立三角关系，再进入局部镜头；不要让第三人的独立 reaction cut 冒充对白反打。
4. 如果门洞、第三人或剧情道具始终比目标听者更像对白对象，导演层应改调度、先结束门口/交接轴，或把对白迁移到能提供动作动机的新场景。空间设计优先于堆叠限制句。

### 门洞与局部特写边界

- 门洞先锁 threshold plane：摄影机在门内还是门外、门向哪侧开启、人物位于门的哪一侧、开门后门洞实际显露什么。
- 锁孔、门把、手、脚、鞋或道具 insert 只控制该 CUT 的局部构图和动作终点，不自动延展为同机位跟随、穿门或绕到人物背后。
- 下一 CUT 是新 setup 且需要阻止局部画面自动延展时，明确有动机的 `hard cut/direct cut`、新 camera world position、look direction、shot size、身份可读画面和动作/视线/视觉重心/声音接力。若同一 CUT 要从局部连续揭示人物，必须写清 camera path、揭示顺序和终点构图。
- 身份关系重要时，默认使用能同时看见脸/发型/服装锚点与动作部位的膝上、腰上或中近景。孤立脚部/手部特写只有在所有权已由同一连续画面明确建立，或道具/服装特征足以唯一识别时使用。

### 继承与过轴规则

- 180 degree rule：先锁角色-角色、角色-门、角色-危险物或运动路线形成的行动轴，再锁摄影机位于轴线哪一侧。常规 CUT 保持同侧；过轴必须使用中性正轴 CUT、可见摄影机/人物移动穿轴、明确空间再建立或用户指定的有动机越轴。
- eyeline match：角色世界朝向不因切镜改变。新机位需要重新计算画面中的视线方向，不能机械复制上一镜的 screen-left/right。
- screen direction：继承的是世界运动路线和轴线侧，不是上一镜的文字标签。每次反拍、侧拍、俯拍后都从摄影机变换重新计算 screen-left/right。
- entrance/exit：入口和出口的世界位置固定；入画/离画边随机位变化重新计算。
- danger line：机器、车辆、刀具、金属管、悬崖、门缝等危险线先锁世界位置，再计算它在当前画面的层级和方向。
- 已验收锁：用户确认过的门窗位置、排数口径、人物座位/朝向、通道和轴线进入连续性正史。后续 CUT 与独立段必须继承；只有用户修改场景或后续 CUT 明确展示世界位置变化时才能更新。
- 参考场景图可以锁世界拓扑、材质和已见布局，但不能迫使所有新机位沿用参考图的前景/背景或 screen-left/right。新角度必须按同一拓扑重建画面投影。反过来（场景脑补禁令，最高优先级）：既然场景参考图承载世界拓扑/材质/已见布局，有场景参考图时就不得自行设计、改写或脑补一个与参考图不同的场景——建筑结构、门窗位置、陈设/家具、材质、光线氛围、时代与地域风格一律以参考图为准，也不复述参考图已载明的陈设外观；只有原文字面写明或参考图直接可见可证的场景事实才可引用，无出处留白交给参考图。只有参考图未覆盖的新增可见世界事实或动态状态（如桌上多了一把刀、灯被打碎、地面湿滑）才另写文字行补充，且不推翻已确立的固定拓扑；角色站位/走位/朝向属位置关系，不算场景设计。仅在无场景参考图时才自行构建最小充分世界拓扑。详见 SKILL.md「场景脑补禁令」。
- 每次相邻CUT/BEAT接力同时执行“空间差分证明门”；过轴解决的是camera投影，不会自动证明人物已经换位、上阶、落地、松手或移动到新支点。

## 构图模板

| 构图 | 用途 | 提示词写法 |
| --- | --- | --- |
| centered composition | 英雄、威胁、仪式、产品 | subject centered, background symmetry locks attention |
| rule of thirds | 日常、对话、纪录感 | face on left third, empty danger space on right third |
| negative space | 孤独、未知威胁 | subject small in lower-left, empty dark space dominates upper-right |
| foreground occlusion | 偷看、转场、压迫 | foreground object wipes across frame, revealing subject behind it |
| leading lines | 路径、命运、危险 | greenhouse pipes form converging lines toward the danger point |
| deep staging | 多人、多层信息 | foreground tool, midground character, background threat all readable |
| top-down map | 群体、路线、困局 | 90-degree top-down view shows escape routes and blocked path |
| low-angle dominance | 权力、巨物、机器压迫 | low-angle frame makes machine fill upper half of image |

## 群像与调度

群体不能随机乱动。必须写：

- 主方向：人群总体向哪里移动。
- 反方向：谁逆流、谁停住、谁回头。
- 拥堵点：门口、桥口、摊位、车辆旁、台阶。
- 逃生路线：哪条路可走，哪条路被堵。
- 反应层级：前景惊慌、中景推挤、背景迟疑或围观。
- 持续锚点：如果人群、后景人物、路人、围观者、队伍或兽群已经进入画面，后续 BEAT、切到 WS/EWS、切回全景或切到 reaction cut 时必须重复他们的位置、密度和方向。后景可以虚化，但要写成“background crowd remains softly blurred but visible”，不能让人群无故消失。
- 变化理由：人群离开、散开、被遮挡或被 frame crop 排除时，必须写清离开方向、遮挡物、裁切边界或剧情原因。

提示词：

```text
crowd blocking is directional: most villagers run from screen-right to screen-left toward the field exit, one elderly man moves against the flow in midground, foreground workers stop at the blocked dirt path, background harvester remains a fixed heavy mass.
```

全景/后景持续写法：

```text
WS wide shot: foreground villagers keep pushing toward the narrow exit, midground protagonist stands against the flow, background crowd remains softly blurred but visible across the market lane, density stays high and no background extras disappear between cuts.
```

## 美术与生活痕迹

场景不要空。每个场景至少有 3 类生活痕迹：

- 使用痕迹：泥、灰、磨损、划痕、油污、脚印。
- 阶层差异：衣料、工具、家具、交通工具的新旧程度。
- 文化逻辑：材料、符号、颜色、宗教或地方工艺要一致。
- 道具用途：道具必须服务剧情，不做随机装饰。
