---
name: opencode-custom-model
description: |
  在 OpenCode 中接入任意 OpenAI 兼容（或自定义协议）的模型端点——例如 AMD
  Radeon AI、ModelScope、OpenRouter、自建 vLLM / Ollama / LM Studio、聚合网关——
  通过编辑用户级或项目级 `opencode.json(c)` 的 `providers` 配置，让模型出现在
  `/models` 列表并可被会话选用。同时维护一份供 `script-draft-forge` 六档位调度器
  直调的自定义端点清单（默认 `~/.config/opencode/models.json`）。
  当用户说「给 OpenCode 加个模型」「接入第三方 / 自建模型」「把某个 API 端点
  加进模型列表」「换聚合网关 / 换 key」「六档位端点没配齐」时使用本技能。
---

# OpenCode 自定义模型接入

## 0. 先分清两条路径（最容易搞混的地方）

| | A. 会话模型（OpenCode 原生） | B. 直调端点清单（脚本专用） |
|---|---|---|
| 用途 | 让模型出现在 `/models`，供会话 / `subagent` 选用 | 供 `script-draft-forge` 的 `engine_dispatch.py --live` 按档位逐条直调 |
| 配置文件 | `~/.config/opencode/opencode.json(c)`（全局）或项目 `opencode.json(c)` / `.opencode/opencode.json(c)` | `~/.config/opencode/models.json`，可用环境变量 `OPENCODE_SKILL_MODELS` 覆盖 |
| 谁在读 | OpenCode 服务（配置 watcher 自动重载） | 只有 `engine_dispatch.py` 读，**OpenCode 不读这个文件** |
| 生效方式 | 保存即自动重载，无需重启；必要时 `/reload` | 下次运行 `plan` / `run` 时读取 |
| 计费 | 按所选模型的用量计费 | 仅 `--live` 才调用、才计费；默认 dry-run 零调用 |

> 二者互不替代：想「在对话框里换模型」走 A；想「六档位自动混跑」走 B（或用
> `script-draft-forge` 的 `rules/opencode-adapter.md` OC-01/OC-03，直接基于
> `tools.opencode.models` 实时探测 + `subagent` 派发，连 B 都可以不配）。

## 1. A · 配置 OpenAI 兼容 provider

编辑 `~/.config/opencode/opencode.jsonc`（JSON / JSONC 均可）：

```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  "providers": {
    "mygateway": {
      "name": "我的聚合网关",
      "env": ["MY_GATEWAY_API_KEY"],
      "package": "@opencode/ai/providers/openai-compatible",
      "settings": {
        "baseURL": "https://gateway.example.com/v1"
      },
      "models": {
        "deepseek-v4-flash": {
          "name": "DeepSeek V4 Flash（网关）",
          "modelID": "DeepSeek-V4-Flash"
        }
      }
    }
  }
}
```

字段口径（以 `opencode.json` schema 为准）：

- `providers` 的键 = **provider ID**，模型引用写作 `providerID/modelID`，例如 `mygateway/deepseek-v4-flash`。
- `models` 的键 = OpenCode 侧的模型 ID；`modelID` 才是发给上游端点的 `model` 字符串。
  **别把两者写反**——这是接入失败最常见的原因。
- `package`：`@opencode/ai/providers/openai-compatible` 用于 OpenAI 兼容协议；
  官方 Anthropic API 不是 OpenAI 兼容格式，需走兼容网关或换用 anthropic 系 runtime。
- `env` 列出可为该 provider 提供凭据的环境变量名；也可用 `{env:VAR}` / `{file:path}` 变量替换写进
  `settings.apiKey` 等字段。**密钥不要明文写进会被提交/分发的配置文件**。
- `headers` / `body` 可给该 provider（或单个 model / variant）追加请求头与请求体字段。
- 想设默认模型：顶层 `"model": "mygateway/deepseek-v4-flash"`。

连接与选择：`/connect` 录入凭据 → `/models` 选模型；或在配置里写全后直接 `/models` 查看。
配置保存后 OpenCode 自动重载（不要让用户去重启客户端），必要时用 `/reload` 强制刷新。

## 2. B · 自定义端点清单（engine_dispatch.py 专用）

