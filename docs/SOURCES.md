# 外部来源登记（部分引入）

本文件记录**非 subtree 引入**的外部技能：只复制了部分文件/技能，或做过改写，需人工跟踪更新。
完整整仓引入见 `vendor-manifest.json`。

## 2026-11-09 · 编剧能力补强

| 本地技能 | 来源仓库 | 方式 | 许可 | 备注 |
|---|---|---|---|---|
| `skills/sw-dialogue` | https://github.com/jtydhr88/screenwriting-skills | 复制 `plugins/screenwriting/skills/sw-dialogue` | MIT | 对白/潜台词 |
| `skills/sw-scene-craft` | 同上 | 复制 `.../sw-scene-craft` | MIT | 场景/细节/动作段落/转场规范 |
| `skills/sw-chinese-series-practice` | 同上 | 复制 `.../sw-chinese-series-practice` | MIT | 国产剧改编/审查；偏长剧，短剧重点读第 6–8 节 |
| `skills/dialogue-subtext` | https://github.com/sethmblack/skill-dialogue-subtext | 复制单文件 | 未标注 | 潜台词四原则/四步转换 |
| `skills/sensitive-adaptation` | 自写；灰区表参考 https://github.com/0xsline/short-drama | 新写 | 自写 | 敏感内容保留氛围改写 |
| `skills/scene-transitions` | 自写；参考 sw-scene-craft 转场规范 + 经典剧作 | 新写 | 自写 | 转场类型库/决策树/Seedance 衔接 |

## 更新方式

- 复制型：重新拉取上游对应目录覆盖，或本地改（改后与上游分叉，需在 CHANGELOG 记录）。
- 自写型：直接维护。
- 引入时上游 HEAD：以实际 clone 为准，如需精确比对可重新 clone 后 `git log -1 --format=%h`。
