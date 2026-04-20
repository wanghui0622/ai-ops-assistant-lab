"""SQLExecutionAgent：执行 SQL / 捕获异常 / 可选 EXPLAIN（第三阶段）。"""

from __future__ import annotations

from typing import Any, Dict, Optional

from config import get_settings
from tools.doris_client import get_doris_client


def run(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    输入:
        optimized_sql: str 或 sql_plan / sql_optimizer 嵌套
        run_explain: bool (默认 True)
        max_rows: int 可选

    输出:
        ok, columns, rows, row_count,
        error_code, error_message,
        explain, engine, raw_execute
    """
    settings = get_settings()
    sql = _resolve_sql(payload)
    max_rows = payload.get("max_rows") or settings.sql_row_limit_default
    run_explain = payload.get("run_explain", True)

    client = get_doris_client()
    explain_result: Optional[Dict[str, Any]] = None
    if run_explain:
        try:
            explain_result = client.explain_sql(sql)
        except Exception as e:  # noqa: BLE001
            explain_result = {"ok": False, "error": str(e), "engine": "explain_failed"}

    raw = client.execute_sql(sql, max_rows=max_rows)

    ok = bool(raw.get("ok", True))
    err = raw.get("error")
    code = None
    if not ok or err:
        ok = False
        code = "DORIS_EXEC_ERROR"

    return {
        "ok": ok,
        "columns": raw.get("columns") or [],
        "rows": raw.get("rows") or [],
        "row_count": raw.get("row_count", 0),
        "error_code": code,
        "error_message": err,
        "explain": explain_result,
        "engine": raw.get("engine"),
        "raw_execute": raw,
    }


def _resolve_sql(payload: Dict[str, Any]) -> str:
    if payload.get("optimized_sql"):
        return str(payload["optimized_sql"]).strip()
    opt = payload.get("sql_optimizer") or {}
    if opt.get("optimized_sql"):
        return str(opt["optimized_sql"]).strip()
    plan = payload.get("sql_plan") or {}
    return str(plan.get("initial_sql", "")).strip()
