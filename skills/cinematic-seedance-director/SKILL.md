---
name: cinematic-seedance-director
description: "触发词 Mode 1：剧本转提示词、视频提示词、生成提示词、Seedance 提示词、转提示词、提示词优化、分镜提示词、镜头提示词、电影级提示词。触发词 Mode 2：文戏优化、武戏优化、丰富画面情绪、剧情扩写、表情动态优化、逻辑优化、剧本打磨。Dual-mode screenplay skill. MODE 1 (剧本转提示词): parse screenplays and convert scenes into world-class Seedance 2.0/2.5 prompts at the level of global top cinematographers (Deakins, Lubezki, Fincher, Richardson, Doyle, Wong Kar-wai, Hoytema 等). MODE 2 (剧本打磨): optimize scripts across four dimensions — enriching visual emotion, expanding plot beats, choreographing character facial dynamics (Ekman micro-expressions), and fixing narrative logic. 分工：剧本深度改写/去OS/美式雌竞/本土化请用 script-cinema-optimizer；本技能 Mode 2 只做转提示词前的四维打磨。The skill matches each scene emotional tone to the best cinematographer visual language (Mode 1) or diagnoses and rewrites script weaknesses (Mode 2), then outputs clean plain-text deliverables directly usable. 内置生产实测规则：资产锁定与反推缓存、逐镜头对账、反馈记事本、动作因果、状态守恒、英文本土化台词、台词中英对照 TXT（剪辑用）、模型路由按管线预设（rules/PIPELINE_PRESETS.md）：P1 国内下沉中老年 9:16/12-15s/Seedance 2.0/中文、P2 国内女频恋爱 16:9/12-15s/2.0/中文、P3 国内女频诡异恐怖 16:9/12-15s/2.0/中文、P4 海外 21:9/≤30s/2.5/英文；未指定管线时按题材判定或提问确认。Outputs plain text — no HTML, no complex production workflow."
when_to_use: 当用户提供剧本并要求转 Seedance 提示词（Mode 1）、打磨剧本（Mode 2），或要求修改、续做、审查既有 Seedance 提示词产物时使用；剧本深度改写/本土化用 script-cinema-optimizer
---

# Cinematic Seedance Director — 总控调度器

导演感知型 Prompt 编译器。**本文件只做调度**：定义流水线阶段、每步读哪个模块文件、输入输出是什么、如何判定通过/回退。具体规则全部在各模块文件里——执行到哪个阶段就读哪个文件，禁止凭记忆复述规则跳过读取。

## 0. 全局铁律（仅 7 条）

1. **管线先定（PP-01/02/03/05）**：开工第一件事读 `rules/PIPELINE_PRESETS.md` 确定管线 ID（P1 国内下沉中老年 9:16 / P2 国内女频恋爱 16:9 / P3 国内女频诡异恐怖 16:9 / P4 海外 21:9），画幅·时长·模型·语言四项常量一律跟随管线（PP-01），题材细节参数按 PP-03 取用，结果按 PP-05 写入 manifest。**用户未说且题材无法判定时必须提问，禁止擅自假设**（国内主力默认 P1）。
2. **产物纯净**：交付文本不含任何反馈/理由/括号注释（rules/purity-wording.md PUR-*）。
3. **反馈记事本先读后改**：修改任何镜头前必读该镜头记事本 + `_全局.md`（rules/feedback-notebook.md NB-01）。
4. **双审查门**：Preflight（内容）+ Audit（执行）全过才能交付，审查报告随交付强制输出（review/）。
5. **状态落盘**：每完成一个阶段更新 `{剧本目录}\pipeline\manifest.json` 对应 status。
6. **常量随管线走**：画幅 / 单段上限 / 模型版本 / 台词语言四项常量分散在多个文件（PP-04 清单），改动或换管线时全局同步，禁止只改一处。
7. **交付必带整合文档（INT-01/02）**：任何一次交付——**包括每一次修改/续做，不只是首次**——除分文件外**必须额外出一个整合文档**（单一 Markdown，一文件看全，内容与分文件一字不差，是交付第一顺位）；一致性用 `scripts/verify_integrated.py` 机器校验（ALL_MATCH），禁止用"我核对过了"结案。**内容清单与例外口径见 `rules/delivery.md`。**
8. **★ 逐镜三行制（SHOT-00，用户 2026-10-15 定，后续所有交付统一此格式）**：
   ```
   ▸ K-XX-X-XX（X.Xs）
   镜头：景别 ｜ 人物角度 ｜ 焦段光圈 ｜ 视角 ｜ 运镜 ｜ 视觉效果真实
   表演：<一整段自然语言：动作→微表情(带顺序)→语气(挂在具体字上)→光影环境→声音，80–220 字>
   台词（角色·语气）：逐字照念
   ```
   镜头行**六段顺序不可换、分隔符用全角 ｜**，解释性描述塞进第②或第⑤段（不能新起一段）。
   **表演必须是一整段，严禁拆成「语气/微表情/微动作」分栏**——分栏会导致模型只抓大动作、
   语气与微表情整段丢失（用户已两次返工确认，见 rules/shots-action.md PERF-00）。
   工序类动作（烹调/装配/处理）若原稿只有起点终点，**必须补工序特写**（ACT-06）。
   **判据：用户复制一段就能直接投喂吗？不能就是交付失败。**

