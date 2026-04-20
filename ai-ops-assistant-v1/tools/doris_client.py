"""Doris 客户端占位：当前全部走内存 Mock，后续替换为 JDBC/SQLAlchemy + Doris。"""

from __future__ import annotations

from typing import Any, Dict, List

from mock_data import game_data, order_data


class DorisClient:
    """最小接口：execute(sql) -> rows。MVP 根据 mock_plan 路由，不真实解析 SQL。"""

    def __init__(self, use_mock: bool = True) -> None:
        self._use_mock = use_mock

    def fetch_by_plan(self, plan: Dict[str, Any]) -> List[Dict[str, Any]]:
        """按结构化计划取数（由 SQL Agent 与 Tool 约定）。"""
        op = plan.get("op")
        if op == "game_daily_metrics_range":
            rows = game_data.table_rows("game_daily_metrics")
            days = int(plan.get("days", 7))
            return rows[-days:]
        if op == "order_daily_summary_range":
            rows = order_data.table_rows("order_daily_summary")
            days = int(plan.get("days", 7))
            return rows[-days:]
        if op == "raw_sql_stub":
            # 预留：未来把 SQL 交给真实 Doris
            return []
        return []

    def execute_sql(self, sql: str, plan: Dict[str, Any]) -> Dict[str, Any]:
        """统一返回：包含原始 SQL、计划与结果行。"""
        rows = self.fetch_by_plan(plan)
        return {
            "sql": sql,
            "plan": plan,
            "row_count": len(rows),
            "rows": rows,
            "engine": "mock_doris",
        }
