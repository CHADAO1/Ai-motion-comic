# 04 Camera Light Color Style

priority: high
scope: 基础风格、camera、lens/focal length、shot size、camera movement、光线、色彩、画家/流派语义编译

## 使用边界

本文件是静默参考库，不是最终输出模板。最终回答必须按 `01_CORE_EXECUTION_CONTRACT.md` 的中文输出格式写，不要把本文件里的英文表头、英文示例或表格结构直接复制给用户。英文只保留必要技术短语，例如 `slow dolly in`、`rack focus`、`IMAX 65mm language`。

## 基础风格写法

`【基础风格】` 是 Wan3.0 提示词的高优先级模块，每个独立段落都要出现。它紧随置顶的 `【角色/场景/素材锁定】`，并位于 `【运镜与时间轴】` 之前；它不是一次性总说明。

写法规则：

- 每段明确写出摄影机系统与感光/画幅基准。真人/写实画面点名具体 cinema camera 或胶片画幅；动画、动漫、游戏和纯CG写 `virtual cinema camera` 与等效 Super 35/large-format 等画幅，不伪装实拍元数据。
- 每段重复项目级统一基调：摄影机、画幅、lens rendering、焦段/景深倾向、扩散/高光、色彩关系、黑位、颗粒与材质基线。
- 每段补充本场景变化：动机光源、方向、主光与环境/practical色温、光比、阴影/negative fill、天气/空气介质、空间材质和情绪反差。
- 不允许后续段落只写“同上”“沿用上一段风格”。如果要保持统一，就写“延续 [项目级基调]，本段改为 [具体场景变化]”。
- 风格参考、画家/流派参考也写进这里，转换成线条、色彩、构图、质感和光线，不单独开素材说明栏目。
- `真人电影风格`、`电影级调色`、`暖光`、`冷光`、`高级质感`只能作为完整技术描述后的摘要，不能单独成段。

### 基础风格最小技术包

1. **Capture**：camera body/film or virtual camera + sensor/film format + aspect ratio。
2. **Optics**：lens family/rendering + focal tendency + depth of field + diffusion/halation/highlight rolloff；flare/畸变只在有用途时写。
3. **Lighting/exposure**：motivated key/fill/practical + direction + key/ambient color temperature + intensity + shadow hardness + negative fill + contrast ratio。
4. **Atmosphere/depth**：空气清晰度、haze/烟尘/湿气、空气透视或体积光，以及前中后景的实际结果。
5. **Surface/texture**：skin/material microtexture + grain + roughness/specular；按材质条件加入 anisotropy、caustics、湿润反光或尘土吸光。
6. **Color finish**：palette relation + saturation + warm/cool separation + black point/toe + highlight behavior + LUT/stock-like visible result。

每项可以压缩成短语，但不能缺项。CUT 内仍负责具体景别、焦段与光线事件；它们不能反向替代 `【基础风格】` 的项目采集与成像基线。

推荐句式：

```text
摄影机/画幅：[camera body or virtual camera] + [sensor/film format] + [aspect ratio]。
镜头/成像：[lens family] + [focal tendency] + [depth of field] + [diffusion/highlight/flare/distortion]。
受光/曝光：[motivated sources] + [direction] + [key/ambient color temperature] + [shadow/negative fill] + [contrast ratio]。
空气/纵深：[air clarity or medium] + [aerial perspective/volumetric result]。
材质/质感：[skin and material microtexture] + [roughness/specular/anisotropy/caustics when supported] + [grain]。
色彩/收尾：[palette relation] + [saturation/warm-cool] + [black toe/highlights] + [LUT/grade result]。
```

## 摄影机与光学镜头风格库

