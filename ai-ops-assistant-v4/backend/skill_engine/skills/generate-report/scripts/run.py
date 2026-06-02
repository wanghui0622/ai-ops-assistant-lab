from __future__ import annotations

import json
from typing import Any, Dict

from report_builder import build_business_report


def generate(ctx, inp):
    payload = {
        k: inp.get(k) or ctx.data.get(k)
        for k in (
            "user_question",
            "understanding",
            "metric_bundle",
            "query_plan",
            "sql_compiler",
            "query_execution",
            "insight",
        )
    }
    if ctx.settings.use_mock_model:
        report = build_business_report(payload)
    else:
        system = (ctx.settings.prompts_dir / "report_prompt.txt").read_text(encoding="utf-8")
        from model_adapter.types import ChatMessage

        llm_payload = {
            "user_question": payload.get("user_question"),
            "understanding": payload.get("understanding"),
            "metric_bundle": payload.get("metric_bundle"),
            "rows": (payload.get("query_execution") or {}).get("rows") or [],
            "insight": payload.get("insight"),
        }
        text = json.dumps(llm_payload, ensure_ascii=False, indent=2)
        resp = ctx.model_adapter.chat(
            [ChatMessage(role="system", content=system), ChatMessage(role="user", content=text)]
        )
        md = resp.content.strip()
        structured = build_business_report(payload)
        report = {
            "markdown": md,
            "format": "markdown",
            "charts": structured.get("charts") or [],
            "metric_cards": structured.get("metric_cards") or [],
        }
    ctx.data["markdown_report"] = report["markdown"]
    ctx.data["report"] = report
    return {"markdown_report": report["markdown"], "report": report}
