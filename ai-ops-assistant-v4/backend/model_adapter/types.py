from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional
Role = Literal["system", "user", "assistant"]

@dataclass
class ChatMessage:
    role: Role
    content: str

@dataclass
class ModelResponse:
    content: str
    provider: str
    model: str
    usage: Dict[str, Any] = field(default_factory=dict)
    raw: Optional[Any] = None

@dataclass
class ModelChunk:
    content: str
    done: bool = False
