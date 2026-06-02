from __future__ import annotations
import asyncio
from typing import Any, Callable, Dict, List, Set
from hook_engine.audit import AuditLogger
from hook_engine.events import HookEvent

class HookDispatcher:
    def __init__(self, audit: AuditLogger | None = None) -> None:
        self.audit = audit or AuditLogger()
        self._subscribers: Dict[str, Set[asyncio.Queue]] = {}
        self._handlers: List[Callable[[HookEvent], None]] = []
    def subscribe(self, session_id: str) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue()
        self._subscribers.setdefault(session_id, set()).add(q)
        return q
    def unsubscribe(self, session_id: str, q: asyncio.Queue) -> None:
        subs = self._subscribers.get(session_id)
        if subs: subs.discard(q)
    async def emit(self, event: HookEvent) -> None:
        self.audit.log(event)
        for handler in self._handlers:
            try: handler(event)
            except Exception: pass
        for q in list(self._subscribers.get(event.session_id, set())):
            await q.put(event)
    def on(self, handler: Callable[[HookEvent], None]) -> None:
        self._handlers.append(handler)
