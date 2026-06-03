"""
运营分析工作流（OWL 编排思想：显式阶段 + 可观测 trace）。

【学习】编排 vs Agent：
  - Agent：单步「输入 dict → 输出 dict」（可能调 LLM）
  - Workflow：按顺序调用多个 Agent/Tool，并把中间结果写入 trace

【学习】Camel Task API（可选，用于与 OWL Workforce 对齐）：
  - Task(content=...)：包装用户问题
  - task.set_state(TaskState.RUNNING)
  - task.update_result(markdown)：结束时写入最终结果

官方 OWL 的 Workforce 适合动态任务分解；本 MVP 用固定 Pipeline，
便于理解数据流。后续可将每个阶段注册为 Worker，接口不变。
"""

from __future__ import annotations

from typing import Any, Dict, List

from camel.tasks.task import Task, TaskState

from agents import analysis_agent
from agents import query_understanding_agent
from agents import report_agent
from agents import sql_generation_agent
from tools import sql_tool

# 【学习】STEP_ORDER 与 trace 键名一致，--json 时可对照阶段顺序阅读
STEP_ORDER: List[str] = [
    "query_understanding",
    "sql_generation",
    "sql_execution",
    "analysis",
    "report",
]


class OpsWorkflow:
    """串联 Query → SQL → Tool → Analysis → Report。"""

    def __init__(self) -> None:
        # 每次 run 会重置；若要做多轮对话可改为实例级累积 trace
        self.trace: Dict[str, Any] = {}

    def run(self, user_question: str) -> Dict[str, Any]:
        task = Task(content=user_question)
        task.set_state(TaskState.RUNNING)

        self.trace = {}
        # context：阶段间传递的「宽」字典；各 Agent 按需取字段
        context: Dict[str, Any] = {"user_question": user_question}

        # ---------- 阶段 1：意图理解 ----------
        understanding = query_understanding_agent.run(
            {"user_question": user_question}
        )
        self.trace["query_understanding"] = understanding
        context["understanding"] = understanding

        # ---------- 阶段 2：生成 SQL（V1 允许 LLM 写 SQL；见 V3 的 Compiler 对比）----------
        sql_bundle = sql_generation_agent.run(
            {"understanding": understanding, "user_question": user_question}
        )
        self.trace["sql_generation"] = sql_bundle
        context["sql_bundle"] = sql_bundle

        # ---------- 阶段 3：执行查询（Tool，非 LLM）----------
        # mock_plan：Mock Doris 不解析 SQL，靠结构化 plan 路由到内存表
        query_tool_result = sql_tool.run(
            {"sql": sql_bundle["sql"], "mock_plan": sql_bundle["mock_plan"]}
        )
        self.trace["sql_execution"] = query_tool_result
        context["query_tool_result"] = query_tool_result

        # ---------- 阶段 4：数据分析 ----------
        analysis = analysis_agent.run(context)
        self.trace["analysis"] = analysis
        context["analysis"] = analysis

        # ---------- 阶段 5：Markdown 报告 ----------
        report_bundle = report_agent.run(context)
        self.trace["report"] = report_bundle

        markdown = report_bundle.get("markdown", "")
        task.update_result(markdown)

        return {
            "task_id": task.id or "root",
            "task_state": task.state.value,
            "task_content": task.content,
            "steps": STEP_ORDER,
            "markdown_report": markdown,
            "trace": self.trace,
        }
