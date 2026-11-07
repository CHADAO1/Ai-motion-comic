# 工作流模块 W1 — Mode 1：剧本转提示词（三阶段细化）

> 总控流水线 S0–S6 的执行细则。本文件定义"做什么、按什么顺序"，具体规则在 rules/ 各模块。

## Phase 1 / S0 — 解析剧本

读整个剧本/段落，提取并整理：

1. **Scene inventory:** scene numbers, INT/EXT, location, time of day
2. **Characters:** name, first appearance, physical description from script, wardrobe if specified
3. **Locations:** each distinct location with brief environmental description
4. **Props:** anything that becomes a visual focus (photos, weapons, artifacts, vehicles, screens, notes)
5. **Emotional register per scene:** dominant and secondary emotions — 驱动风格选择（见 references/DIRECTOR_STYLES.md Style Selection Matrix）
6. **Action beats per scene:** each discrete physical action that will become a shot or beat
7. **Dialogue:** verbatim lines with speaker identification

同时提取输入解析项：
- 本段开始状态 / 结束状态；必须发生的剧情事件 / 可自由设计区域
- 角色位置与朝向 / 世界方向与屏幕方向
- 道具位置与数量 / 伤势与服装状态
- 已产生和已核销特效 / 场景破坏状态
- 上一镜动作势能 / 目标模型、时长、平台

**输出** `pipeline\01_解析清单.json`（场景清单 + 角色 + 资产图清单 + 拍点表数据）。同时输出简要场景清单表（中文）给用户看：

```
场景 | INT/EXT | 位置 | 时间 | 角色 | 情绪基调 | 风格匹配
1   | INT    | 公寓  | 夜   | A   | 悲伤/孤独 | Deakins
2   | EXT    | 街道  | 日   | A,B | 紧张/对峙 | Fincher
```

如果用户指定了要处理的场景，进入 Phase 2；否则询问哪些场景（或"全部"）。

## Phase 2 / S1–S3 — 风格选择、估时拆段、空间图

### S1 风格选择 + 估时
1. 按 Style Selection Matrix 把每个场景的情绪基调匹配到导演/DP 风格；用户指定风格则服从；场景中段情绪转向时规划风格过渡（如 `Deakins → Richardson`）。
2. 按拍点表跑估时脚本生成 `02_时间轴.json`，AI 复核分段点（rules/timeline-splitting.md TIME-01~05）。
3. 设计节奏弧线——slow burn / crescendo / pulse / sustained note / freefall / breathing room（见 references/RHYTHM_CONTROL.md）。高潮后必须有至少一个长镜做情绪恢复。

### S2 拆段定稿
按时间轴确定最终拆段方案 → `03_拆段表.json`（每段：段名/秒数/出场角色全集/衔接切点）。同步确认 SPLIT-01 全员站位义务与 CLOSE-01 收尾镜义务。

### S3 空间图（硬性门）
对每段生成站位空间图三件套并审查站位逻辑（rules/spatial-assets.md SVG-01~04、SPAT-03）。资产反推缓存先查后推（CACHE-01）。
**中途审查（硬性）**：S3 完成后执行 Audit A1–A4（review/audit.md），全部 ✅ 才进 Phase 3。

## Phase 3 / S4–S6 — 生成提示词与交付

### S4 提示词编译（每段一块）
按 references/PROMPT_PATTERNS.md 的九段结构顺序写提示词清单：
1. 风格声明 → 2. 场景概述（含 ANCHOR-01 一句话剧情锚点）→ 3. 空间布局+资产锁定 → 4. 镜头块 → 5. 表演指导 → 6. 环境活动 → 7. 对白规则 → 8. 失败模式警告+负面约束 → 9. 收尾

规则来源（只读本段用到的）：
- 空间/资产/方位 → rules/spatial-assets.md
- 镜头块/表演/动作/负面约束 → rules/shots-action.md
- 台词/声音 → rules/dialogue-sound.md
- 衔接/收尾镜/守恒 → rules/continuity-state.md
- 题头/纯净/特殊措辞 → rules/purity-wording.md
- 模型差异 → rules/routing.md

输出纯文本，每段包含：Scene header（代码块外）、完整中文 Seedance 提示词（九段结构）、Duration + aspect footer、Shot analysis block（镜头语言/构图/节奏 analysis，2-3 句 each，代码块外）。
保存到 `{剧本目录}\outputs\{段名}.txt`。

### S4.1 逐段验收（防偷懒核心机制，硬性）

多段时**逐段循环**：生成一段 → 立即校验 → 填验收表一行 → 再写下一段。**禁止把全部段落写完后攒批补验**——攒批补验是漏检主因。

每段生成完立即跑：

```powershell
node <技能目录>\scripts\validate_prompt.mjs {剧本目录}\outputs\{段名}.txt --max 30
```

并把该行追加进 `{剧本目录}\pipeline\05_逐段验收表.md`：

```
| 段 | 秒数(取02_时间轴值) | validate结果 | 九段结构完整 | 镜头块七要素齐(逐一列出) | 出画角色全锁定(SPLIT-01,列名单) | 站位与空间图一致 | 台词结尾收尾镜(CLOSE-01) | 结论 |
|----|----|----|----|----|----|----|----|----|
| 6-1 | 28.5 | PASS | ✅ | ✅ 机位/构图/景深/角度/运动/动作/微表演 | ✅ 塞拉/莉拉/艾琳 | ✅ 与6-1空间说明一致 | ✅ 无台词余韵镜 | ✅ |
```

- 每个 ✅ 必须落到可核查证据（文件/脚本输出原文/角色名单）；"已检查""没问题"这类空泛结论按未检查处理。
- 完整性以**要素计数**为准（七要素是否逐项在位、弧线是否≥3拍、关键句是否六参数齐全），**禁止以最低字数为标准**——提示词长短由内容决定，短而全即合格。
- 任一格不过 → 该段当场返工重跑，更新该行；全部行 ✅ 才可进入 S5。

### S5 台词对照 TXT
按 dialogue-sound.md TXT-01 生成 `{剧本目录}\outputs\{剧本名}-台词中英对照.txt`。
提示词经任何修订（R 反馈返工、局部改动）后，按 TXT-01 的修订触发条款同步复核/更新本 TXT（比对提示词对白行 ↔ TXT 条目 + 各段头时长），同步完成才进 S6。

### S6 双审查 + 交付（硬性）
1. 跑 review/preflight.md 全项内容检查；
2. 跑 review/audit.md 终审全清单（A1–A13），输出审查报告随交付给出——**报告缺失 = 任务未完成，禁止交付**；
3. 全部通过后更新 manifest 各 stage status，交付：提示词 TXT + 对照 TXT + 审查报告。最终提示词放在代码块中，可直接复制到 Seedance。
