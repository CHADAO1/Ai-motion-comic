# script-content-audit（剧本内容红线审核）

拿到剧本、准备优化或转提示词**之前**先用本技能审核。按 `rules/content-policy.md` 的十二类 YouTube 发布红线 + 暴力血腥正面框架逐条扫描，输出带行号与正面改写建议的《内容审核报告》。

## 它解决什么
- 避免把含禁止内容的剧本直接送进优化/提示词环节，导致成品在 YouTube 被判违规。
- 把"不能这样不能那样"的负向清单，转成 AI 更好遵从的"要这样"正面画面指令。

## 与另外两个技能的关系
| 技能 | 角色 |
|---|---|
| script-content-audit（本技能） | 先审：扫描违规、出报告、交回修改 |
| script-cinema-optimizer | 后改：在优化阶段清除违规并按正面框架重写 |
| cinematic-seedance-director | 后写：提示词画面描写避开血腥视觉 |

三者共用 `rules/content-policy.md` 的 CP-* 编号规范。
