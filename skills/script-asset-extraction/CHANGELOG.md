# CHANGELOG

## [1.1] 2026-08-26 英文名词·称呼对照表联动（跨技能命名圣经）
- 动机：面向海外发行需要全项目统一的英文名词；用户拍板凯尔定稿 Kael、父母定名 Alaric Voss/Seren Voss，并要求资产表/音色/视频提示词三方共享同一套称呼。
- 变更点：
  - rules/table.md 新增 TBL-09（对照表联动：位置命名/复用优先/初版生成/同步义务/下游约束）
  - SKILL.md S2 阶段输出与通过条件加入对照表；§4 Mode 2 加入同步审查步骤；§6 门禁加第⑧项
  - review/preflight.md 新增「E 名称一致性」检查组
- 兼容性：纯增量；TBL-01~08 不变；产物新增一份 txt（与 xlsx 同级正式交付物）。
- 关联：cinematic-seedance-director [2.3] DLG-04、character-voice-design 硬性要求第 6 条同期注入同名联动。

## [1.0] 2026-08-26 初版发布
- 动机：AI 电影工作流需要把剧本转化为可生成参考图的视觉资产总表（角色/场景/道具），现有技能仅覆盖音色与视频提示词，缺资产提取环节。
- 变更点：新建技能包——SKILL.md 总控（双模式）、rules/character.md、rules/prop.md、rules/scene.md、rules/fx.md、rules/table.md、review/preflight.md、scripts/build_xlsx.mjs（免依赖 xlsx 写入器）、scripts/docx2txt.mjs（免依赖 docx 提取）、scripts/lint_skill.mjs（skill-forge 通用版）、README/MAINTENANCE。
- 兼容性：无既有版本；架构 T1（瘦总控+编号规则+脚本，未上 manifest 双门，后续复杂度增长可升 T2 并在此记录）。
