# CHANGELOG — 修改记录

> 每条变更独立成条（回滚单元）：`[版本] 日期 标题` + 动机/变更点/兼容性。新条目置顶。规则编号只增不复用。

## [1.2] 2026-08-28 同步 CP-18/CP-19 与细化参考

**动机**：script-content-audit 补充 YouTube 合规细化参考（判定标准/安全边界/案例）并新增 CP-18 自杀/自残、CP-19 仇恨言论；本技能同步覆盖。

**变更点**：rules/content-policy.md 本地 CP 索引补 CP-18/CP-19；OPT-05 增加自杀/自残与仇恨言论清除动作；头部 CP 范围 CP-01~CP-17 → CP-01~CP-19。

## [1.1] 2026-08-27 接入内容红线与暴力血腥正面框架

**动机**：用户要求"拿到剧本先审核再修改后继续"，并明确 YouTube 十二类硬性禁止内容 + 暴力血腥正面框架（打斗杀伤允许、飙血红伤断肢禁止、化灰非裂开再化灰、婴幼儿孕妇绝对禁区、反派可施恶但须被击败），且要用"要这样"代替"不要那样"的正向措辞。审核/优化/提示词三技能共用 script-content-audit 的 CP-* 规范。

**变更点**：
- 新增 `rules/content-policy.md`：引出审核技能规范 + 定义优化阶段动作 OPT-01~05（冲突戏/亲密戏/危险角色/反派落点/其余红线清除）
- `SKILL.md`：铁律增第 8 条内容红线优先；S2/S3 必读文件增 `rules/content-policy.md`；File Map 补登记
- `review/preflight.md`：新增"内容红线"分组（CP-*/OPT-* 六项核查）
- `review/audit.md`：终审查表增 A7 内容红线无残留
- 全局改写总原则：负面约束须配正面落点画面（CP-0）

**兼容性**：纯增量；规则编号 OPT-* 独立于既有 DIAG/VIS/AMZ/VCB/CON，不改既有流程阶段。

## [1.0] 2026-08-25 初始版本
**动机**：用户长期写国内短剧，习惯大量对话+AI 高速产出，剧本质量差；受众为 YouTube 国际观众，需转 AI 电影视听驱动。用户提供长篇优化对话（10 方向 + 美式雌竞分析 + 五步流水线），要求固化为可重复执行 Skill。
**变更点**：
- 建 T2 流水线技能包 `script-cinema-optimizer`
- `SKILL.md` 六步流水线 S0–S5（切片/冷读诊断/视听化重写/美式雌竞+双语本土化/视觉概念落地/一致性终审）
- `rules/` 三域文件，编号 DIAG/VIS/AMZ/VCB/CON 共 18 条规则
- `review/` 双审查门 preflight + audit
- `reference/learning-material.md` 提炼对话为学习资料
- `scripts/lint_skill.mjs` 复制通用版
- 文档三件套 README/MAINTENANCE/CHANGELOG
**兼容性**：初始版本，无回滚基准（原始对话见 `reference/learning-material.md`）。