| 风格组 | 适合题材 | 画面特征 | 提示词写法 |
| --- | --- | --- | --- |
| ARRI Alexa 35 + Cooke S8/i | 高级剧集、人物文戏、自然高光 | 柔和皮肤、圆润高光、轻微温暖、情绪可信 | `ARRI Alexa 35 feel, Cooke S8/i lens warmth, 35mm or 50mm, gentle highlight rolloff, natural skin tone` |
| ARRI Alexa LF + Panavision Ultra Panatar | 史诗宽银幕、沙漠、巨物、宏大空间 | 大画幅、宽银幕、压迫尺度、空间纵深 | `ARRI Alexa LF large-format look, Panavision Ultra Panatar wide-screen language, 2.76:1, distant scale reveal` |
| Sony Venice 2 + Panavision Primo 70 | 科幻、夜景、城市、冷调高动态范围 | 冷调、干净、夜景细节、霓虹高动态 | `Sony Venice 2 high dynamic range night look, Primo 70 lenses, crisp urban highlights, cool cyan shadows` |
| RED V-Raptor XL + Atlas Orion Anamorphic | 广告、动作、锐利强质感 | 锐利、对比强、横向 flare、速度感 | `RED V-Raptor XL sharp texture, Atlas Orion anamorphic flare, high-contrast action commercial energy` |
| IMAX 65mm / 70mm language | 神迹、灾难、宇宙尺度、巨物 | 超大尺度、垂直震撼、清晰空间层级 | `IMAX 65mm/70mm scale language, immense vertical space, ultra-clear foreground-to-background depth` |

每个独立段的 `【基础风格】` 必须写摄影机系统；不要在该段每个普通 CUT 重复摄影机型号。摄影机/光学镜头品牌只作为视觉特征速记，不代表真实拍摄设备或元数据；必须同时写出可见的高光滚降、肤色、锐度、flare、对比、边缘和纵深特征。目标模型对具体品牌词理解不稳定时，仍保留明确 camera class/format 和这些可见特征，不能把整项删成“真人电影风格”。

### 焦段 + FOV 补充锁定

FOV 不代替焦段。默认仍按“焦段/光学特征 + 摄影机物理距离 + 景别 + 可见透视结果”编译；只有画面边缘覆盖、超广角直线保持、远距离压缩或平台对角度语言响应更明确时，才补充 `diagonal field of view`。

全画幅等效下可使用以下近似对照，数字只用于避免自相矛盾，不作为每个 CUT 的必填项：

| 焦段近似 | 对角 FOV 近似 | 可见结果 |
| --- | --- | --- |
| 310mm | 8° | 极强长焦压缩、远距离观察、前景遮挡明显 |
| 135mm | 18° | 长焦隔离、背景明显压缩、浅景深倾向 |
| 85mm | 29° | 短长焦人像、面部比例稳定、背景靠近 |
| 50mm | 47° | 自然标准透视、空间比例中性 |
| 24mm | 84° | 广角空间扩张、摄影机靠近、环境边缘可读 |
| 16mm | 107° | 超广角 rectilinear、近大远小显著、直线仍保持直线 |

若同时写焦段和 FOV：

- 明确这是同一画幅/裁切下的近似关系；换成大画幅、Super 35、竖屏裁切或后期 crop 时重新核算，不机械照抄。
- 摄影机距离必须支持目标景别；不能一面写“20米外观察”，一面要求16mm贴脸透视。
- 最终提示词仍要写可见结果，例如背景压缩、环境覆盖、边缘直线、前景放大、主体大小和景深，不让数字独自承担控制。
- 一个 CUT 内保持同一焦段/FOV，除非明确执行 `zoom`；换焦段发生在新 CUT，或写成可见、连续且有叙事理由的变焦动作。

## 景别库

| 景别 | 用途 | 提示词写法 |
| --- | --- | --- |
| ECU 极特写 | 眼睛、伤痕、按钮、接触点 | `extreme close-up on fingertips tightening around the lever` |
| CU 特写 | 表情、反应、关键道具 | `close-up, face fills frame, background falls soft` |
| MCU 中近景 | 台词、微表演 | `medium close-up, shoulders and face readable` |
| MS 中景 | 人物动作和姿态 | `medium shot shows torso, hands and object relationship` |
| MLS 中远景 | 人物与空间关系 | `medium long shot keeps body movement and hazard line visible` |
| WS 全景 | 场景路线 | `wide shot maps entrance, exit, machine path and bystanders` |
| EWS 大远景 | 尺度、孤立、灾难 | `extreme wide shot, human figure small against huge landscape` |
| OTS 越肩 | 对话、主观压力 | `over-the-shoulder from driver toward blind zone` |
| POV 主观 | 恐惧、误判、寻找 | `POV through dusty rear mirror, blocked by straw` |
| top-down 90 | 路线、围困、群体 | `90-degree top-down view shows the blocked escape path` |

### 景别覆盖可行性门

