---
name: script-final-pipeline
description: "剧本全流程/先审后改流水线/剧本终稿/完整走一遍/合规逻辑台词一条龙/剧本双语化最终稿。剧本终稿流水线总控：对一部剧本连续执行 ①合规审核(script-content-audit) ②逻辑审核(script-logic-audit，含画面链) ③合规修改对照单+应用→合规修订版 ④逻辑修改对照单(含画面连续性)+应用→合规+逻辑修订版 ⑤台词双语对照单(全量英文设计+回译中文，三档标注+活人感判定+术语表)+应用→最终双语版。每阶段产出差异化 docx 与对照文档，全程集合差校验+违禁词兜底重扫+覆盖率预检。应用引擎已固化在 scripts/pipeline_apply.py。用户要求逐段确认时在每份对照单后暂停；授权连续执行时一路到底。MODE 1 (全流程到终稿). MODE 2 (指定阶段执行)."
when_to_use: 当用户要求把一部剧本按固定流程从审核一路做到最终双语剧本、或要求执行其中某一阶段时使用。
---

# 剧本终稿流水线 — 总控调度器

把"先审后改 + 双语化"固定为五阶段流水线。**规则与判定全部引用三个既有技能，本文件只做调度与产物约定**：合规判据=script-content-audit `rules/content-policy.md`（CP-*）；逻辑判据=script-logic-audit `rules/logic-rubric.md`（LG-01~LG-13，含对话情境原则/画面优先原则/活人感判定）；台词双语判据=script-cinema-optimizer `AMZ-02/03`+对照单 v2 惯例（英文先行设计、回译中文、原文/重设计/表演优化三档、术语表）。

## 0. 全局铁律
1. **只审不改 → 对照单 → 应用**：任何修改必须先落对照单（行号+原文+拟改为+标注），再由脚本按对照单应用；禁止直接手改剧本。
2. **源不可变**：每阶段应用一律从上一阶段 docx 读取，原始 docx 永不改动。
3. **三道校验**：应用脚本必须做 ①集合差校验（零计划外改动）②违禁词兜底重扫 ③双通道提取一致性；双语阶段加 ④覆盖率预检（未覆盖台词不得写盘）。**四道校验已固化在 `scripts/pipeline_apply.py`，禁止运行时另写一套。**
4. **行号即证据**：所有对照单条目带修订基准 txt 的行号；应用脚本用"行号±6 窗口+标点剥离句尾唯一匹配"自动定位并记录修正。
5. **中间产物落盘**：`pipeline\` 下 00_全文、01_合规报告、10-13_台账、20_逻辑报告、应用记录；对照单与各阶段 docx 落在剧本根目录。
6. **确认模式**：默认每份对照单交用户批注后应用；用户明确授权连续执行时跳过批注，但预检/校验失败必须停下修复。
7. **模型路由**：规则层（CP/LG/AMZ/standards）永不绑模型名；阶段→模型分工、默认模型、降级与追溯统一按 `rules/model-routing.md`（MR-01~07），换模型只改该文件。
8. **失败停机不写盘**：定位失败、多候选冲突、覆盖率未达、校验未过 → 报错退出且不产出 docx；修对照单后重跑，不得猜测写盘。

## 1. 模式触发
| 模式 | 触发短语 | 入口 |
|---|---|---|
| Mode 1 | 完整走一遍 / 一路做到终稿 / 全流程 | A→E 全部 |
| Mode 2 | 只跑某阶段（如"只做双语"） | 指定阶段 |

## 2. 流水线
| Stage | 做什么 | 必读 | 输出 | 通过条件 | 模型路由 |
|---|---|---|---|---|---|
| S0 | docx→txt（`scripts/pipeline_apply.py extract`） | — | pipeline\00_剧本全文.txt | 字符数>0 | MR-01（不用模型） |
| A 合规 | 逐场按 CP-01~CP-24 扫描 | content-audit 规则 | pipeline\01_审核报告.md（总判定+分级+行号证据+正面改写） | CP 全覆盖、每条有行号 | MR-02 审核档 |
| B 逻辑 | 四台账（时间线/人物状态/设定规则/画面链）+ LG-01~13 扫描 | logic-audit 规则 | pipeline\10_~13_台账.md、20_逻辑审核报告.md | 台账齐、双证据、悬念豁免 | MR-02 审核档 |
| C 合规修复 | 合规修改对照单（原文→拟改为→CP 编号）→**固化脚本应用** | A 报告 | 《合规修改对照单》.md、《合规修订版》.docx | 三道校验过 | MR-02 改写档 |
| D 逻辑修复 | 逻辑修改对照单（含 LG 编号/画面连续性）→**固化脚本应用** | B 报告 | 《逻辑修改对照单》.md、《合规+逻辑修订版》.docx | 三道校验过 | MR-02 改写档 |
| E 台词双语 | 全量台词英文设计（术语表先行；原文/重设计/表演优化/删除四档；压缩与活人感判定）→**固化脚本应用 + 覆盖率预检** | AMZ-02/03 | 《台词双语对照单》.md、《……（最终双语版）》.docx | 覆盖率预检 100%、残留中文 OS=0 | MR-02 双语档 |

## 3. 固化应用引擎（不再运行时现写）

`scripts/pipeline_apply.py` 是 standards.md §3 的唯一可执行实现，纯标准库、无第三方依赖。开工前先跑 `python scripts/pipeline_apply.py selftest` 确认引擎可用。

```bash
# S0 抽取（段落序号 = 行号）
python scripts/pipeline_apply.py extract --docx 剧本.docx --out pipeline/00_剧本全文.txt

