# AI 运营助手 V3（语义层 + 指标体系）

**指标驱动** 的数据分析链路：LLM 只负责选指标与理解意图，**SQL 由 `sql_compiler` 根据 `metrics/registry.yaml` 模板拼装**，从架构上避免模型直连生成可执行 SQL。

## 架构

```
用户问题
   │
   ▼
Query Understanding ──► intent
   │
   ▼
Metric Agent ──► metric_bundle（白名单指标 + 维度 + 时间范围）
   │
   ▼
Semantic Planner ──► query_plan（逻辑查询计划）
   │                    ▲
   │              term_map.yaml（业务术语映射）
   ▼
SQL Compiler ──► 确定性 SQL（仅使用 registry 模板）
   │
   ▼
SQL Execution + Doris/Mock ──► 数据集
   │
   ▼
Insight Agent ──► 洞察
   │
   ▼
Report Agent ──► Markdown 报告
```

核心原则：**禁止 LLM 直连 SQL**；所有可执行语句来自注册表中的 `sql_template` 与编译器规则。

## 技术栈

| 层级 | 选型 |
|------|------|
| 语言 | Python 3.10+ |
| Agent 框架 | Camel-AI（Intent / Metric / Insight / Report） |
| 语义层 | `semantic_layer/semantic_planner.py`、`sql_compiler.py` |
| 指标 | `metrics/registry.yaml` |
| 术语 | `semantic_layer/term_map.yaml` |
| 编排 | `workflow/owl_workflow.py`（`OWLSemanticWorkflow`） |
| 数据 | Doris / Mock（同 V2） |

## 快速启动

```bash
cd ai-ops-assistant-v3
python3 -m pip install -r requirements.txt

python3 main.py
python3 main.py "最近七天活跃度与留存怎么样？"
python3 main.py --json
```

## 环境变量

复制 `.env.example` 为 `.env`（与 V2 类似）：

| 变量 | 说明 |
|------|------|
| `OPENAI_API_KEY` / `USE_MOCK_AGENTS` | LLM 配置 |
| `DORIS_*` | Doris 连接；留空走 Mock |
| `WORKFLOW_CACHE` | 阶段缓存 |

## 指标注册表示例

`metrics/registry.yaml` 定义如 `active_user`、`retention_rate`、`order_amount` 等指标，每项包含：

- `sql_template`：编译器使用的表达式片段
- `source_table` / `dimensions` / `grain`：物理表与粒度

扩展新指标时 **只改 YAML + 编译规则**，无需改动 Agent 提示词中的 SQL 示例。

## 典型流程

1. 解析用户问题 → `intent`
2. Metric Agent 从 registry 白名单中选择指标组合
3. Semantic Planner 生成 `query_plan`（含过滤、聚合、时间窗口）
4. SQL Compiler 输出可审计的 SQL
5. 执行查询 → Insight → Report

## 目录

| 路径 | 说明 |
|------|------|
| `metrics/registry.yaml` | 指标白名单与 SQL 模板 |
| `semantic_layer/` | Planner、Compiler、术语映射 |
| `agents/metric_agent.py` | 指标选择 Agent |
| `workflow/owl_workflow.py` | `OWLSemanticWorkflow` |
| `agents/` | 其他 Camel Agent |
| `mock_data/` | 演示数据 |

## 与后续版本的关系

V3 的 `metrics/registry.yaml` 与语义层被 **V4 复用**（`backend/metrics/`、`compile-and-query` Skill）。V4 在此基础上增加 Runtime、Hook、HITL 与 React 三栏 UI。详见 [根 README](../README.md)。
