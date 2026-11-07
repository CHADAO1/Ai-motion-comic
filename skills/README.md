# 自有技能目录

放你自己写的技能，一个技能一个目录：

```
skills/
└── <skill-id>/
    ├── SKILL.md      # 必须有 frontmatter 的 description 才会被 OpenCode 自动发现
    ├── scripts/      # 可选
    └── references/   # 可选
```

`<skill-id>` 建议小写 kebab-case，且不要与 `vendor/` 下外部方案的技能 ID 重名（重名时后注册的源胜出）。

外部方案不放在这里，统一放 `vendor/`，由 `vendor-manifest.json` 登记。
