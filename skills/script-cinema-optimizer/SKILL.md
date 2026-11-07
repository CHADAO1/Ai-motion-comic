---
name: script-cinema-optimizer
description: "触发词：优化剧本、剧本转AI电影、去OS、美式雌竞、剧本本土化、剧本视听化、剧本深度改写、短剧本土化。将对话驱动的中文短剧剧本深度改写为面向 YouTube 国际观众的 AI 电影视听驱动剧本。MODE 1 (剧本视听优化): 把长剧本按六步流水线（切片→冷读诊断→视听化重写→美式雌竞+双语本土化→视觉概念落地→一致性终审）转化为去OS、转潜台词、美式雌竞、视觉奇观的最终剧本。与 cinematic-seedance-director 的分工：本技能做动剧情动结构的深度改写与本土化；转提示词前的文戏武戏四维打磨（画面情绪/节拍/微表情/逻辑）用 cinematic-seedance-director Mode 2。内置规则：DIAG(诊断)/VIS(视听化)/AMZ(美式化)/VCB(视觉概念)/CON(一致性) 五域编号规则 + 双审查门。"
when_to_use: 当用户想把中文短剧/网文剧本深度改写（去OS/美式雌竞/本土化/视听化）为适合 AI 电影（尤其 YouTube 国际受众）的剧本时使用；转提示词前的轻度打磨请用 cinematic-seedance-director。
---

# 剧本视听优化器 — 总控调度器

把"语言驱动"的中文短剧重写为"视听驱动"的 AI 电影剧本。**本文件只做调度**：执行到某阶段才读取对应 `rules/` 模块，禁止凭记忆复述规则跳过读取。每条规则的唯一事实源在 `rules/*.md`，编号见 `MAINTENANCE.md`。

## 0. 全局铁律（≤7 条）
1. **流水线优先**：一次性改写几万字必致中间丢失与指令稀释；必须按 S0→S5 分步，每步只做一件事。
2. **记忆结晶落盘**：每步产物写入 `pipeline/`，下一步靠读文件衔接，不靠模型记忆。
3. **双审查门**：`review/preflight.md` + `review/audit.md` 全过才交付，审计报告随交付输出。
4. **单一事实源**：规则正文只在 `rules/` 定义；本文件与 stage 表只写"动作 + 编号引用"。
5. **去 AI 套话**：通用模板表情词（瞳孔骤缩/眼底/冷笑…）必须替换为角色专属动作（`DIAG-04`/`VIS-04`）。
6. **美式而非翻译腔**：雌竞动机改写与台词本土化按 `AMZ-*` 规则，不是最后翻译改几个词。
7. 验收用要素计数+证据绑定；禁止字数下限与空泛结论。
8. **内容红线优先**：优化全程受 script-content-audit 的 CP-* 红线约束（规范见本技能 `rules/content-policy.md`）；冲突/亲密/危险角色须按正面框架改写，婴幼儿/孕妇绝对规避。

## 1. 模式触发
| 模式 | 触发短语 | 入口 |
|---|---|---|
| Mode 1 | 优化剧本 / 剧本转AI电影 / 去OS / 美式雌竞 / 剧本本土化 / 剧本视听化 | 本文件 S0–S5 |

## 2. 产物与目录约定
```
{工作目录}\                      ← 即用户给出的剧本所在目录或新建工作目录
├── pipeline\                    ← 中间产物（断点续跑依据，必须落盘）
│   ├── manifest.json           ← 各 stage status，断点续跑依据
│   ├── 00_slices.md            ← S0 切片索引 + 各场纯文本
│   ├── 01_diagnosis.md         ← S1 人物卡+视觉圣经+问题清单+钩子地图+角色动作库
│   ├── 02_rewritten/           ← S2 视听化后各场文本
│   ├── 03_localized/           ← S3 双语本土化各场文本
│   ├── 04_visual/              ← S4 视觉概念落地各场文本
│   └── 05_audit.md             ← S5 终审报告
└── outputs\
    └── 优化剧本_完成版.md        ← 最终交付物
```