## 1. 模式触发

| 模式 | 触发短语 | 入口 |
|------|---------|------|
| Mode 1 剧本转提示词 | 剧本转提示词 / 视频提示词 / 生成提示词 / Seedance 提示词 / 分镜提示词 | §3 流水线 |
| Mode 2 剧本优化 | 剧本优化 / 优化剧本 / 文戏优化 / 武戏优化 | workflows/mode2-script-opt.md |

- 用户链式要求（"先优化再转提示词"）→ 先 Mode 2 后 Mode 1。
- 表述含糊（"帮我处理这个剧本"）→ 先问用户要哪种模式。
- 修改/续做已有产物 → 按 Mode 1 流水线从 manifest 断点续跑。

## 2. 产物与目录约定

```
{剧本目录}\
├── pipeline\            ← 结构化中间产物（跨阶段传递只靠这些文件）
│   ├── manifest.json    ← 阶段状态表（断点续跑依据）
│   ├── 01_解析清单.json  ← S0 场景清单+拍点表数据
│   ├── 02_时间轴.json    ← S1 脚本估算结果
│   ├── 03_拆段表.json    ← S2 最终拆段方案
│   ├── 05_逐段验收表.md  ← S4 每段生成后逐段验收的证据表（模板见 workflows/mode1-prompt.md）
│   └── 06_审查报告.md    ← S6 Audit 报告
├── 空间图\              ← {段名}_空间图.svg/.png/_空间说明.md 三件套
├── 资产图\_反推缓存\     ← 每张资产图一个同名 .txt
├── 反馈历史\            ← {镜头}.md 记事本 + _全局.md
└── outputs\             ← {段名}.txt 提示词 + {剧本名}-台词中英对照.txt
                           + {场次}_整合文档_{标题}.md ← INT-01 交付入口（一文件看全，排最前）
```

manifest.json 结构：

```json
{
  "script": "剧本名", "mode": "1", "model": "2.0",
  "pipeline": "P1", "aspectRatio": "9:16", "maxSeconds": 15, "language": "zh",
  "stages": {
    "parse":        { "status": "pending|done", "output": "pipeline/01_解析清单.json" },
    "timeline":     { "status": "pending|done", "output": "pipeline/02_时间轴.json", "tool": "scripts/estimate_timeline.mjs" },
    "split":        { "status": "pending|done", "output": "pipeline/03_拆段表.json" },
    "spatial":      { "status": "pending|done", "output": "空间图/" },
    "prompts":      { "status": "pending|done", "files": [] },
    "dialogue_txt": { "status": "pending|done", "file": "" },
    "preflight":    { "status": "pending|done" },
    "audit":        { "status": "pending|done", "report": "pipeline/06_审查报告.md" }
  },
  "updated": "ISO 时间"
}
```

## 3. Mode 1 流水线（总览）

执行细则在 workflows/mode1-prompt.md；下表是调度依据：

