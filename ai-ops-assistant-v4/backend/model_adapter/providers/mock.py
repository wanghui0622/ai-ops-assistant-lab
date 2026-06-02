from __future__ import annotations
import json, re
from typing import Any, Dict, List
from model_adapter.providers.base import BaseProvider
from model_adapter.types import ChatMessage, ModelResponse

class MockProvider(BaseProvider):
    name = "mock"
    def __init__(self, model_name: str = "mock") -> None:
        self.model_name = model_name
    def chat(self, messages, *, json_mode=False, temperature=0.2):
        user_text = next((m.content for m in messages if m.role == "user"), "")
        system_text = next((m.content for m in messages if m.role == "system"), "")
        payload = self._infer(user_text, system_text)
        content = json.dumps(payload, ensure_ascii=False) if json_mode else payload.get("text", json.dumps(payload, ensure_ascii=False))
        return ModelResponse(content=content, provider=self.name, model=self.model_name)
    def _infer(self, user_text, system_text):
        s = system_text.lower()
        if "metric" in s or "指标" in system_text:
            days = 7
            m = re.search(r"(\d+)\s*天", user_text)
            if m: days = int(m.group(1))
            mids = ["active_user", "retention_rate"]
            if any(k in user_text for k in ("收入","gmv","订单")): mids = ["order_amount","paying_user"]
            return {"metric_ids": mids, "dimensions": ["dt"], "time_range_days": days, "confidence": 0.85, "reasoning": "Mock 指标选择"}
        if "intent" in s or "意图" in system_text:
            days = 7
            m = re.search(r"(\d+)\s*天", user_text)
            if m: days = int(m.group(1))
            label = "活跃度趋势" if any(k in user_text for k in ("活跃","dau","活跃度")) else "通用趋势分析"
            intent = "general_trend"
            if any(k in user_text for k in ("流失","留存")): intent, label = "churn_analysis", "用户流失与活跃变化"
            return {"intent": intent, "intent_label": label, "time_range_days": days, "metrics": [], "entities": {}, "confidence": 0.9}
        if "洞察" in system_text or "insight" in s:
            return {"summary": "Mock 洞察：指标序列整体平稳。", "key_findings": ["active_user 首尾 flat"], "trends": {}, "risks": ["Mock 模式"], "suggestions": ["接入真实 LLM"]}
        return {"text": "# Mock Report\n\n占位报告。"}
