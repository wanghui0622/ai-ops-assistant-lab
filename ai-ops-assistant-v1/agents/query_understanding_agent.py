"""
Query Understanding Agent：自然语言 → 结构化意图。

【学习】Agent 模式（本仓库约定）：
  1. 模块暴露 run(payload: dict) -> dict
  2. 先读 get_settings()，Mock 走 _mock_*，否则 load_prompt + run_json_agent
  3. _normalize_* 把 LLM 输出规整为稳定 schema，避免下游 KeyError

对应 LEARNING.md 阶段 2。
"""

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
        # 【学习】Mock 用关键词 + 正则，保证离线演示结果可复现
        return {**base, **_mock_understand(question)}

    system = load_prompt_file(settings, "query_prompt.txt")
    parsed = run_json_agent(system, {"user_question": question}, settings=settings)
    return {**base, **_normalize_understanding(parsed)}


def _normalize_understanding(data: Dict[str, Any]) -> Dict[str, Any]:
    """把 LLM 可能缺失/类型不对的字段兜底为默认值。"""
    return {
        "intent": data.get("intent", "adhoc_analysis"),
        "intent_label": data.get("intent_label", "数据分析"),
        "time_range_days": int(data.get("time_range_days", 7)),
        "metrics": data.get("metrics") or [],
        "entities": data.get("entities") or {},
        "confidence": float(data.get("confidence", 0.8)),
    }


def _mock_understand(question: str) -> Dict[str, Any]:
    """
    无 API Key 时的确定性意图。

    【学习】re.search 提取「N天」里的 N；any(k in question for k in ...) 做关键词路由
    做中文关键词路由。扩展意图时改这里或 query_prompt.txt 即可。
    """
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
