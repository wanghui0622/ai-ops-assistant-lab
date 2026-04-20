"""
运营分析工作流（OWL 编排思想：显式阶段 + 可观测 trace）。

说明：官方 OWL 仓库中的 `camel.societies.Workforce` 适合动态任务分解；
本 MVP 采用「固定 Pipeline」编排，便于对接 Doris/SQL 顺序执行，后续可将各阶段
注册为 Workforce 中的 worker，无需改动 Agent 接口。
"""

from __future__ import annotations

from typing import Any, Dict, List

from camel.tasks.task import Task, TaskState

from agents import analysis_agent
from agents import query_understanding_agent
from agents import report_agent
from agents import sql_generation_agent
from tools import sql_tool


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
        self.trace: Dict[str, Any] = {}

    def run(self, user_question: str) -> Dict[str, Any]:
        task = Task(content=user_question)
        task.set_state(TaskState.RUNNING)

        self.trace = {}
        context: Dict[str, Any] = {"user_question": user_question}

        # 1. Query Understanding
        understanding = query_understanding_agent.run(
            {"user_question": user_question}
        )
        self.trace["query_understanding"] = understanding
        context["understanding"] = understanding

        # 2. SQL Generation
        sql_bundle = sql_generation_agent.run(
            {"understanding": understanding, "user_question": user_question}
        )
        self.trace["sql_generation"] = sql_bundle
        context["sql_bundle"] = sql_bundle

        # 3. Doris Tool（Mock）
        query_tool_result = sql_tool.run(
            {"sql": sql_bundle["sql"], "mock_plan": sql_bundle["mock_plan"]}
        )
        self.trace["sql_execution"] = query_tool_result
        context["query_tool_result"] = query_tool_result

        # 4. Analysis
        analysis = analysis_agent.run(context)
        self.trace["analysis"] = analysis
        context["analysis"] = analysis

        # 5. Report
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