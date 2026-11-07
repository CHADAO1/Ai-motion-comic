# 情绪转折点沉淀库（emotion-turns）

> 情绪热力图模块（EH-03/05/06）的沉淀库。机器可读的唯一事实源 = `reference/emotion-turns.jsonl`（每行一个 JSON 对象）。
> 本文件是**库说明与索引**；实际条目与统计由 `scripts/emotion_library.py` 管理。
> 归档 2026-11-02 创建，2026-11-04 结构化落地。

## 0. 诚实边界（先说清楚）

SaaS 竞品的「3000+ 爆款情绪转折点」来自真实项目数据积累，是数据壁垒，不是格式问题。
**本库不伪造 3000 条，也不把方法论派生条目冒充实测数据。** 当前规模以 `stats` 输出为准：

```bash
python scripts/emotion_library.py stats     # 当前条数 + 来源构成 + 距 3000 差多少
python scripts/emotion_library.py verify   # 字段/编号/强度差/去重校验
```

增长路径只有两条，都是真实数据：
1. 每轮闸门A **过关版本**的转折点 `append` 入库；
2. 历史项目导出的 JSONL / CSV 走 `import` 批量去重入库。

规模随项目累积，不靠一次性批量造数。派生条目一律标「方法论派生」，错误案例一律标「实测错误案例」，
且 `query`（EH-04 生成注入）自动排除错误案例，避免把翻车样例学进新稿。

## 1. 字段规范（EH-05）

| 字段 | 含义 | 约束 |
|---|---|---|
| `id` | ET-0001 起，脚本自动编号 | 唯一、连续 |
| `genre` | 题材 / 通用维度 | 必填 |
| `scene` | 场次或位置 | 必填 |
| `trigger` | 触发事件 | 必填，与 `transition` 组合做去重键 |
| `transition` | 情绪转换方向（如 愤怒→震惊） | 必填 |
| `intensity_delta` | 强度差 | 整数 -5~5 |
| `source_type` | 来源类型 | 闸门A实测 / 对标拆解 / 方法论派生 / 实测错误案例 / 项目导入 |
| `source` | 可指回的出处（文件 + 位置） | 必填，无出处不得入库 |
| `date` | YYYY-MM-DD | 必填 |
| `note` | 判据/坑/使用条件 | 选填 |

## 2. 准入标准（EH-03 / EH-05）

- **只收闸门A过关版**的转折点；杀稿里的亮点不进库，除非作为「实测错误案例」单独标注。
- 对标剧拆解可入库，标「对标拆解」并写作品名。
- 21 节方法论、ST/HK 规则推导出的条目标「方法论派生」，明确不占实测数。
- 每次改动后 `verify` 必须 PASS；不 PASS 的导入不写盘。

## 3. 常用命令

```bash
# 闸门A 过关后入库
python scripts/emotion_library.py append --json '{"genre":"年代/穿越","scene":"ep004 集尾","trigger":"...","transition":"憋屈→反讽","intensity_delta":4,"source_type":"闸门A实测","source":"outputs/ep004_A_v1.md","date":"2026-11-04","note":"..."}'

# S3 生成注入（EH-04）：取同题材最近 3 条
python scripts/emotion_library.py query --genre 年代/穿越 --limit 3

# 历史项目批量导入（.jsonl / .csv）
python scripts/emotion_library.py import --file 历史转折点.jsonl --source-type 项目导入
```

## 4. 当前种子构成（2026-11-04，20 条）

| 来源类型 | 条数 | 说明 |
|---|---|---|
| 闸门A实测 | 10 | 穿越七零初稿包 + 写作/挑稿极限测试卷的合格卡点与台词 |
| 实测错误案例 | 5 | 情理门事故、钩子疲劳、自造系统条款、凭空落地 |
| 方法论派生 | 4 | ST-01 / HK-05 / HK-06 / CR-17 |
| 对标拆解 | 1 | 同素材换视角（女本位搞钱） |

> 这 20 条全部可指回本地真实文件与方法论章节，不是编的。目标 3000 条，差 2980 条。
