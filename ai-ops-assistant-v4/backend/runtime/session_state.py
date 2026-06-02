from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid

class SessionPhase(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    AWAITING_METRIC_REVIEW = "awaiting_metric_review"
    AWAITING_REPORT_CONFIRM = "awaiting_report_confirm"
    COMPLETED = "completed"
    ERROR = "error"
    CANCELLED = "cancelled"

@dataclass
class ChatMessage:
    role: str
    content: str
    actions: Optional[List[Dict[str, Any]]] = None

@dataclass
class PendingAction:
    action_type: str
    prompt: str
    actions: List[str]
    payload: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SessionState:
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    phase: SessionPhase = SessionPhase.IDLE
    user_question: str = ""
    workflow_name: str = "ops-analysis"
    skill_index: int = 0
    data: Dict[str, Any] = field(default_factory=dict)
    messages: List[ChatMessage] = field(default_factory=list)
    pending_action: Optional[PendingAction] = None
    markdown_report: str = ""
    error: Optional[str] = None
    def to_dict(self):
        return {
            "session_id": self.session_id,
            "phase": self.phase.value,
            "user_question": self.user_question,
            "workflow_name": self.workflow_name,
            "skill_index": self.skill_index,
            "data": self.data,
            "messages": [{"role": m.role, "content": m.content, "actions": m.actions} for m in self.messages],
            "pending_action": None if not self.pending_action else {"action_type": self.pending_action.action_type, "prompt": self.pending_action.prompt, "actions": self.pending_action.actions, "payload": self.pending_action.payload},
            "markdown_report": self.markdown_report,
            "error": self.error,
        }
