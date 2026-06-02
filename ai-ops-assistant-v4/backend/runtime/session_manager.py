from __future__ import annotations
from pathlib import Path
from typing import Dict, Optional
import yaml
from runtime.session_state import SessionState

class SessionManager:
    def __init__(self) -> None:
        self._sessions: Dict[str, SessionState] = {}
    def create(self) -> SessionState:
        s = SessionState()
        self._sessions[s.session_id] = s
        return s
    def get(self, session_id: str) -> Optional[SessionState]:
        return self._sessions.get(session_id)
    def load_workflow(self, name: str, workflows_dir: Path) -> dict:
        path = workflows_dir / f"{name.replace('_','-')}.yaml"
        if not path.exists(): path = workflows_dir / f"{name}.yaml"
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
