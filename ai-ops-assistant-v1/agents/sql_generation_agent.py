"""SQL Generation Agent：意图 → Doris SQL + mock 执行计划。"""

from __future__ import annotations

from typing import Any, Dict

from agents._camel_runtime import load_prompt_file, run_json_agent
from config import get_settings


def run(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    输入:
        understanding: Query Understanding Agent 的输出（dict）
    可选:
        user_question

    输出:
        sql, sql_comment, mock_plan, tables_used
    """
    settings = get_settings()
    understanding = payload.get("understanding") or {}
    if settings.use_mock_agents:
        return _mock_sql(understanding)
    system = load_prompt_file(settings, "sql_prompt.txt")
    user_payload = {
        "understanding": understanding,
        "user_question": payload.get("user_question"),
    }
    data = run_json_agent(system, user_payload, settings=settings)
    return _normalize_sql(data)


def _normalize_sql(data: Dict[str, Any]) -> Dict[str, Any]:
    plan = data.get("mock_plan") or {}
    return {
        "sql": data.get("sql", "SELECT 1"),
        "sql_comment": data.get("sql_comment", ""),
        "mock_plan": plan,
        "tables_used": data.get("tables_used") or [],
    }


def _mock_sql(understanding: Dict[str, Any]) -> Dict[str, Any]:
    intent = understanding.get("intent", "")
    days = int(understanding.get("time_range_days", 7))
    if intent == "revenue_analysis":
        sql = (
            f"-- last {days} days order summary\n"
            "SELECT dt, orders, gmv_cny FROM order_daily_summary "
            f"WHERE dt >= DATE_SUB(CURRENT_DATE(), INTERVAL {days} DAY) "
            "ORDER BY dt;"
        )
        plan = {"op": "order_daily_summary_range", "days": days}
        tables = ["order_daily_summary"]
        comment = "按日汇总商城订单量与 GMV，观察付费与流失是否同向波动。"
    else:
        sql = (
            f"-- last {days} days game metrics\n"
            "SELECT dt, dau, new_users, retention_d1_pct, churn_users_7d_window "
            "FROM game_daily_metrics "
            f"WHERE dt >= DATE_SUB(CURRENT_DATE(), INTERVAL {days} DAY) "
            "ORDER BY dt;"
        )
        plan = {"op": "game_daily_metrics_range", "days": days}
        tables = ["game_daily_metrics"]
        comment = "按日提取 DAU、新增、次留与 7 日流失窗口人数，支撑流失结论。"
    return {
        "sql": sql,
        "sql_comment": comment,
        "mock_plan": plan,
        "tables_used": tables,
    }