# C / D 阶段
python scripts/pipeline_apply.py apply --src 上一阶段.docx --changes 修改对照单.md \
  --baseline pipeline/00_剧本全文.txt --out 修订版.docx \
  --txt pipeline/01_修订版.txt --record pipeline/01_应用记录.json --model "会话模型"

# E 阶段（加覆盖率预检）
python scripts/pipeline_apply.py apply --src 上一阶段.docx --changes 台词双语对照单.md \
  --baseline pipeline/02_修订版.txt --out 最终双语版.docx \
  --txt pipeline/03_最终双语版.txt --record pipeline/03_应用记录.json \
  --stage E --whitelist pipeline/白名单.txt --model "会话模型"

# 独立复核
python scripts/pipeline_apply.py verify --docx 最终双语版.docx --txt pipeline/03_最终双语版.txt
```

引擎实现要点（细则见 `rules/standards.md` §3）：
- minidom 直改 word/document.xml；源 docx 只读；行号=上阶段 txt 行号=段落序号。
- 定位：行号直中 → 失败走 ±6 窗口；多候选取距行号最近且唯一；`CHECK_OVERRIDE` 片段 / `POS_OVERRIDE` 段号兜底；冲突/失败报错停机，**不写盘**。
- 应用后输出：新 txt（下一阶段行号基准）、新 docx、应用记录 JSON + MD（操作数/定位修正/四道校验/违禁词命中/覆盖率未映射/执行模型标注 →MR-07）。

## 4. File Map
```
SKILL.md                        总控（本文件）
rules/standards.md              对照单/应用/校验硬标准（细则）
rules/model-routing.md          模型路由唯一事实源（MR-01~07：分工/默认模型/降级/追溯）
scripts/pipeline_apply.py       固化应用引擎（extract / apply / verify / selftest）
MAINTENANCE.md / CHANGELOG.md   编号索引 / 变更记录
（CP-*、LG-*、AMZ-* 判据分别引用三个既有技能，不在本包重复定义）
```

## 5. 维护约定
流程细节变更改 rules/standards.md 并在本文件阶段表同步；三技能判据变更各自归属其包；模型分工/默认模型变更只改 rules/model-routing.md（→MR-01）；**应用/校验逻辑变更只改 scripts/pipeline_apply.py 并跑 selftest**，禁止在会话里另写临时脚本绕过引擎。
