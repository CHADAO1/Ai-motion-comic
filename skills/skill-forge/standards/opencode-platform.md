# 标准S1 — OpenCode 平台硬约束

> 制作或安装任何技能前必读。以下以 OpenCode V2 官方文档
> <https://opencode.ai/docs/skills/> 与 <https://opencode.ai/docs/config/> 为准。

## F1 发现机制

- **Global**：`~/.config/opencode/skills`
- **Project**：`.opencode/skills`（从当前目录向上直到项目根，每一层都算）
- **兼容性来源**：`~/.claude/skills`、`~/.agents/skills` 及其项目级同名目录
- **额外来源**：任意 `opencode.json(c)` 里的 `skills` 数组，可放本地目录（相对 cwd / `~/` / 绝对路径）或 HTTP catalog（`index.json`）。多个配置文件的 `skills` 数组是**合并**而非替换。

一个 source root 里可以有两种形态：

```text
skills/
├── review.md                 ← 根目录的 *.md
└── git-release/
    └── SKILL.md              ← 分组目录里名为 SKILL.md 的文件
```

- `SKILL.md` 可以嵌套在分组目录中（如 `skills/teams/release/SKILL.md`），搜索最深 **6 层**。
- **一个含 `SKILL.md` 的目录就是一个技能，OpenCode 不会再往它内部找更多技能。**
- 隐藏文件/目录、`node_modules` 被跳过。
- 因此技能目录要平铺在 source root 下（推荐 `<root>/<id>/SKILL.md`）；
  把技能塞进别的技能目录内部是无效的，而放进纯分类子目录虽然仍可能被发现，
  但会改变 ID 的解析路径、容易造成 ID 冲突，不推荐。

## F2 frontmatter 与 ID

- 运行时**所有 frontmatter 都是可选的**，但要让技能被模型发现，必须有清晰的 `description`；
  没有 `description` 的技能不会出现在可用列表里。
- `name` 只是**显示名**，默认取路径派生 ID；它不是 ID。
- **ID 由文件路径决定**、精确且大小写敏感：`<source>/git-release/SKILL.md` → `git-release`；
  `<source>/teams/release/SKILL.md` → `release`。
- 可移植技能建议使用 `^[a-z0-9]+(-[a-z0-9]+)*$` 的 kebab-case ID（1–64 字符），并与目录名一致。
  V2 目前**不强制**该正则、不强制 `name` 与目录一致、也不限制 description 长度——
  所以中文目录名（如 `wan3专用`）可用，但跨工具移植时不推荐。
- `metadata.opencode/autoinvoke: false` 或 `disable-model-invocation: true` 把技能从可用列表隐藏；
  仍可按 ID 显式加载。两者同时设置时 `opencode/autoinvoke` 优先。
- 触发词写进 `description`（列表里只有 ID / name / description，不含正文）。

## F3 加载与自动重载

- 每个模型步只列出有 `description` 且未被隐藏的技能的 ID / name / description，不加载正文。
- 加载方式：模型调 `skill` 工具传 `{"id":"<skill-id>"}`，或用户在提示里写 `@skill-id`。
- 加载后：body（去掉 frontmatter）加入对话，并给出技能基目录 + 最多 10 个配套文件路径样本。
  **配套文件不自动载入**，必须由 SKILL.md 指挥 agent 按需 `read`。
  → 「总控越瘦、配套文件按需读」仍然是最有效的上下文预算手段。
- 配置与技能文件由 watcher 监听，**保存即自动重载，无需重启客户端**；必要时 `/reload` 强制刷新。
  改 frontmatter 后确认技能出现在可用列表；未出现按 F1/F2 排查（最常见：缺 `description`、
  文件不在 source root 下、ID 被更高优先级来源覆盖）。

## F4 文件格式

- 一律 UTF-8 无 BOM（含中文内容时尤须确认）；脚本 LF / CRLF 均可。
- SKILL.md 内写的相对路径，基准是**该文件所在目录**。
- Markdown 代码块围栏配对完整（模板复制后检查 ``` 数量为偶数）。

## F5 安装位置决策与优先级

| 场景 | 位置 |
|---|---|
| 仅当前项目用 | `<项目根>/.opencode/skills/<id>/SKILL.md` |
| 所有项目共享 | `~/.config/opencode/skills/<id>/SKILL.md` |
| 跨工具共享（兼容源） | `~/.claude/skills/<id>/`、`~/.agents/skills/<id>/` |
| 额外目录 / 远程 catalog | `opencode.json(c)` 的 `skills` 数组 |

同 ID 按来源优先级，**后注册者覆盖前者**：

1. 内置技能 → 2. `.claude/skills`（全局→各层）→ 3. `.agents/skills`（全局→各层）
→ 4. `~/.config/opencode/skills` → 5. 项目 `.opencode/skills`（项目根→当前目录）
→ 6. 显式 `skills` 配置条目（按配置优先级与数组顺序）

避免重复 ID，除非有意覆盖。外部下载的技能包先落暂存目录做体检（Mode B），
通过后再复制进上述正式位置；原下载目录永久保留作为回滚基准。

## F6 迁移前旧口径的差异（必读）

| 迁移前旧口径 | OpenCode 实际 |
|---|---|
| 只发现一级目录下的 SKILL.md，移进二级目录等于停用 | 搜索最深 6 层；移进纯分类子目录**仍会被发现**（ID 取路径末段）。停用请用 `opencode/autoinvoke: false`、移出 source root，或用 `permissions` 的 `skill` deny 规则 |
| `name` 必须 kebab-case 且 `name == 目录名`，否则丢弃 | `name` 只是显示名；ID 由路径决定，正则仅为可移植性建议，V2 不强制 |
| 驼峰键 `disableModelInvocation` 等致命、整包丢弃 | 用 `metadata.opencode/autoinvoke` / `disable-model-invocation`；V2 接受 `license`、`compatibility` 等可移植字段但不解释 |
| 改完要重启宿主刷新技能列表 | watcher 自动重载，无需重启；必要时 `/reload` |
| 自建模型写宿主私有 `models.json` | 会话模型写 `opencode.json(c)` 的 `providers`；`~/.config/opencode/models.json` 只是脚本用的端点清单 |

> 权限：可用 `permissions` 的 `{ "action": "skill", "resource": "<id>", "effect": "allow|ask|deny" }`
> 控制技能的广告与加载；`deny` 会从模型可见列表里隐藏并拒绝加载。
