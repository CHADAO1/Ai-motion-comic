# 基准快照 — 2026-11-04（MR-03 季度复核对照基线）

> 用途：MR-03 引擎表的选型依据存档。季度复核时拿新数据对照本表，变化超 2 个名次即触发 MR-03 更新。**本文件是快照，不是规则**——判定以 MR-03 为准。

## 数据来源（四基准交叉）

| 基准 | 测什么 | 规模 | 来源 |
|---|---|---|---|
| ToneBench Scriptwriting | 长视频脚本写作，盲评 | 127 模型 | modelmarkets.ai/benchmarks/tonebench（2026-10-26） |
| lechmazur 短篇 pairwise | 同题短篇小说两两对judged | 51 模型 / 17,022 对 / 113,566 判 | github.com/lechmazur/writing |
| EQ-Bench 汇总 | 创意写作/长篇/角色声线 | 52 模型 | evy.so/compare/best-llms-for-writing（2026-10-12） |
| SuperCLUE-Writing | 中文原生创意写作 | 14 模型 | superclueai.com（2026-05 版） |

## 核心数据

### ToneBench（脚本写作，与短剧最相关）
1. Claude Opus 5.5 (max) 85.9　2. Claude Fable 5.1 84.5　3. GPT-6 Sol 83.5　6. GLM-5.3 (max) 82.4　9. Kimi K3 82.2　11. GLM-5.3 Flash 81.8　13. DeepSeek V4.1 Flash 81.0　16. DeepSeek V4 Pro 80.1

> ⚠️ **口径冲突（2026-11-04 复核发现）**：benchize 聚合的 ToneBench 11-04 版（132 模型）第一为 **GPT-6 Sol Medium 81.06**、第二 GPT-6 Sol Max 80.55、第三 GPT-6 Astra Max 80.37，**Claude 不在前三**。与上表（10-26 版，Claude 85.9）不一致，疑为版本或评分口径差异。
> **处置**：MR-03 自 v1.0.5 起**停止以 ToneBench 作为挑稿档依据**，改用「2026-11-04 挑稿卷实测 ＋ 长篇第 1 ＋ NC Bench 第 1」。本行保留作冲突留痕，不作判定用。

### 短篇 pairwise（前10）
1. Claude Fable 5.1 (high) 3.745（胜率93%）　2. Claude Opus 5.5 (high) 3.693　3. Claude Opus 5 (xhigh) 3.685　4. GPT-6 Astra (high) 3.416　6. GLM-5.3 (max) 2.950　8. Kimi K3.1 Pro 2.723　11. Kimi K3 2.347

### 长篇（八章节，前三全 Claude）
Opus 5.5 17.53 / Opus 5 17.51 / Fable 5.1 17.48

### SuperCLUE 中文原生（2026-05）
1. Claude-Opus-4.7(max) 87.97（受约束创作 95.41 全场最高）　2. ERNIE-5.1 87.57　4. Kimi-K2.6 86.65　5. 豆包-Seed-2.0-Pro 86.52　12. DeepSeek-V4-Flash(max) 76.61（内容质量 66.40 显著偏弱）

## 追加 · 2026-11-04 二次复核（开放创作专项）

### Arena 创意写作（人类盲投，175 模型，11-04）
1. Claude Opus 5.5 High 1534.38　2. Gemini 4 Carbon High 1530.87　3. Gemini 4 Argon High 1527.42
**行业榜**：「写作与文学」Gemini 4 Carbon 1543.18 第一、「娱乐媒体」Carbon 1526.1 第一——类型化题材 Gemini 领先，通用创意写作 Claude 领先。

### EQ-Bench Creative Writing v3（rubric 口径，93 模型，11-04）
1. Kimi K3.1 Pro 16.63　2. GLM-5.3 16.44　3. Ox Alpha 16.43
**同 benchmark 的 Elo 口径**（79 模型，10-25）：1 GPT-6 Astra 2174　2 Claude Fable 5.1 2163　3 Claude Opus 5 2134　5 Kimi K3 2084　6 GLM-5.3 2077　7 Claude Opus 5.5 2051
> ⚠️ 同一 benchmark 两套指标给出两个冠军（Elo＝GPT-6 Astra，rubric＝Kimi K3.1 Pro）。**引用时必须写明口径**，否则结论互相打脸。

### NC Bench（作者工作流，147 模型，11-04）
1. Claude Opus 5.5 96.43%　2. Kimi K3.1 Pro 96.26%　3. GPT-6.1 Sol 95.88%
> 国产在此项已进前二，与 Claude 仅差 0.17 个百分点。

### 长篇八章（95 模型，11-04）
Opus 5.5 17.53 / Opus 5 17.51 / Fable 5.1 17.48（前三仍全 Claude，维持原判）

### 混元 Hy4（2026-11-04 正式发布）
770B MoE／49B 激活／1M 上下文；输入 ¥6、输出 ¥18、缓存 ¥0.3 每百万。
官方评测：金融众测 3.04 > DeepSeek V4.1 2.97 > Kimi K3.1 2.68 = GLM-5.3 2.68；内部 203 工程任务 preview 2.99 > Kimi 2.94 > GLM 2.92；办公场景 83.18 分、通过率 96.15%；幻觉率 7.2%。
**创意写作零指标**；Hy3 旧数据（Arena 创意 1407，第 84/417）不可外推。官方自认「与顶尖闭源仍有较大差距」。

### 挑稿卷实测（本技能自建，2026-11-04，满分 40）
混元4 **40** ／ Claude 39 ／ DeepSeek 39 ／ GLM 36 ／ MiniMax 39.5（A）↔ 25（B，不稳定，禁用）。
> 四家 A/B 除卷别、选择行、甲乙标签外完全相同 → 位置偏差**未验证**；本轮仅证明「按规则挑错」能力，不可与写作卷相加。

## 关键结论（映射 MR-03）

1. **挑稿位**：Claude Opus 5.5 三榜加冕（ToneBench #1 / 长篇 #1 / NC Bench 作者工作流 #1 96.4%），优势=长文一致性+受约束创作+改稿不注水；短板=贵、慢（44s vs 23s）、第三方渠道思考链受限时质量浮动（网文平台实测低思考档输 Kimi K3）。
2. **批量位**：GLM-5.3 Flash 性价比最优——ToneBench 81.8 距 Opus 5.5 仅 4.1 分，价格约 1/10。
3. **台词位**：豆包（实操报道）+ Kimi K3（基准加推）双选；Kimi 系中文原生第 4、价格中档、非受限渠道稳定。
4. **骨架位**：DeepSeek 反转逻辑强（MR-03 原判定维持），但中文创意写作偏弱（SuperCLUE 第12），只做骨架不做台词。
5. **Claude 三个只有它**：长文人设声音不漂（断层第一）；受约束创作 95.4 全场最高；弱稿重写不注水。代价是贵+慢，故只放挑稿位。

## 季度复核约定
- 复核时用同四源取最新数据，任一职责位模型名次变动 ≥2 → 更新 MR-03 并在本文件追加新快照（不覆盖旧快照）。
- 渠道质量浮动（聚合站思考链限制）单独记录，不进模型排名。
