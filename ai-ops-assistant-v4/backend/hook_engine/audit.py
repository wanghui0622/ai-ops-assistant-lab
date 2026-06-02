from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional
from config import Settings, get_settings
from hook_engine.events import HookEvent

class AuditLogger:
    def __init__(self, settings: Optional[Settings] = None) -> None:
        self.settings = settings or get_settings()
        self.sink = self.settings.hook_audit_sink
        self.path = self.settings.audit_log_path
        self.path.parent.mkdir(parents=True, exist_ok=True)
    def log(self, event: HookEvent, extra: Optional[Dict[str, Any]] = None) -> None:
        record = {"logged_at": datetime.now(timezone.utc).isoformat(), **event.to_dict()}
        if extra: record.update(extra)
        line = json.dumps(record, ensure_ascii=False)
        if self.sink == "stdout":
            print(line)
        else:
            with self.path.open("a", encoding="utf-8") as f:
                f.write(line + "\n")
