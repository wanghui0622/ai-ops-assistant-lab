from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class CreateSessionResponse(BaseModel):
    session_id: str
    phase: str

class MessageRequest(BaseModel):
    content: str

class ActionRequest(BaseModel):
    action: str
    payload: Dict[str, Any] = Field(default_factory=dict)

class SessionResponse(BaseModel):
    session_id: str
    phase: str
    user_question: str
    messages: List[Dict[str, Any]]
    pending_action: Optional[Dict[str, Any]] = None
    markdown_report: str = ""
    data: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
