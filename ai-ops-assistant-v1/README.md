# AI 运营助手 V1（MVP）

最小可行版本：用 **固定 Pipeline** 跑通「自然语言 → SQL → 查询 → 分析 → Markdown 报告」全链路。数据层默认 **内存 Mock**，LLM 默认 **Mock Agent**，无需联网即可演示。

## 架构

```
用户问题
   │
   ▼
Query Understanding Agent ──► 意图 / 时间范围 / 关注指标
   │
   ▼
SQL Generation Agent ──► SQL + mock_plan（演示用执行计划）
   │
   ▼
SQL Tool（Doris Client / Mock）──► 行集结果
   │
   ▼
Analysis Agent ──► 结构化洞察
   │
   ▼
Report Agent ──► Markdown 分析报告
```

编排采用 **OWL 编排思想**（显式阶段 + 可观测 `trace`），实现为确定性 `OpsWorkflow`，便于后续替换为 Camel OWL `Workforce` 动态编排。

## 技术栈

| 层级 | 选型 |
|------|------|
| 语言 | Python 3.10+（3.9 亦可） |
| Agent 框架 | [Camel-AI](https://github.com/camel-ai/camel) `ChatAgent` |
| 编排 | `workflow/ops_workflow.py` 固定 Pipeline |
| 数据 | `tools/doris_client.py`（未配置 Doris 时走 Mock） |
| 配置 | `pydantic` + `python-dotenv` |

## 快速启动

```bash
cd ai-ops-assistant-v1
python3 -m pip install -r requirements.txt

# 默认演示问题
python3 main.py

# 自定义问题
python3 main.py "最近7天用户流失情况如何？"

# 输出完整 trace（JSON，不含长报告正文）
python3 main.py --json
```

## 环境变量

复制 `.env.example` 为 `.env`：

| 变量 | 说明 |
|------|------|
| `OPENAI_API_KEY` | 接入真实 LLM；留空则 `USE_MOCK_AGENTS` 生效 |
| `USE_MOCK_AGENTS=1` | 强制 Mock，离线演示 |
| `CAMEL_MODEL_NAME` | 默认 `gpt-4o-mini` |
| `CAMEL_TEMPERATURE` | 默认 `0.2` |

## 典型流程

1. 输入运营问题（如「最近 7 天用户流失情况如何？」）
2. Query Agent 解析意图与时间窗口
3. SQL Agent 生成查询语句（Mock 模式下带 `mock_plan` 供 Tool 路由）
4. Mock Doris 返回 `game_daily_metrics` / `order_daily_summary` 数据
5. Analysis + Report Agent 输出 Markdown 报告

## Mock 数据

`mock_data/` 提供 **14 个交易日**（`2026-04-07`～`2026-04-20`）的 `game_daily_metrics` 与 `order_daily_summary`，支持「最近 7 天」「最近 14 天」等问法。

```bash
python3 -m mock_data.verify
```

## 目录

| 路径 | 说明 |
|------|------|
| `agents/` | Query / SQL / Analysis / Report 四类 Agent |
| `workflow/ops_workflow.py` | 五阶段 Pipeline + trace |
| `tools/` | `sql_tool`、`doris_client` |
| `mock_data/` | 演示数据集与自检 |
| `prompts/` | 各 Agent 提示词模板 |

## 与后续版本的关系

V1 验证 **端到端闭环**；V2 起引入 Schema 目录与 SQL 三阶段；V3 用指标注册表替代 LLM 直出 SQL；V4 在此基础上增加 Agent Runtime、Skill/Hook 与 Web UI。详见仓库根目录 [README](../README.md)。
