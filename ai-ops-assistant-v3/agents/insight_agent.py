"""Insight Agent：查询结果 → 结构化洞察（V3：指标驱动语义）。"""

from __future__ import annotations

import statistics
from typing import Any, Dict, List

from agents._camel_runtime import run_json_agent
from config import get_settings

_INSIGHT_SYSTEM = """你是游戏数据分析师。用户问题基于「指标字典」查询 Doris。请根据查询结果行（JSON）输出洞察。
输出 JSON：
- summary, key_findings, trends, risks, suggestions

不要编造列中不存在的字段。仅输出 JSON。"""


def run(payload: Dict[str, Any]) -> Dict[str, Any]:
    settings = get_settings()
    rows = _extract_rows(payload)
    if settings.use_mock_agents:
        return _mock_insight(payload, rows)

    user_payload = {
        "user_question": payload.get("user_question"),
        "understanding": payload.get("understanding"),
        "metric_bundle": payload.get("metric_bundle"),
        "query_plan": payload.get("query_plan"),
        "compiled_sql": (payload.get("sql_compiler") or {}).get("sql"),
        "rows": rows,
    }
    data = run_json_agent(_INSIGHT_SYSTEM, user_payload, settings=settings)
    return _normalize(data)


def _extract_rows(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    qe = payload.get("query_execution") or {}
    return list(qe.get("rows") or [])


def _normalize(data: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "summary": data.get("summary", ""),
        "key_findings": list(data.get("key_findings") or []),
        "trends": data.get("trends") or {},
        "risks": list(data.get("risks") or []),
        "suggestions": list(data.get("suggestions") or []),
    }


def _direction(series: List[float]) -> str:
    if len(series) < 2:
        return "unknown"
    first, last = series[0], series[-1]
    if last > first * 1.02:
        return "up"
    if last < first * 0.98:
        return "down"
    return "flat"


def _mock_insight(payload: Dict[str, Any], rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    qe = payload.get("query_execution") or {}
    mb = payload.get("metric_bundle") or {}
    mids = mb.get("metric_ids") or []

    if not qe.get("ok", True):
        return {
            "summary": "查询失败，无法生成洞察。",
            "key_findings": [],
            "trends": {},
            "risks": [qe.get("error_message") or "执行错误"],
            "suggestions": ["检查语义计划与 Doris 连通性。", "查看 sql_compiler 报错。"],
        }

    if not rows:
        return {
            "summary": "查询成功但无数据行。",
            "key_findings": [],
            "trends": {},
            "risks": ["时间范围或过滤条件可能导致空集。"],
            "suggestions": ["尝试扩大日期窗口或核对分区加载。"],
        }

    lines: List[str] = []
    for mid in mids:
        if mid in rows[0]:
            col = mid
            ser = [float(r.get(col, 0) or 0) for r in rows]
            if ser:
                lines.append(
                    f"{mid}: 首尾 {_direction(ser)}，区间 [{ser[0]:,.2f}, {ser[-1]:,.2f}]"
                )

    if not lines:
        lines.append(f"返回 {len(rows)} 行，指标列别名与注册名可能不一致，请对照列名分析。")

    return {
        "summary": f"基于指标 {mids} 的 {len(rows)} 日（行）序列分析。",
        "key_findings": lines[:5],
        "trends": {},
        "risks": ["Mock 洞察仅作演示；生产应接入完整指标血缘与置信区间。"],
        "suggestions": ["将 metric 与可视化看板对齐，沉淀「指标→SQL」审计日志。"],
    }