先列出本CUT必须由画面证明的最远证据边界，再选择能容纳它们的最紧景别。若同一动作必须同时读清双方支撑脚、髋肩发力、双手握点、长兵器功能端与接触点，使用MLS/WS或能明确覆盖全身的等价构图；MS只能承诺真实入框的躯干、手和局部道具，MCU/CU/ECU不能同时声称脚步、全长兵器或全身距离可见。坚持紧景别时，删除画外可见要求，或在接触前/后用有动机宽景接力补足，不用文字假装裁切外证据仍在画面内。
| low-angle | 威胁、权力、巨物 | `low-angle view makes harvester rear fill upper frame` |
| Dutch angle | 失衡、恐慌 | `subtle Dutch angle, horizon tilted by 8 degrees` |

## 运镜语法

完整运镜指令按下式编译：

```text
[承载装置/运动类型] + [相对主体的路线和方向] + [速度与加减速轮廓] + [主体在画面中的保持方式] + [起点画面] + [终点画面] + [剧情作用]
```

在 `【运镜与时间轴】` 中把该式落成动态几何：IN写camera高度/距离/看向与主体起始depth/screen位置；PATH分别写camera和主体的三维横向、纵深、高度、弧线/圆心与速度曲线；运动中写主体跨前中后景、遮挡峰值/解除、screen滑移或可见缩放，以及近层快/远层慢的真实后景视差；OUT写减速/稳定点或保留明确速度向量的运动切点。`locked-off camera` 是零长度camera path且无camera parallax，不等于主体投影、焦点或环境静止。

只写“推进、拉远、平滑、渐进、快速”都不完整。`smooth` 描述稳定性或加减速曲线，不等于慢；`gradual` 描述变化过程，不说明方向和终点；`fast` 必须同时给目标、可读主体和制动终点。

同一个中文词可能对应不同摄影机操作，必须在可见提示词中补英文消歧：

- `推近/拉远`：在 `camera dollies forward/back` 与 `zoom in/out with camera position fixed` 中二选一。
- `摇镜`：写 `pan`、`tilt` 或 `roll`，不能让模型自行选择旋转轴。
- `升降`：写 `pedestal/boom`、`crane` 或仅摄影机光轴俯仰变化的 `tilt`。
- `跟拍`：写 `follow tracking`、`lead tracking` 或 `lateral tracking`，并说明摄影机在主体前、后或侧面。
- `环绕`：写 `camera orbits [命名圆心]`，说明顺/逆时针、角度、半径/高度和终点。
- `固定镜头`：写 `locked-off camera`；只固定摄影机，不冻结演员、焦点、光影、环境或声音。
- `聚焦到`：如果改变焦平面写 `rack focus`；如果只是把对象作为画面主体，改写构图或切镜，不能冒充光学对焦。
- `慢动作`：写明是动作时间重映射 `action plays in slow motion`；摄影机速度另写。

