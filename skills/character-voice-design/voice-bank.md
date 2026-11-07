# 音色词汇库（Voice Bank）

本文件是 `character-voice-design` 技能的配套词汇库。
设计五维画像时从这里取词，保证描述精确、TTS 工具能正确理解。
允许组合与引申，但不允许使用含义模糊的词（如"好听""有磁性"单独出现）。

## 维度 A｜音高与共鸣（Pitch & Resonance)

| 档位 | 中文 | English |
|------|------|---------|
| 很低 | 极低沉、胸腔共鸣厚重 | very deep, booming chest resonance |
| 低 | 低沉、沉稳 | deep, low-pitched |
| 中低 | 中低音、温厚 | moderately low, warm midrange |
| 中 | 中音、自然 | medium pitch, neutral register |
| 中高 | 明亮、清朗 | bright, clear upper-midrange |
| 高 | 高亢、尖细 | high-pitched, thin |

共鸣修饰：胸腔共鸣 chest resonance ／ 头腔共鸣 head-forward resonance ／
鼻音 nasal twang ／ 喉音 throaty ／ 口腔靠前 forward oral placement

## 维度 B｜语速与节奏（Pace & Prosody)

| 档位 | 中文 | English |
|------|------|---------|
| 慢 | 迟缓、字斟句酌 | slow, deliberate, measured |
| 中慢 | 从容 | unhurried |
| 中 | 自然对话速度 | natural conversational pace |
| 快 | 急促、连珠炮 | fast-paced, rapid-fire |
| 节奏习惯 | 抢话、打断自己 | interrupts himself, clipped urgency |
|  | 长停顿后再开口 | long pauses before answering |
|  | 尾音下沉（笃定） | falling intonation, declarative |
|  | 尾音上扬（犹疑/讨好） | rising intonation, hesitant uptalk |
|  | 语调平直（冷静/疏离） | flat affect, monotone undertone |

## 维度 C｜口音与发音习惯（Accent & Diction)

| 口音 | 适用设定 | English |
|------|----------|---------|
| General American 标准美音（默认） | 无特殊设定的美国角色 | neutral General American accent |
| 南方口音（德州/深南部） | 农场、军人、小镇、传统家庭 | gentle Southern drawl |
| 纽约口音 | 城市、市井、强势 | thick New York accent |
| 波士顿口音 | 老钱、东区工人 | Boston accent with dropped R's |
| 中西部口音 | 温和的小城普通人 | soft Midwestern accent |
| 加州口音 | 年轻、休闲 | laid-back Californian accent |
| Chicano English | 拉美裔社区成长的角色 | light Chicano-inflected English |
| 英国 RP | 精英、学者、反派贵族 | refined British RP accent |
| 苏格兰/爱尔兰 | 粗犷、豪爽 | burry Scottish lilt / soft Irish brogue |
| 微弱母语痕迹 | 第一代移民 | faint trace of a (Spanish/Mandarin…) accent |

微观习惯：吞掉词尾 t/d ／ 卷舌明显 strong rhotic R's ／ 说话爱缩读 gonna, wanna ／
咬字极清楚 precise enunciation ／ 常拖长元音 drawn-out vowels

## 维度 D｜质感与纹理（Texture)

| 中文 | English |
|------|---------|
| 沙哑、烟嗓 | gravelly, raspy, smoke-worn |
| 微哑但有弹性 | slightly hoarse but resilient |
| 温暖圆润 | warm, rounded timbre |
| 清亮干净 | clean, crisp, clear voice |
| 气声重、耳语感 | breathy, airy quality |
| 带颗粒感的粗粝 | rough, gritty texture |
| 松弛带振动感 | relaxed with a subtle rattle |
| vocal fry（气泡音） | noticeable vocal fry at sentence ends |
| 柔软童声 | soft childlike timbre |
| 苍老但稳 | aged but steady, unbroken by tremor |

## 维度 E｜能量与表演习惯（Energy & Acting Habits)

| 类型 | 中文示例 | English 示例 |
|------|----------|--------------|
| 外放型 | 大笑、拍桌子式的强调 | big laugh, pounds emphasis into key words |
| 压抑型 | 生气时反而更轻更慢 | gets quieter and slower when angry |
| 讨好型 | 爱用反问和笑声缓冲 | cushions statements with nervous laughter |
| 冷淡型 | 几乎不笑，句子短 | rarely laughs, keeps sentences short |
| 絮叨型 | 爱跑题、自我修正 | goes off on tangents, self-corrects mid-sentence |
| 标志动作 | 说谎前先清嗓子 | clears throat before lying |
|  | 紧张时语速突然加快 | speech speeds up when nervous |
|  | 习惯用一声长叹结束话题 | ends topics with a long resigned sigh |
|  | 低沉的笑藏在鼻子里 | low hum of laughter through the nose |

## English Prompt Template（TTS 用）

```
A {age descriptor} {gender} voice, {accent}, speaking English.
{Pitch/resonance line}. {Texture line}. {Pace/prosody line}.
{Personality/energy line}. Sounds like {one-sentence scene anchor}.
Natural, realistic delivery with audible breaths — not announcer-like.
```

填写规则：
1. 第一行锁定"是谁"：年龄感 + 性别 + 口音（默认 `neutral General American accent`）。
2. 中间三行分别对应维度 A+D、B、E，每行 1–2 个短语，禁止堆砌超过 4 个形容词。
3. `scene anchor` 用一个画面感场景收尾，例如
   `Sounds like a tired detective talking over diner coffee at 3 a.m.`。
4. 结尾固定带上自然写实声明（模板最后一行），呼应"真人写实"定位。

## 对比示范（一对刻意拉开差距的角色）