manifest.json 结构：`{ "stages": { "s0": {"status":"pending|done","output":""}, … }, "updated": "" }`；任一审查 ❌ → 受影响 stage 及其后置置回 `pending` 重跑。

## 3. 流水线（总览）
| Stage | 做什么 | 必读文件 | 输出 | 通过条件 | 失败回退 |
|---|---|---|---|---|---|
| S0 | 读全文、按"集→场"切分为 `E{nn}-S{nn}` 文本块，块头注入本场人物+目标 | `reference/learning-material.md` | `pipeline/00_slices.md`, `manifest.json` | 每场可独立读懂、无悬空指代 | 重切，场边界按空行+场景标题 |
| S1 | 冷读诊断（零修改）：人物卡/视觉圣经/问题清单/钩子地图/角色动作库 | `rules/diagnose.md` | `pipeline/01_diagnosis.md` | OS 全数定位、`VIS-04`动作库≥2条/角色、视觉圣经≥4设定 | 补诊断，回 S0 校验切片 |
| S2 | 视听化重写：砍OS至三类、解释性对白转潜台词/动作、每场≥1无台词节拍、**逐场清除内容红线并按正面框架改写冲突/亲密戏** | `rules/rewrite.md` (`VIS-*`), `rules/content-policy.md` (`OPT-*`) | `pipeline/02_rewritten/` | OS残留≤20%、无"角色念出阴谋"、专属动作已落地、**无飙血/创口/断肢/擦边/受害描写** | 回 S1 取诊断重改该场 |
| S3 | 美式雌竞+双语本土化：动机改写、中英双语共生、称谓/羞辱词简化、**红线本土化同步清除** | `rules/rewrite.md` (`AMZ-*`), `rules/content-policy.md` (`OPT-*`) | `pipeline/03_localized/` | 无勾引/贱人/粗鄙类词、每句英文母语可读、**无 CP-01~17 残留** | 回 S2 重做该场 |
| S4 | 视觉概念落地：超自然元素质感、动作戏连续节拍 | `rules/visual-consistency.md` (`VCB-*`) | `pipeline/04_visual/` | 每个超自然元素有质感描述、动作戏≥3拍 | 回 S3 重做该场 |
| S5 | 一致性终审：跨场矛盾/性格漂移/钩子留存，汇编完成版 | `rules/visual-consistency.md` (`CON-*`), `review/audit.md` | `outputs/优化剧本_完成版.md`, `pipeline/05_audit.md` | 0 处设定矛盾、每集钩子齐全、首15秒冷开场 | 回到出错 stage 重跑 |

## 4. 断点续跑与回退
任务开始先读 `pipeline/manifest.json` → 从第一个非 `done` 的 stage 继续；审查 ❌ → 补执行 → 受影响 stage 置回 `pending` 重跑。每完成一个 stage 立即更新 `manifest.json` 的 `status` 与 `updated` 时间戳。

## 5. 执行顺序约束
1. S0 用 Read/或 python 提取 `.docx` 文本（`.docx` → 解压 `word/document.xml` 取 `<w:p>` 文本；`.txt` 直接读）。
2. S1–S4 每场独立处理，处理 `E{nn}-S{nn}` 时只把该场文本 + `01_diagnosis.md` 相关段落喂给模型，**不**把全本塞进上下文。
3. S5 读全部 `04_visual/` + `01_diagnosis.md`，产出审计报告与完成版。

## 6. File Map
```
SKILL.md
README.md
MAINTENANCE.md
CHANGELOG.md
rules/diagnose.md
rules/rewrite.md
rules/visual-consistency.md
rules/content-policy.md
review/preflight.md
review/audit.md
reference/learning-material.md
scripts/lint_skill.mjs
pipeline/manifest.json
```

## 7. 维护约定
修改前读 `MAINTENANCE.md`；变更记 `CHANGELOG.md`；改完跑 `node scripts/lint_skill.mjs`（exit 1 必须修复）。禁止把规则正文写回本文件。
