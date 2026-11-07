---
name: script-draft-forge
description: "编剧初稿锻造/出初稿/生成剧本初稿/多版初稿/剧本初稿包/素材变剧本/题材怎么写/编剧AI/剧本生成器/小说改编剧本/按细纲出初稿/小说原文+大纲+细纲出初稿/六档位自动混跑/自动分档/引擎调度/对白二次调整/台词口语化/单句8-15字/授权净稿/改编权登记/分集规划/信息增量/逐集三要素表/稿件形态门/空稿不验收。纯编剧服务的初稿锻造流水线：给素材（小说/对标剧/题材想法）→ 五维拆解（人物/题材/金手指/背景/立意）→ 需求登记（集数/时长/风格/钩子自定义/挂载模块）→ 钩子预算 → 多引擎出每集多版初稿 → 闸门A验收（钩子回提+情理门，杀稿不修稿）→ 交付初稿包（多版+体检报告+分级推荐）。编剧知识三层为纲：要素层建档案、动力层定验收、呈现层管生成。MODE 1 (完整初稿包): 需求登记→素材体检→钩子预算→多版初稿→验收→交付. MODE 2 (单集重跑): 只重出指定集的多版. MODE 3 (按纲改编): 小说原文+编剧大纲/细纲→原文入库切片+逐集生成包→结构锁定下多版初稿→细纲覆盖验收（GA-06~08）→交付. 内置规则：编剧核心（CR）、钩子系统（HK）、一致性注入（DR）、多引擎路由（MR）、杀稿闸门（GA）+ 可插拔自定义模块（modules/）。只出初稿不精修——挑稿与合并由用户完成，初稿包即交付终点。可选执行层 scripts/engine_dispatch.py 按 MR-07 端点逐档直调 API，实现六档位自动混跑（默认演练、加 --live 才计费）。"
when_to_use: 当用户给出素材（小说/对标作品/题材想法）想要专业剧本初稿、要求"出几版让我挑"、"把这个素材变成剧本"、"出初稿包"，或要对某集重出多版时使用；当用户给出小说原文文件并给出编剧大纲或细纲、要求"按这个纲出初稿 / 把原文和细纲放进去出初稿 / 小说改编成剧本"时走 Mode 3；当要求"六档位自动混跑 / 按档位自动调模型 / 调度引擎跑一批"时用 MR-08 自动调度执行层。
---

# 编剧初稿锻造 — 总控调度器

把素材变成**可挑选的专业剧本初稿包**：每集多版、结构差异化、钩子可验收。**专业度来自编剧知识层（CR 三层方法论——要素/动力/呈现），语言质感来自引擎层（MR 路由），平台与题材适配来自可插拔模块（modules/）**。**本文件只做调度**：执行到哪个阶段读哪个模块，禁止凭记忆复述规则跳过读取。

## 0. 全局铁律（8 条）

1. **杀稿不修稿**（GA）：闸门A不过的版本直接淘汰，禁止精修烂稿——精修只花在过关稿上，这是本技能存在的意义。
2. **需求先于一切**：用户需求（集数/单集时长/题材/风格/钩子自定义/挂载模块/引擎）登记后才执行；未声明的维度主动问或走默认，**禁止猜**。平台包是可选模块之一，不强制挂载。
3. **成本可控**（CC）：规则文件只读一次；S0-S3 用便宜引擎打底、挑稿档引擎只做 S4 挑稿或用户点名；分批跑（每批 5-10 集）且前情压缩。详见 rules/cost-control.md。
4. **三层知识为纲**（CR）：要素层管建档（S0 五维拆解/S2 锚点）、动力层管验收（S4 情理门/矛盾情绪结算）、呈现层管生成（S3 画面思维/台词约束/卡点）——所有阶段判断回 CR，不回平台模板。
5. **钩子即预算**（HK-01）：钩子预算表是每集的支出计划，初稿必须花完预算；出稿后反向提取验收（HK-09），四维任一不过即杀。预算来源两级：用户自定义优先；未指定按挂载模块折算（HK-04），禁止凭空拍数字。每个钩子声明信息差模式（HK-02），类型必须轮换防疲劳（HK-03）。
6. **多版必须结构差异化**：同集多版=不同结构模板或不同结构参数（挂载模块的组合策略），同结构改几个词不算多版。**唯一例外：Mode 3 细纲锁定结构**（SO-03）——事件结构不可改，差异化降级到呈现层（切入点/场面调度/台词密度/卡点切法），版本头部必须声明差异轴；用户明说「细纲仅供参考」才恢复结构差异化。
7. **一致性注入强制**（DR-01）：每次生成必注入人物小传+金手指+前情提要+术语表，防长线忘设定（豆包 40 集漂移实证）。
8. **结果可见 + 验收即证据**：每次跑完（含 Mode 2 局部重跑、Mode 3 按纲改编、MR-08 自动调度），S5 交付必须做三件事，缺一即视为未交付：①用文件呈现工具**打开全部版本文本与索引**（正文直接可见，不允许只给路径）②在回复中**贴出每集推荐版本的正文摘录**（至少含该版卡点/最强段落）③给出**挑稿决策点清单**（需用户拍板的事项）。验收本身用要素计数+证据绑定（脚本输出/行号/数值），禁止字数下限与"感觉不错"式结论。**轮次/字数等硬指标必须取 `scripts/check_gate_a.py` 的脚本输出，禁止模型自报数**（GA-01）；Mode 3 再加 `scripts/source_outline.py check`，**细纲覆盖禁止模型自报**（GA-06~08），两份脚本报告与纲解析报告一并呈现。**DRY-RUN 演练稿一律不得计入交付**（MR-08）。