| 运镜 | 情绪 / 剧情 | 错误用法 | 稳定写法 |
| --- | --- | --- | --- |
| locked-off camera | 观察、权力僵持、证据、喜剧延迟 | 把演员也冻结 | `locked-off camera; actor task, focus or sound carries the beat` |
| pan left/right | 横向寻找、交接信息、接住入画 | 不写起止对象 | `pan right from the empty doorway to the entering doctor, ending with both characters readable` |
| tilt up/down | 垂直揭示、从后果回到人物 | 只写上摇/下摇 | `tilt up from the dropped report to the listener's face` |
| pedestal / boom up-down | 保持摄影机光轴方向的垂直位移 | 与 tilt 混淆 | `camera pedestals down from eye level to desk height while lens stays level` |
| slow dolly in | 压力逼近、情绪收紧 | 只写“推进” | `slow dolly in toward the fixed danger point` |
| fast dolly back | 惊吓、尺度突然变大 | 画面主体丢失 | `fast dolly back, subject stays centered while danger fills background` |
| lateral truck | 追踪、横向路径 | 方向不清 | `camera trucks left parallel to the worker's movement` |
| follow / lead tracking | 跟随路线、引导逃亡或进入 | 不写摄像机在前还是在后 | `lead tracking shot moves backward ahead of the runner, maintaining a readable full body` |
| camera orbit | 展示关系、困局 | 未说明是摄影机绕行还是人物旋转 | `camera makes a slow 120-degree clockwise orbit around both characters, ending at shoulder height; axis remains readable` |
| descending spiral orbit | 坠落、命运压迫 | 空间漂移 | `descending spiral orbit from high angle to shoulder height` |
| crane rise | 尺度揭示 | 无信息变化 | `crane rise reveals blocked exit behind the crowd` |
| crane descend | 压力落到人物、从地图进入困局 | 下降但无落点 | `crane descends from the office layout into the trapped employee's desk` |
| tilt up reveal | 从物到威胁 | 只写“上摇” | `tilt up from muddy wheel track to the towering machine rear` |
| dolly-in tension | 心理压迫 | “推进”未说明摄影机位移还是变焦 | `camera slowly dollies forward toward the driver's eyes in the mirror, 75mm focal length stays fixed` |
| dolly-back scale reveal | 人与巨物关系 | “拉远”未说明摄影机位移还是变焦 | `camera dollies backward with focal length fixed, revealing the elderly man inside the harvester blind triangle` |
| handheld panic | 逃亡、混乱 | 随机晃动 | `handheld panic with readable subject center, footsteps shake frame` |
| stabilized tracking / Steadicam-like glide | 优雅、潜入、仪式 | 把品牌名当成完整路径 | `stabilized tracking camera glides forward through the narrow corridor, subject held on the left third, no visible cut` |
| whip pan | 快速转移注意 | 乱切无目标 | `whip pan from shouted warning to machine rear impact zone` |
| zoom / crash zoom | 改变取景角而不改变透视位置；突发线索 | 与 dolly 混写 | `short crash zoom to the red value on the fixed report image` |
| rack focus | 信息转移 | 焦点对象不清 | `rack focus from rice stalks in foreground to hidden figure behind them` |
| bullet time | 超现实冲击 | 只写名称，不区分时间与摄影机 | `action slows almost to a freeze while a virtual camera arcs 90 degrees around the named contact point; debris remains spatially consistent` |
| dolly zoom / Hitchcock effect | 恐惧认知崩塌 | 只写人名或把 dolly 与 zoom 同向 | `camera dollies backward while zooming in to hold the driver's face size; background perspective expands` |

每个 time beat 只用一个主运镜；只有机械耦合且共同完成同一剧情变化的复合运动可计为一个主运镜，否则分到不同 time beat。

### 运镜速度与组合

速度词必须落到可见运动曲线：

| 速度轮廓 | 适合 | 可执行写法 |
| --- | --- | --- |
| subtle micro-movement | 纪实呼吸感、轻微不安 | `low-amplitude irregular handheld drift, face remains readable` |
| very slow / slow | 倾听、压迫、发现 | `very slow dolly in at a steady pace, ending before the desk edge` |
| moderate / walking pace | 走位、带领、空间浏览 | `lateral track at the actor's walking pace` |
| brisk / fast | 追逐、惊吓、信息突变 | `camera rapidly dollies backward with focal length fixed, then brakes to a stop as the exit enters frame` |
| snap / whip | 单一注意力跳转 | `snap pan from the warning hand to the moving wheel` |
| gradual acceleration | 威胁累积、追逐升级 | `tracking move gradually accelerates with the runner` |
| gradual deceleration | 抵达、认知、后果 | `camera decelerates into a stable close-up and holds` |
| ease-in / ease-out | 稳定商业、抒情、产品展示 | `smooth ease-in, constant middle speed, soft ease-out on the hero object` |
| speed ramp | 接触前蓄势、撞击、后果 | `action remains real-time on entry, ramps to 40% across contact and the first force response, then returns to real-time for recovery; camera path remains separately defined` |

