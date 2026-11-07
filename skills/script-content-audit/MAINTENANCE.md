# MAINTENANCE — script-content-audit

## 修改流程
1. 动任何文件前先读本文件。
2. 红线内容只改 `rules/content-policy.md`（单一事实源）。
3. 新增/修改规则须带 CP-* 编号，并在 SKILL.md / preflight.md 同步引用。
4. 改完跑 `node scripts/lint_skill.mjs`，exit 0 才算合格；孤儿规则（C2 INFO）若为核心规则需补登记到 preflight。
5. 变更记 `CHANGELOG.md`，新条目置顶。

## 编号段
- CP-01~CP-12：十二类硬性禁止内容
- CP-13~CP-17：暴力血腥正面框架
- CP-18~CP-19：补充红线（自杀/自残、仇恨言论）
- CP-20~CP-25：二级管控替代词库（限流级·建议优化）
- CP-26：儿童向判定 Made for Kids（结构级·收益级，仅适用 YouTube 类平台）
- CP-30~CP-39：`[TT]` TikTok 敏感内容十大类（政策原文层，见 content-policy.md §1.5；与 CP-01~19 重叠映射，从严判定）
- CP-40~CP-50：`[YT]` YouTube 敏感内容十一大类（政策原文层，见 content-policy.md §1.6；比 TikTok 组多「危险行为 CP-49」「抽烟吸毒 CP-50」；投 YouTube 逐条必过）
- **⚠️ 平台差异登记处**（改规则前必看）：自残自杀 YouTube 宽（CP-48 可写心理困境）vs TikTok 严（CP-34 零容忍 + 禁作反转）；虚构宗教豁免仅 YouTube 明确（CP-43）
- **平台标签**（见 content-policy.md §0.2）：`[TT]`=TikTok ／ `[YT]`=YouTube ／ `[DY]`=国内抖音系；无标签条目（CP-0、CP-13~17、CP-20~25）全平台通用。新增规则必须带平台标签。
- 预留更高编号段（当前止于 CP-39）给未来新增红线