| Stage | 做什么 | 必读文件 | 输出 | 通过条件 | 失败回退 |
|---|---|---|---|---|---|
| **S0-前 管线确认** | 定管线 ID，锁定画幅/时长/模型/语言 | rules/PIPELINE_PRESETS.md PP-01~05 | manifest 写入 pipeline/aspectRatio/maxSeconds/model/language | 管线 ID 已确定且已落盘；无法判定时已向用户提问 | 回退到提问 |
| S0 解析 | 提取场景/角色/拍点 | mode1-prompt.md Phase 1 | `01_解析清单.json` + 场景清单表给用户 | 字段齐全；用户确认范围 | 补提取 |
| S1 估时 | 跑脚本算时长 | timeline-splitting.md + routing.md + PIPELINE_PRESETS.md | `02_时间轴.json` | 分段落剧情断点上；AI 复核过 | 改拍点表重跑 |
| S2 拆段 | 定最终拆段方案 | timeline-splitting.md + continuity-state.md(SPLIT/CLOSE) + anti-warp.md(AW-04/05/06/09) | `03_拆段表.json` | 每段 ≤管线 maxSeconds（P1-P3=15s，P4=30s）；每组自包含；全员站位义务已确认；跨组防消失已核；**台词守恒门1通过**（`check_dialogue_coverage.mjs` 门1 exit 0） | 回 S1 |
| S3 空间图 | 三件套+站位审查 | spatial-assets.md(SVG/SPAT/DIR) + CACHE-01 + anti-warp.md(AW-11/12) | 空间图三件套 | 站位逻辑审查过；无方位脑补 | 补图/改图 |
| — 中途门 | **Audit A1–A4（硬性）** | review/audit.md | — | A1–A4 全 ✅ | AUD-05 补执行 |
| S4 提示词 | 九段结构编译每段 | PROMPT_PATTERNS.md + rules/(spatial-assets, shots-action, camera-motion, dialogue-sound, continuity-state, purity-wording, content-safety, omni-reference, voice-direction, drama-performance, anti-warp, negatives-layered) + routing.md | `outputs\{段名}.txt` + `05_逐段验收表.md` | **逐段循环**：每段生成即验，验收表全 ✅（mode1-prompt §S4.1） | 当段返工重跑 |
| S5 台词TXT | 中英对照（生成/修订后同步） | dialogue-sound.md(TXT-01) + voice-direction.md(VO-01/03/06) | `outputs\{剧本名}-台词中英对照.txt` | 逐条收录完整且与当前提示词同版本；配音指令已按五段式；音色标签取自标准库；**台词守恒门2通过**（`check_dialogue_coverage.mjs` 门2 exit 0） | 补条目/重同步 |
| S6 审查交付 | 双门+报告 | review/preflight.md + review/audit.md | `06_审查报告.md` + 交付 | Preflight 全过 + A1–A13 全 ✅ + 报告已输出 | AUD-05 补执行 |

估时/校验脚本用法见各文件头注释；脚本负责确定性计算，AI 负责创意复核。

## 4. Mode 2 入口

读 workflows/mode2-script-opt.md 执行三阶段（诊断→提案→完整优化），交付附三阶段完成声明。之后转 Mode 1 时从 S0 起，自动触发完整审查流程。

## 5. 断点续跑与回退

1. 任务开始：定位剧本目录，读 `pipeline\manifest.json`。存在 → 从第一个非 done 的 stage 继续；不存在 → 从 S0 创建。
2. 任一审查项 ❌ → 按 review/audit.md AUD-05 补执行 → 受影响的 stage 及其后的 status 全部置回 pending 并重跑 → 更新 manifest。
3. 用户手动改了任何中间产物（拍点表/拆段表/空间图/提示词）→ 同样按第 2 条回退受影响阶段。

## 6. File Map