- 运镜节奏与演员主动作同向或有明确反向理由；人物匀速走，摄影机通常同节奏跟随，紧张升级才逐步加速。
- 手持必须同时写晃动幅度、频率、身体/步伐来源和可读主体：低幅低频呼吸式漂移适合纪实与轻微不安，高频微震适合紧张，剧烈晃动只服务逃生或灾难冲击；产品细节展示和已有复杂复合运镜默认不再叠加手持。
- POV 必须点名视角来源、视线高度和运动逻辑，例如“郭大江眼睛 POV”“低于人眼的动物 POV”“车辆前挡风玻璃 POV”；无人机属于 `drone/aerial viewpoint`，不写成角色主观 POV。除非用户要求持续沉浸式主观视角，人物/生物 POV 只作为短暂信息或情绪视角，避免长时间失去客观空间。
- 组合运镜只保一个复合主句：`dolly zoom` 写清摄影机和变焦的相反方向及主体大小保持；`orbit + zoom` 写圆心、旋转角度、远近变化和终点；`lateral truck + counter-pan` 写轨道方向、反向摇摄和主体居中。
- 复杂复合运镜优先调用 `@视频`，但参考视频只控制已指派的运镜路径、速度和节奏，不控制当前角色、地点、服装、剧情或声音。

## 对白场景的摄影调度

对白 CUT 先看关系和语义归属，再选 shot size、camera setup 与 camera movement，不默认使用平视正反打：

| 戏剧关系 | 演员与摄影调度 | 适合的可见机制 |
| --- | --- | --- |
| 权力不平等 | 强者少动或占据高位，弱者在前景/纵深暴露手、呼吸和重心变化 | 深景双人构图、高低差、前景压迫、有明确戏剧理由的 `locked-off camera`，或写明起止距离的极慢 `camera dolly-in` |
| 亲密靠近 | 两人共享构图，用递物、接物、坐下、靠近或距离缩短承载台词 | 紧双人构图、低速 `lateral truck`、以两人中点为圆心的小弧度 `camera orbit`、焦点在手与脸之间 `rack focus` |
| 回避与隐瞒 | 角色不正面相对，用负空间、遮挡、错开的 eyeline 和道具任务暴露真实意图 | 斜构图、frame-within-frame、前景遮挡、从道具 rack focus 到反应 |
| 喜剧延迟 | 动作按严肃逻辑继续，让错误细节和晚半拍的反应形成笑点 | 保持双人/全景关系、短暂停留、reaction cut；不靠夸张晃镜制造笑点 |
| 威胁与逼问 | 施压者侵入对方空间或封住出口，构图同时读清距离变化和反应者 | 纵深调度、侧向重构图、低角度前景、`slow camera dolly-in` 或压力型 `locked-off camera` |
| 告白与反转 | 先让说话者维持表面控制，再把画面交给听者的理解或关系变化 | 共享双人构图转 reaction cut、L-cut/J-cut、由脸转手或由物件转眼神 |

规则：

- 台词的摄影机不必始终拍说话者；信息属于谁，就让焦点、构图或切镜落到谁身上，但说话来源必须清楚。
- 摄影机运动必须跟随距离、权力、信息或反应的变化，不能用“camera持续移动”掩盖人物缺少调度。
- `locked-off camera` 只在证据、权力、等待、尴尬延迟、震惊或情绪压迫需要时使用；它只固定摄影机，画内仍要有呼吸、握力、视线、焦点、光影、环境或声音变化。
- 用户或项目已锁定“破水平”、特定斜构图或其他 camera lexicon 时，按其明确定义执行；不要把 Dutch angle 当作所有对白的通用美化。

## 光线库

写光线必须包含：光源、方向、强度、主光与环境/practical色温、阴影、光比或negative fill、材质反应。色温是来源属性，不给整幅画面随意贴一个数字。

光比按可读性选择：`2:1` 适合高调商业、温和人物和明亮科普；`4:1` 适合多数剧情片，在立体塑形与面部可读之间平衡；`8:1` 适合低调悬疑、恐惧、权力压迫和局部隐藏。需要识别人脸、危险点、武器路线或群众时，阴影侧仍保留最低必要细节；不能一面写8:1压黑，一面要求暗部全部清晰如高调广告。

