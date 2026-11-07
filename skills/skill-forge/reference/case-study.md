# 案例 — cinematic-seedance-director 单体→分层重构复盘

> 本案例是 skill-forge 标准的来源与验证。两个版本都在磁盘上，可直接对照阅读。

## 背景
外部下载的单体技能：SKILL.md 859 行（约79KB），双模式剧本→Seedance 提示词流水线。问题：注意力稀释、同规则重复 2–6 处、审查清单整批视角导致漏检难发现。

## 关键决策（对照标准的映射）

| 决策 | 对应标准 | 备注 |
|---|---|---|
| 判定 T2 流水线级（多阶段+中间产物+可计算估时） | architecture T1 分诊表 | 没有盲目上全家桶前先做此判定 |
| 859 行 → 106 行总控，规则拆 R1–R8 模块并编号（74 条） | architecture T2/T3 | 去重与编号同步进行——重复是膨胀主因 |
| Preflight/Audit 双门 + A1–A13 证据列 | architecture T4 | 后在 v2.1 补"证据形式约束"堵糊弄空间 |
| estimate_timeline.mjs / validate_prompt.mjs | architecture T5 | 计算交脚本，AI 无法谎报时长格式 |
| manifest.json 断点续跑 | architecture T5 | 中断/修改后自动定位重跑点 |
| README/MAINTENANCE/CHANGELOG 三件套 | docs-set D1–D3 | MAINTENANCE 的"最小阅读集"使修改不必通读全包 |
| v2.1 逐段验收表 + 要素计数原则 + 禁字数下限 | anti-lazy L2/L3/L4 | 用户明确拒绝字数标准后固化为红线 |

## 教训
1. **先分析后动手**：当时若照搬外部建议"限制字数/简单限长"会损害功能；正确做法是差距分析后只采纳适用项。
2. **重复比长度更毒**：拆分时必须同时去重，否则膨胀只是换目录。
3. **原版备份是安全网**：`历史备份（cinematic-seedance-director 原版）` 保留 v1 原状，全程未动，多次支持语义核对。
4. **lint 是变更闭环的最后一步**：所有 SOP 以 "lint PASS 才算完成" 收尾，悬空引用和路径腐烂都能被机器抓到。

## 对照阅读路径
- v1 原版单体：`历史备份（cinematic-seedance-director 原版 SKILL.md）`
- v2 分层现役：`项目技能目录（cinematic-seedance-director）`（结构见其 SKILL.md §6 File Map）
- 变更全记录：`项目技能目录 CHANGELOG.md`
