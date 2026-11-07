# CHANGELOG — script-final-pipeline

## v2.1.0 · 2026-11-04 · 固化应用引擎（补齐「运行时现写脚本」缺口）

**动机**：v2.0.0 包内只有 SKILL.md + 2 份 rules + 文档，§3 的「应用脚本」是每次运行时按规范现写，产物稳定性取决于当次会话，不是开箱即用。

**改动清单**：

| # | 文件 | 变更 |
|---|---|---|
| 1 | `scripts/pipeline_apply.py` | **新增**固化引擎：`extract`（docx→txt，段落序号=行号）、`apply`、`verify`、`selftest`。实现 minidom 直改 document.xml、行号±6 窗口+CHECK_OVERRIDE/POS_OVERRIDE 定位、集合差/违禁词重扫/双通道提取一致/E 阶段覆盖率预检、应用记录 JSON+MD（含 MR-07 执行模型标注）。失败停机不写盘。纯标准库。 |
| 2 | `SKILL.md` | 铁律 3 声明引擎唯一、新增铁律 8（失败停机不写盘）；S0 与 C/D/E 阶段表改指固化脚本；§3 改写为「固化应用引擎」含四条可复制命令；File Map 与维护约定同步。 |
| 3 | `rules/standards.md` | §3 新增第 7 条「固化引擎唯一」，明确禁止运行时另写脚本、放行必须记录。 |
| 4 | `MAINTENANCE.md` | 编号索引补固化引擎条目。 |

**验证**：`python scripts/pipeline_apply.py selftest` → PASS（应用 / 三道校验 / 定位失败停机不写盘 / 双通道复核）。最小样例用 zipfile 自造 docx，不依赖任何外部文件。

**兼容性**：Mode 1 / Mode 2 触发与入口未改；对照单格式、CP/LG/AMZ 判据、模型路由全部不变。

---

## v2.0.0 · 2026-11-02 · 模型路由层重构

**动机**：编剧流程开工前定档模型（Claude Opus 5.5 xhigh 主力 + GLM-5.3 Flash 副手）。原架构无模型路由层，模型名一旦散入规则文件，每次换模型都要动一批判据，违反单一事实源。

**改动清单**（旧→新映射）：

| # | 文件 | 变更 |
|---|---|---|
| 1 | `rules/model-routing.md` | **新增**（MR-01~07：规则层模型无关 / 阶段→角色分工 / 默认模型表含依据与采集日期 / 跨厂评审 / 降本策略 / 端点接入与降级 / 产物头部标注执行模型） |
| 2 | `SKILL.md` | 全局铁律新增第 7 条（模型路由按 MR-\*）；流水线表新增「模型路由」列（只写 MR 编号）；File Map 补 model-routing.md；§5 维护约定补模型变更路径 |
| 3 | `rules/standards.md` | §3 第 6 条应用记录补「头部含执行模型标注 →MR-07」，判据本体未动 |
| 4 | `MAINTENANCE.md` | **新增**（编号索引 + 变更纪律） |
| 5 | `CHANGELOG.md` | **新增**（本文件） |

**兼容性**：使用方式不变（Mode 1 / Mode 2 触发与入口未改）；无外部端点时按 MR-06 降级为会话默认模型照常执行，不阻塞。

**默认模型表快照**（详见 model-routing.md MR-03，依据 2026-11-02 采集）：主力 Claude Opus 5.5 xhigh；副手 GLM-5.3 Flash；逻辑审核不排 DeepSeek；写作不用 Gemini。

**回滚基准**：`历史备份 script-final-pipeline_备份_模型路由重构前_20261102`（含原 SKILL.md + rules/standards.md）。