**侦探 Cole（45 岁，男）**
> A weary 45-year-old American man, neutral General American accent with a hint of
> Texas drawl. Deep, gravelly, smoke-worn voice with heavy chest resonance.
> Slow and deliberate, falling intonation, long pauses before he answers.
> Quiet authority; gets softer instead of louder when angry. Sounds like a veteran
> detective interrogating a suspect across a scarred wooden table. Natural,
> realistic delivery with audible breaths — not announcer-like.

**实习生 Danny（22 岁，男）**
> An anxious 22-year-old American man, neutral General American accent. Medium-high,
> bright voice with a clean, crisp timbre and occasional vocal fry when flustered.
> Fast, rapid-fire pace with rising intonation, self-corrects mid-sentence.
> Eager to please, cushions bad news with nervous laughter. Sounds like an intern
> rambling through his first pitch in a glass-walled startup office. Natural,
> realistic delivery with audible breaths — not announcer-like.

对比点：音高一低一高、质感一哑一净、语速一慢一快、能量一压一放 —— 四维全开，
这就是"主角级区分度"的标准。

---

## 附录 A｜即梦/短剧配音「精准音色标签库」（中文语境）

> 用途区分：本文件主体（维度 A-E + English Prompt Template）服务 **TTS 引擎**（ElevenLabs 等）的英文音色设计；本附录服务 **短剧/漫剧配音指令**——即 `cinematic-seedance-director` 的 `rules/voice-direction.md` VO-01 五段式配音指令里那个「精准音色标签」字段。
>
> **强制规则**：配音指令中的音色标签必须取自本库，**禁止**"古风男音/古风女音/古风公子音/古风绝望女音/古风冷淡男音/古风娇媚女音"等**无人物性格、无角色属性**的模糊标签。
>
> 推理逻辑：先从文案提取人物**年龄 / 身份 / 核心性格 / 人设**，再从下表匹配最贴合的一个标签。

### 男性青年角色
温润公子音、腹黑公子音、桀骜少年音、清冷少年音、威严帝王音、霸道将军音、阴狠反派音、玩世不恭少爷音、沉稳谋士音、疯批反派音、高冷男神音、霸道哥哥音、奶糖弟弟音、悄语男友音、不羁少爷音、偏执弟弟音、霸道总裁音、高尚郎君、青年才俊音、逍遥浪客音、高傲少爷音、叛逆青年音、青春男大音、阳光少年音、元气男友音、娇弱弟弟音、志气小伙音、固执男友音、冷漠总裁音、文弱书生音、少年统帅音、温吞少爷音、柔情盟主音、耿直君子音、玉面公子音、温润君子音、阴险男主音、冷面霸总音

### 女性青年角色
清冷御姐音、绿茶甜心音、成熟温柔女神音、恶毒女配音、娇蛮大小姐音、飒爽侠女音、温婉大家闺秀音、疯批美人音、柔弱小白花音、心机庶女音、甜美萌妹音、傲娇女王音、稚嫩少女音、软糯萝莉音、超嗲萌妹音、冰山女王音、纯情闺蜜音、青春女神音、温暖御姐音、阳光甜心音、俏皮姐姐音、甜心少女音、成熟白领音、娇媚女神音、知性御姐音、娇媚萝莉音、俏皮公主音、开朗妹妹音

### 中老年角色
沉稳国公音、沧桑老者音、疯癫老妇音、刻薄老嬷嬷音、威严太后音、慈祥老夫人音、腹黑权臣音、雄浑霸主音、儒雅文士音、阴鸷厂公音、豪迈老侠音、慈蔼族长音、疯癫道士音、市侩商贾音、悲苦老农音、诙谐老仆音、刚烈老将音、华贵老旦音、泼辣悍妇音、病弱孀妇音、慈柔乳娘音、刁钻媒婆音、清修尼姑音、刻薄掌事音、痴情老妪音、健壮农妇音、诡异巫婆音、慈祥奶奶音、老干部男音、广场舞大妈音、老教授男音、退休工人男音、时髦外婆音、居委会主任女音、老中医男音、健身达人老大爷音、空巢老人女音、老年合唱团女高音、公园棋王音、失智老人女音、老江湖骗子音

### 特殊角色
空灵仙音、鬼魅妖音、憨厚壮汉音、尖酸小厮音、谄媚管家音、霸气寨主音、傀儡师音、赶尸人音、河神音、狐仙音、屠夫音、赌坊老千音、哑仆喉音、巫医音、山魈精怪音、刽子手音、更夫音、戏班琴师音、造畜人音、守陵人音

### 儿童角色
虎头虎脑小男娃音、鼻涕虫小可怜音、拆家小霸王音、小暖男音、运动健将音、小书虫音、受气包音、小机灵鬼音、小胖墩音、留守儿童音、扎辫子小丫头音、小公主音、贴心小姐姐音、女汉子音、文静小淑女音、鬼马小精灵音、学舌小鹦鹉音、小戏精音、睡醒迷糊音

### 使用示例（配音指令五段式）

```text
【配音指令：沈惊鸿｜疯批美人音｜冷艳带刺｜状态（惊疑/不服）｜语气（质问/发冷/不躲不闪）：我和她又不是直系亲属，给她放哪门子的血？】
【配音指令：裴砚辞｜高冷男神音｜冷硬压迫｜状态（暴怒/逼迫）｜语气（命令/不容置疑/强压）：把她拖出来，给如眉放血！】
```

> **P4 海外管线**：本库为中文语境设计。海外管线改用英文口音 + 音色描述（配合本文件主体的 English Prompt Template），标签改为 `refined RP English, low and controlled` 这类写法。
>
> 详细格式与规则见 `cinematic-seedance-director` 技能的 `rules/voice-direction.md`（VO-01 / VO-03）。