默认路径 `~/.config/opencode/models.json`，是一个数组：

```json
[
  {
    "id": "deepseek-v4.1-flash",
    "name": "骨架档 · DeepSeek V4.1 Flash",
    "vendor": "Custom",
    "url": "https://gateway.example.com/v1",
    "apiKey": "YOUR_KEY",
    "supportsToolCall": true,
    "supportsImages": false,
    "supportsReasoning": false,
    "useCustomProtocol": false
  }
]
```

- `id` 必须**严格等于** API 请求体里的 `model` 字符串；先拉端点 `GET /v1/models` 拿准确 ID，禁止凭印象写。
- `url` 只写 base（不要带 `/chat/completions`），脚本会自动拼接。
- `apiKey` 是 Bearer token，只在内存中使用；`engine_dispatch.py` 保证不写进任何产物/日志/报告。
- 需要配齐 `script-draft-forge` MR-07 的六个档位 id：
  `deepseek-v4.1-flash`（骨架）、`claude-opus-5-5`（定调/回顾）、`kimi-k3.1-pro`（台词）、
  `glm-5.3-flash`（批量）、`hy4`（挑稿）。缺档时 `plan` 直接停机，不静默降级。
- 临时换一套清单：`OPENCODE_SKILL_MODELS=<路径> python scripts/engine_dispatch.py plan ...`

## 3. 操作顺序

1. 先确认用户要的是 A（换会话模型）还是 B（六档位直调）；两者可以都做。
2. **A**：读现有 `opencode.json(c)`，保留无关配置，只追加/修改 `providers` 段；
   `$schema` 保持不变。不要覆盖用户已有设置。
3. **B**：读 `~/.config/opencode/models.json`；不存在则新建 `[]` 再追加，**不覆盖已有条目**。
   校验 JSON 合法性，并确认 `id` 与上游 `/v1/models` 一致。
4. **连通性验证**（在让模型进 GUI 之前）：
   ```bash
   curl -s 'https://gateway.example.com/v1/chat/completions' \
     -H "Authorization: Bearer $MY_GATEWAY_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{"model":"DeepSeek-V4-Flash","messages":[{"role":"user","content":"hi"}]}'
   ```
   要求返回 200 且有中文正文；推理模型若 `max_tokens` 给太小会只返回 `reasoning_content`、
   `content` 为空——那是预算问题不是端点故障（见 `script-draft-forge` MR-07）。
5. **A 验证**：`/models` 能看到新条目；必要时 `/reload`。
   **B 验证**：`python scripts/engine_dispatch.py plan --project <剧本目录> --episodes 1-2`
   能解析出六个 id（这一步仍是演练，零调用）。

## 4. 已知坑

- **不要把 `models.json` 当成 OpenCode 配置**：它是本技能包为脚本自定义的端点清单，
  OpenCode 服务不会读取，改它不会让 `/models` 多出任何模型。
- **不要让用户重启客户端**：配置 watcher 自动重载；只有服务端卡住才用 `opencode service restart`。
- 聚合网关偶发 `404 Invalid URL (GET /v1/chat/completions)` 与读超时属瞬时故障，重试即可恢复。
- 模型列表不显示用量/预算；如需成本统计要在调用层或 MCP 侧另行实现，不要在 `providers` 里找这个开关。
- `Anthropic 官方 API` ≠ OpenAI 兼容协议；`{env:}` 未设置时变量替换为空串，会表现为鉴权失败。
- 换 key / 换聚合商只改 `settings.baseURL` 与凭据（或清单里的 `url` + `apiKey`），
  不动 `script-draft-forge` 的 MR-03 分工表；改动前备份原配置。

## 5. 与编剧技能包的关系

- `script-draft-forge` 的 `rules/model-routing.md` MR-07 / MR-08 依赖清单 B。
- 但 OpenCode 宿主下**优先**走 `rules/opencode-adapter.md` 的 OC-01（`tools.opencode.models`
  实时探测可用模型）+ OC-03（`subagent` 显式指定模型派发）；静态六档位表只是历史推荐快照，
  端点清单是可选的「脱离会话直调」通道。
- `script-final-pipeline` 的 MR-06「接入外部端点」同样指向本技能。
