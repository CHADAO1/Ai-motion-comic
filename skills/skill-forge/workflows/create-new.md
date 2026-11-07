# 工作流 — Mode A：制作新技能（A0–A5）

## A0 需求澄清
问清五件事（用户已说明的跳过）：①技能解决什么任务、给谁用 ②在哪个宿主跑（OpenCode/其他工具/都要） ③期望的触发方式与触发词 ④输入是什么、最终交付物长什么样 ⑤流程是否分阶段、有没有可确定性计算的部分。

## A1 分诊定层
读 standards/architecture.md T1 分诊表，判定 T0/T1/T2，**向用户报告结论与理由**。拿不准选低档。

## A2 骨架生成
- T0 → 直接写单个 SKILL.md（frontmatter 按 opencode-platform.md F2），完成。
- T1/T2 → 从 templates/controller-skeleton.md 复制总控骨架；T2 再复制 templates/module-skeletons.md 的规则模块/预检/审计骨架与 templates/docs-skeletons.md；把本包 `scripts/lint_skill.mjs`（通用版）复制进目标包 scripts/。
- 目录名 = frontmatter name（kebab-case）。

## A3 内容填充
- 规则写入对应模块并编号；每条新规则同步登记进审查清单项（引用编号）。
- 阶段表填全五列（必读文件/输出/通过条件/回退缺一不可）。
- 可计算部分写成脚本（头注释含用法+映射编号）；产物约定与 manifest 按 architecture.md T5。
- 文档三件套按 docs-set.md D1–D3 填写；防偷懒机制按 anti-lazy.md L1–L6 落实。

## A4 验证（交付前自检清单，逐项过）
- [ ] frontmatter 合规：name 匹配 kebab-case 且 ==目录名；description 非空且含触发词；无驼峰遗留键（F2）
- [ ] 布局一层性：SKILL.md 位于 `<skills根>\<名>\SKILL.md`（F1）
- [ ] 全部 UTF-8 无乱码；代码围栏成对（F4）
- [ ] File Map 与实际文件一一对应（无多列、无漏列）
- [ ] 引用完整性：清单项引用的编号都有定义；反引号路径都存在 → `node <目标包>\scripts\lint_skill.mjs` exit 0
- [ ] 自带脚本用样例输入实测通过（构造最小样例跑一遍）
- [ ] 安装后可用技能列表出现该技能；用一句触发短语冒烟测试能正确进入模式

## A5 安装交付
按 F5 决策安装位置；向用户交代：怎么触发、产物在哪、怎么修改（指向 MAINTENANCE.md）、怎么回滚（CHANGELOG）。
