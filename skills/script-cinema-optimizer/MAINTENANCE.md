# MAINTENANCE — 维护与修改指南

> 改技能前先读本文，按"最小阅读集"只读相关模块，不必通读全包。

## 1. 架构一页图
`SKILL.md`(总控) → `rules/`(编号唯一事实源) → `review/`(双门) → `reference/`(学习资料) → `scripts/lint_skill.mjs` → `pipeline/`(中间产物)

## 2. 最小阅读集
| 要改什么 | 必读 | 联动检查 |
|---|---|---|
| 调整某优化方向 | 对应 `rules/*.md` + `reference/learning-material.md` | 同步 `MAINTENANCE.md` 规则注册表 |
| 改阶段顺序/产物 | `SKILL.md` 第 3 节流水线表 | `pipeline/manifest.json` 字段 |
| 改审查口径 | `review/preflight.md` + `review/audit.md` | 确认 `rules/` 编号引用一致 |
| 加新规则 | 建/扩 `rules/*.md` 带编号 | 登记到 `review/preflight.md` 对应分组 |

## 3. 规则编号注册表
| 前缀 | 定义文件 | 领域 |
|---|---|---|
| DIAG | `rules/diagnose.md` | 冷读诊断（OS/对白/雌竞/模板表情/钩子/视觉圣经） |
| VIS | `rules/rewrite.md` | 视听化重写（砍OS/潜台词/无台词节拍/专属动作） |
| AMZ | `rules/rewrite.md` | 美式雌竞与双语本土化 |
| VCB | `rules/visual-consistency.md` | 视觉概念落地（质感/动作节拍） |
| CON | `rules/visual-consistency.md` | 一致性终审（矛盾/漂移/钩子） |

## 4. 标准变更流程 SOP
- 新增规则：写模块带编号 → 登记审查清单项 → `CHANGELOG.md` → lint PASS
- 修改规则：grep 编号定位 → 改正文 → 核对全部引用点语义 → `CHANGELOG.md` → lint PASS
- 删除规则：先清所有引用 → 再删定义 → `CHANGELOG.md` 注明取代关系 → lint PASS
- 新增阶段：Workflow 加细则 → 总控表加行 → `manifest.json` 加字段 → `CHANGELOG.md` → lint PASS

## 5. 一致性防线
单一事实源 / `lint_skill.mjs`（改完必跑, exit 1 必须修复）/ name 不动、description 改动影响触发需谨慎 / 回滚单元=`CHANGELOG.md` 条目。

## 6. 禁止事项
- ❌ 规则正文塞回总控　❌ 最低字数类验收标准（用要素计数）　❌ 空泛验收结论
- ❌ 交付文本加元注释　❌ 删审查门　❌ 跳过 SOP 改 `reference/` 基准库
