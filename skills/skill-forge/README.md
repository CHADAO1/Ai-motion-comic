# skill-forge — 技能锻造（制作/优化/体检技能的元技能）

把一次完整技能工程的经验固化为可复用标准：分层架构分诊（T0/T1/T2）、规则编号体系、防偷懒验收设计、文档三件套、一致性 lint。

## 触发方式
- 制作新技能：制作技能 / 新建技能 / 创建技能 / 写一个技能
- 优化/体检：优化技能 / 重构技能 / 技能体检 / 这个技能有没有问题 / 安装技能
- 快速合规检查：帮我看看这个技能能不能装

## 三档能力要求（跨工具使用）
1. 全能宿主（读文件+跑 node）：完整体验，含 lint 校验
2. 只能读文件：按 workflows 步骤人工执行；lint 改为逐条手工核对
3. 只能贴文本：贴 SKILL.md + 对应 standards 单文件

## 包内导航
- 调度入口：SKILL.md　·　标准：standards/ 四件　·　流程：workflows/
- 骨架模板：templates/（复制即用）　·　校验工具：scripts/lint_skill.mjs
- 实战案例复盘：reference/case-study.md

维护见 MAINTENANCE.md 约定（本包为 T1.5 结构：标准层代替规则层，无 pipeline）。