| 光线 | 适合场景 | 提示词写法 |
| --- | --- | --- |
| Dune daylight harsh sun | 沙漠、灾难、史诗 | `harsh high sun, short black shadows, dust turns gold, skin highlights dry and unforgiving` |
| Dune firelit interior | 宗教、密室、古老权力 | `large fire source from screen-left, flickering amber light, deep negative fill` |
| golden hour | 温情、回忆、收获 | `low golden sun from back-right, long soft shadows, rim light on rice stalks` |
| blue hour | 孤独、悬疑、转场 | `blue hour ambient sky, weak practical light, cool shadows` |
| moonlight | 夜逃、恐惧 | `cold moonlight from high back, silver rim on shoulders, foreground in soft darkness` |
| oil lamp / candlelight | 古代、亲密、危险 | `small warm practical flame, fast falloff, moving shadows across face` |
| torchlight | 洞穴、追逐、仪式 | `handheld torchlight, unstable orange highlights, walls breathe with shadow` |
| neon | 城市、科幻、诱惑 | `cyan-magenta neon from opposite sides, wet surfaces reflect color` |
| fluorescent | 医院、工厂、办公室 | `flat greenish overhead fluorescent, hard under-eye shadows, sterile texture` |
| overcast natural light | 纪录、现实、事故 | `overcast sky as broad softbox, low contrast, muddy ground reflects dull gray` |
| skip-bleach contrast | 罪案、战争、冷硬现实 | `skip-bleach contrast, desaturated midtones, crushed blacks` |
| low-key horror | 恐惧、未知 | `low-key lighting, one motivated practical, black negative fill, threat half-hidden` |
| high-key commercial | 产品、科普、广告 | `high-key softbox lighting, minimal shadows, clean readable surfaces` |

## 质感、空气与光学响应

| 技术描述 | 适用条件 | 稳定写法与边界 |
| --- | --- | --- |
| 强空气透视 | 大空间、长距离、山谷、城市、沙尘/湿气中有明确前中后景 | 写介质来源、密度梯度和远景降对比/偏色；近景不能同时被同等雾化 |
| 轻度柔光扩散 | 人物文戏、回忆、柔和广告、需要收敛高光 | 写 `light diffusion, restrained halation, softened highlight edges`；不把皮肤磨成塑料 |
| 压黑黑位 | 罪案、夜景、悬疑、低调权力 | 写 `compressed black toe, rich blacks with retained narrative detail`；剧情信息所在阴影不死黑 |
| 各向异性高光 | 拉丝金属、缎面、头发、唱片纹路、方向性湿表面 | 写明材料纹理方向和高光沿哪个方向拉伸；皮肤、石墙和漫反射布料不机械使用 |
| 焦散 | 水面、玻璃、晶体、弧形反射金属把光投到另一表面 | 写明光源、折射/反射介质、接收表面和随介质运动的图样；没有传播路径不生成装饰光纹 |
| 电影级调色 | 所有需要统一成片基调的项目 | 必须继续写 palette relation、饱和度、black toe、高光、肤色保护和 LUT/stock-like 可见结果，不能单独使用该词 |
| 同类色 | 温和统一、衰败单调、品牌或场景综合色 | 点名相邻色相、明度/饱和度层级和10%强调色，避免主体与背景融成一块 |

## 色彩系统

- 60/30/10：60% 环境主色，30% 人物/道具辅色，10% 危险或情绪强调色。
- 色彩关系必须点名：同类色、互补色、分裂互补或冷暖分离中选择当前剧情需要的一种；同类色仍用明度、饱和度或10%强调色分离主体。
- 角色色彩：主角、反派、受害者、机器、超自然元素不能混成同一色块。
- 危险色：红、橙、黑黄警示、冷白机械光，用于突出风险点。
- 超自然例外色：只给异常能量、预兆、梦境、神迹，避免污染现实场景。
- HEX 锁定：产品、UI、装备、品牌色需要稳定时才写 HEX。
- LUT 语言：`warm Kodak-like highlights with cool cyan shadows`、`bleach bypass contrast`、`muted documentary LUT`；同时写 black toe、高光滚降、肤色保护或饱和度结果，不只写“电影级调色”。

## 画家 / 流派风格语义编译

如果用户提到画家、流派、插画风格或风格图，不要只复述名称。必须翻译为：

- 线条：硬边、软边、墨线、厚涂、速写。
- 色彩：饱和度、冷暖、主辅色、强调色。
- 构图：平面装饰、纵深透视、对称、负空间。
- 材质：油画、胶片颗粒、水彩扩散、PBR、黏土、赛璐璐。
- 光线：自然光、戏剧性明暗、图形化阴影。
- 情绪：童话、荒诞、史诗、压抑、温柔、冷峻。

写法：

```text
Style reference is compiled into soft watercolor edges, low-saturation moss green and warm ochre palette, simple graphic silhouettes, gentle ambient light and hand-painted paper texture; do not copy any signature or exact artwork.
```
