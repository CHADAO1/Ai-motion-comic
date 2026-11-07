# 07 Style Genre Famous Scene Compiler

priority: medium
scope: 用户说“感觉像某名场面”时的静默机制、类型场景语法、视觉冲击与反转

## 版权边界

可以学习机制，不能复制具体电影人物、台词、造型、场景和精确 CUT 顺序。输出时把“像某片”的感觉翻译为可迁移的视听结构。

## 名场面感觉编译器

| 用户感觉 | 可复用机制 | 提示词内核 |
| --- | --- | --- |
| 闪灵砸门式压迫 | 封闭空间、门作为薄弱边界、重复冲击、受害者反应 | `threshold horror: locked door dominates foreground, repeated impacts deform the barrier, reaction cut to trapped face` |
| 教父式权力压迫 | 低调光、稳定构图、说话者低幅掌控、对方紧张 | `low-key interior power scene, seated figure slowly turns a ring once, practical lamp side-light, listener's tightening hands reveal fear` |
| 黑客帝国子弹时间 | 时间冻结、轨迹可见、环绕视角 | `bullet-time freeze; debris and fabric remain suspended while the camera orbits the named contact point through a 180-degree arc` |
| 斯巴达 300 式图形动作 | 高反差剪影、slow-fast-slow、队形冲击 | `graphic combat silhouette, speed ramp from slow anticipation to fast strike to slow aftermath` |
| Mad Max 追逐 | 中心动作向量、车辆方向清楚、因果快切 | `center-framed chase vector; hold one readable screen direction until an explicit neutral re-establishing shot; each cut confirms distance and damage` |
| Spielberg wonder | 先看反应，再揭示奇观 | `reaction first, warm backlight on face, then tilt up reveal to impossible scale` |
| Nolan scale dread | 小人物对巨物、低频、几何压迫 | `tiny human figure against a massive structure, large-format deep-space composition, low-frequency pressure` |
| Kurosawa weather drama | 风雨/尘土塑造冲突方向 | `wind and rain show emotional force, fabric and dust move with conflict direction` |
| Wong Kar-wai longing | 近距离、慢速、遮挡、色彩记忆 | `close obstructed framing; camera trucks laterally at low speed while saturated practical color and delayed reaction carry memory` |
| Tarkovsky dream drift | 长镜头、自然元素、时间变慢 | `one continuous slow stabilized tracking shot with a defined route; water, fire or wind texture carries memory` |
| Fincher procedural tension | 精确构图、冷色、控制感 | `precise locked-off composition, cool practical light; camera subtly dollies toward the evidence with focal length fixed` |
| Villeneuve monumental silence | 巨物、负空间、低频、少动作 | `vast negative space, restrained movement, sub-bass rumble, human scale overwhelmed` |
| John Woo standoff | 双方对称、道具指向、慢动作前奏 | `symmetrical standoff, weapons or hands aim across centerline, slow-motion fabric movement before action` |
| Bourne handheld panic | 近距离、读得清的手持、身体接触 | `handheld close combat, readable center subject, shoulder hits wall, quick reaction inserts` |
| Ghibli quiet magic | 日常细节、风、食物、温柔奇观 | `domestic texture, soft wind, small magical exception color, childlike wonder` |
| Pixar clarity | 动作姿态清晰、表情可读、因果强 | `clear pose silhouette, expressive eyes, one action idea per beat` |
| Anime impact frame | 极短定格、速度线、强轮廓 | `single impact pose, graphic speed streaks, sharp silhouette, then debris follow-through` |
| Disaster movie reveal | 正常生活被远处异常打断 | `ordinary foreground activity, background anomaly grows, sound arrives late` |
| Heist precision | 工具、时间、手势、静默 | `macro inserts of tools, synchronized hand signals, ticking sound bridge` |
| Psychological collapse | 空间变形、主观声音、焦点转移 | `camera dollies backward while zooming in to hold face size; ambience becomes muffled; rack focus transfers from the face to the named empty doorway` |

