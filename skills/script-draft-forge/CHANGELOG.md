# CHANGELOG — script-draft-forge

## v1.2.4 · 2026-11-09 · 授权模块剥离（SH-01/02 整体移除，净稿保留）

**动机**：用户拍板「剥离编剧技能的授权模块，彻底去除」。S0 每次出稿都要求先填九字段《00_授权登记表》并通过 `check_authorization.py` 阻断检查，是流水线最大的固定摩擦；IP 授权核对本就不是脚本能判的事（SH-02 自己也声明「只核字段不判法律效力」）。净稿清洗（SH-03~07）与出稿质量直接挂钩，用户拍板保留。

**改动**：
1. 删除 scripts/check_authorization.py 及 ingest 的 `--authorization` 参数、ingest-manifest.json 的 authorization 字段、相关 WARN 提示——授权登记/阻断从流水线里消失，S0 不再因授权拦稿。
2. `modules/process/source-hygiene.md` 更名为「净稿（原文清洗）」，删除 SH-01/02 两节；SH-01/02 编号永久弃用，SH-03~07 编号不变以免连锁改号。SH-07 验收门改为只核净稿报告落盘与待确认清单处置。
3. 摘要、S0/S4 流水线表、产物目录树、Mode 3 工作流、preflight 清单、模块注册表、MAINTENANCE、README 同步去除全部授权阻断表述；净稿门成为 S0 唯一前置硬门。
4. `_text_util.py` / `check_gate_a.py` 自检取消「00_授权检查.md」fixture；`_text_util.py` 报告标题关键词移除「授权检查」（旧项目里已生成的授权检查报告仍会被「检查/报告」类文件名兜住，不会混进验收分母）。
5. **净稿全部能力不变**：SH-L01~06 词表、乱码/板块头只标记、`--exclude-patterns`、`--apply-sections`、超上限降级，照旧。

**边界（不夸大）**：本版只剥授权，不改任何验收判据；SH-03~07 规则编号与词表未动；旧项目 pipeline 里遗留的 `00_授权登记.md`／`00_授权检查.md` 文件不做删除，也不参与验收（报告类过滤兜底）；本版未重出任何稿件，未跑 LIVE。

## v1.2.3 · 2026-11-06 · 回归遗留四项口径修复（报告自扫 / 授权表命名 / packets 预算行 / 中间批次集数）

**动机**：`第10-12集链路回归测试报告.md` §4 登记了 6 个问题，v1.2.2 修掉最严重的 2 个（GA-12 假绿、净稿词表），剩 4 条只登记未改，用户拍板「继续修」后落地本版。四条都属**口径不一致**，不是新增能力，故不加模块、不加门禁编号。

**改动（每条=回滚单元）**：
1. **报告自扫污染**：`scripts/_text_util.py` 新增 `is_draft_candidate()` / `iter_draft_files()`，文件名（任意 `NN_` 编号前缀 + 报告/索引/检查/验收/规划/登记…关键词）与首部标题双层判定；`check_gate_a.py`、`source_outline.py check`、`check_adapt.py` 三个入口共用。旧规则只排 `00_/01_` 与「报告/索引」，漏了 `闸门A.md`、`03_覆盖验收_E10-12.md`。`check_adapt.py` 增 `--no-filter`（默认过滤显式传入的报告类文件，打印 SKIP 清单；过滤后为空返回 2）。显式单文件传参仍被尊重。
2. **授权表自定义名判 BLOCK**：scripts/check_authorization.py（已于 v1.2.4 删除）新增 `discover_registry()`。优先级＝显式 `--registry` > 默认名 `00_授权登记.md` > pipeline 内自动发现（名字含「授权登记／授权表／授权与净稿」，排除检查报告/模板/副本，内容排除「阻断项／字段快照」）。多候选按字段完整度取最全者，并在报告 `infos` 列出全部候选要求人工确认唯一来源；缺表时报告列出目录内 .md 清单。检查报告永不被误认为登记表。默认名与九字段判据不变。
3. **packets 钩子预算行缺失**：`scripts/source_outline.py` 新增 `episode_plan_hooks()`。`build_packets()` 在 `01_钩子预算表.md` 缺失或只有占位内容（未命中本集行）但有《逐集三要素表》时，钩子预算行改为「尾钩取自《…》「尾钩」列，与下方三要素行同源」＋尾钩文本，**不再谎报「S1 尚未产出本集预算行」**；两者都没有时才提示补 S1。三要素行照常注入。
4. **中间批次集数口径**：`scripts/check_episode_plan.py` 新增 `parse_episode_spec()` / `scope_of()`。`--episodes` 纯数字 N＝全剧口径（要求 1..N 齐备，向后兼容）；区间 `10-12`／逗号列表＝**批次口径**（只要求这批齐备）；不给＝只查表内集号连续。`init-template --episodes 10-12` 直接生成第 10–12 行。报告与 JSON 增 `episode_scope` 字段，非法串返回 exit 2。`engine_dispatch.py plan --episodes` 本来就是区间语法，未改。

同步 `SKILL.md`、`review/preflight.md`、`MAINTENANCE.md`、`modules/process/episode-plan.md`（EP-08）、`modules/process/source-hygiene.md`、`workflows/full-draft.md`、`workflows/source-outline-draft.md`。改动前 52 个文件整包备份在 `测试/_work/技能改动备份_四处修复_20261106/`。

