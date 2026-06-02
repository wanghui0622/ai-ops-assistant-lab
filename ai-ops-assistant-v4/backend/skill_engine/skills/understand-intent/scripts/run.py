from __future__ import annotations
import re
from typing import Any, Dict

def parse_intent(ctx, inp: Dict[str, Any]) -> Dict[str, Any]:
    question = inp.get("user_question", ctx.user_question).strip()
    settings = ctx.settings
    if settings.use_mock_model:
        data = _mock(question)
    else:
        system = (ctx.settings.prompts_dir / "query_prompt.txt").read_text(encoding="utf-8")
        data = ctx.model_adapter.chat_json(system, {"user_question": question})
        data = _normalize(data)
    return {"understanding": data, "raw_question": question, "intent": data}

def _normalize(data):
    return {"intent": data.get("intent","adhoc_analysis"), "intent_label": data.get("intent_label","数据分析"), "time_range_days": int(data.get("time_range_days",7)), "metrics": data.get("metrics") or [], "entities": data.get("entities") or {}, "confidence": float(data.get("confidence",0.8))}

def _mock(question):
    days = 7
    m = re.search(r"(\d+)\s*天", question)
    if m: days = int(m.group(1))
    if any(k in question for k in ("活跃","dau","活跃度")):
        return {"intent":"general_trend","intent_label":"活跃度趋势","time_range_days":days,"metrics":[],"entities":{},"confidence":0.9}
    if any(k in question for k in ("流失","留存","沉默")):
        return {"intent":"churn_analysis","intent_label":"用户流失与活跃变化","time_range_days":days,"metrics":[],"entities":{},"confidence":0.95}
    if any(k in question for k in ("收入","付费","gmv","订单")):
        return {"intent":"revenue_analysis","intent_label":"商城收入与订单","time_range_days":days,"metrics":[],"entities":{},"confidence":0.9}
    return {"intent":"general_trend","intent_label":"通用趋势分析","time_range_days":days,"metrics":[],"entities":{},"confidence":0.75}