## 1. 模式触发

| 模式 | 触发短语 | 入口 |
|---|---|---|
| Mode 1 完整初稿包 | 出初稿 / 多版初稿 / 素材变剧本 / 初稿包 / 锻造初稿 | workflows/full-draft.md |
| Mode 2 单集重跑 | 第N集重出 / 这集不行再来几版 / 单集重跑 | workflows/ep-redraft.md |
| Mode 3 按纲改编 | 小说原文+细纲出初稿 / 按这个纲出初稿 / 小说改编成剧本 / 大纲细纲放进去出初稿 | workflows/source-outline-draft.md |

Mode 3 自动挂载两个模块：`modules/process/source-outline.md`（SO-01~08，原文切片与结构锁定）＋ `modules/process/dialogue-pass.md`（DP-01~08，对白二次调整 S3.5）。**对白二次调整是独立工序，禁止并进 S3 生成提示词**——小说转剧本链路里它是返工率最高的一环，混在生成里会被结构目标吃掉。Mode 1/2 不自动挂 DP，可显式声明挂载，卸载须在 `00_需求与体检.md` 记显式声明。

**全部 Mode 默认挂载** `modules/process/source-hygiene.md`（SH-01~07，授权阻断＋净稿）与 `modules/process/episode-plan.md`（EP-01~07，分集规划三要素）。授权阻断**不可卸载**：未登记改编权覆盖短剧/漫剧与分发渠道，S0 不出稿、只出提示。分集规划表是**技能自己产出的 S1 产物**，不是只消费外部细纲；三要素（明确冲突／本集信息增量／尾钩）在生成期注入 `packets/`，S4 缺一即杀。

**OpenCode 宿主适配（优先）**：`rules/opencode-adapter.md`（OC-01~08）是宿主适配层，优先于 `rules/model-routing.md` 的静态引擎表：OC-01 用 `tools.opencode.models` 实时探测可用模型建 `pipeline\05_引擎路由表.md`，OC-03 用 `subagent` 显式指定模型为每集每版独立派发，OC-04 管上下文预算，OC-05 用 `browser.preview` 做结果可见。未配外部端点时按 MR-05 降级为会话默认模型，流程照常不阻塞。只有需要脱离会话、按 MR-07 端点逐档直调时才启用下面的 `engine_dispatch.py`。

**可选执行层（不是第 4 个 Mode，附加在任一 Mode 之上）**：`scripts/engine_dispatch.py` 按 MR-07 的六个 model id 逐档直调 API，把六档位混跑自动化。命令链 `init-config → plan → run → status → verify`；**默认演练零计费，加 `--live` 才真实调用**（产生 DMXAPI 费用）。演练产物带占位标记、`verify` 会拒绝验收。它只换「谁来生成」，不改 CR/HK/DR/MR 任何判据，也不替用户挑稿。细则见 `rules/model-routing.md` MR-08。

## 2. 产物与目录约定