**验证**：8 个脚本自检全过（新增 4 组用例）、`py_compile` 全过、`lint_skill.mjs` exit 0；E10-12 隔离回归复跑：报告写进被扫目录不再计入分母、自定义名授权表 PASS、packets 预算行同源派生、`--episodes 10-12` 放行而全剧 12 集口径仍判缺 1..9；真稿 10 份零误杀。详见 `测试/四项缺陷修复报告.md`。

**边界（不夸大）**：自动发现只认「像登记表」的文件名，**不判定授权真实有效**（SH-02 不变）；多候选仍需人确认唯一来源；报告过滤是「防自扫」不是「防绕过」，故意验收报告类文件用 `--no-filter`；批次口径只改字段齐备判定，不改变 `source_outline.py check` 的细纲必留条目判杀；本版**没有重出任何稿件**，未跑 LIVE，ddhz 与六档位真实项目未改动。

## v1.2.2 · 2026-11-06 · 稿件形态门（GA-12）与默认净稿词表补漏

**动机**：第 10–12 集链路回归（零计费、隔离目录）实测出两处漏放。① 12 份 DRY 演练占位稿（57–68 字、0 场、0 句人物对白）被 `check_gate_a.py` 与 `check_adapt.py` **全部判「验收通过」**——门只查「有没有违规」，不查「有没有戏」，与之前「16/16 全绿」是同一类病；当时只靠 `verify` 的 DRY 标记和覆盖验收兜底，单独跑门禁脚本必给假绿。② 默认净稿词表漏「本站所有小说为转载作品，所有章节均由网友上传…」句式，3 行残留进了生成包（当时靠 `--exclude-patterns` 临时补，未回流默认词表）。用户拍板「落地①形态门＋②净稿词表」后修本版。

**改动（每条=回滚单元）**：
1. `scripts/_text_util.py` 新增 `scene_count()` / `draft_shape()` 与 `selftest()`：稿件形态统一口径＝演练占位标记／人物对白句 0／场次标记 0。场次**宽松识别** `【场1｜…】`／`## 场1`／`第1场`／`1-1　日　外　…`（六档位调度真稿用最后一种，只认一种格式会把真稿误杀）。**不设字数下限、不判语义、不判质量**。
2. `scripts/check_gate_a.py` 增 **GA-12**（默认启用，与 DP 模块挂载无关）：形态不达标 → FAIL，报告写「不予验收」并与内容违规分开陈述；`config.skip_shape_gate=true` 只关判杀、数值仍留痕。报告增形态与场次数两列，CLI 打印形态，配置模板加说明。
3. `scripts/check_adapt.py` 增 `稿件形态门（GA-12）` 字段与 `--skip-shape`；结论三态区分「不予验收／未通过／验收通过」，机械项场数改用共用的 `scene_count()`（与闸门A 同口径）。新增 `--selftest`；**退出码改为 0=全通过／1=有未通过或不予验收**（此前恒为 0，结论文案改了但命令链/CI 仍会读成通过）。
4. `reference/source_clean.rules.json` 升 **v1.1**：新增 `SH-L06` 删「本站所有小说为转载作品…」整行免责声明；疑似脏行标记 ID 由 `SH-L06` 改 `SH-G01`，避免与整行噪声规则同号。`scripts/source_outline.py` 同步改 ID，selftest 增 3 条断言。
5. 同步 `SKILL.md`（S4 验收栏／File Map）、`review/preflight.md`（GA-12 定义与清单）、`MAINTENANCE.md`（编号表）、`modules/process/dialogue-pass.md`（DP-08）、`modules/process/source-hygiene.md`（SH-04 类别表）、`workflows/full-draft.md`、`workflows/source-outline-draft.md`（判定顺序／词表）、`README.md`、`scripts/engine_dispatch.py`（verify 标签）。改动前 52 个文件备份在 `测试/_work/技能改动备份_形态门_20261106/`。

**开发中发现并修掉的缺陷（留痕）**：形态门初版只认 `【场N｜` 一种场次格式，会把六档位实跑真稿（`1-1　日　外　国营饭店门口`）误判成「没有戏」→ 改宽松识别并写进自检；`body_lines()` 有场标记时会截掉首场之前的 DRY 提示行 → DRY 检测改查全文；`SH-L06` 与疑似脏行标记同号 → 后者改 `SH-G01`。

**验证**：`_text_util.py` / `check_gate_a.py` / `check_adapt.py`（新增）/ `source_outline.py` 自检全过；默认词表在真实原文第 10–12 章上删 6 行（3 行 SH-L06 + 3 行 SH-L03）、逐条登记、待确认 0 行，章节数仍为 3；E10-12 回归复跑：12 份 DRY 稿全部「不予验收」，故障注入稿原有 GA-04／GA-10／GA-11／G2／G9 命中不变，ddhz v3 真稿与六档位实跑真稿零误杀；`py_compile` 全脚本通过、`lint_skill.mjs` exit 0。详见 `测试/第10-12集链路回归测试报告.md` 与 `测试/形态门与净稿词表修复报告.md`。

**边界（不夸大）**：形态门只判「有没有戏」，**不判断这一集好不好看、不替代 G8 逐句溯源与 DP-04 朗读**；`--skip-shape` / `skip_shape_gate` 关掉判杀后仍会给假绿，仅用于兼容存量异格式稿，不得当验收结论；净稿词表只删整行高置信噪声，番外／乱码仍待人确认；本版**没有重出任何稿件**，ddhz 与六档位真实项目未改动。环节 2／4／6／7 与 1→7 总编排仍未做。

## v1.2.1 · 2026-11-06 · 补齐环节 1「授权与净稿」与环节 3「信息增量字段」