```
SKILL.md                     总控调度（本文件）
workflows/
  mode1-prompt.md            Mode 1 三阶段执行细则
  mode2-script-opt.md        Mode 2 三阶段流程
rules/
  PIPELINE_PRESETS.md R0 管线预设：P1-P4 画幅/时长/模型/语言/题材（PP-*），所有常量的唯一事实源
  routing.md                 R1 模型路由 2.0/2.5（RT-*）
  timeline-splitting.md      R2 估时公式/段上限/脚本用法（TIME-*）
  spatial-assets.md          R3 空间布局/资产锁定/双重方位/空间图（ASSET/CACHE/SPAT/BLOCK/DIR/SVG/FACE/AXIS-*）
  shots-action.md            R4 镜头块/表演/动作因果/POV/负面约束（SHOT/PERF/ENV/ACT/CAM/POV/NEG-*）
                   ★ SHOT-00 镜头行格式（用户 2026-10-15 定）：`镜头：景别｜人物角度｜焦段光圈｜视角｜运镜｜视觉效果` 六段，顺序不可换；
                     PERF-00 表演**写成一整段**（用户两次返工定案，严禁拆成语气/微表情/微动作分栏）；ACT-06 工序缺失必补工序特写
  camera-motion.md           R4-companion 摄影机运动方法论与时序分段编排（CAM-02~08 + SEQ-*，与 R4 配套；详见 reference/quick-ref.md §6）
  dialogue-sound.md          R5 台词本土化/演绎/对照TXT/声音（DLG/TXT/SND-*）
  continuity-state.md        R6 衔接/站位约束/收尾镜/守恒/特效/破坏（LINK/SPLIT/CLOSE/ANCHOR/CON/VFX/DEST-*）
  purity-wording.md          R7 题头/纯净/收尾格式/深空与巨型结构措辞（FMT/PUR/SCENE-*）
  feedback-notebook.md       R8 反馈记事本（NB-*）
  content-safety.md          R9 提示词内容安全与血腥正面框架（SAFE-/CP-*，规范见 script-content-audit 技能）
  horror-suspense.md         R10 女频诡异恐怖题材（P3 管线专用，HOR-*）：三要素/惊吓节奏/光源/视角/合规红线/声音/两级表演
  omni-reference.md          R11 即梦全能参考·@全模态素材绑定（OR-*）：@语法/素材命名/参考范围/权重上限/四类禁用/资产闭环
  voice-direction.md         R12 配音指令与音色标签（VO-*）：五段式格式/内心OS/标准音色标签库150+/标点→表演/语速表/强弱约束分层
  drama-performance.md       R13 文戏表演引擎（DRA-*）：情绪过程弧线六段/机制六型/微表情字段库/降噪1+3+1+1/留白/镜头目的/动作五层/步态五型/Blocking四要素
  anti-warp.md               R14 防畸变与组包连续性（AW-*）：黄金搭配五套餐/节奏硬规则/运镜衔接五模式/组包自包含/起始状态/跨组防消失/尾镜锚定/高级转场/首集开局/轴线/禁脑补
  negatives-layered.md       R15 三层负面词（NEG-05~11）：基础+类型+场景三层/情绪失败模式表/降噪公式/正面落点配对
  delivery.md                R16 交付包形态（INT-*）：整合文档内容13项清单/三条硬要求/一致性机器校验与声明式例外
review/
  preflight.md               C1 内容检查清单（S6 第一道门）
  audit.md                   C2 执行审查 A1–A13（两段式+报告强制）
reference/
  quick-ref.md               表演微事件/景别/焦段/构图/运镜/节奏弧线/失败模式对策速查
  lessons-testing.md         核心经验31条 + 低成本测试协议（归因诊断时读）
references/                  外部风格库（原有，未改动）
  DIRECTOR_STYLES.md         8 位 DP 风格库 + Style Selection Matrix
  SHOT_LANGUAGE.md           景别/运动/焦段/构图/转场词汇
  RHYTHM_CONTROL.md          节奏弧线/时长指南/声画同步
  PROMPT_PATTERNS.md         九段提示词结构模板 + 完整示例（S4 的结构圣经）
  SCRIPT_OPTIMIZATION.md     Mode 2 完整方法论
scripts/
  estimate_timeline.mjs        台词/表演估时 + 段上限自动拆段 → 时间轴 JSON（TIME-01/02, CLOSE-01）
                                英文走 dialogueEn+speechRateWps；中文走 dialogueZh+speechRateCps（原生支持）
  validate_prompt.mjs          提示词交付格式校验：题头/尾行/时长/分隔线/镜头数声明（FMT/TIME/NEG-03）
  check_dialogue_coverage.mjs  台词守恒校验（防漏台词）：门1 拍点表→拆段表；门2 拍点表→提示词配音指令
  verify_integrated.py         INT-01 一致性校验：整合文档 ⇄ 分文件逐块比对（ALL_MATCH / HAS_DIFF）
                               `python verify_integrated.py --integrated <整合.md> --sources <分文件目录> [--skip 2]`
                               --skip 只用于「该块按交付需要改造过」的声明式例外，禁止用它掩盖真实漂移
```

## 7. 维护约定

修改本技能前先读 `MAINTENANCE.md`（架构图、规则编号注册表、常见任务最小阅读集、增删改 SOP）。变更记录写入 `CHANGELOG.md`。

- 新规则 → 写进对应 rules/*.md 并带编号，同时在 review/preflight.md 或 audit.md 加一条引用该编号的清单项；**不要**把规则正文写进本总控。
- 新阶段 → workflows 加细则 + 本文件 §3 表加一行 + manifest.json 加字段。
- 新脚本 → scripts/ 下加文件并在 §3 表或相关模块登记调用方式。
- 任何改动完成后跑 `node scripts/lint_skill.mjs`，exit 1 必须修复后才算完成。
