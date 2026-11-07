---
name: skill-forge
description: "触发词：制作技能、新建技能、创建技能、写一个技能、做个技能、优化技能、重构技能、技能体检、检查技能、安装技能、这个技能有没有问题。Meta-skill for building, optimizing, and auditing other AI skills. MODE A (制作新技能): turn requirements into a complete skill — tier selection (T0 single-file / T1 modular / T2 pipeline), thin controller + rule modules with unique IDs, docs suite (README/MAINTENANCE/CHANGELOG), lint self-check, install & verify. MODE B (优化/体检既有技能): health-check an existing or externally downloaded skill (format, completeness, platform compliance, repetition), refactor bloated monoliths into controller+modules, add anti-lazy mechanisms, never touch the original backup. MODE C (快速合规检查): minimal frontmatter/layout validation before use. Built-in standards: OpenCode platform constraints, tiered architecture, single-source-of-truth + rule IDs, anti-lazy acceptance (evidence-bound checks, element counting, NO word-count floors), lint consistency tool."
when_to_use: 当用户要制作新技能、优化或重构或体检既有技能（尤其外部下载的技能）、或在某技能未按说明执行时想排查技能本身问题时使用
---

# Skill Forge — 技能锻造（制作/优化/体检其他技能）

本技能是"造技能的技能"。它把一次完整技能工程的经验固化为标准：分层架构、规则编号体系、防偷懒验收、文档套件、一致性校验。**本文件只做调度**；标准在 standards/，流程在 workflows/，骨架在 templates/。

## 0. 铁律（全局）

1. **先定层再动手**：任何技能先按 standards/architecture.md 分诊为 T0/T1/T2，禁止给简单技能上全家桶，禁止让复杂技能裸奔单文件。
2. **原版神圣**：优化外部/既有技能时先完整备份原版且永不在其上开发；所有变更记入目标技能 CHANGELOG.md（每条=回滚单元）。
3. **单一事实源**：一条规则只在一个文件定义并持有唯一编号；其余位置只允许"动作+编号引用"。
4. **验收即证据**：完整性用要素计数表达（几要素/几件套/几个文件），每个 ✅ 绑定磁盘路径/脚本输出/数值；**禁止字数下限标准**（长度由内容决定，短而全即合格）；"已检查/无问题"按未检查处理。
5. **文档进包不进步口**：README/MAINTENANCE/CHANGELOG 放技能文件夹内（对加载器零成本），规则正文永不写进 SKILL.md 总控。
6. **先分析后动手**：优化类任务先出差距报告（哪些达标/哪些缺口/为什么不采纳某些建议），经用户确认再改。

## 1. 模式触发

| 模式 | 触发短语 | 入口 |
|---|---|---|
| A 制作新技能 | 制作技能 / 新建技能 / 创建技能 / 写一个技能 | workflows/create-new.md |
| B 优化/体检既有技能 | 优化技能 / 重构技能 / 技能体检 / 这个技能有没有问题 | workflows/optimize-existing.md |
| C 快速合规检查 | 快速检查 / 能不能装 / 格式对不对 | workflows/optimize-existing.md §C |

表述含糊时问一句：新建还是改造现有？

## 2. 流水线概览

**Mode A（新建）**：A0 需求澄清（目标/宿主/触发词/输入输出） → A1 分诊定层 → A2 骨架生成（读 templates/） → A3 内容填充（按需读 standards/） → A4 验证（lint + 脚本样例测试 + 目录出现确认） → A5 安装交付。

**Mode B（优化）**：B0 备份原版 → B1 技能体检（输出逐项体检报告） → B2 差距分析与方案确认（对照 standards/，明确"采纳/不采纳及理由"） → B3 执行改造 → B4 验证（同 A4） → B5 CHANGELOG + 交付。

**Mode C（快检）**：只查 frontmatter 合法性 + 布局一层性 + 引用完整性，输出 PASS/FAIL 清单，不改文件。

## 3. File Map

```
SKILL.md                        总控调度（本文件）
README.md                       通用说明（跨工具使用）
CHANGELOG.md                    本技能自身变更记录
standards/
  opencode-platform.md         OpenCode 平台硬约束（发现机制/frontmatter/安装位/自动重载）
  architecture.md               分层架构标准：T0/T1/T2 分诊 + 总控/模块/审查规范
  anti-lazy.md                  防偷懒设计标准（证据绑定/逐单元验收/要素计数）
  docs-set.md                   文档套件标准（README/MAINTENANCE/CHANGELOG 各自必备内容）
workflows/
  create-new.md                 Mode A 六步细则 + 交付前自检清单
  optimize-existing.md          Mode B 六步细则 + 体检清单 + Mode C 快检清单
templates/
  controller-skeleton.md        T1/T2 总控骨架（复制即用）
  module-skeletons.md           规则模块/预检/审计骨架（复制即用）
  docs-skeletons.md             README/MAINTENANCE/CHANGELOG 骨架（复制即用）
scripts/
  lint_skill.mjs                通用版一致性校验（复制进目标技能 scripts/ 后运行）
reference/
  case-study.md                 实战案例：cinematic-seedance-director 单体→分层重构复盘
```

## 4. 维护约定

本技能自身的修改同样遵守铁律 2/3/4/5；变更记入本包 CHANGELOG.md。若 standards 与实战冲突，以实战反馈为准修订 standards 并记录案例。