**动机**：承接 7 环节覆盖度核查的 P1。此前技能全库只有 `clean_xml_dump()` 清 docx 残留标签，**IP 改编权链零命中**，番外／作者附言／转载站广告／乱码行无任何规则；环节 3 则是**倒着走**——Mode 3 只消费外部细纲，从不用技能产出分集大纲，`01_钩子预算表.md` 有四级钩位/台账却无「本集核心事件」「本集信息增量」字段，「冲突／信息增量／尾钩」三者从没一起判过。项目里两处纲源事实错误被原样继承到 16 版，根子就在这。用户拍板「先做①授权净稿＋③信息增量字段」后落地本版。

**改动（每条=回滚单元）**：
1. 新增 `modules/process/source-hygiene.md`（SH-01~07）：授权链 S0 必填阻断（九字段、短剧与漫剧双覆盖、渠道不得「待定」）、**只核字段不判法律效力**、净稿副本与不默删、剔除类别置信分层、乱码只标记、番外整段剔除须显式开启、验收门。注册进 `_registry.md`，**全部 Mode 默认挂载，授权阻断不可卸载**。
2. 新增 `reference/source_clean.rules.json`：整行噪声 5 类默认 remove，板块头与疑似乱码默认 flag；`apply_sections` / `max_removed_ratio` 等可调。项目专属规则走 `--exclude-patterns`，不改默认词表。
3. 新增 scripts/check_authorization.py（已于 v1.2.4 删除；init-template / check / selftest）：缺登记表或字段 → **exit 1 阻断**，报告固定带法律效力边界声明。
4. `scripts/source_outline.py ingest` 接入净稿：新增 `--clean-config` / `--exclude-patterns` / `--no-clean` / `--apply-sections` / `--authorization`；产出 `pipeline/00_净稿报告.md`（逐条原始行号＋原句＋规则 ID＋理由、原文件 sha1、两套行号口径说明），`source-index.json` 增 `cleaning`，`10_原文索引.md` 增净稿小节，`ingest-manifest.json` 记授权状态。**原文件只读不改**；乱码/板块头默认只标记；删除超上限整体降级为不删。
5. 新增 `modules/process/episode-plan.md`（EP-01~07）：S1 必产《逐集三要素表》＝集／本集核心事件／明确冲突／本集信息增量／尾钩／出处；信息增量定义为**新知道的事实**（非钩子复述、非「爽点升级」）、相邻集不得逐字相同、出处回指、S4 合并门缺一即杀、**生成期注入 packets**。
6. 新增 `scripts/check_episode_plan.py`（init-template / check / selftest）：机检集号连续、三要素齐备率、相邻集逐字重复（FAIL）、增量复述核心事件/尾钩与非汉字出处（INFO 候选）。齐备率 <100% 不得写「HK-09 通过」。
7. `scripts/source_outline.py build_packets` 新增 `episode_plan_rows()`：refresh 时把本集三要素行注入 `packets/ep{NNN}.md` 的「需求与预算」段。**只放进验收表不进生成上下文等于这一环没落地**。
8. 同步 `SKILL.md`（触发词／目录树／S0/S1/S4 流水线表／Mode 3 差异／File Map）、`modules/_registry.md`、`MAINTENANCE.md`、`review/preflight.md`（S0 前置阻断与 S4 合并门）、`workflows/full-draft.md`、`workflows/source-outline-draft.md`（N0/S1/N4/S5 命令链）。改动前 9 个文件备份在 `测试/_work/技能改动备份_P1_20261106/`。

**开发中发现并修掉的四个缺陷（留痕）**：
- **短文本上安全上限让净稿整失效**：`max_removed_ratio=0.05` 按整篇字符数算，测试短原文里两条广告行就占 16% → 触发「整体降级为只标记」，删除数为 0。现取「比例上限」与 `min_removed_chars_floor=200` 的较大值，短文本少量噪声不受误伤，长文比例约束仍生效。
- **出处列被汉字数误判为空**：`CH001` 这类引用汉字数为 0，被 `missing()` 判缺出处。三要素仍按中文事实句验，出处改用只查空/占位的 `empty_value()`。
- **复述检测没做汉字归一**：`longest_common` 直接比原始串会被标点打断，现统一传 `cjk_only()`，与语义门口径一致。
- **自检用例重合长度不足阈值**：复述用例连续重合仅 6 字、默认阈值 8，改成真实长度用例，另加断言确保非汉字出处不误报。

**验证**：`source_outline.py selftest` 新增 5 组净稿/注入断言（含 `--no-clean`、`--exclude-patterns`、`--apply-sections`、超上限降级）、`check_authorization.py selftest` 4 组、`check_episode_plan.py selftest` 5 组，全部通过；`py_compile` 全脚本通过；`lint_skill.mjs` exit 0（无悬空引用、无路径腐烂）；`engine_dispatch.py selftest` 37 项、`check_gate_a.py` / `adapt_gate.py` 自检不受影响（CLI 向后兼容，ingest 新增参数全部用 `getattr` 兜底）。

**边界（不夸大）**：① 授权检查只核字段，**不判法律效力**，也不替用户确认改编权是否真实覆盖分发渠道；② 净稿规则只删整行高置信噪声，番外/乱码一律待人确认，不判断语义、不替用户决定「这段算不算正文」；③ 三要素门只查字段齐备、集号连续与逐字重复，**不判语义、不判这一集好不好看**，出处缺失只给 INFO 不自动判过；④ 本版**没有重出任何稿件**，ddhz 项目未被改动；环节 2 人物功能表、环节 4 场数↔时长、⑥ 资产自动核对、⑦ 全片时长误差率、1→7 总编排仍未做。

