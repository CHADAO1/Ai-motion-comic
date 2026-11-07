# CHANGELOG — skill-forge 修改记录

> 每条变更独立成条（回滚单元）。新条目置顶。

## [1.0] 2026-08-23 初版

**动机**：将 cinematic-seedance-director 重构过程中形成的技能工程经验固化为元技能，避免后续每个新技能重复手工添加同类要求。

**变更点**：
- SKILL.md 总控：三模式（A 制作/B 优化体检/C 快检）+ 六条铁律 + File Map
- standards/ 四件：opencode-platform（平台硬约束 F1–F5）、architecture（T0/T1/T2 分诊与各层规范）、anti-lazy（L1–L6 防偷懒标准）、docs-set（文档三件套标准）
- workflows/ 两件：create-new（A0–A5 含交付自检清单）、optimize-existing（B0–B5 体检七项+差距分析纪律；Mode C 快检）
- templates/ 三件骨架 + scripts/lint_skill.mjs 通用版（相对 cinematic-seedance-director 版泛化：脚本目录动态扫描、无 rules/review 时自动跳过编号检查、支持 standards/templates/knowledge 目录路径检查）
- reference/case-study.md 实战复盘案例

**兼容性**：纯新增技能，不影响既有技能。
