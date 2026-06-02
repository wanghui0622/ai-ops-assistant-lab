from __future__ import annotations
import asyncio
import json
from typing import AsyncGenerator
from fastapi import APIRouter, HTTPException, Request
from sse_starlette.sse import EventSourceResponse
from api.schemas import ActionRequest, CreateSessionResponse, MessageRequest, SessionResponse
from config import get_settings
from metrics.loader import get_metric_registry

def build_router(runtime) -> APIRouter:
    router = APIRouter(prefix="/api")
    @router.post("/sessions", response_model=CreateSessionResponse)
    async def create_session():
        s = await runtime.create_session()
        return CreateSessionResponse(session_id=s.session_id, phase=s.phase.value)
    @router.get("/sessions/{session_id}", response_model=SessionResponse)
    async def get_session(session_id: str):
        s = runtime.sessions.get(session_id)
        if not s: raise HTTPException(404, "session not found")
        d = s.to_dict()
        return SessionResponse(**d)
    @router.post("/sessions/{session_id}/messages", response_model=SessionResponse)
    async def post_message(session_id: str, body: MessageRequest):
        try:
            s = await runtime.handle_message(session_id, body.content)
        except KeyError:
            raise HTTPException(404, "session not found")
        except Exception as e:
            s = runtime.sessions.get(session_id)
            if s: s.phase = s.phase.ERROR if hasattr(s.phase, 'ERROR') else s.phase
            raise HTTPException(500, str(e))
        return SessionResponse(**s.to_dict())
    @router.post("/sessions/{session_id}/actions", response_model=SessionResponse)
    async def post_action(session_id: str, body: ActionRequest):
        try:
            s = await runtime.handle_action(session_id, body.action, body.payload)
        except KeyError:
            raise HTTPException(404, "session not found")
        except Exception as e:
            raise HTTPException(500, str(e))
        return SessionResponse(**s.to_dict())
    @router.get("/sessions/{session_id}/stream")
    async def stream(session_id: str, request: Request):
        q = runtime.hooks.subscribe(session_id)
        async def gen() -> AsyncGenerator[dict, None]:
            try:
                while True:
                    if await request.is_disconnected(): break
                    try:
                        event = await asyncio.wait_for(q.get(), timeout=15.0)
                        yield {"event": event.type, "data": json.dumps(event.to_dict(), ensure_ascii=False)}
                    except asyncio.TimeoutError:
                        yield {"event": "ping", "data": "{}"}
            finally:
                runtime.hooks.unsubscribe(session_id, q)
        return EventSourceResponse(gen())
    @router.get("/metrics")
    async def list_metrics():
        reg = get_metric_registry()
        return {"metrics": [{"id": mid, "name": mid, "description": (reg.get(mid) or {}).get("description", ""), "source_table": (reg.get(mid) or {}).get("source_table", "")} for mid in reg.list_ids()]}
    @router.get("/skills")
    async def list_skills():
        return {"skills": runtime.skills.list_skills()}
    return router
