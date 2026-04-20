"""OWL Workflow V3：语义层 + 指标体系编排（禁止 LLM 直连 SQL）。"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from camel.tasks.task import Task, TaskState

from agents import (
    insight_agent,
    metric_agent,
    query_understanding_agent,
    report_agent,
    sql_execution_agent,
)
from semantic_layer.semantic_planner import plan_query
from semantic_layer.sql_compiler import compile_query_plan
from workflow.cache import StageCache, stable_hash
from workflow.state import SemanticWorkflowState

PIPELINE_STAGES: List[str] = [
    "user_question",
    "intent",
    "metric_bundle",
    "query_plan",
    "sql_compiler",
    "query_execution",
    "insight",
    "report",
]


class OWLSemanticWorkflow:
    """指标驱动的多阶段流水线 + 缓存。"""

    def __init__(self, cache: Optional[StageCache] = None) -> None:
        self.cache = cache or StageCache()

    def run(self, user_question: str) -> Dict[str, Any]:
        state = SemanticWorkflowState(user_question=user_question.strip())
        task = Task(content=state.user_question)
        task.set_state(TaskState.RUNNING)

        intent, hi = self.cache.memo(
            "intent_v3",
            {"q": state.user_question},
            lambda: query_understanding_agent.run({"user_question": state.user_question}),
        )
        state.intent = intent
        state.cache_hits["intent"] = hi

        mb, hm = self.cache.memo(
            "metric_bundle_v3",
            {"q": state.user_question, "intent_sig": stable_hash(intent)},
            lambda: metric_agent.run(
                {"user_question": state.user_question, "understanding": intent}
            ),
        )
        state.metric_bundle = mb
        state.cache_hits["metric_bundle"] = hm

        qp, hqp = self.cache.memo(
            "query_plan_v3",
            {"mb_sig": stable_hash(mb), "intent_sig": stable_hash(intent)},
            lambda: plan_query(mb, intent),
        )
        state.query_plan = qp
        state.cache_hits["query_plan"] = hqp

        sc, hsc = self.cache.memo(
            "sql_compiler_v3",
            {"plan_sig": stable_hash(qp)},
            lambda: compile_query_plan(qp),
        )
        state.sql_compiler = sc
        state.cache_hits["sql_compiler"] = hsc

        compiled_sql = (sc or {}).get("sql") or ""

        qe, hq = self.cache.memo(
            "query_execution_v3",
            {"sql_sig": stable_hash(compiled_sql)},
            lambda: sql_execution_agent.run(
                {
                    "compiled_sql": compiled_sql,
                    "sql_compiler": sc,
                    "run_explain": True,
                }
            ),
        )
        state.query_execution = qe
        state.cache_hits["query_execution"] = hq

        insight_payload = state.to_report_payload()
        insight_payload["query_execution"] = qe

        ins, hin = self.cache.memo(
            "insight_v3",
            {
                "q": state.user_question,
                "rows_sig": stable_hash(qe.get("rows")),
            },
            lambda: insight_agent.run(insight_payload),
        )
        state.insight = ins
        state.cache_hits["insight"] = hin

        report_bundle, hr = self.cache.memo(
            "report_v3",
            {"ins_sig": stable_hash(ins)},
            lambda: report_agent.run(state.to_report_payload()),
        )
        state.report = report_bundle
        state.cache_hits["report"] = hr

        markdown = (report_bundle or {}).get("markdown", "")
        task.update_result(markdown)

        return {
            "workflow_version": "v3_semantic",
            "pipeline_stages": PIPELINE_STAGES,
            "task_state": task.state.value,
            "markdown_report": markdown,
            "state": _public_state(state),
            "cache_hits": dict(state.cache_hits),
        }


def _public_state(state: SemanticWorkflowState) -> Dict[str, Any]:
    qp = state.query_plan or {}
    sc = state.sql_compiler or {}
    return {
        "user_question": state.user_question,
        "intent": state.intent,
        "metric_bundle": state.metric_bundle,
        "query_plan_ok": qp.get("ok"),
        "compiled_sql_preview": (sc.get("sql") or "")[:800],
        "sql_compilation_method": sc.get("compilation_method"),
        "query_execution_ok": (state.query_execution or {}).get("ok"),
        "row_count": (state.query_execution or {}).get("row_count"),
        "insight_summary": (state.insight or {}).get("summary"),
    }


def run_semantic_pipeline(question: str) -> Dict[str, Any]:
    return OWLSemanticWorkflow().run(question)
