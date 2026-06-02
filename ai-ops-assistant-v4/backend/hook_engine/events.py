from __future__ import annotations
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Literal, Optional

HookType = Literal[
    "session_start", "session_end", "session_message",
    "skill_start", "skill_step", "skill_complete", "skill_error",
    "pre_skill_execute", "post_skill_execute",
    "model_call", "hitl_pause", "user_action", "report_ready", "error",
]

@dataclass
class HookEvent:
    type: HookType
    session_id: str
    summary: str
    skill_name: Optional[str] = None
    step_id: Optional[str] = None
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