## 视觉反转机制

反转不是台词解释，而是画面信息顺序变化：

- 安全物变危险物：日常道具突然对齐成危险线。
- 背景变主体：background threat becomes focus.
- 主观误判：POV 看不见，客观 CUT 显示观众看见。
- 声音欺骗：听到安全提示，却被环境声盖住。
- 关系反转：保护者变阻挡者，逃生路线变封闭路线。
- 尺度反转：看似小问题，摄影机保持焦段并实体后移 `camera dollies backward`，显露巨大系统性危险。

提示词：

```text
visual reversal: the harmless rice stalks in foreground become the object that hides the blind-zone figure; focus racks through them only after the machine begins reversing.
```

反转必须改变至少一种状态：观众认知、角色认知、危险等级、权力、尺度、行动选项或后果。静默层记录“初始假设 -> 隐藏事实 -> 揭示载体 -> 反应归属者 -> 新 OUT”，再选择下表：

| 反转类型 | 视觉/剪辑机制 | 新状态要求 |
| --- | --- | --- |
| 危险线显现 | foreground/midground/background 重新对齐，或 `rack focus` 从无知主体转到危险线 | 原本安全的路线被证明会发生接触 |
| 道具价值翻转 | 道具 insert -> 反应 -> 更宽关系构图 | 普通物成为证据、武器、记忆、陷阱或通行条件 |
| 安全空间变陷阱 | `locked-off camera` 先建立日常秩序，门、窗、机器或人群随后改变状态 | 至少一条退路被可见地关闭 |
| 画外原因/画内后果 | 声音先行 -> 环境物受力 -> 人物反应 -> 延迟揭示来源 | 观众先确认力量存在，再确认来源 |
| 假胜利 | 结果成立后短暂停留，background、道具或身体状态显露代价 | 胜利变成更严重的问题 |
| 延迟后果 | 接触 -> 短暂静止/声音抽离 -> 材料、身体或空间结果 | 接触和后果的因果仍清楚，延迟只增强重量 |
| 尺度反转 | 从个人细节 `camera dollies backward`（焦段固定）或 `crane rise` 到完整几何 | 私人问题变为群体、系统或灾难尺度 |
| 权力交换 | 高低、门口、座位、桌面、证据或沉默的控制权发生交换 | 被动方获得行动权，原控制者失去选择 |
| 信息不对称 | 观众看见 background 线索，角色仍执行错误行动；或 POV 缺失后切客观证据 | 明确谁知道、谁不知道、错误行动因此继续 |
| 道德翻转 | 动作结果后把持镜时间交给真正承担代价的人 | “成功/失败”的意义被反应重新定义 |

## 实战分镜结构路由

这些是静默结构，不是固定剧本。只在剧情机制匹配时选择一套主结构；把角色、地点、道具、台词和结局全部替换为当前故事事实。最终仍按 `06_TIMELINE_EDITING_SOUND.md` 编译为独立段和 CUT。

