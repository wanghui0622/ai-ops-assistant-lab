"""
OWL Workflow V2：多阶段、状态传递、StageCache。

【学习】相对 V1 的变化：
  1. SQL 拆为 Planner → Optimizer → Execution（三个 Agent）
  2. SchemaRetriever 从 catalog.yaml 注入表结构，约束 LLM
  3. OpsWorkflowState 集中保存各阶段产物；StageCache.memo 可缓存 intent/sql_plan 等

【学习】阅读顺序：本文件 → workflow/state.py → tools/schema_retriever.py
       → agents/sql_planner_agent.py

可与 camel-ai/owl 的 Workforce 组合；此处为确定性 DAG + 缓存层。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from camel.tasks.task import Task, TaskState

from agents import (
    insight_agent,
    query_understanding_agent,
    report_agent,
    sql_execution_agent,
    sql_optimizer_agent,
    sql_planner_agent,
)
from workflow.cache import StageCache, stable_hash
from workflow.state import OpsWorkflowState
from tools.schema_retriever import SchemaRetriever, infer_tables_from_intent

PIPELINE_STAGES: List[str] = [
    "user_question",
    "intent",
    "schema_context",
    "sql_plan",
    "optimized_sql",
    "query_execution",
    "insight",
    "report",
]


class OWLWorkflow:
    """结构化状态流转 + 中间结果缓存。"""

    def __init__(
        self,
        schema_retriever: Optional[SchemaRetriever] = None,
        cache: Optional[StageCache] = None,
    ) -> None:
        self.schema_retriever = schema_retriever or SchemaRetriever()
        self.cache = cache or StageCache()

    def run(self, user_question: str) -> Dict[str, Any]:
        state = OpsWorkflowState(user_question=user_question.strip())
        task = Task(content=state.user_question)
        task.set_state(TaskState.RUNNING)

        # -------- Intent（理解问题；缓存键仅含 question）--------
        intent, hit_i = self.cache.memo(
            "intent",
            {"question": state.user_question},
            lambda: query_understanding_agent.run({"user_question": state.user_question}),
        )
        state.intent = intent
        state.cache_hits["intent"] = hit_i

        # 【学习】Schema 不进缓存键的独立阶段：由 intent 推断表名再拼 Prompt 文本
        tables = infer_tables_from_intent(intent)
        state.candidate_tables = tables
        state.schema_context = self.schema_retriever.build_prompt_context(tables)

        # -------- SQL Plan（逻辑计划，尚未是终稿 SQL）--------
        plan, hit_p = self.cache.memo(
            "sql_plan",
            {
                "question": state.user_question,
                "intent_sig": stable_hash(intent),
                "schema_sig": stable_hash(state.schema_context),
            },
            lambda: sql_planner_agent.run(
                {
                    "user_question": state.user_question,
                    "understanding": intent,
                    "schema_context": state.schema_context,
                    "candidate_tables": tables,
                }
            ),
        )
        state.sql_plan = plan
        state.cache_hits["sql_plan"] = hit_p

        # -------- Optimizer --------
        opt, hit_o = self.cache.memo(
            "sql_optimizer",
            {"plan_sig": stable_hash(plan), "schema_sig": stable_hash(state.schema_context)},
            lambda: sql_optimizer_agent.run(
                {
                    "sql_plan": plan,
                    "understanding": intent,
                    "schema_context": state.schema_context,
                }
            ),
        )
        state.sql_optimizer = opt
        state.cache_hits["sql_optimizer"] = hit_o

        opt_sql = (opt.get("optimized_sql") or "").strip()

        # -------- Execution --------
        qe, hit_e = self.cache.memo(
            "query_execution",
            {"sql_sig": stable_hash(opt_sql)},
            lambda: sql_execution_agent.run(
                {
                    "optimized_sql": opt_sql,
                    "sql_optimizer": opt,
                    "sql_plan": plan,
                    "run_explain": True,
                }
            ),
        )
        state.query_execution = qe
        state.cache_hits["query_execution"] = hit_e

        # -------- Insight --------
        insight_payload = {
            "user_question": state.user_question,
            "understanding": intent,
            "sql_plan": plan,
            "sql_optimizer": opt,
            "query_execution": qe,
        }

        insight, hit_in = self.cache.memo(
            "insight",
            {
                "question": state.user_question,
                "rows_sig": stable_hash(qe.get("rows")),
                "ok": qe.get("ok"),
            },
            lambda: insight_agent.run(insight_payload),
        )
        state.insight = insight
        state.cache_hits["insight"] = hit_in

        # -------- Report --------
        report_bundle, hit_r = self.cache.memo(
            "report",
            {
                "question": state.user_question,
                "insight_sig": stable_hash(insight),
            },
            lambda: report_agent.run(state.to_report_payload()),
        )
        state.report = report_bundle
        state.cache_hits["report"] = hit_r

        markdown = (report_bundle or {}).get("markdown", "")
        task.update_result(markdown)

        return {
            "workflow_version": "v2",
            "pipeline_stages": PIPELINE_STAGES,
            "task_state": task.state.value,
            "markdown_report": markdown,
            "state": _state_public_dict(state),
            "cache_hits": dict(state.cache_hits),
        }


def _state_public_dict(state: OpsWorkflowState) -> Dict[str, Any]:
    return {
        "user_question": state.user_question,
        "intent": state.intent,
        "candidate_tables": state.candidate_tables,
        "schema_context_preview": state.schema_context[:1200]
        + ("..." if len(state.schema_context) > 1200 else ""),
        "sql_plan": state.sql_plan,
        "sql_optimizer": state.sql_optimizer,
        "query_execution": state.query_execution,
        "insight": state.insight,
        "report": {"format": (state.report or {}).get("format"), "length": len((state.report or {}).get("markdown", ""))},
    }


def run_pipeline(question: str) -> Dict[str, Any]:
    return OWLWorkflow().run(question)
