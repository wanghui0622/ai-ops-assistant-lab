"""SQL 工具：对接 DorisClient；输入/输出均为结构化 dict。"""

from __future__ import annotations

from typing import Any, Dict

from tools.doris_client import DorisClient


def run(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    执行查询。

    期望 payload:
        - sql: str
        - mock_plan: dict（与 Doris mock 路由约定）
    """
    sql = payload.get("sql", "")
    plan = payload.get("mock_plan") or {}
    client = DorisClient(use_mock=True)
    result = client.execute_sql(sql, plan)
    return {
        "ok": True,
        "query_result": result,
    }