## v1.2.0 · 2026-11-06 · 补齐「对白二次调整」独立工序与语义门禁

**动机**：拿「小说转剧本 7 环节」清单对 25 个生效技能做覆盖度核查，结论是**用户标注「返工率最高」的第 5 环恰好是技能里最弱的一环**——全库只有 `cinematic-seedance-director` 一句「单句 ≤15 字为宜」（软建议、仅 P1 管线、且写在视频提示词层），`script-draft-forge` 的口语化只是 MR-08 的可选台词档（默认批次不跑）。实测后果：《怼父皇打皇兄》Mode1 旧 16 版被 v2 尺子判 16/16 全绿，实际满是人称错位、剧透、破第四面墙、A/B 逐字同旁白；为修它而在项目目录里临时补的 `改编规范_v3.md` / G1~G9 / 事实台账**从未回流技能**，换项目必然原样复发。本版把这一环做成技能内的常设工序与机检门。

**改动（每条=回滚单元）**：
1. 新增 `modules/process/dialogue-pass.md`（DP-01~08），注册进 `modules/_registry.md`：**S3.5 独立工序**（禁止并进 S3 生成提示词）、单句 8–15 字（按占比判）、书面语→口语、朗读顺口、旁白三禁、叙述腔直搬禁令、A/B 同旁白禁令、验收登记。**Mode 3 自动挂载**（与 SO 并列），Mode 1/2 显式声明挂载、卸载须登记。
2. 新增 `scripts/_text_util.py`：统一正文边界（首场 → 登记块之前）、汉字归一、最长公共子串、旁白行与跨文件同旁白。**两个脚本共用**，杜绝「同一份稿两种结论」，同时修掉「文末登记引用被删原句 → 门禁自污染」这个已实测的误报。
3. 新增 `scripts/adapt_gate.py`（G1~G9 通用版）：项目专属判据（G5 规则剧透／G6 说话人映射／G7 关键动作断言／G9⑤ 无据概念／G4 禁用表）**全部改为 `adapt_gate_config.json` 配置驱动**，未配置即跳过并给提示、不编造期望值；通用剧作法判据（叙述腔进台词／不可见内心／破第四面墙／解说型旁白／数字白名单）保留为内置。带 `--init-config` / `--selftest`。
4. 新增 `scripts/check_adapt.py`：机械项（只报数不判杀）＋语义门禁合并成一份结论，附 8–15 字区间外占比门。
5. `scripts/check_gate_a.py` 扩到 **GA-01~11**：GA-09 单句占比（`enforce_dialogue` 未开时只报数，避免误杀存量稿）、GA-10 旁白与原文连续重合、GA-11 跨文件同一旁白。正文口径统一到 `_text_util.body_lines`，字数/轮次不再把文末登记算进去。selftest 补 5 组断言。
6. `scripts/engine_dispatch.py` verify 标签改 GA-01~11，并在存在 `pipeline/source/` 时自动带 `--source-dir`（让 GA-10 真正生效）。**CLI 接口向后兼容**，37 项 selftest 全过。
7. 同步 `SKILL.md`（触发词／模式表／产物目录／流水线表新增 S3.5／File Map）、`workflows/source-outline-draft.md`（新增 S3.5 章、N4 三条命令、S5 四份报告）、`review/preflight.md`（GA-09~11 定义与 DP 挂载验收项）、`MAINTENANCE.md`（编号表）、`rules/model-routing.md`（验收口径）。

**回归中发现并修掉的两处新门禁自身缺陷**（都是「尺子量错地方」的同型问题，留痕以防复发）：
- **切句器误判**：动作括号里的冒号（「（一声闷响。特写：键盘上一个巴掌印。）」）被当成说话人，B 版虚增 10 句。`_text_util.dialogue_sentences` 现跳过动作行／场景行、并拒绝含句读的「说话人」，selftest 加断言。
- **8-15 字口径挂上即全杀**：按「区间外总占比」判时，v3 两版越界 72%／59%，拆开看 **<8 字短节奏句占 33%／42%、>15 字超长句占 39%／17%**——短剧短句合法，机械套区间必误杀。GA-09 与 `check_adapt.py` 占比门统一改为**只拿 >15 字超长句占比判杀**（短句按 DP-02 登记例外），DP-02／GA-09 定义／配置模板同步。修正后 A 版 39% 超阈值（真实待拆长句），B 版 17% 通过。

**验证**：
- `check_gate_a.py --selftest` 4 组（含 GA-09 超长句占比判／纯短句不误杀／GA-10 直搬／GA-11 同旁白／正文截断／未启用不误杀）、`adapt_gate.py --selftest` 7 组（含动作行排除）、`engine_dispatch.py selftest` 37 项、`source_outline.py selftest` 全过、`py_compile` 全脚本通过、`lint_skill.mjs` exit 0。
- **等价性回归**：把项目专属判据导出成 JSON 后，通用器在 ddhz Mode1 旧 16 版上得到 **判杀 9 版／G9 命中 16/16 版／A-B 同旁白 7 组**，与项目脚本 `pipeline/adapt_gate.py` 原有结论完全一致；Mode3 清理后与 Mode1 v3 已修稿均零命中。

**诚实边界**：本版只补第 5 环与其配套门禁。**7 环节里的 ①授权与净稿（IP 改编权链、番外/转载站清洗）、②人物功能表／删人测试、③分集大纲产出与信息增量字段、④场数↔时长换算与每场戏剧任务，仍未补**；⑥⑦ 已有能力但链路未接通。GA-10 未给 `--source` 时只降级 INFO、不假装检查过；改写型解说旁白逐字重合抓不到，仍须人工按 DP-05 判；拼音级绕口检测需注音库，本版不做。S3.5 只改呈现层，不替用户重出稿。