| 套路 | 适用情节 | 静默结构 |
| --- | --- | --- |
| 面对面遮挡揭示 | 相遇、谈判、告白、对峙 | 从A背后跟随 -> A身体遮住前方对象 -> 摄影机侧向 `lateral truck` 移开遮挡显露B -> A单人/B单人/双人关系 -> 人物离开后让中心道具或空位承担余味 |
| 决斗时间拉伸 | 一次决定性攻击、高手对峙 | 不只展示命中；用武器、脚步和手部三类预载 insert 延长准备 -> 主动方接触前 CU -> 公平双人关系构图确认接触与结果 |
| 四级逃生 | 追逐、被围、动作喜剧逃亡 | 就地道具解围 -> 新障碍进入唯一逃生路线 -> 高度落差迫使犹豫 -> 增援从明确 screen direction 封堵；只有进入生死逃跑后才切换 `follow/lead tracking` |
| 告别空间分离 | 分手、离队、离家、艰难决定 | 道路、门框、树或高低地形把两人分区 -> 离开者的路线与留下者的阻挡同时可读 -> 决定后保留短暂沉默和距离扩大 |
| 人质救援/神秘来援 | 营救、惩罚、英雄登场 | 先显示压迫行为及受害者代价 -> 武器/影子/风/光先于救援者入镜 -> 每次制服后给对方反应 -> 最后才完整揭示救援者身份 |
| 弱者起身 | 弱小角色保护他人 | 弱者从遮挡后进入 -> 高机位显示其劣势、低机位显示压迫方 -> 对话通过重复高低关系推进 -> 即使失败也必须获得一项可见的道德或空间成果 |
| 重复任务蒙太奇 | 工作、训练、投递、日常压力 | 先完整展示一次动作 -> 用地点、道具、方向、景别变化重复 -> 中段插入一个较慢的真实障碍 -> 以开场动作或构图回环，但状态已改变 |
| 败北到转化 | 觉醒、重生、变身、能力开启 | 身体失去行动能力 -> 外部压力或真相逼近 -> 主观空间/记忆触发 -> 回到现实的局部变化 -> 变化沿材料或身体传播 -> 环境与旁观者确认代价 -> 新形态定格 |
| 街角寻人 | 目标丢失、城市追逐、错过 | 角色在路口停下并分别检查两条可见路线 -> POV 搜索失败 -> 高度、隧道或遮挡重排焦点 -> 重新发现目标 -> 由 `lateral tracking` 与自然遮挡压缩距离 |
| 不可能人物到场 | 死者归来、证人出现、卧底现身 | 画外人声或局部身体先出现 -> 逐步扩大可见信息 -> 反应者保持客观机位，异常主体可用极高/低机位 -> 脚步和停顿证明空间，不用无来源瞬移 |
| 规划型长镜头 | 走廊、桥、办公室、人物汇合/分离 | 选择天然路线 -> 空场 `locked-off camera` 起步 -> 人物入画后摄影机只为构图和信息变化移动 -> 预设停、谈、分开、道具 cue、离画等内部 BEAT |
| 物件与镜中独白 | 自我对话、告解、排练 | 台词下先给3-4个道具 insert -> 说话者朝摄影机方向说话 -> 摄影机实体后移显露镜面，证明其在自言自语 -> 手部任务承载语气 -> 镜边新人物/物打断 |
| 平行欲望/色物关联 | 三角关系、诱惑、回忆冲突 | 一条现实动作作节奏骨架 -> 在动作接点插入两条平行空间 -> 每段关系绑定一种颜色/物件/材质 -> 重复“动作局部 -> 面部 -> 另一空间”显示内心权重 |

补充导演结构：

| 结构 | 核心顺序 |
| --- | --- |
| 反应先行揭示 | 声音/异常 -> 角色反应 -> 局部细节 -> 环境受力 -> 完整揭示 -> 最终反应 |
| 灾难预兆 | 环境异常 -> 道具异常 -> 动物/群体异常 -> 人类认知 -> 第一物理后果 |
| 威胁轨迹认知 | 观察异常 -> 判断路线 -> 计算后果 -> 恐惧进入身体 -> 发出警告/行动 |
| 人类代价 insert | 每个 insert 只承载一个具体人物的选择或损失，避免抽象“群众受难” |
| 四拍救援 | 失误/滑落 -> 抓取点 -> 双方受力与代价 -> 救援成功或失败的新状态 |
| 横版动作路线 | 主体保持单一 screen direction：奔跑 -> 一次接触 -> 继续移动 -> 第二障碍 -> 结果 |
| 机械孤独弧 | 重复任务 -> 私人微小庆祝 -> 故障/惊吓 -> 发现同伴或新目标 -> 温柔的新日常 |

