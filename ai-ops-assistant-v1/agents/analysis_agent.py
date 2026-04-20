"""Analysis Agent：查询结果 → 结构化分析结论（供 Report Agent 使用）。"""

from __future__ import annotations

import json
import statistics
from typing import Any, Dict, List

from agents._camel_runtime import run_json_agent
from config import get_settings

_ANALYSIS_SYSTEM = """你是游戏数据分析师。根据用户问题与查询结果行（JSON 数组），输出简短、可验证的结论。
输出 JSON：
- summary: 一句话摘要（中文）
- key_findings: 字符串数组，每条基于数据
- trends: 对象，可含 dau_direction / churn_direction / gmv_direction，取值 up|down|flat|unknown
- risks: 字符串数组
- suggestions: 字符串数组

不要编造数据中不存在的指标。仅输出 JSON。"""


def run(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    输入:
        user_question: str
        understanding: dict
        sql_bundle: sql_generation_agent 输出
        query_tool_result: sql_tool 输出

    输出:
        summary, key_findings, trends, risks, suggestions
    """
    settings = get_settings()
    rows = _extract_rows(payload)
    if settings.use_mock_agents:
        return _mock_analysis(payload, rows)
    user_payload = {
        "user_question": payload.get("user_question"),
        "understanding": payload.get("understanding"),
        "sql": (payload.get("sql_bundle") or {}).get("sql"),
        "rows": rows,
    }
    data = run_json_agent(_ANALYSIS_SYSTEM, user_payload, settings=settings)
    return _normalize_analysis(data)


def _extract_rows(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    tool = payload.get("query_tool_result") or {}
    qr = tool.get("query_result") or {}
    return list(qr.get("rows") or [])


def _normalize_analysis(data: Dict[str, Any]) -> Dict[str, Any]:
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


def _mock_analysis(payload: Dict[str, Any], rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    understanding = payload.get("understanding") or {}
    intent = understanding.get("intent", "")
    if not rows:
        return {
            "summary": "本次 Mock 查询未返回任何行，无法计算趋势。",
            "key_findings": [],
            "trends": {},
            "risks": ["数据为空，请检查 mock_plan 与表名配置。"],
            "suggestions": ["确认 Doris 连通后重新执行同一工作流。"],
        }

    if intent == "revenue_analysis":
        gmv = [float(r.get("gmv_cny", 0)) for r in rows]
        return {
            "summary": (
                f"最近 {len(rows)} 个统计日商城 GMV 从 {gmv[0]:,.0f} 元变动至 {gmv[-1]:,.0f} 元。"
            ),
            "key_findings": [
                f"GMV 变动方向：{_direction(gmv)}（首尾对比）。",
                f"日均订单约 {statistics.mean([float(r.get('orders',0)) for r in rows]):,.0f}。",
            ],
            "trends": {"gmv_direction": _direction(gmv)},
            "risks": ["收入下滑可能与活跃流失同步，建议结合分层人群核对。"],
            "suggestions": ["对高价值道具做限时礼包测试，观察 ARPPU 与转化率。"],
        }

    dau = [float(r.get("dau", 0)) for r in rows]
    churn = [float(r.get("churn_users_7d_window", 0)) for r in rows]
    ret = [float(r.get("retention_d1_pct", 0)) for r in rows]
    return {
        "summary": (
            f"最近 {len(rows)} 天内 DAU 由约 {dau[0]:,.0f} 降至 {dau[-1]:,.0f}；"
            f"7 日流失窗口人数由 {churn[0]:,.0f} 升至 {churn[-1]:,.0f}。"
        ),
        "key_findings": [
            f"DAU 趋势：{_direction(dau)}；7 日流失窗口人数趋势：{_direction(churn)}。",
            f"次日留存均值约 {statistics.mean(ret):.1f}%。",
        ],
        "trends": {
            "dau_direction": _direction(dau),
            "churn_direction": _direction(churn),
        },
        "risks": ["活跃与流失指标同向恶化时，付费与内容节奏需联合排查。"],
        "suggestions": [
            "对新用户推送 3 日回流任务；对沉默 7 日用户尝试推送轻量 PVP 赛季入口。",
        ],
    }