## v1.1.3 · 2026-11-04 · 首次 `--live` 实跑后的稳定性修复

**动机**：用《穿越七零》真实生成包跑 `run --live --dialogue-pass`（2 集 × 2 版，11 个任务，5 个档位），三轮断点续跑全部完成。实跑暴露的问题全部是「演练 mode 测不出来」的真故障，逐条修掉并补自检。

**改动**：
1. **`disable_thinking` 默认改为 `true`**：GLM 在 3096 字符编剧 prompt 下把 4500 token 全花在 `reasoning_content`（11620 字符）导致正文为空；关思考后 1109 token 即出 1463 字正文。GLM 发 `enable_thinking:false`、Hy4 发 `thinking:{"type":"disabled"}`。
2. **空正文自动升级**：首次空正文后强制关思考并把 `max_tokens` 抬高 50% 再试，不再原样重试三次白烧预算。
3. **瞬时故障重试**：聚合网关偶发 `404 Invalid URL (GET /v1/chat/completions)` 纳入 `RETRY_CODES`；`TimeoutError` / `URLError` / `ConnectionError` 纳入 `RETRY_EXC`（kimi 台词档实测读超时）；每次重试重建 Request，`timeout` 默认 120→180 且逐次递增。
4. **真实 HTTP 调用计数修正**：原先 `API 调用` 只在 mock transport 下递增，LIVE 报告恒为 0；现两条路径都计数。
5. **下游注入剥离产物头**：`strip_product_head()` 去掉 MR-06 版本头与演练占位，修复挑稿档把 `> 版本：…` 当成「输出非剧本正文」硬伤的误判；`status` 区分「当前计划 10 个」与「含历史归档 11 个」。
6. **GA-02 白名单真正生效**：`check_gate_a.py` 注释写了「确认不同角色则写入 name_whitelist」但代码从未读取该字段；现双角色均命中白名单时降为 INFO 不判杀。原文中「青年甲（得意）」「青年乙（羡慕）」是两个独立角色，据此生成 `gate_a_config.json`（13 人）。
7. **验收文件筛选统一**：`check_gate_a.py` 与 `source_outline.py` 的 `draft_files` 都排除 `00_/01_` 前缀及含「报告/索引/README/manifest/config」文件，修复体检报告把自己当稿件扫描的自我污染。
8. **成本报告补口径**：只汇总成功返回 `usage` 的任务，空正文/超时重试若已计费不计入，账单可能略高。

**实跑结果（留痕，非演练）**：11 任务全 done；成功任务合计 **47,377 token**（prompt 20,447 / completion 26,930），未配单价故不折算金额；GA-06~08 细纲覆盖 8/8 版本 100% 通过；GA-01~05 原始 11 FAIL，配置复核后降到 **4 条真实 GA-04 AI 套话硬伤**（ep002 四版「绕着屋子走…冷笑」）；挑稿档推荐 ep001/ep002 的 `A_v2`。真实稿件保留在 `历史实跑目录（六档位调度_实跑）`。

**验证**：`engine_dispatch.py selftest` 37 项、`check_gate_a.py --selftest` 3 项、其余 5 个 selftest、`lint_skill.mjs` exit 0、全量 `py_compile` 全过。

## v1.1.2 · 2026-11-04 · 六档位自动调度引擎（MR-08）

**动机**：MR-07 补齐端点后，仍只解决「选得到」。OpenCode 一个会话只加载一个模型，六档位混跑要手动分批切换；用户要求把「按 id 逐档直调、配合 manifest 断点续跑」真正做出来。

**改动**：
1. 新增 `scripts/engine_dispatch.py`（纯标准库，6 子命令）：`plan` 按 MR-03 自动排任务（骨架→定调→批量→[台词精修]→挑稿，满 10 集自动排卷级回顾）、`run` 逐档直调 API、`status`、`verify`、`init-config`、`selftest`。读 `~/.config/opencode/models.json` 解析 MR-07 的六个 id，端点缺档直接停机不静默降级。
2. **默认演练零计费**：不带 `--live` 零 API 调用，产物带 `DRY_MARK` 占位，`verify` 一律拒绝验收；`--live` 才真实调用 DMXAPI。apiKey 只在内存，selftest 含零外泄断言。
3. **断点续跑**：`manifest.dispatch.tasks` 逐任务记录 done / failed / blocked，done 跳过、失败不写产物、下游自动 blocked，`--retry-failed` 重跑 failed + blocked。
4. **成本与验收**：`dispatch-cost.md` 只报 token 用量，未配 `price_per_1k` 不编造金额（CC-04）；规则不整读、只注入精简硬约束 + 本集生成包（CC-01）；`verify` 只验不改，明确区分退出码 1（判杀）与 ≥2（执行异常）。
5. 新增 `rules/model-routing.md` MR-08；`MAINTENANCE.md` 改 MR-01~08 并加调度引擎回归项；`SKILL.md` 加触发词 / 可选执行层说明 / 产物与 File Map；README、安装说明、图解指南同步。

**验证**：`selftest` 27 项全过（六档位全覆盖、定调仅 1 次、依赖顺序、端点缺失拦截、演练零调用与占位、MR-06 产物头、凭据零外泄、mock live 全链路、断点不重复计费、双脚本闸门A 的判杀/异常区分、失败不写产物 + 下游 blocked、init-config 模板）。真实《穿越七零》生成包端到端演练：7 任务全部 done、0 API 调用、verify 正确拒绝演练稿。

