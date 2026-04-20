"""V3 工作流状态：指标 → 语义计划 → 编译 SQL → 执行。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class SemanticWorkflowState:
    """Question → Intent → Metrics → QueryPlan → SQLCompiler → Doris → Insight → Report"""

    user_question: str = ""
    intent: Optional[Dict[str, Any]] = None
    metric_bundle: Optional[Dict[str, Any]] = None
    query_plan: Optional[Dict[str, Any]] = None
    sql_compiler: Optional[Dict[str, Any]] = None
    query_execution: Optional[Dict[str, Any]] = None
    insight: Optional[Dict[str, Any]] = None
    report: Optional[Dict[str, Any]] = None
    cache_hits: Dict[str, bool] = field(default_factory=dict)

    def to_report_payload(self) -> Dict[str, Any]:
        return {
            "user_question": self.user_question,
            "understanding": self.intent,
            "metric_bundle": self.metric_bundle,
            "query_plan": self.query_plan,
            "sql_compiler": self.sql_compiler,
            "query_execution": self.query_execution,
            "insight": self.insight,
        }
