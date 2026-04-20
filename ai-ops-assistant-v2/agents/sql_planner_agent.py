"""SQLPlannerAgent：用户问题 + Schema → 初始 SQL（SQL 三阶段第一阶段）。"""

from __future__ import annotations

from typing import Any, Dict

from agents._camel_runtime import load_prompt_file, run_json_agent
from config import get_settings


def run(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    输入:
        user_question, understanding, schema_context (str),
        candidate_tables (list)

    输出:
        initial_sql, rationale, tables_used, estimated_scan_hint
    """
    settings = get_settings()
    if settings.use_mock_agents:
        return _mock_plan(payload)

    system = load_prompt_file(settings, "sql_planner_prompt.txt")
    user_payload = {
        "user_question": payload.get("user_question"),
        "understanding": payload.get("understanding"),
        "schema_context": payload.get("schema_context"),
        "candidate_tables": payload.get("candidate_tables"),
    }
    data = run_json_agent(system, user_payload, settings=settings)
    return _normalize(data)


def _normalize(data: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "initial_sql": data.get("initial_sql", "").strip(),
        "rationale": data.get("rationale", ""),
        "tables_used": list(data.get("tables_used") or []),
        "estimated_scan_hint": data.get("estimated_scan_hint", ""),
    }


def _mock_plan(payload: Dict[str, Any]) -> Dict[str, Any]:
    u = payload.get("understanding") or {}
    intent = u.get("intent", "")
    days = int(u.get("time_range_days", 7))
    if intent == "revenue_analysis":
        sql = (
            f"SELECT dt, orders, gmv_cny\nFROM order_daily_summary\n"
            f"WHERE dt >= DATE_SUB(CURRENT_DATE(), INTERVAL {days} DAY)\n"
            "ORDER BY dt;"
        )
        tables = ["order_daily_summary"]
        hint = "单表分区扫描 order_daily_summary.dt"
    else:
        sql = (
            f"SELECT dt, dau, new_users, retention_d1_pct, churn_users_7d_window\n"
            "FROM game_daily_metrics\n"
            f"WHERE dt >= DATE_SUB(CURRENT_DATE(), INTERVAL {days} DAY)\n"
            "ORDER BY dt;"
        )
        tables = ["game_daily_metrics"]
        hint = "分区裁剪 game_daily_metrics.dt"
    return {
        "initial_sql": sql,
        "rationale": "Mock：按意图映射到演示表并带分区日期过滤。",
        "tables_used": tables,
        "estimated_scan_hint": hint,
    }