**诚实边界**：调度器只是执行层，**不挑稿拍板、不合并版本、不改稿、不出终稿**；S5 仍按铁律 8 由人确认。默认批次不会跑满六档（台词精修需 `--dialogue-pass`、回顾需满 10 集、定调每卷仅 1 集），这是 MR-03/CC-03 的正确行为，不是漏跑。端点失效时停机，按 MR-05 由用户切内置模型重跑并注明降级。演练稿一律不得计入交付。

## v1.1.1 · 2026-11-04 · 补齐六档位端点并固化映射（MR-07）

**动机**：本机 `~/.config/opencode/models.json` 原先只有 1 条外部端点，MR-03「质量优先」预设的六档位混跑实际会按 MR-05 全部降级为会话模型，分工形同虚设。

**改动**：
1. 先查聚合端点 `/v1/models`（返回 522 个模型）取真实 `model` id，再追加骨架 / 骨架备选 / 台词 / 批量 / 挑稿 5 条 `Custom` 端点；连同原有定调·回顾·挑稿备选共 6 条覆盖全部档位。复用原条目的 url + apiKey，原条目保持不动，改动前备份 `models.json.bak-20261104`。
2. 6 条端点逐条实机验证：普通 chat 返回 200、能出中文正文、function calling 均返回 `tool_calls`；记录推理模型思考预算实测（80 空 3 条 / 200 仍空 glm·hy4 / 400 与 800 全正常）与直调降本参数，据此保留 `supportsReasoning=false`、`supportsToolCall=true`。
3. 新增 `rules/model-routing.md` MR-07「本机端点映射」：档位 ↔ 选择器显示名 ↔ API id、验证口径、零成本预设不走外部端点、端点故障降级纪律、换 key 流程、「端点补齐 ≠ 自动分档」硬约束。
4. `MAINTENANCE.md` 编号表（MR-01~07）与季度复核项同步。

**诚实边界**：补齐的是「可选端点」，不是自动调度。OpenCode 一个会话只使用一个模型，六档位仍需按 MR-03 在 S1/S3/S4 分批切换，或由外部编排层按 id 逐档直调；配置保存后自动重载（必要时 /reload）。选中外部端点会产生 DMXAPI 计费，零成本预设仍走内置模型。

## v1.1.0 · 2026-11-04 · 新增 Mode 3「按纲改编」（小说原文 + 大纲/细纲 → 初稿）

**动机**：用户要求「能把小说原文放进去，再把编剧细纲大纲放进去，然后出初稿」。原 Mode 1 只收素材简介，遇到整本小说 + 编剧已定细纲有两个真问题：全文入上下文必然爆窗、模型会自作主张改结构；细纲逐条有没有落地靠模型自报等于没查。

**改动**：
1. 新增 `scripts/source_outline.py`（纯标准库）：`ingest` 读原文（.txt/.md/.docx，含 docx 残留 `<w:t>` 脏文本清洗）、按章节切片入库（稳定 ID + 字符偏移 + 人名/术语候选）；解析大纲/细纲（md/txt/docx/csv/tsv/xlsx，支持 `# 大纲`/`# 细纲` 分节、表格列名、行内 `锚点/人物/钩子/原文第X-Y章/可选` 标签），逐条编号 `EP{NNN}-B{NN}`；显式章节引用作准、无引用按左右邻居插值推定并告警；产出 `10_原文索引.md`、`12_纲解析报告.md`、`packets/ep{NNN}.md` 逐集生成包。`refresh` 在 S1/S2 后重打包注入预算行与四件套；`init-template` 出模板；`check` 执行 GA-06~08；`selftest` 端到端（含 docx/xlsx 二进制读取器、只有大纲、邻居插值、refresh）。
2. 新增 `modules/process/source-outline.md`（SO-01~08）与 `workflows/source-outline-draft.md`（N0→S0→S1→S2→refresh→N3→N4→S5）。**结构听细纲、事实听原文**；细纲锁定结构（铁律 6 唯一例外），同集多版差异化降级到呈现层四轴并在文件头声明；只给大纲时升格为「事件锁定」。
3. `SKILL.md`：description/when_to_use 加 Mode 3 触发词；铁律 6 加例外；§1 模式表、§2 产物目录、§3 Mode 3 差异、§6 File Map 同步；`modules/_registry.md` 登记 SO 模块。
4. `review/preflight.md` 定义 GA-06~08 并列为 Mode 3 必过项；`review/audit.md` 加 A12/A13、A7 加 Mode 3 例外；`MAINTENANCE.md` 编号表同步。
5. `README.md` 加场景 6、需求表两行、文件地图；`安装与使用说明.md` 升版本并加快上手；`图解使用指南.html` 加 Mode 3 图解段。

**诚实边界**：脚本不判断语义（锚点命中 ≠ 细纲落地）；章节自动分配是推定、人名术语是候选；原文与细纲冲突只摆证据不替用户拍板；不生成图片/视频/终稿，产物止于初稿包。

**兼容性**：Mode 1 / Mode 2 的 CR/HK/DR/MR/CC/GA-01~05 判定一律不变；SO 模块仅在 Mode 3 挂载。新增脚本纯标准库，`selftest` 不依赖任何外部数据。

---

## v1.0.6 · 2026-11-04 · 闸门A 脚本化 + 两个沉淀库落地

