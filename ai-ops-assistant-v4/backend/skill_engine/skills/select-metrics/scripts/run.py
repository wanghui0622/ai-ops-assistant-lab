from __future__ import annotations
import re
from typing import Any, Dict, List
from metrics.loader import get_metric_registry
from semantic_layer.term_mapping import get_term_mapper

def load_registry(ctx, inp):
    reg = get_metric_registry()
    return {"registry_ids": reg.list_ids(), "registry_summary": reg.as_prompt_summary()}

def select_metrics(ctx, inp):
    question = inp.get("user_question", ctx.user_question)
    understanding = inp.get("understanding") or inp.get("intent") or {}
    mapper = get_term_mapper()
    term_hits = mapper.lookup_terms(question)
    if ctx.settings.use_mock_model:
        bundle = _mock(question, understanding, term_hits)
    else:
        reg = get_metric_registry()
        system = (ctx.settings.prompts_dir / "metric_agent_prompt.txt").read_text(encoding="utf-8")
        data = ctx.model_adapter.chat_json(system, {"user_question": question, "understanding": understanding, "term_candidates": term_hits, "allowed_metric_whitelist": reg.list_ids(), "metric_catalog_summary": reg.as_prompt_summary()})
        bundle = _normalize(data, term_hits)
    ctx.data["metric_bundle"] = bundle
    return {"metric_bundle": bundle}

def _normalize(data, term_hits):
    return {"metric_ids": list(data.get("metric_ids") or []), "dimensions": list(data.get("dimensions") or ["dt"]), "time_range_days": int(data.get("time_range_days",7)), "confidence": float(data.get("confidence",0.8)), "reasoning": data.get("reasoning",""), "matched_terms": term_hits.get("matched_terms") or [], "registry_version": "registry.yaml"}

def _mock(question, understanding, term_hits):
    intent = understanding.get("intent","")
    days = int(understanding.get("time_range_days",7))
    m = re.search(r"(\d+)\s*天", question)
    if m: days = int(m.group(1))
    candidates = list(term_hits.get("candidate_metric_ids") or [])
    if intent == "revenue_analysis": mids = ["order_amount","paying_user"]
    elif intent == "churn_analysis": mids = ["active_user","retention_rate"]
    elif any(k in question for k in ("活跃","dau","活跃度")): mids = ["active_user"]
    elif candidates: mids = candidates[:3]
    else: mids = ["active_user"]
    reg = get_metric_registry()
    ordered = [x for x in dict.fromkeys(mids) if reg.get(x)] or ["active_user"]
    return {"metric_ids": ordered, "dimensions": ["dt"], "time_range_days": days, "confidence": 0.92, "reasoning": "Mock：意图 + 术语映射驱动指标选择", "matched_terms": term_hits.get("matched_terms") or [], "registry_version": "registry.yaml"}
