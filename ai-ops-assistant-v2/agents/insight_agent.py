"""Insight Agent：查询结果 → 结构化洞察（对接 Report）。"""

from __future__ import annotations

import statistics
from typing import Any, Dict, List

from agents._camel_runtime import run_json_agent
from config import get_settings

_INSIGHT_SYSTEM = """你是游戏数据分析师。根据用户问题与 Doris 查询结果（JSON 行数组），输出简短、可验证的结论。
输出 JSON：
- summary: 一句话摘要（中文）
- key_findings: 字符串数组，每条基于数据
- trends: 对象，可含 dau_direction / churn_direction / gmv_direction，取值 up|down|flat|unknown
- risks: 字符串数组
- suggestions: 字符串数组

不要编造数据中不存在的指标。仅输出 JSON。"""


def run(payload: Dict[str, Any]) -> Dict[str, Any]:
    settings = get_settings()
    rows = _extract_rows(payload)
    if settings.use_mock_agents:
        return _mock_insight(payload, rows)

    user_payload = {
        "user_question": payload.get("user_question"),
        "understanding": payload.get("understanding"),
        "initial_sql": (payload.get("sql_plan") or {}).get("initial_sql"),
        "optimized_sql": (payload.get("sql_optimizer") or {}).get("optimized_sql"),
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
    understanding = payload.get("understanding") or {}
    intent = understanding.get("intent", "")
    qe = payload.get("query_execution") or {}
    if not qe.get("ok", True):
        return {
            "summary": "查询执行失败，无法产出业务洞察。",
            "key_findings": [],
            "trends": {},
            "risks": [qe.get("error_message") or "Doris 执行错误"],
            "suggestions": ["检查 SQL、表权限与 Doris FE 连通性。", "查看 explain 输出是否全表扫描。"],
        }

    if not rows:
        return {
            "summary": "查询成功但结果为空，请确认分区范围与过滤条件。",
            "key_findings": [],
            "trends": {},
            "risks": ["可能分区无数据或条件过严。"],
            "suggestions": ["放宽日期范围或核对表分区加载情况。"],
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
            "对新用户推送 3 日回流任务；对沉默用户尝试赛季轻量玩法入口。",
        ],
    }