**动机**：写作极限测试与挑稿测试实测证明「轮次/字数靠模型自己数不可靠」；闸门A 缺「人设逐场核对」「系统条款不新增」；`reference/emotion-turns.md` 与 `reference/market-baseline.md` 长期是空壳，对 SaaS 的两处数据劣势没有可运行补位。

**改动**：
1. 新增 `scripts/check_gate_a.py`（纯标准库）：GA-01 轮次/字数脚本计数、GA-02 人设逐场核对（等长一字之差人名混用 + 旧名映射 + 固定特征）、GA-03 系统条款不新增（白名单比对，无配置只列行号不误杀）、GA-04 情绪名称词/AI 套话 lint、GA-05 术语零变体。含 `--init-config` / `--selftest` / JSON 输出，FAIL 退出码 1。
2. `review/preflight.md` 定义 GA-01~05 并把脚本报告列为闸门A 必过项；`review/audit.md` 新增 A11；SKILL.md 铁律 8、S4 行、File Map 同步。
3. 新增 `scripts/topic_radar.py` + `reference/topic-snapshot.json`：题材×平台雷达（带采集日期、90 天时效闸门、稀缺三档、`--check` / `--refresh` / `--selftest`），`reference/market-baseline.md` 填入首批带来源与日期的真实快照。
4. 新增 `scripts/emotion_library.py` + `reference/emotion-turns.jsonl`：编号化情绪转折点库（字段校验、去重、按题材查询、批量导入、统计、selftest），`reference/emotion-turns.md` 改为库说明与索引。
5. `modules/process/market-scan.md` 增 MS-05/06，`modules/process/emotion-heatmap.md` 增 EH-05/06；MAINTENANCE 编号表同步。

**诚实边界**：本补位给的是「带日期的本地快照 + 强制时效闸门 + 可增长的库」，不是 SaaS 的实时榜单 API，也不是凭空捏造的 3000 条实测转折点。3000+ 只能靠每轮闸门A 过关版自动入库与历史项目批量导入累积。

**兼容性**：核心 CR/HK/DR/MR/CC 判定不变；未配置 `gate_a_config.json` 时脚本只报数不判杀。

---

## v1.0.5 · 2026-11-04 · MR-03 升级为长文本「六档位分工」

**动机**：银时问「长文本剧本工作流用哪个／哪几个模型混合最强」。原 MR-03 只按四类职责分引擎，缺了长篇特有的「定调」与「卷级回顾」两个岗位，也没有任何条款约束跨引擎混写的接缝风险。

**改动**：
1. MR-03 由四职责扩为**六档位**：骨架档、**定调档（新增）**、台词档、批量档、挑稿档、**回顾档（新增）**，每档标注适用阶段与依据。
2. 新增**分工纪律五条**（MR-03 附则）：按「集」切不按「场」切／定调只做一次／一致性靠外置记忆不靠模型／最强引擎不写全程／验收线不随引擎浮动。
3. 新增**两套预设组合**：质量优先（约 10–15 元／40 集）、零成本（全内置 0 元）。
4. **挑稿档换人**：混元 Hy4（内置）升为首选，Claude Opus 5.5 降为备选——依据 2026-11-04 挑稿实测 40/40 第一、Claude 39 并列第二。
5. **更正 v1.0.4 证据**：ToneBench 11-04 版（132 模型）第一为 GPT-6 Sol Medium 81.06，Claude 不在前三；停止以 ToneBench 支撑挑稿档，改用本轮实测＋长篇第 1＋NC Bench 第 1。
6. 增补：混元 Hy4 于 2026-11-04 正式发布（770B MoE／1M 上下文），官方评测全为生产力场景（办公／金融／代码／科研），**创意写作零指标**；其挑稿成绩不可外推创作力。

**兼容性**：档位名保持（骨架档／台词档／批量档／挑稿档），CC-02 引用不受影响；新增档位不改变既有流程。

---

## v1.0.4 · 2026-11-04 · MR-03 四基准复核 + 台词位双选

**动机**：银时要求对比多款模型；联网采集 2026-11-04 四基准（ToneBench / lechmazur pairwise / EQ-Bench 汇总 / SuperCLUE 中文原生）交叉验证 MR-03。

**改动**：
1. MR-03 台词位改双选：豆包（保留）+ Kimi K3 加推（ToneBench #9 / SuperCLUE 中文原生 #4 / 价格中档渠道稳定）。
2. MR-03 各行补基准证据；骨架位补「中文创意写作偏弱（SuperCLUE 第12），台词位禁用」；挑稿位补「三榜验证 + 渠道思考链受限质量浮动警示」。
3. 新增 `reference/benchmark-snapshot-2026-11.md`：四基准数据快照 + MR-03 映射 + 季度复核约定（名次变动 ≥2 触发更新，快照追加不覆盖）。
4. MAINTENANCE.md §3 季度复核项挂上对照基线。
5. 同日勘误：银时截图证实宿主 **内置**即有 Kimi-K3/K3.1 Pro（订阅可用），台词位改用内置、零接入成本，Moonshot API 外接方案取消（未充值）；MR-03 同步改为「内置优先，API 为外接备选」。教训：推荐外接前先让用户翻一遍内置模型列表。

**兼容性**：无破坏性；引擎职责分工不变，仅证据更新与台词位扩容。

---

## v1.0.3 · 2026-11-04 · 成本控制规则（CC-01~04）

**动机**：实跑暴露——为读 4 万字规则花 8 元，大头是同一份上下文被系统反复重发计费；不控制则 40 集会滚成几百元。

