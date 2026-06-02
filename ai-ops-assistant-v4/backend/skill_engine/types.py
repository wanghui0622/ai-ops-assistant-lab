from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

@dataclass
class SkillContext:
    session_id: str
    user_question: str
    data: Dict[str, Any] = field(default_factory=dict)
    model_adapter: Any = None
    settings: Any = None

@dataclass
class SkillResult:
    ok: bool
    outputs: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
