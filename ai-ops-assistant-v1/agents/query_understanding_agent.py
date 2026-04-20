"""Query Understanding Agent：自然语言 → 结构化意图（Camel ChatAgent + Mock 兜底）。"""

from __future__ import annotations

import re
from typing import Any, Dict

from agents._camel_runtime import load_prompt_file, run_json_agent
from config import get_settings


def run(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    输入:
        user_question: str

    输出:
        intent, intent_label, time_range_days, metrics, entities, confidence,
        raw_question
    """
    settings = get_settings()
    question = payload.get("user_question", "").strip()
    base = {"raw_question": question}
    if settings.use_mock_agents:
        return {**base, **_mock_understand(question)}
    system = load_prompt_file(settings, "query_prompt.txt")
    parsed = run_json_agent(system, {"user_question": question}, settings=settings)
    return {**base, **_normalize_understanding(parsed)}


def _normalize_understanding(data: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "intent": data.get("intent", "adhoc_analysis"),
        "intent_label": data.get("intent_label", "数据分析"),
        "time_range_days": int(data.get("time_range_days", 7)),
        "metrics": data.get("metrics") or [],
        "entities": data.get("entities") or {},
        "confidence": float(data.get("confidence", 0.8)),
    }


def _mock_understand(question: str) -> Dict[str, Any]:
    """无 API Key 时的确定性意图，便于演示闭环。"""
    q = question.lower()
    days = 7
    m = re.search(r"(\d+)\s*天", question)
    if m:
        days = int(m.group(1))
    churn_kw = any(k in question for k in ("流失", "留存", "沉默", "流失率", "退坑"))
    if churn_kw or "churn" in q:
        return {
            "intent": "churn_analysis",
            "intent_label": "用户流失与活跃变化",
            "time_range_days": days,
            "metrics": ["churn_users_7d_window", "dau", "retention_d1_pct"],
            "entities": {},
            "confidence": 0.95,
        }
    rev_kw = any(k in question for k in ("收入", "付费", "商城", "订单", "gmv"))
    if rev_kw:
        return {
            "intent": "revenue_analysis",
            "intent_label": "商城收入与订单",
            "time_range_days": days,
            "metrics": ["gmv_cny", "orders"],
            "entities": {},
            "confidence": 0.9,
        }
    return {
        "intent": "general_trend",
        "intent_label": "通用趋势分析",
        "time_range_days": days,
        "metrics": ["dau", "new_users"],
        "entities": {},
        "confidence": 0.75,
    }
