"""Metric Agent：自然语言 + 术语映射 → 白名单指标组合（结构化）。"""

from __future__ import annotations

import re
from typing import Any, Dict, List

from agents._camel_runtime import load_prompt_file, run_json_agent
from config import get_settings
from metrics.loader import get_metric_registry
from semantic_layer.term_mapping import get_term_mapper


def run(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    输入:
        user_question: str
        understanding: intent agent 输出

    输出:
        metric_ids, dimensions, time_range_days, confidence,
        reasoning, matched_terms (来自 term_map), registry_version
    """
    settings = get_settings()
    question = payload.get("user_question", "").strip()
    understanding = payload.get("understanding") or {}

    mapper = get_term_mapper()
    term_hits = mapper.lookup_terms(question)

    if settings.use_mock_agents:
        return _mock_select_metrics(question, understanding, term_hits)

    registry = get_metric_registry()
    system = load_prompt_file(settings, "metric_agent_prompt.txt")
    user_payload = {
        "user_question": question,
        "understanding": understanding,
        "term_candidates": term_hits,
        "allowed_metric_whitelist": registry.list_ids(),
        "metric_catalog_summary": registry.as_prompt_summary(),
    }
    data = run_json_agent(system, user_payload, settings=settings)
    return _normalize_bundle(data, term_hits)


def _normalize_bundle(
    data: Dict[str, Any],
    term_hits: Dict[str, Any],
) -> Dict[str, Any]:
    mids = list(data.get("metric_ids") or [])
    dims = list(data.get("dimensions") or ["dt"])
    return {
        "metric_ids": mids,
        "dimensions": dims,
        "time_range_days": int(data.get("time_range_days", 7)),
        "confidence": float(data.get("confidence", 0.8)),
        "reasoning": data.get("reasoning", ""),
        "matched_terms": term_hits.get("matched_terms") or [],
        "candidate_terms_metric_ids": term_hits.get("candidate_metric_ids") or [],
        "sql_limit": int(data.get("sql_limit", 5000)),
        "registry_version": "registry.yaml",
    }


def _mock_select_metrics(
    question: str,
    understanding: Dict[str, Any],
    term_hits: Dict[str, Any],
) -> Dict[str, Any]:
    """确定性规则 + 术语候选（无 LLM）。"""
    intent = understanding.get("intent", "")
    days = int(understanding.get("time_range_days", 7))
    m = re.search(r"(\d+)\s*天", question)
    if m:
        days = int(m.group(1))

    candidates: List[str] = list(term_hits.get("candidate_metric_ids") or [])

    if intent == "revenue_analysis":
        mids = ["order_amount", "paying_user"]
    elif intent == "churn_analysis":
        mids = ["active_user", "retention_rate"]
    elif candidates:
        mids = candidates[:3]
    else:
        mids = ["active_user"]

    # 去重保序
    seen = set()
    ordered: List[str] = []
    for x in mids:
        if x not in seen:
            ordered.append(x)
            seen.add(x)

    reg = get_metric_registry()
    ordered = [x for x in ordered if reg.get(x)]
    if not ordered:
        ordered = ["active_user"]

    return {
        "metric_ids": ordered,
        "dimensions": ["dt"],
        "time_range_days": days,
        "confidence": 0.92 if term_hits.get("matched_terms") else 0.75,
        "reasoning": "Mock：意图 + term_map 候选驱动的指标组合。",
        "matched_terms": term_hits.get("matched_terms") or [],
        "candidate_terms_metric_ids": candidates,
        "sql_limit": 5000,
        "registry_version": "registry.yaml",
    }
