"""
Doris 客户端：MVP 全部走内存 Mock，接口预留真实 OLAP。

【学习】Tool 与 Agent 的分工：
  - Agent：可能非确定性（LLM）
  - Tool（本 Client）：确定性取数，输入/输出结构固定

【学习】V2+ 可配置 DORIS_HOST；V1 仅 use_mock=True。
"""

from __future__ import annotations

from typing import Any, Dict, List

from mock_data import game_data, order_data


class DorisClient:
    """
    最小接口：execute_sql(sql, plan) -> { rows, row_count, ... }。

    【学习】Mock 不解析 SQL 的原因：教学重点在 Pipeline，而非 SQL 解析器。
    真实接入时：execute_sql 应把 sql 发给 Doris，mock_plan 仅用于演示回退。
    """

    def __init__(self, use_mock: bool = True) -> None:
        self._use_mock = use_mock

    def fetch_by_plan(self, plan: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        按结构化计划取数（与 SQL Agent 约定）。

        plan 字段：
          - op: 路由操作名
          - days: 取最近 N 天（mock 表共 14 天，见 mock_data/）
        """
        op = plan.get("op")
        if op == "game_daily_metrics_range":
            rows = game_data.table_rows("game_daily_metrics")
            days = int(plan.get("days", 7))
            return rows[-days:]  # 【学习】Python 切片：最后 N 行 = 最近 N 天
        if op == "order_daily_summary_range":
            rows = order_data.table_rows("order_daily_summary")
            days = int(plan.get("days", 7))
            return rows[-days:]
        if op == "raw_sql_stub":
            # 预留：未来把 SQL 交给真实 Doris
            return []
        return []

    def execute_sql(self, sql: str, plan: Dict[str, Any]) -> Dict[str, Any]:
        """统一返回结构，供 analysis_agent 消费。"""
        rows = self.fetch_by_plan(plan)
        return {
            "sql": sql,
            "plan": plan,
            "row_count": len(rows),
            "rows": rows,
            "engine": "mock_doris",
        }
