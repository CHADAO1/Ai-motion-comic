# 模板 — 文档三件套骨架（复制到目标包根目录后填空）

## A. README.md

```markdown
# {{技能名}} — {{一句话身份}}

> 本文件是通用说明；平台内调度入口是 SKILL.md，维护入口是 MAINTENANCE.md。

## 模式与触发
| 模式 | 触发短语 | 功能 |
|---|---|---|

## 在 OpenCode 中使用
放入 .opencode/skills/{{名}}\ 自动发现。流水线概览：S0→S1→…

## 在其他工具中使用
1. 全能宿主（读文件+跑脚本）：以 SKILL.md 为入口完整体验
2. 只能读文件：按总控阶段表"必读文件"列逐段贴入；跳过脚本用手工公式（见 rules/…）
3. 只能贴文本：总控 + 当前阶段单个模块拼接；保持一次只带一个阶段的规则

## 注意事项（最易踩的坑 TOP）
1. …（≤8 条）

维护：见 MAINTENANCE.md；变更历史：见 CHANGELOG.md。
```

## B. MAINTENANCE.md

```markdown
# MAINTENANCE — 维护与修改指南

> 改技能前先读本文，按"最小阅读集"只读相关模块，不必通读全包。

## 1. 架构一页图
SKILL.md(总控) → workflows/ → rules/(编号唯一事实源) → review/(双门) → scripts/ → pipeline\(中间产物)

## 2. 最小阅读集
| 要改什么 | 必读 | 联动检查 |
|---|---|---|

## 3. 规则编号注册表
| 前缀 | 定义文件 | 领域 |
|---|---|---|

## 4. 标准变更流程 SOP
新增规则：写模块带编号 → 登记审查清单项 → CHANGELOG → lint PASS
修改规则：grep 编号定位 → 改正文 → 核对全部引用点语义 → 常量全局同步 → CHANGELOG → lint PASS
删除规则：先清所有引用 → 再删定义 → CHANGELOG 注明取代关系 → lint PASS
新增阶段：workflows 加细则 → 总控表加行 → manifest 加字段 → CHANGELOG → lint PASS
新增脚本：scripts/ 新建(头注释用法+编号) → 总控登记 → CHANGELOG → lint PASS

## 5. 一致性防线
单一事实源 / lint_skill.mjs（改完必跑, exit 1 必须修复）/ 常量全局同步 / name 不动、description 改动影响触发需谨慎 / 回滚单元=CHANGELOG 条目

## 6. 禁止事项
- ❌ 规则正文塞回总控　❌ 最低字数类验收标准（用要素计数）　❌ 空泛验收结论
- ❌ 绕过 SOP 改 references/ 基准库　❌ 交付文本加元注释　❌ 删审查门
```

## C. CHANGELOG.md

```markdown
# CHANGELOG — 修改记录

> 每条变更独立成条（回滚单元）：`[版本] 日期 标题` + 动机/变更点(列文件)/兼容性。新条目置顶。规则编号只增不复用。

## [2.0] {{日期}} {{标题}}
**动机**：…
**变更点**：…
**兼容性**：…（回滚基准路径：…）

## [1.0] 原始版本
- 存档位置：…（永久保留勿改动）
```