```
{剧本目录}\
├── pipeline\ manifest.json / 00_需求与体检.md / 01_钩子预算表.md / 02_人物小传.md / 03_术语表.md / 各集生成记录
│   ├── 【SH】00_授权登记.md（S0 必填阻断）／00_净稿报告.md（删除逐条登记+待人工确认）
│   ├── 【EP】01_分集规划表.md（逐集三要素，也可并入 01_钩子预算表.md 作一节）
│   ├── 【Mode 3 追加】原文纯文本.txt / source-index.json / 10_原文索引.md / outline.json
│   │   12_纲解析报告.md / 13_改编决策.md / packets\ep{NNN}.md / ingest-manifest.json
│   │   04_对白调整登记.md（DP-08：原句→改为→理由；删除必须登记，禁止默删）
│   │   adapt_gate_config.json（项目专属语义判据，缺省时对应门跳过）
│   └── 【MR-08 自动调度追加】dispatch-config.json / dispatch-plan.json / dispatch-cost.md
│       dispatch-report.md / verify-report.md / pick\ep{NNN}.md / 04_卷级回顾_第N-N+9集.md
└── outputs\
    ├── ep001_A_v1.md  ep001_B_v1.md  …（每集每版一文件：ep{NNN}_{版型}_v{n}.md，版型由挂载模块定）
    ├── 【挂 DP 时】ep001_A_v1_dlg.md …（S3.5 可生产对白稿，S4 验这个而非初稿）
    ├── 00_初稿包索引.md（每集版本清单+闸门A结果+三流/二流/一流分级推荐）
    ├── 00_授权检查.md（SH-01/02 阻断检查，含法律效力边界声明）
    ├── 01_分集规划检查.md／.json（EP-06 三要素齐备率，缺一即杀）
    ├── 01_体检报告.md（lint 结果：钩子四维/情理门/节拍达标）
    ├── 01_体检报告_脚本.md（GA-01~12 脚本数值）
    ├── 01_语义门禁.json（adapt_gate G1~G9）／ 01_验收.json（check_adapt 合并结论）
    └── 01_体检报告_纲源.md（Mode 3：GA-06~08 细纲覆盖/原文忠实/新增事件）
```

manifest.json：`{"mode":"1|2|3","stages":{"s0_brief":{"status":"done","output":"…"},"s1_hook":{…},…},"modules_loaded":[],"engines":{},"dispatch":{"plan":"pipeline/dispatch-plan.json","tasks":{"<task_id>":{"status":"done|failed|blocked","model":"…","output":"…","usage":{…}}},"batch":{…}},"updated":""}`

## 3. 流水线

| Stage | 做什么 | 必读 | 输出 | 通过条件 | 失败回退 |
|---|---|---|---|---|---|
| S0 需求登记+素材体检 | 五维拆解（人物/题材/金手指/背景/立意）+需求登记表（集数/时长/风格/钩子自定义/挂载模块/引擎）+成本路由确认（CC-02）+**授权登记阻断（SH-01/02）＋原文净稿（SH-03~07）** | rules/craft-core.md、rules/cost-control.md、modules/_registry.md、modules/process/source-hygiene.md、`scripts/check_authorization.py` | pipeline\00_需求与体检.md、**00_授权登记.md（自定义名自动发现）**、**00_净稿报告.md**、原文纯文本.txt（Mode 3） | 需求表填全且模块确认；**授权检查退出码 0**；净稿删除逐条登记、待确认清单有人处置 | 授权未确认→**阻断不出稿，只出提示**；需求不明则问用户，不猜 |
| S1 钩子预算 | 钩子提取（用户自定义优先→HK-04 折算兜底）→四级钩位配额（开头锁人/节拍/卡点/长线）+钩子台账＋**逐集三要素表（本集核心事件／明确冲突／本集信息增量／尾钩／出处）** | rules/hook-quota.md、modules/process/episode-plan.md | pipeline\01_钩子预算表.md（注明预算来源+台账列）、**01_分集规划表.md** | 每集四级钩位齐+台账完整（HK-07）＋**三要素齐备率 100%（EP-06）** | 素材钩子不足→填空模板并列缺口（HK-09）；三要素缺项→补齐再进 S3，禁止编造 |
| S2 锚点建档 | 人物小传（含金手指登记）+术语表+前情提要卡 | rules/consistency.md、rules/craft-core.md（要素层） | pipeline\02_人物小传.md、03_术语表.md | 主要角色每张小传含固定特征≥5项+金手指已登记 | — |
| S3 多版初稿 | 挂载模块的结构组合×引擎路由，每集出 2-3 版，注入 S2 锚点 | rules/craft-core.md（呈现层）、**rules/opencode-adapter.md（OC-\*，OpenCode 宿主优先）**、rules/model-routing.md、rules/consistency.md、已挂载模块 | outputs\ep{NNN}_{版型}_v{n}.md | 每集≥2版且结构差异化 | 单版失败重跑该版，不阻塞他版 |
| **S3.5 对白二次调整**（挂 DP 时） | **独立工序**，只改对白/旁白呈现层：单句 8–15 字、书面语→口语、朗读顺口、旁白三禁、叙述腔直搬禁令、A/B 同旁白禁令；不动场次/事件/人物/数字/规则/视角 | modules/process/dialogue-pass.md（DP-01~08） | outputs\ep{NNN}_{版型}_v{n}_dlg.md、pipeline\04_对白调整登记.md | 登记齐全（删除不默删）；例外有戏剧理由；DP-04 已念 ≥5 句 | 超出呈现层 → 回 S3 重出，不在本工序修 |
| S4 闸门A验收 | 钩子回提四维+情理门（CR 动力层：合乎情理+情绪结算）+台词双重约束 lint + **GA-01~12 脚本化硬指标** + **语义门禁 G1~G9（含叙述腔直搬／解说型旁白／A-B 同旁白）** + **分集规划合并门（EP-06）＋ S0 授权/净稿留痕复核（SH-07）** | rules/hook-quota.md（HK-09）、rules/craft-core.md（动力层）、review/preflight.md、`scripts/check_gate_a.py`、`scripts/adapt_gate.py`、`scripts/check_adapt.py`、`scripts/check_episode_plan.py`、`scripts/check_authorization.py` | outputs\00_初稿包索引.md、01_体检报告.md、**01_体检报告_脚本.md**、**01_分集规划检查.md**、**00_授权检查.md**、**01_验收.json** | 全部版本有判定（过/杀+证据）；过关版≥1；脚本报告 FAIL=0；**G9／GA-10／GA-11 任一命中、或三要素齐备率 <100%，均不得写「通过」；GA-12 形态不达标一律「不予验收」** | 全杀→S1 复核预算是否过苛再重跑 S3；脚本 FAIL→杀稿重跑，不精修 |
| S5 交付 | 索引+体检报告+分级推荐随初稿包输出，初稿包即终点 | review/audit.md | 交付说明（怎么挑、怎么补跑） | audit 清单全✅ | — |

