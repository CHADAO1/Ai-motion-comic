---
name: script-asset-extraction
description: "触发词：剧本资产、资产提取、资产总表、角色资产、场景资产、道具资产、连镜分析、提取资产、更新资产表、资产增量更新、新版剧本资产。剧本视觉资产提取师：通读影视/短剧剧本全文，提取角色、道具、场景、特效资产，按外观状态与镜头连续性(连镜)拆分成可直接生成参考图的 Excel 总表。MODE 1 (全量提取): 解析剧本 docx/txt/md，输出《资产总表.xlsx》. MODE 2 (增量更新): 剧本改版后对照旧 assets.json 增补/修订并重新出表. 内置规则：外观状态拆分、连镜风险三级评级、一次性小道具豁免、场景视角/状态切分、特效独立归类、免依赖 xlsx 生成脚本。"
when_to_use: 当用户要把剧本转成 AI 电影/AI 视频生产用的角色、场景、道具参考图资产总表(Excel)时使用
---

# 剧本资产提取 — 总控调度器

把剧本变成"AI 电影前期资产总表"：每个**上镜可见的外观单元**一行，供生成外观参考图给视频 AI 做一致性(连镜)锁定。音色不在本技能范围，只做关联引用。**本文件只做调度**：执行到哪个阶段就读哪个规则文件，禁止凭记忆跳过读取。

## 0. 全局铁律
1. **先通读全文再提取**：必须逐场建立出场流水，禁止抽样或只读部分集数。
2. **只登记上镜可见差异**：台词/OS 提及但画面不呈现的变化不建行（CHA-06）。
3. **豁免要有出处**：一次性小道具/单场视角的豁免必须符合 PRP-04 / SCN-04，并在报告中留豁免清单。
4. **数据落盘再出表**：先写 `pipeline\assets.json`，再由 `scripts/build_xlsx.mjs` 出 xlsx（TBL-06）；禁止手搓表格文件。
5. 验收用要素计数+证据绑定；禁止字数下限与"已检查/无问题"式空泛结论。
6. 交付必须附预检报告（§6 清单全过），报告缺失=任务未完成。

## 1. 模式触发
| 模式 | 触发短语 | 入口 |
|---|---|---|
| Mode 1 全量提取 | 剧本资产/资产提取/资产总表/连镜分析 | 本文件 §3 流水线 S0→S5 |
| Mode 2 增量更新 | 更新资产表/新版剧本资产 | §4 |

## 2. 产物与目录约定
以剧本所在目录为工作目录：
```
{工作目录}\
├── pipeline\  00_剧本全文.txt / 01_出场流水.md / assets.json （中间产物，断点续跑依据）
└── outputs\   资产总表.xlsx （最终交付物）
```

## 3. Mode 1 流水线
| Stage | 做什么 | 必读文件 | 输出 | 通过条件 | 失败回退 |
|---|---|---|---|---|---|
| S0 | 源定位与转文本：docx 用 `node scripts/docx2txt.mjs <docx> <out>`；txt/md 直接复制 | — | pipeline\00_剧本全文.txt | 文件存在且字符数>0（报告数值） | 换源文件或请用户提供文本版 |
| S1 | 全文逐场通读，建立集-场流水（场次/场景/人物/道具/特效/外观变化备注） | rules/scene.md 的 SCN-01 记录粒度 | pipeline\01_出场流水.md | 覆盖全部集数：首场与末场的场次号在流水中可核对 | 补读漏掉的分集段落 |
| S2 | 归纳资产清单：角色/道具/场景/特效四大类+状态拆分+连镜评级；同步产出/更新《剧名》-英文名词与称呼对照.txt | rules/character.md、rules/prop.md、rules/scene.md、rules/fx.md、rules/table.md | pipeline\assets.json ＋ 剧本目录《剧名》-英文名词与称呼对照.txt | node 解析通过且四类齐备（TBL-07 校验脚本输出）；对照表存在且含拼写禁例速查（TBL-09） | 缺类回 S1 对应集数补查 |
| S3 | 出表：`node scripts/build_xlsx.mjs pipeline\assets.json outputs\资产总表.xlsx` | rules/table.md TBL-02 列结构 | outputs\资产总表.xlsx | 脚本 exit 0 并打印统计行（各类型行数） | 修 json 后重跑 S3 |
| S4 | 预检+交付：过 §6 清单，向用户输出报告 | review/preflight.md | 报告（对话内+pipeline\05_预检报告.md） | 清单全 ✅ 且每项附证据 | ❌ 项回到对应 Stage 返工 |

## 4. Mode 2 增量更新
读旧 `pipeline\assets.json` + 新剧本 → 重跑 S0/S1 → 差异合并进 assets.json：**资产ID 永不复用**，新增续号，废弃行加 `"status":"废弃"` 保留不删 → 按 TBL-09 同步审查《剧名》-英文名词与称呼对照.txt 的增删改 → S3 重跑出表 → S4 预检。

## 5. File Map
```
SKILL.md                 总控调度（本文件）
README.md                通用说明
MAINTENANCE.md           维护入口
CHANGELOG.md             变更记录
rules/character.md       CHA-* 角色资产与状态拆分规则
rules/prop.md            PRP-* 道具资产规则（含一次性豁免）
rules/scene.md           SCN-* 场景与视角切分规则
rules/fx.md              FXR-* 特效资产规则
rules/table.md           TBL-* 表格列结构/ID体系/连镜评级/JSON schema
review/preflight.md      交付前内容门清单
scripts/build_xlsx.mjs   assets.json → xlsx（免第三方依赖）
scripts/docx2txt.mjs     docx → txt 提取
scripts/lint_skill.mjs   一致性自检（skill-forge 通用版）
```

## 6. 交付前预检（细则见 review/preflight.md，此处为门禁）
逐项 ✅ 且附证据后才可交付：①流水覆盖全部集数 ②assets.json 四类齐备可解析 ③每个角色有基础形象行（CHA-04）④高风险行均有 needRef=是 ⑤豁免清单已列出（PRP-04/SCN-04）⑥xlsx 打开校验通过（脚本统计行数=预期）⑦lint exit 0 ⑧《剧名》-英文名词与称呼对照.txt 已同步且无同义异拼（TBL-09）。

## 7. 维护约定
修改任何文件前读 MAINTENANCE.md；变更记 CHANGELOG.md；改完跑 `node scripts/lint_skill.mjs` 且 exit 0。
