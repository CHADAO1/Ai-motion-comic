# MAINTENANCE — 维护者/AI 编辑入口

## 1. 架构一页图
```
SKILL.md(调度) ──► S0 docx2txt.mjs ──► S1 出场流水 ──► S2 rules/*归纳 ──► assets.json
                                                    └─► S3 build_xlsx.mjs ──► outputs/资产总表.xlsx
                                                                          └─► S4 review/preflight.md 门禁
数据流：规则(rules/, 单一事实源) -> 中间产物(pipeline/) -> 交付物(outputs/) -> 报告
```

## 2. 最小阅读集对照表
| 修改任务 | 只需读 |
|---|---|
| 加/改一条角色规则 | rules/character.md + review/preflight.md B 组 + 本文件§3 SOP |
| 改表格列结构 | rules/table.md(TBL-02) + scripts/build_xlsx.mjs(HEADERS/WIDTHS/push) |
| 改 xlsx 样式/列宽 | 仅 scripts/build_xlsx.mjs |
| 换输出文件名/位置 | SKILL.md §2/S3 + build_xlsx.mjs 默认 outPath |
| 新增支持格式(如 .fountain) | SKILL.md S0 行 + scripts/ 新增解析器 |

## 3. 规则编号注册表
| 前缀 | 文件 | 领域 |
|---|---|---|
| CHA-01..06 | rules/character.md | 角色资产与状态拆分 |
| PRP-01..06 | rules/prop.md | 道具（含一次性豁免） |
| SCN-01..06 | rules/scene.md | 场景与视角切分 |
| FXR-01..04 | rules/fx.md | 特效资产 |
| TBL-01..08 | rules/table.md | 表格列结构/ID/评级/schema |

## 4. 标准变更 SOP
- **新增规则**：目标 rules/*.md 追加编号（只增不复用）→ 同步登记 review/preflight.md 对应组 → 跑 `node scripts/lint_skill.mjs` PASS 收尾。
- **修改规则**：原位修改正文 → 检查引用方(SKILL.md/preflight)语义仍成立 → lint PASS。
- **删除规则**：正文保留加"已废止，由 XX-nn 取代"标注 → 清理引用 → lint PASS。
- **新增阶段**：SKILL.md §3 表加行（五列齐全）→ preflight 加对应检查项 → lint PASS。
- **新增脚本**：放 scripts/ → 头注释含用法+映射编号 → 用最小样例实测 → SKILL.md File Map 补一行 → lint PASS。

## 5. 一致性防线
- 单一事实源：schema 只在 TBL 定义，build_xlsx.mjs 是其代码化，两处必须同步改。
- frontmatter 纪律：name 不动；description 改动会改变触发行为，需谨慎并在 CHANGELOG 记录。
- 回滚单元 = CHANGELOG 一条目，按条目内文件清单反向操作。
- 禁止：最低字数标准、空泛验收结论、规则正文写进 SKILL.md。

## 6. 自检命令
```
node scripts/lint_skill.mjs          # 一致性校验, exit 0 才算过
node -e "JSON.parse(require('fs').readFileSync('pipeline/assets.json','utf8'))"   # 数据可解析
```