**Mode 3 差异（只改输入侧与差异化口径，S1/S2/S4/S5 规则照用）**：N0 原文入库（含 SH 净稿清洗与授权登记留痕）与纲解析 → S0 需求登记（集数/版本数/细纲约束从纲里读）→ S1 钩子预算（细纲 `钩子：` 标签作自定义输入）＋ 逐集三要素表 → S2 锚点建档 → `refresh` 重打生成包（**注入本集三要素行**，EP-07）→ N3 结构锁定下生成（只准读 `packets/ep{NNN}.md`）→ **S3.5 对白二次调整（DP 自动挂载，出 `*_dlg.md`）** → N4 加跑 `scripts/source_outline.py check`（GA-06~08）＋ `scripts/check_adapt.py`（G1~G9）→ S5 额外呈现四份脚本报告（`01_体检报告_脚本.md` / `01_体检报告_纲源.md` / `01_验收.json` / `01_语义门禁.json`）＋ `04_对白调整登记.md` ＋ `00_净稿报告.md` ＋ `00_授权检查.md` ＋ `01_分集规划检查.md` ＋ 纲解析报告，决策点清单含四类待确认项。细则见 `workflows/source-outline-draft.md`。

**MR-08 自动调度差异（只换生成执行方）**：`plan` 按 MR-03 排逐档任务，`run --live` 直调 API 产出同上格式的初稿，`verify` 只验不改；**不产出终稿、不合并版本、不替用户挑稿**。默认批次不含台词精修（需 `--dialogue-pass`）与卷级回顾（需满 10 集），定调档每卷仅 1 集——这是 CC-03/MR-03 的正确行为，不是漏跑。

## 4. 断点续跑与回退

开始先读 manifest.json → 从第一个非 done 的 stage 继续；S4 杀稿后用户要求补版 → S3 只补被杀版本，S4 只复验补版；改预算（S1）或改挂载模块 → S3/S4 置回 pending 重跑。走 MR-08 时另有**任务级**续跑：`manifest.dispatch.tasks` 中 done 跳过、failed 不写产物、下游 blocked，`run --retry-failed` 只重跑 failed + blocked。

## 5. 自定义模块系统

核心规则（CR/HK/DR/MR）之外的一切扩展都是**可插拔模块**，放 `modules/<类型>/<名称>.md`（类型：platform 平台包 / genre 题材包 / style 风格包 / process 流程包），规范与注册见 `modules/_registry.md`。挂载点：S0 选择、S3 生成注入、S4 附加验收。新增模块不改核心规则文件；用户可在对话中即兴声明新需求（如"按武侠套路来"），该需求按 registry 规范落成模块文件后挂载——即兴需求沉淀为可复用资产。

