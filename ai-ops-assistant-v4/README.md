# AI 运营助手 V4（Agent Native）

面向产品化交互的 **Agent Native** 版本：四层后端架构 + **React 三栏 UI**，支持 **HITL（人在回路）**、Hook 审计时间线与多模型适配。业务数据链路继承 V3 的 **指标注册表 + SQL Compiler**。

## 架构

```
                Agent Runtime
              (Session + Workflow + HITL)
                       │
       ┌───────────────┼───────────────┐
       │                               │
    Skill Engine                  Hook Engine
  SKILL.md + workflow.yaml      lifecycle hooks
  scripts/run.py                pre/post + audit (SSE)
       │                               │
       └───────────────┬───────────────┘
                       │
                 Model Adapter
    mock / openai / anthropic / deepseek / gemini
                       │
              metrics + semantic_layer + Doris/Mock
```

### 三栏 UI

| 栏位 | 功能 |
|------|------|
| 左 | 智能对话 + HITL 按钮（确认指标 / 修改指标 / 生成报告） |
| 中 | Markdown 分析报告（含图表组件） |
| 右 | Hook Engine 推理过程时间线（SSE 推送） |

## 技术栈

| 层级 | 选型 |
|------|------|
| 后端 | Python 3.10+、FastAPI、uvicorn、SSE |
| 前端 | React、Vite、TypeScript、Tailwind |
| Agent | 声明式 Skill（非 Camel ChatAgent 流水线） |
| 数据 | V3 指标 registry + Doris Mock |
| 模型 | `model_adapter/` 多 Provider 统一接口 |

## 快速启动

```bash
# Backend
cd backend
python3 -m pip install -r requirements.txt
python3 -m uvicorn main:app --reload --port 8000

# Frontend（新终端）
cd frontend
npm install && npm run dev
```

浏览器打开 http://localhost:5173

## 环境变量

复制 `backend/.env.example` 为 `backend/.env`：

| 变量 | 说明 |
|------|------|
| `MODEL_PROVIDER=mock` | 离线演示（默认） |
| `MODEL_PROVIDER=openai\|anthropic\|deepseek\|gemini` | 接入真实 LLM |
| `DORIS_USE_MOCK=1` | 内存 Mock OLAP |
| `HOOK_AUDIT_SINK=file` | Hook 审计写入 `logs/audit.jsonl` |

## 典型流程

1. 输入「最近七天活跃度怎么样？」
2. Workflow `ops-analysis.yaml` 依次执行 Skill：
   - `understand-intent` → `select-metrics` → `compile-and-query`
3. 右侧 Hooks 面板展示各 Skill 推理步骤（SSE）
4. **HITL 闸门**：数据就绪后暂停，可「继续 / 修改指标」（白名单内调整 registry 指标）
5. 确认后执行 `analyze-insight`，再询问是否生成报告
6. 确认后 `generate-report`，中间面板渲染 Markdown

## Skill 清单

| Skill | 职责 |
|-------|------|
| `understand-intent` | 解析用户意图 |
| `select-metrics` | 从 registry 选择指标 |
| `compile-and-query` | 编译 SQL 并查询 Doris/Mock |
| `analyze-insight` | 数据洞察 |
| `generate-report` | Markdown 报告 |

## 目录

| 路径 | 说明 |
|------|------|
| `backend/runtime/` | Agent Runtime、Session、Workflow YAML |
| `backend/skill_engine/skills/` | 声明式 Skill（SKILL.md + workflow.yaml + scripts） |
| `backend/hook_engine/` | Hooks 分发与 audit |
| `backend/model_adapter/` | 多模型适配 |
| `backend/metrics/` | V3 指标 registry（复用） |
| `backend/api/` | FastAPI 路由与 SSE |
| `frontend/src/` | React 三栏 UI |

## 与前期版本的关系

| 版本 | V4 继承点 |
|------|-----------|
| V1 | 端到端「问 → 数 → 报告」产品形态 |
| V2 | Doris 客户端、Mock 数据 |
| V3 | `metrics/registry.yaml`、语义层编译查询逻辑（封装进 Skill） |

CLI 演示见 V1～V3；**交互式运营台以 V4 为准**。演进全貌见 [根 README](../README.md)。
