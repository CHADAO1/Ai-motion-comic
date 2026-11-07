# 技能仓库结构说明

本仓库以**你自己的仓库为主干**，用 `git subtree` 把外部技能方案整仓收编到 `vendor/`，
再用 OpenCode 的 `skills` 配置数组把各方案的 `skills/` 目录挂成技能源。

## 目录结构

```
Ai-motion-comic/
├── README.md                     # 原仓库说明（未改动）
├── vendor-manifest.json          # 外部方案登记表：url / ref / commit / 来源
├── opencode.jsonc                # OpenCode skills 配置示例
├── scripts/sync-vendor.ps1       # 一键更新所有上游
├── docs/SETUP.md                 # 本文件
├── skills/                       # 【你自己的技能】<id>/SKILL.md
└── vendor/                       # 【外部方案，勿手工改动】
    └── anthropics-skills/        # git subtree 引入，保留上游完整结构
        └── skills/               # ← 挂到 OpenCode 的技能源
```

## 为什么整仓收编、而不是只拷技能目录

`git subtree add` 会把上游**整个仓库**放进 `--prefix`，没法只取子目录。
所以保留上游原结构，改由 `opencode.jsonc` 的 `skills` 数组分别指向每个上游的 `skills/` 子目录：

- 不用拆上游历史、不用 `filter-repo`
- 不用改上游文件、不用符号链接
- 上游更新时 `git subtree pull` 一次即可
- 各方案彼此隔离，ID 冲突可控（后注册的源胜出）

## 新增一个外部方案

```powershell
# 1. 整仓并入（--squash 压缩上游历史，保持主仓库干净）
git subtree add --prefix=vendor/<方案名> <仓库URL.git> <分支> --squash

# 2. 在 vendor-manifest.json 追加一条（id / prefix / url / ref / skill_source / upstream_commit）

# 3. 在 opencode.jsonc 的 skills 数组加一行指向该方案的 skills/ 目录

# 4. commit
git add -A; git commit -m "vendor: add <方案名> via subtree"
```

## 更新已有方案

```powershell
powershell -ExecutionPolicy Bypass -File scripts/sync-vendor.ps1              # 全部
powershell -ExecutionPolicy Bypass -File scripts/sync-vendor.ps1 -Only anthropics-skills
powershell -ExecutionPolicy Bypass -File scripts/sync-vendor.ps1 -DryRun     # 只看会跑什么
```

脚本要求工作区干净。更新后 commit / push 到你自己的仓库。

## 接入 OpenCode

把 `opencode.jsonc` 里的 `skills` 数组合并进 `~/.config/opencode/opencode.json(c)`。
OpenCode 会热重载，**无需重启**。技能 ID 由目录名决定，大小写敏感；
`SKILL.md` 的 frontmatter 必须有 `description` 才会被模型自动发现。

## 注意事项

- `vendor/` 由 subtree 管理，不要手工改文件，改动会在下次 pull 时冲突。
  要定制就在 `skills/` 里另建自己的技能，或用不同的 ID。
- 外部方案的许可证见各自目录（如 `THIRD_PARTY_NOTICES.md`），商用前请核对。
- 推送到 GitHub 需要 PAT 或 SSH key，凭据不要写进仓库或配置文件。
- 当前为**本地试跑状态**：subtree 与骨架已在本地 commit，**尚未 push**。