## 6. File Map

```
SKILL.md                                 总控（本文件）
workflows/full-draft.md                  Mode 1 六步细则
workflows/ep-redraft.md                  Mode 2 单集重跑细则
workflows/source-outline-draft.md        Mode 3 按纲改编（原文+大纲/细纲→初稿）
rules/craft-core.md                      编剧核心 CR-01~NN（三层方法论：要素/动力/呈现）——技能的灵魂
rules/hook-quota.md                      钩子系统 HK-01~09
rules/consistency.md                     一致性注入 DR-01~04
rules/model-routing.md                   引擎路由 MR-01~08（含 MR-07 端点映射 / MR-08 自动调度）
rules/opencode-adapter.md                OpenCode 宿主适配层 OC-01~08（实时模型探测 / 子会话派发 / 上下文预算 / 结果可见；宿主优先）
rules/cost-control.md                    成本控制 CC-01~04（规则只读一次/便宜引擎打底/分批跑）
modules/_registry.md                     自定义模块规范与注册表
modules/platform/structure-templates.md  平台结构包 ST-00~07（可选挂载）
modules/process/source-outline.md        按纲改编 SO-01~08（Mode 3 自动挂载）
modules/process/dialogue-pass.md         对白二次调整 DP-01~08（S3.5 独立工序；Mode 3 自动挂载）
modules/process/source-hygiene.md        授权与净稿 SH-01~07（S0 阻断 + N0 入库；全部 Mode 默认挂载）
modules/process/episode-plan.md          分集规划三要素 EP-01~07（S1 产出 + S4 合并门；全部 Mode 默认挂载）
reference/source_clean.rules.json        净稿默认词表 v1.1（SH-04 / SH-L06 转载站声明；项目专属规则走 --exclude-patterns）
review/preflight.md                      闸门A验收清单（C1）+ 脚本化硬指标 GA-01~12（含 GA-12 形态门）+ SH/EP 前置阻断
review/audit.md                          执行审查（C2，含 A12/A13）
reference/screenwriting-theory.md        编剧方法论 21 节原文（事实源备份，永不改）
reference/topic-snapshot.json            题材雷达数据快照（带采集日期，MS-05 时效闸门）
reference/emotion-turns.jsonl            情绪转折点库（EH-05/06，每行一 JSON）
reference/market-baseline.md            题材快照人读索引 / reference/emotion-turns.md 库说明
scripts/check_gate_a.py                  闸门A 脚本化硬指标（GA-01~12，含 GA-12 形态门；纯标准库）
scripts/adapt_gate.py                    语义门禁 G1~G9（通用版；项目专属判据走 adapt_gate_config.json）
scripts/check_adapt.py                   一键验收：机械项 + 稿件形态门 GA-12 + 语义门禁合并结论（--selftest / --skip-shape / --no-filter）
scripts/_text_util.py                    正文边界/汉字归一/最长公共子串/旁白行/稿件形态 GA-12/**稿件文件识别（三入口共用防报告自扫）**（含 selftest）
scripts/check_authorization.py           S0 授权阻断（init-template / check / selftest；SH-01/02；登记表自定义名自动发现）
scripts/check_episode_plan.py            分集规划三要素门（init-template / check / selftest；EP-01~08；--episodes 支持区间批次口径）
scripts/source_outline.py               按纲改编引擎（ingest 含净稿清洗 / refresh 含三要素注入与钩子预算同源派生 / check / init-template / selftest；GA-06~08）
scripts/engine_dispatch.py              六档位自动调度（plan / run / status / verify / init-config / selftest；MR-08）
scripts/topic_radar.py                  题材雷达（query / check / refresh / selftest）
scripts/emotion_library.py              情绪库（verify / stats / query / append / import / selftest）
scripts/lint_skill.mjs                   包一致性自检
MAINTENANCE.md / CHANGELOG.md / README.md / 安装与使用说明.md / 图解使用指南.html
```

## 7. 维护约定

修改前读 MAINTENANCE.md；变更记 CHANGELOG.md；改完跑 `node scripts/lint_skill.mjs`。平台包数据每季度联网复核（平台机制/榜单变化），以复核为准更新并注明日期；新题材/新风格按 registry 规范增模块，不动核心。改动调度引擎或 MR-03/07 表后，另跑 `python scripts/engine_dispatch.py selftest`（离线零调用）。
