# 自有技能目录

本目录存放你自己的技能，当前 **25 个**。

**来源**：从 `~/.config/opencode/skills`（当前生效版本）同步而来，2026-11-07。

`F:\工作区\技能库\_原始包_20261107\单技能包\*.zip` 是历史分发包，比生效版本旧
（实测 11/25 个技能有内容差异，`script-draft-forge` 少 3 个文件，`skill-forge` 有 7 处改动），
因此**未采用** zip 内容，仅保留其归档。

结构：一个技能一个目录 `<skill-id>/SKILL.md`，可附 `scripts/`、`references/`、`modules/` 等。

## 维护约定

- **本目录是权威副本**：`opencode.jsonc` 里 `skills` 数组指定的源优先级高于
  `~/.config/opencode/skills`，因此同名技能以本目录为准。
  改技能请改这里，改完 commit / push；全局目录里的同名副本不要再改，否则改动不生效。
- 建议后续把 `~/.config/opencode/skills` 里的同名副本移走或停用，避免两份并存造成「改了不生效」。
- 外部方案统一放 `vendor/`，由 `vendor-manifest.json` 登记，不要放进本目录。
- `<skill-id>` 建议小写 kebab-case，且不要与 `vendor/` 下外部方案的技能 ID 重名。
