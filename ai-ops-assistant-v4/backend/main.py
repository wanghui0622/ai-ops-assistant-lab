from __future__ import annotations
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import build_router
from runtime.agent_runtime import AgentRuntime

runtime = AgentRuntime()
app = FastAPI(title="AI Ops Assistant V4", version="4.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(build_router(runtime))

@app.get("/health")
def health():
    return {"status": "ok", "model_provider": runtime.model.provider_name}
