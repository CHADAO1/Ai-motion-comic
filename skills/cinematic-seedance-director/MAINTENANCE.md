# MAINTENANCE — 技能维护与修改指南

> 给谁看：要修改/优化/增减本技能的人类和 AI。**改技能前先读本文，再按"最小阅读集"只读相关模块**——不需要通读全包。
> 配套自检工具：`scripts/lint_skill.mjs`（引用一致性与路径完整性校验）。变更记录写 `CHANGELOG.md`。

## 1. 架构分层与数据流（一页图）

```
SKILL.md（总控，~106行）        只管调度：流水线表 + 产物约定 + 回退规则
   │ 按阶段读
   ├─ workflows/               "做什么、按什么顺序"（Mode1/Mode2 三阶段细则）
   │    ├─ 每阶段读
   │    ├─ rules/ R1~R8        规则唯一事实源：一条规则一个编号，只在此定义一次
   │    └─ references/         外部风格库（原版未动，一般不改）
   ├─ review/                  两道审查门：preflight(内容) + audit(执行)，只引用规则编号
   ├─ reference/               速查与经验沉淀（低频加载）
   └─ scripts/                 确定性计算：估时拆段 / 提示词格式校验 / 本包自检
中间产物 → {剧本目录}\pipeline\manifest.json（跨阶段状态，断点续跑依据）
```

