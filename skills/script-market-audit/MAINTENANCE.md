# MAINTENANCE — 维护者 / AI 编辑入口

本文件是修改本技能包的入口。**动任何文件前先读这里。**

## 1. 架构分层一页图

```
                    ┌─────────────────┐
                    │   SKILL.md      │  瘦总控：铁律/模式表/阶段表/File Map
                    │   （≤200行）     │  禁止出现任何规则正文
                    └────────┬────────┘
             ┌───────────────┴───────────────┐
             ▼                               ▼
      ┌─────────────┐                 ┌──────────────┐
      │ workflows/  │                 │   rules/     │  规则正文唯一来源
      │ M1 / M2     │───必读────────▶ │ structure.md │  SC-*
      │ 六步细则    │                 │ platform-    │  PL-* / MK-*
      └──────┬──────┘                 │ market.md    │
             │                        │ hook.md      │  HK-*
             ▼                        └──────────────┘
      ┌─────────────┐                        ▲
      │  scripts/   │──────出数──────────────┘
      │ 体检/提取   │  产出 01_结构体检.json
      └─────────────┘
             │
             ▼
      ┌─────────────┐        ┌──────────────────┐
      │ review/     │        │ reference/       │  基线数据 / 分享清单
      │ preflight   │        └──────────────────┘
      │ audit       │
      └─────────────┘
```

数据流：脚本出数 → rules 给判读口径 → workflows 定步骤 → review 双门卡交付。

## 2. 最小阅读集对照表

**不用通读全包。** 按任务查表：

| 我要改… | 只需读 |
|---|---|
| 加一条结构判读规则 | `rules/structure.md` + `review/preflight.md` 的 A 段 |
| 更新平台数据/机制 | `rules/platform-market.md` PL-06 + `reference/market-baseline.md` |
| 加一条钩子规则 | `rules/hook.md` + `review/preflight.md` 的 E 段 |
| 改流程步骤/加阶段 | `workflows/full-review.md` + `SKILL.md` 阶段表（两处必须同步） |
| 改脚本指标 | `scripts/analyze_script.py` 头注释 + `rules/structure.md` 对应 SC 段 |
| 改报告结构 | `workflows/full-review.md` S5 + `review/preflight.md` F 段 |
| 排查漏检/空泛结论 | `review/audit.md` + `review/preflight.md` 使用原则 |
| 对外分享前检查 | `reference/sharing-checklist.md` |
| 加文件/删文件 | `SKILL.md` File Map（必须同步）+ 本文件 §3 |

## 3. 规则编号注册表

| 前缀 | 文件 | 领域 | 归属审查清单分组 |
|---|---|---|---|
| `SC-*` | `rules/structure.md` | 结构量化判读（集数/字数/同场景/爆点埋深/版本增量） | preflight A、B、C |
| `PL-*` | `rules/platform-market.md` | 平台硬机制（形态/算法/卡点/监管/饱和度/时效自查） | preflight D |
| `MK-*` | `rules/platform-market.md` | 市场适配（对标证据/日期/结论前置/视角/保留资产/可执行） | preflight D、F |
| `HK-*` | `rules/hook.md` | 钩子工程（类型/双拍/数字/素材纪律/格式/边界/自检） | preflight E |

编号规则：`[A-Z]{2,6}-\d{2}`，全包唯一，**只增不复用**。废止的编号留在原文件
并注明「由 XX-nn 取代」，不得删除后重复启用。

## 4. 标准变更 SOP

### 新增一条规则
1. 在对应 `rules/*.md` 定义，分配新编号（不复用）
2. 在 `review/preflight.md` 对应分组加一行，括号标编号 ← **漏这步 = 死规则**
3. 若新增可计算项：在 `scripts/analyze_script.py` 实现，并在 `rules/structure.md`
   的对应 SC 段写清阈值口径
4. `CHANGELOG.md` 加条目
5. `node scripts/lint_skill.mjs` → exit 0

### 修改一条规则
同上 1–5，改动记 CHANGELOG（每条 = 回滚单元，列明涉及文件）。

### 删除一条规则
1. **不删编号**。在原处标注「已废止，由 XX-nn 取代」或「已废止，无取代」
2. 清理所有引用处（含 preflight）
3. lint 必须 exit 0（C1 会检出悬空引用）

### 新增一个阶段
`workflows/*.md` + `SKILL.md` 阶段表**两处必须同步**，否则会出现
"总控有这一步但工作流没写"或反之。

### 新增脚本
`scripts/` 下 + 头注释写清「用法 + 映射的规则编号」+ 在 SKILL.md File Map
登记 + 同步 `README.md` 手动运行段。

## 5. 一致性防线

- **单一事实源**：规则正文只在 `rules/`。`workflows/`、`review/`、`SKILL.md`
  只写「动作 + 编号引用」。发现重复正文即违规。
- **lint 用法**：`node scripts/lint_skill.mjs`（在包根目录跑）。
  - `C1 FAIL` 悬空引用 → 有编号被引用但没定义
  - `C2 INFO` 孤儿规则 → 定义了但没被引用；速查表类可忽略，核心规则须登记清单
  - `C3 FAIL` 路径腐烂 → 反引号路径或 File Map 里的文件不存在
- **常量同步意识**：`reference/market-baseline.md` 的采集日期一旦更新，
  `rules/platform-market.md` 正文里引用的具体数字也要同步（PL-06 提到的那些）。
- **frontmatter 纪律**：`name` 不改（改了等于换技能）。
  `description` 改动会影响自动触发，改动需谨慎并在 CHANGELOG 说明。
  **禁止驼峰键**（`whenToUse` 等）——会导致整个包被静默丢弃。
- **回滚单元 = CHANGELOG 条目**。单条回滚按条目内所列文件反向操作。

## 6. 禁止事项

- ❌ 禁最低字数标准（提示词/产物长短由内容决定，短而全即合格）
- ❌ 禁空泛验收结论（"已检查""无问题""符合要求"一律按未检查处理）
- ❌ 禁规则正文进 SKILL.md 总控（总控 ≤200 行，只做调度）
- ❌ 禁编号复用
- ❌ 禁在包内留本机绝对路径 / 内网地址 / 他人稿件原文
  （`reference/sharing-checklist.md` 有自检命令）
- ❌ 禁把市场数据当常量硬编码进规则而不标采集日期

## 7. 已知的可争议点（留给下一位维护者）

1. **基尼系数阈值（>0.45）来自少量样本**，只有 3 部实测剧本。
   样本扩大后应重新标定，或改为分位数表述。
2. **同场景判定对地点别名无能为力**（"宋知节家" vs "宋家客厅"）。
   当前靠 AI 人工合并兜底。若要自动化，需要引入地点同义词表，
   但这会引入维护成本与误判风险，需权衡。
3. **套路词频表偏向婆媳/都市家庭题材**。若本技能要扩展到
   战神/逆袭/悬疑赛道，需扩充 `CLICHE_KW` 并重新校准 SC-05 阈值。
4. **`analyze_script.py` 的场景头解析依赖 `集-场` 编号格式**。
   遇到纯文字场景头（无编号）的稿件会漏判，此时只能靠 S3 人工通读兜底。
