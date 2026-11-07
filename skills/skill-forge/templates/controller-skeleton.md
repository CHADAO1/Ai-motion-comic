# 模板 — 技能总控骨架（T1/T2 复制后填空）

> 用法：整体复制为 `<技能名>\SKILL.md`，替换 `{{占位符}}`；T0 不用本骨架（直接写单文件）。行数预算 ≤200 行。

```markdown
---
name: {{kebab-case-name}}
description: "{{一句话身份}}。MODE 1 ({{模式一名}}): {{做什么}}. Triggers include '{{触发词1}}', '{{触发词2}}'. MODE 2 ({{模式二名}}): {{做什么}}. Triggers include '...'. 内置规则：{{3-6个关键机制名词}}。"
whenToUse: 当用户{{典型场景}}时使用
---

# {{技能中文名}} — 总控调度器

{{一句话定位}}。**本文件只做调度**：执行到哪个阶段就读哪个模块文件，禁止凭记忆复述规则跳过读取。

## 0. 全局铁律（≤7 条）
1. {{最高优先级约束}}
2. **产物纯净**：交付文本不含任何反馈/理由/括号注释
3. {{状态落盘要求}}
4. **双审查门**：Preflight + Audit 全过才能交付，报告随交付输出
5. 验收用要素计数+证据绑定；禁止字数下限与空泛结论

## 1. 模式触发
| 模式 | 触发短语 | 入口 |
|---|---|---|
| Mode 1 | {{短语列表}} | workflows/xxx.md |
| Mode 2 | {{短语列表}} | workflows/yyy.md |

## 2. 产物与目录约定
{工作目录}\
├── pipeline\ manifest.json / 01_… / 02_… （中间产物，断点续跑依据）
└── outputs\ 最终交付物

manifest.json 结构：{ "stages": { "{{s0}}": {"status":"pending|done","output":""}, … }, "updated": "" }

## 3. 流水线（总览）
| Stage | 做什么 | 必读文件 | 输出 | 通过条件 | 失败回退 |
|---|---|---|---|---|---|
| S0 | … | rules/xxx.md | … | …（可核查） | 回退到 |

## 4. 断点续跑与回退
任务开始先读 manifest.json → 从第一个非 done 的 stage 继续；审查 ❌ → 补执行 → 受影响 stage 置回 pending 重跑。

## 5. File Map
（逐文件一行职责，改结构必须同步此表）

## 6. 维护约定
修改前读 MAINTENANCE.md；变更记 CHANGELOG.md；改完跑 node scripts/lint_skill.mjs。
```
