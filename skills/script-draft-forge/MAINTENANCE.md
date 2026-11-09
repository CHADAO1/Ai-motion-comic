# MAINTENANCE — 编号索引与维护地图

## 1. 规则编号唯一事实源

| 编号段 | 归属文件 | 内容 |
|---|---|---|
| CR-01~20 | `rules/craft-core.md` | 编剧核心三层：要素层（CR-01~05）/ 动力层（CR-06~11）/ 呈现层（CR-12~17）/ 改编专线（CR-18~20）。事实源 = reference/screenwriting-theory.md（21 节原文，永不修改） |
| HK-01~09 | `rules/hook-quota.md` | 钩子系统五层：来源/引擎/类型/部署/生命周期/验收 |
| DR-01~04 | `rules/consistency.md` | 一致性注入：四件套/小传/金手指卡/术语表 |
| MR-01~08 | `rules/model-routing.md` | 引擎路由（规则层模型无关、默认引擎表、降级、追溯、本机端点映射、六档位自动调度） |
| OC-01~08 | `rules/opencode-adapter.md` | OpenCode 宿主适配层（实时模型探测、职责路由、子会话派发、上下文预算、结果可见、路由追溯、成本闸门、故障转移）；宿主优先于 MR-03 静态表 |
| CC-01~04 | `rules/cost-control.md` | 成本控制（上下文重发、便宜引擎打底、分批跑+前情压缩、自检） |
| GA-01~05 | `review/preflight.md` | 闸门A 脚本化硬指标（轮次/字数、人设逐场核对、系统条款不新增、情绪词 lint、术语零变体） |
| GA-09~11 | `review/preflight.md` | 对白二次调整三项（单句 8-15 字占比、旁白与原文连续重合、A/B 同一旁白逐字相同；由 `scripts/check_gate_a.py` 执行，与 `scripts/adapt_gate.py` G9 共用 `scripts/_text_util.py`） |
| GA-12 | `review/preflight.md` | 稿件形态门（演练占位／人物对白 0／场次 0 → **不予验收**；只量形态、不设字数下限、不判语义质量；场次宽松识别 `【场1｜】`／`## 场1`／`第1场`／`1-1　日　外`；`check_gate_a.py` 与 `check_adapt.py` 共用 `_text_util.draft_shape()`，默认启用，关闭判杀仍保留报数） |
| GA-06~08 | `review/preflight.md` | 按纲改编附加硬指标（细纲覆盖、原文忠实、大纲外新增事件；由 `scripts/source_outline.py check` 执行） |
| MS-01~06 | `modules/process/market-scan.md` | 题材探测（联网检索、速查表、数据沉淀、S0 接口、时效闸门、快照刷新） |
| EH-01~06 | `modules/process/emotion-heatmap.md` | 情绪热力图（逐场标注、热力图、转折点沉淀、生成注入、库校验、批量导入） |
| SO-01~08 | `modules/process/source-outline.md` | 按纲改编（输入优先级、原文切片、结构锁定、逐条落地、无依据条目、冲突登记、覆盖验收、生成包续跑；Mode 3 自动挂载） |
| DP-01~08 | `modules/process/dialogue-pass.md` | 对白二次调整（S3.5 独立工序、单句 8-15 字、书面语转口语、朗读顺口、旁白三禁、叙述腔直搬禁令、A/B 同旁白禁令、验收登记；Mode 3 自动挂载，Mode 1/2 显式声明） |
| SH-03~07 | `modules/process/source-hygiene.md` | 净稿（净稿副本与不默删、剔除类别置信分层、乱码只标记、板块剔除须显式开启、验收门；`source_outline.py ingest`；原「授权登记/字段核对」两节已于 2026-11-09 剥离删除，对应脚本已从包内移除） |
| EP-01~08 | `modules/process/episode-plan.md` | 分集规划三要素（S1 必产物、字段定义、信息增量＝新增事实、相邻集不重复、出处回指、S4 合并门缺一即杀、生成期注入 packets、**集数口径：全剧 N vs 中间批次 10-12**；`scripts/check_episode_plan.py`；三要素表单独成文件时 packets 钩子预算行同源派生） |
| 无编号（共用口径） | `scripts/_text_util.py` | 三验收入口共用的稿件文件识别：`is_draft_candidate()` / `iter_draft_files()` 排除编号前缀、报告/索引/登记类文件名与首部标题，防门禁报告写进 `outputs/` 后被下一轮自扫成稿；`check_adapt.py --no-filter` 可关闭 |
| ST-00~07 | `modules/platform/structure-templates.md` | 平台结构包（可选挂载模块） |
| （模块自定前缀） | `modules/<类型>/*.md` | 用户自建模块，前缀在模块头声明，登记于 modules/_registry.md |

## 2. 变更纪律

- 任何变更记 CHANGELOG.md，每条=回滚单元。
- 核心规则（CR/HK/DR）变更：先对照 reference/screenwriting-theory.md 原文确认语义，冲突以原文为准。
- 新题材/新风格/新平台：**加模块**（modules/_registry.md 规范），不动核心。
- 引擎更换：OpenCode 宿主下以 `rules/opencode-adapter.md` OC-01 实时探测为准；仅外部端点直调路径才改 rules/model-routing.md MR-03 表（MR-01）。
- 模块间禁止互引编号，只能引用核心 CR/HK/DR/MR。

## 3. 季度复核项

- platform 包数据（平台机制/榜单/题材分布）联网复核，注明日期。
- **题材雷达时效**：每季跑 `python scripts/topic_radar.py check`；>90 天标需复核、>180 天标过期。复核结果走 `refresh --input` 导入，旧条目标 `[过期]` 保留；同步在 `reference/market-baseline.md` §4 追加一行复核记录（MS-05/06）。
- MR-03 默认引擎表按新基准复核；对照基线 = `reference/benchmark-snapshot-2026-11.md`（任一职责位名次变动 ≥2 → 更新 MR-03 并追加新快照，不覆盖旧快照）。
- **端点可用性（MR-07）**：换 key / 换聚合商 / 模型下线后，按 `~/.config/opencode/models.json` 逐条实机验证（200 + 中文正文 + tool_calls），失败项在 MR-07 映射表标注并按 MR-05 降级；配置改动保存后自动重载（必要时 /reload）。
- **调度引擎回归（MR-08）**：改动 `scripts/engine_dispatch.py` 或 MR-03/07 表后，跑 `python scripts/engine_dispatch.py selftest`（离线零调用）核对六档位映射与故障恢复；真实端点变更后另跑一次 `plan`，确认六个 id 全部解析成功。
- **闸门A 配置资产（GA-02）**：新项目开跑前，按原文 `source-index.json` 的 `name_candidates` 填 `pipeline/gate_a_config.json` 的 `name_whitelist`（确认为两个不同角色的等长一字之差人名）；不填则 GA-02 会把「青年甲 / 青年乙」这类正常角色误判为混写。白名单只解除误杀，不放宽其它检查。
- **LIVE 实跑抽样**：每换聚合商或大改引擎，抽 1–2 集 ×2 版跑一次 `run --live`（会计费），核对 `disable_thinking` 生效、无空正文、404/超时可恢复、成本报告与验收报告口径一致；演练 mode 测不出这几类故障。