## 蒙太奇与时间扭曲

| 技法 | 用途 | 写法 |
| --- | --- | --- |
| rhythmic montage | 训练、准备、调查、事故前奏 | `short rhythmic CUTs of hands, tools, warning sign and machine vibration; each CUT carries one readable clue` |
| intellectual montage | 概念对照 | `cut from locked gate to clenched hand to silent machine panel` |
| emotional montage | 情绪累积 | `faces, objects and empty spaces repeat with rising sound` |
| time compression | 压缩漫长过程 | `morning light shifts to noon through three match cuts` |
| slow-motion insert | 强调关键因果 | `slow-motion insert on the lever snapping backward` |
| speed ramp | 动作冲击 | `normal motion, sudden slow at contact, fast debris burst` |
| bullet time | 超现实冲击 | `time freezes around the named impact point; camera orbits that point through a specified arc while dust remains suspended` |
| Hitchcock dolly zoom | 认知恐惧 | `dolly in while zooming out, background stretches away from the face` |

## 类型场景语法包

事故/安全警示：

```text
客观纪实质感，先建立危险几何关系，先让观众看到盲区，再发生接触，不渲染血腥，后果用停顿、静默和物体状态变化表达。
```

恐怖：

```text
低调动机光，先用画外声音引出危险，保留负空间，延迟揭示威胁，先给反应再给完整威胁。
```

动作：

```text
route, contact point, counter, reversal, impact, consequence; center action vector and keep screen direction stable.
```

产品/科普：

```text
clean locked-off composition, macro inserts, high-key lighting, readable material response, no narrative clutter.
```

漫画/动画：

```text
clear silhouette, pose-to-pose action, exaggerated timing, readable VFX, final held pose.
```

音乐卡点：

```text
use audio as beat grid; for 单镜模式 mark roughly 3-6 motion accents, while 多镜模式 may use roughly 5-10 across a 30-second structure. These are planning ranges rather than hard counts; avoid sacrificing story readability for every beat.
```

神迹/灾难：

```text
large-format deep-space composition, tiny human foreground, huge background force, low-frequency rumble, slow reveal then sudden consequence.
```

悬疑调查：

```text
macro clue insert, controlled camera, cool practical light, J-cut from clue sound to investigator reaction.
```

情感文戏：

```text
soft warm skin rendering, gentle highlight rolloff, restrained camera movement, face and body actions written separately, silence or room tone carries hesitation.
```

## 生物揭示、灾难、喜剧与转化

生物具体物理按 `05_ACTION_PERFORMANCE_BODY_MECHANICS.md` 的“生物与威胁物理路由”执行；本节只决定叙事显现顺序。

- 生物揭示：声音/环境异常 -> 反应 -> 局部身体或痕迹 -> 环境受力 -> 完整体型 -> 最终反应。不可见力量则用物体受力和声音替代身体局部。
- 山体即生物：先让地貌的一处细节移动，再让阴影、尘土和地平线发生连锁，最后才让观众理解整体是活体。
- 灾难升级：预兆 -> 第一物理变化 -> 个体反应 -> 群体主方向形成 -> 逃生路线拥堵 -> 结构失效 -> 余波中的具体物件/人物。
- 喜剧动作：人物以严肃目标执行完整动作，笑点来自结果不匹配、晚半拍反应、道具失效或时机反转；摄影机不额外乱晃替角色制造笑点。
- 转化/变身：变化前身份锚点 -> 触发接触 -> 局部材料/身体变化 -> 沿明确路径传播 -> 结构组装或形态完成 -> 代价/环境反应 -> 可读终态。每一步只改变已点名区域，脸、服装和身体结构的连续性由素材锁定决定。
- 表面群袭恐怖：微小表面征兆 -> 局部破裂/涌出 -> 群体沿明确主方向传播 -> 身体与环境反作用 -> 逃生/封堵结果；不把密度写成随机粒子。
