"""结构化工作流状态（阶段间显式传递）。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class OpsWorkflowState:
    """User Question → Intent → SQL Plan → Optimized SQL → Query Result → Insight → Report"""

    user_question: str = ""
    intent: Optional[Dict[str, Any]] = None
    schema_context: str = ""
    candidate_tables: List[str] = field(default_factory=list)
    sql_plan: Optional[Dict[str, Any]] = None
    sql_optimizer: Optional[Dict[str, Any]] = None
    query_execution: Optional[Dict[str, Any]] = None
    insight: Optional[Dict[str, Any]] = None
    report: Optional[Dict[str, Any]] = None
    cache_hits: Dict[str, bool] = field(default_factory=dict)

    def to_report_payload(self) -> Dict[str, Any]:
        return {
            "user_question": self.user_question,
            "understanding": self.intent,
            "sql_plan": self.sql_plan,
            "sql_optimizer": self.sql_optimizer,
            "query_execution": self.query_execution,
            "insight": self.insight,
        }
