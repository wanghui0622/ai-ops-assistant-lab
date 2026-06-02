# AI 运营助手 V2（Doris + OWL Workflow）

在 V1 闭环之上，接入 **Doris（MySQL 协议，可 Mock）**、**Schema 语义目录**，并将 SQL 生成拆为 **Planner → Optimizer → Execution** 三阶段；编排升级为带 **阶段缓存** 的 OWL Workflow。

## 架构

```
用户问题
   │
   ▼
Query Understanding ──► intent（表候选、指标、时间范围）
   │
   ▼
Schema Retriever ◄── catalog.yaml（表/列/分区语义）
   │
   ▼
SQL Planner Agent ──► 逻辑 SQL 计划
   │
   ▼
SQL Optimizer Agent ──► 优化后 SQL（分区过滤、LIMIT 等）
   │
   ▼
SQL Execution Agent + Doris Client ──► 查询结果
   │
   ▼
Insight Agent ──► 业务洞察
   │
   ▼
Report Agent ──► Markdown 报告
```

`StageCache` 对 intent / sql_plan / optimized_sql 等阶段做 memo，相同签名可复用中间结果，降低重复 LLM 调用成本。

## 技术栈

| 层级 | 选型 |
|------|------|
| 语言 | Python 3.10+ |
| Agent 框架 | Camel-AI |
| 编排 | `workflow/owl_workflow.py` + `workflow/state.py` |
| Schema | `schema/catalog.yaml` + `tools/schema_retriever.py` |
| 存储 | Doris（`pymysql`）或 `mock_data/` 内存 OLAP |
| 配置 | `pydantic`、`PyYAML`、`python-dotenv` |

## 快速启动

```bash
cd ai-ops-assistant-v2
python3 -m pip install -r requirements.txt

python3 main.py
python3 main.py "最近7天 DAU 和 GMV 趋势如何？"
python3 main.py --json
```

## 环境变量

复制 `.env.example` 为 `.env`：

| 变量 | 说明 |
|------|------|
| `OPENAI_API_KEY` / `USE_MOCK_AGENTS` | LLM 与 Mock 开关 |
| `DORIS_HOST` 等 | 未配置时 `DORIS_USE_MOCK` 走内存 Mock |
| `SQL_ROW_LIMIT` | 查询行数上限，默认 5000 |
| `WORKFLOW_CACHE` / `WORKFLOW_CACHE_MAX` | 阶段缓存开关与容量 |

## 典型流程

1. 理解用户问题，产出结构化 `intent`
2. 根据 intent 推断候选表，从 `catalog.yaml` 拼装 Schema 上下文
3. Planner 在 Schema 约束下生成 SQL 计划
4. Optimizer 强化分区谓词、行数限制等
5. 执行查询（Mock 或真实 Doris）
6. Insight + Report 生成可读报告

## 目录

| 路径 | 说明 |
|------|------|
| `agents/` | Query、SQL Planner/Optimizer/Execution、Insight、Report |
| `workflow/` | `owl_workflow.py`、`cache.py`、`state.py` |
| `schema/catalog.yaml` | OLAP 表/列语义目录 |
| `tools/schema_retriever.py` | Schema 上下文构建 |
| `tools/doris_client.py` | Doris / Mock 查询 |
| `mock_data/` | 与 V1 对齐的演示数据 |

## 与后续版本的关系

V2 解决 **「LLM 瞎写 SQL」的第一道闸**：Schema 注入 + 分阶段生成。V3 进一步用 **指标注册表 + SQL Compiler** 禁止 LLM 直接落库 SQL。详见 [根 README](../README.md)。