铁律：**规则正文只出现在 rules/*.md；workflows/review/SKILL.md 只允许出现"动作 + 编号引用"**。

## 2. 最小阅读集（常见任务 → 只需读这些）

| 要改什么 | 必读 | 联动检查 |
|---|---|---|
| 台词/配音/对照TXT | rules/dialogue-sound.md | preflight「台词与表演」组；grep `DLG-\|TXT-\|SND-` |
| 估时/拆段/30s上限 | rules/timeline-splitting.md + scripts/estimate_timeline.mjs 头注释 | preflight「时长与路由」组 |
| 空间图/资产锁定/方位 | rules/spatial-assets.md | audit A2–A4；grep `SPAT-\|SVG-\|DIR-` |
| 镜头块/表演/战斗/POV | rules/shots-action.md | preflight「动作与守恒」组 |
| 衔接/收尾镜/守恒/特效 | rules/continuity-state.md | preflight 同上组 + timeline TIME-05 |
| 模型路由 2.0/2.5 | rules/routing.md | SKILL.md 铁律1 + preflight 路由项 |
| **管线参数（画幅/时长/模型/语言）** | **rules/PIPELINE_PRESETS.md（唯一事实源）** | SKILL.md 铁律1/6 + S0-前阶段 + preflight「管线与常量」组 + audit A14 + manifest 五字段 |
| **恐怖题材（P3）** | rules/horror-suspense.md | preflight「管线与常量」组 P3 项；grep `HOR-` |
| 流程顺序/加阶段 | workflows/mode1-prompt.md + SKILL.md §3 表 + manifest 字段 | review 两道门的时机描述 |
| 审查标准本身 | review/preflight.md 或 audit.md | 所引规则编号必须已存在（跑 lint） |

定位某条规则的权威位置：`grep -n "编号" rules/`（如 `SPAT-01`）。

## 3. 规则编号注册表

格式 `[A-Z]{2,6}-\d{2}`，前缀即领域：

| 前缀 | 定义文件 | 领域 |
|---|---|---|
| RT | rules/routing.md | 模型路由 |
| TIME | rules/timeline-splitting.md | 估时/拆段 |
| ASSET/CACHE/SPAT/BLOCK/DIR/SVG/FACE/AXIS | rules/spatial-assets.md | 资产/空间/方位/空间图/朝向/轴线 |
| SHOT/PERF/ENV/ACT/CAM/POV/NEG | rules/shots-action.md | 镜头块/表演/环境/动作/运镜/POV/负面约束 |
| DLG/TXT/SND | rules/dialogue-sound.md | 台词/对照TXT/声音 |
| LINK/SPLIT/CLOSE/ANCHOR/CON/VFX/DEST | rules/continuity-state.md | 衔接/站位/收尾镜/锚点/守恒/特效/破坏 |
| FMT/PUR/SCENE | rules/purity-wording.md | 格式/纯净/特殊场景措辞 |
| NB | rules/feedback-notebook.md | 反馈记事本 |
| AUD | review/audit.md | 执行审查机制 |
| **PP** | **rules/PIPELINE_PRESETS.md** | **管线预设（画幅/时长/模型/语言/题材）** |
| **HOR** | **rules/horror-suspense.md** | **女频诡异恐怖题材（P3 专用）** |
| **INT** | **rules/delivery.md** | **交付包形态（整合文档/一致性校验）** |

新编号必须顺延最大号，不复用已删除的号（避免旧 CHANGELOG 引用错位）。

## 4. 标准变更流程（SOP）

**S-A 新增规则**：① 在对应 rules 文件追加 `### XX-nn 标题` 与正文 → ② 若属必检项，在 review/preflight.md 或 audit.md 对应分组加一行清单项（引用编号，不抄正文）→ ③ 影响流程则在 workflows/SKILL.md §3 同步 → ④ CHANGELOG 记一行 → ⑤ 跑 lint_skill.mjs 必须 PASS。

**S-B 修改现有规则**：① grep 编号找到定义处 → ② 改正文 → ③ grep 该编号的所有引用点（清单项/workflows），确认语义仍成立 → ④ 涉及常量（30s / 15s / 9:16 / 16:9 / 21:9 / 0.75s / 2.5词/s / 3.5-4字/s / 2.0 / 2.5）时全局搜索该数值同步所有出现点 → **管线类常量以 `rules/PIPELINE_PRESETS.md` 为唯一事实源，改管线参数只改该文件并在引用点注明"（PP-01）"，不要在各处重复定义新值** → ⑤ CHANGELOG → ⑥ lint PASS。

**S-C 删除规则**：① 全包 grep 编号列出全部引用点 → ② 先删/改所有引用（清单项删除或替换为替代规则）→ ③ 最后删定义正文 → ④ CHANGELOG 注明"XX-nn 废止，由 YY-nn 取代/无替代" → ⑤ lint PASS 且无 dangling 引用。

**S-D 新增阶段**：workflows 加细则 → SKILL.md §3 表插一行（含必读/输出/通过条件/回退）→ manifest.json 加 stage 字段 → 相关审查门时机核对 → CHANGELOG → lint。

**S-E 新增脚本**：scripts/ 下新建（头注释写用法+映射的规则编号）→ 在 SKILL.md §3 或对应 rules 模块登记调用方式 → CHANGELOG → lint。

## 5. 一致性防线（防多次修改积累逻辑错误）

1. **单一事实源**：任何规则正文禁止在第二处复述；发现重复立即收敛为"定义 + 编号引用"。
2. **lint_skill.mjs**（每次改动后必跑）：检查 ① 所有被引用的规则编号都有定义（防悬空引用）② File Map 与各处反引号路径真实存在（防文件改名后链接腐烂）③ 定义了但从未被引用的编号给出 WARN（提示可能是死规则或漏登记清单项）。`node scripts/lint_skill.mjs`，exit 1 = 有 FAIL 必须修复。
3. **常量集中意识**：30s/15s/21:9/0.75s/2.5 这类数字分散在多个文件是刻意的（各视角就近表述），但改动时必须全局同步——用 lint + 手工 grep 双保险。**例外：管线四项常量（画幅/时长/模型/语言）的唯一事实源是 `rules/PIPELINE_PRESETS.md`（PP-01）**，各文件只写"按管线取值（PP-01）"并给出取值表，不各自写死默认值。
4. **frontmatter 纪律**：name 不变（kebab-case）；description 只在触发词增减时改——它直接决定自动触发行为。
5. **回滚单元 = CHANGELOG 条目**：每条变更独立成条、写明动机与影响文件；单条回滚按条目内列出的文件反向操作即可。

## 6. 禁止事项

- ❌ 把规则正文塞回 SKILL.md 总控（总控只许长"调度表的一行"，不许长"一段规则"）
- ❌ 设置最低字数类验收标准——完整性一律用**要素计数**表达（七要素/≥3拍/六参数/三件套），长度由内容决定，短而全即合格
- ❌ 验收清单允许空泛结论（"已检查""无问题"）——每个 ✅ 必须绑定文件路径/脚本输出/具体数值
- ❌ 绕过 SOP 直接改 references/（外部风格库是参照物，改它等于换基准）
- ❌ 在提示词模板/交付文本中加入元注释（违反 PUR-03）
- ❌ 删除审查门或把两段式审查合并成一次（AUD-01 是硬性设计）