**改动**：
1. 新增 `rules/cost-control.md`（CC-01~04）：CC-01 上下文重发是最大成本（规则只读一次、长文件按需读）；CC-02 便宜引擎打底（S0-S3 用便宜引擎，挑稿档只做 S4 挑稿或用户点名）；CC-03 分批跑+前情压缩（每批 5-10 集）；CC-04 交付前成本自检。
2. SKILL.md 铁律 2→新增铁律 3「成本可控」，原铁律 3-7 顺延为 4-8（7 条→8 条）；§3 S0 增加成本路由确认；§6 File Map 增加 cost-control.md。
3. MAINTENANCE.md 编号索引新增 CC-01~04 行。
4. 同日补充（用户确认）：CC-03 增加**卷级回顾**条款——每 10 集强制拉平摘要查全局节奏/台账进度/人设漂移，结论 ≤10 行入后续上下文；CC-02 去除具体模型名，改引 MR-03 档位（修复 MR-01 违例）。背景：40 集裸跑成本实测推算 400-600 元且会撞上下文窗口，外置记忆四层架构（锚点/台账/滚动/冷存）确认为长剧生成方案。

**兼容性**：非破坏性；CR/HK/DR/MR 判定不变，只新增“用什么跑、怎么跑不烧钱”。引擎名不写入 CC（MR-01 原则）。

---

## v1.0.2 · 2026-11-02 · 安装说明扩充模型建议（实测口径）

**动机**：银时要求安装说明加入"使用什么大模型"建议，且必须真实可靠经过检验。

**改动**：安装与使用说明.md §四 重写——①按职责分工推荐表（Claude Opus 5.5 xhigh 挑稿位 / 豆包台词位 / DeepSeek 骨架位 / GLM-5.3 Flash 批量位），每条附实测来源（LMArena / ToneBench / CNWB / Towards AI 9,050 脚本基准 / 一线编剧实操报道）②明确不推荐清单（DeepSeek 做审核主力 / Gemini 做写作主力 / max 档）③接入方式三条（零配置降级 / 支付宝聚合站 / 官方 API 协议不兼容警示）④成本参考 ⑤可信度声明（采集日期 2026-11-02 + 季度复核约定）。

**修复**：首次分发误写 C:\192.168.0.240\（Git Bash 双引号 UNC 转义坑），已转入真共享并清理假目录。

---

## v1.0.1 · 2026-11-02 · 交付纪律强化（首次实跑反馈）

**动机**：首次实跑（穿越七零测试）跑完后只交付了表格摘要，用户追问"文本呢"才补——暴露交付缺陷：结果不可见。

**改动**：
1. SKILL.md 铁律 7 重写为「结果可见 + 验收即证据」：S5 交付硬性三件套（呈现全部版本文本与索引 / 贴每集推荐版正文摘录 / 给挑稿决策点清单），缺一即未交付。
2. workflows/full-draft.md S5 与 ep-redraft.md 第 6 步同步三件套。
3. review/audit.md 新增 A10：交付回复若只给路径 = ❌。

**兼容性**：无破坏性变更；Mode 1/Mode 2 流程不变，仅交付动作收紧。

---

## v1.0.0 · 2026-11-02 · 初版建成

**定位**：纯编剧服务的初稿锻造流水线——给素材，吐可挑选的专业剧本初稿包（每集多版、结构差异化、钩子可验收、杀稿不修稿）。

**设计沿革（同日三轮迭代）**：
1. 初版架构：平台模板为纲（ST 先于一切）+ 生态耦合（指路下游四技能）。
2. 净化重构（13:00）：编剧知识三层（CR）升格为灵魂；平台包降级为可选模块；零外部技能引用；新增 modules/ 自定义模块系统（platform/genre/style/process 四类型，即兴需求沉淀为模块）。
3. 钩子系统升级（12:52）：数量预算制 → 五层钩子系统（信息差引擎/六母型轮换/四级钩位/松紧节拍/兑现台账/显隐过渡/回提四维验收）。

**文件清单（15 文件）**：

| 文件 | 职责 |
|---|---|
| SKILL.md | 总控：7 铁律 + 6 阶段流水线 + 模块系统 + 断点续跑 |
| rules/craft-core.md | CR-01~20 编剧核心三层（灵魂） |
| rules/hook-quota.md | HK-01~09 钩子系统 |
| rules/consistency.md | DR-01~04 一致性注入 |
| rules/model-routing.md | MR-01~06 引擎路由 |
| modules/_registry.md | 模块规范与注册表 |
| modules/platform/structure-templates.md | ST-00~07 平台结构包（可选） |
| workflows/full-draft.md | Mode 1 六步细则 |
| workflows/ep-redraft.md | Mode 2 单集重跑 |
| review/preflight.md | 闸门A验收清单（含情理门） |
| review/audit.md | 执行审查 |
| reference/screenwriting-theory.md | 21 节方法论原文（事实源，永不修改） |
| scripts/lint_skill.mjs | 一致性校验 |
| MAINTENANCE.md / README.md / CHANGELOG.md | 文档三件套 |

**关键决策记录**：
- 13 句钩子强制 → 用户自定义优先 + 折算兜底（12:51 银时指示）。
- 纯编剧服务净化：去除对机器既有技能生态的适配，初稿包即交付终点（13:00 银时指示）。
- CR-10 情理门为闸门A核心：AI 初稿最大质量变量 = 保矛盾情绪弃情理（21 节教程 §13 点破）。
- 钩子疲劳实证（帝一 2026）驱动五层系统：密度会反噬，类型×时序×强度×生命周期四维管理。

**回滚**：本版即首版；后续变更逐条记录，每条=回滚单元。
