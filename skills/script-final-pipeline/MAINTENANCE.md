# MAINTENANCE — 编号索引与维护地图

## 1. 规则编号唯一事实源（改哪条去哪个文件）

| 编号段 | 归属文件 | 内容 |
|---|---|---|
| MR-01~07 | `rules/model-routing.md` | 模型路由：规则层模型无关 / 阶段分工 / 默认模型表 / 跨厂评审 / 降本 / 降级 / 产物追溯 |
| （无编号） | `rules/standards.md` | 对照单格式 / 应用脚本硬要求 / 交付清单 / 经验条目 |
| （无编号） | `scripts/pipeline_apply.py` | **固化应用引擎**（extract / apply / verify / selftest）：minidom 改 document.xml、±6 窗口定位、四道校验、应用记录；应用/校验逻辑变更只改此文件并跑 selftest，禁止运行时另写脚本 |
| CP-01~CP-50 | script-content-audit `rules/content-policy.md` 等 | 合规红线（外引，不在本包定义） |
| LG-01~LG-13 | script-logic-audit `rules/logic-rubric.md` | 逻辑判据（外引） |
| AMZ-02/03 | script-cinema-optimizer | 台词双语判据（外引） |

## 2. 变更纪律

- 本包任何规则变更记入 `CHANGELOG.md`，每条=回滚单元。
- 模型分工/默认模型变更：只改 `rules/model-routing.md`（MR-01），禁止把模型名写进其他文件。
- 流程/校验细节变更：改 `rules/standards.md` 并同步 SKILL.md 阶段表。
- 外引判据（CP/LG/AMZ）变更在各自技能包内进行，本包只改引用。
