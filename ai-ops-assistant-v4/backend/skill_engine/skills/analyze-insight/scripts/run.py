from __future__ import annotations
from typing import Any, Dict, List

_INSIGHT_SYSTEM = """你是游戏数据分析师。根据查询结果行（JSON）输出洞察 JSON：summary, key_findings, trends, risks, suggestions。不要编造列中不存在的字段。"""

def analyze(ctx, inp):
    payload = {k: inp.get(k) or ctx.data.get(k) for k in ("user_question","understanding","metric_bundle","query_plan","sql_compiler","query_execution")}
    rows = list((payload.get("query_execution") or {}).get("rows") or [])
    if ctx.settings.use_mock_model:
        insight = _mock(payload, rows)
    else:
        user_payload = {**payload, "compiled_sql": (payload.get("sql_compiler") or {}).get("sql"), "rows": rows}
        insight = _normalize(ctx.model_adapter.chat_json(_INSIGHT_SYSTEM, user_payload))
    ctx.data["insight"] = insight
    return {"insight": insight}

def _normalize(data):
    return {"summary": data.get("summary",""), "key_findings": list(data.get("key_findings") or []), "trends": data.get("trends") or {}, "risks": list(data.get("risks") or []), "suggestions": list(data.get("suggestions") or [])}

def _mock(payload, rows):
    qe = payload.get("query_execution") or {}
    mb = payload.get("metric_bundle") or {}
    mids = mb.get("metric_ids") or []
    if not qe.get("ok", True):
        return {"summary": "查询失败", "key_findings": [], "trends": {}, "risks": [qe.get("error_message") or "执行错误"], "suggestions": ["检查 SQL 与 Doris 连通性"]}
    if not rows:
        return {"summary": "查询成功但无数据", "key_findings": [], "trends": {}, "risks": ["可能为空集"], "suggestions": ["扩大日期窗口"]}
    lines = []
    for mid in mids:
        if mid in rows[0]:
            ser = [float(r.get(mid,0) or 0) for r in rows]
            if ser: lines.append(f"{mid}: 区间 [{ser[0]:,.0f}, {ser[-1]:,.0f}]")
    if not lines: lines.append(f"返回 {len(rows)} 行数据")
    return {"summary": f"基于指标 {mids} 的 {len(rows)} 日序列分析", "key_findings": lines[:5], "trends": {}, "risks": ["Mock 洞察仅作演示"], "suggestions": ["对齐看板指标定义"]}
