"""Doris 执行：输入必须为 sql_compiler 产出的 compiled_sql（或等价键）。"""

from __future__ import annotations

from typing import Any, Dict, Optional

from config import get_settings
from tools.doris_client import get_doris_client


def run(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    输入:
        compiled_sql / sql_compiler_bundle.sql
        run_explain: bool
    """
    settings = get_settings()
    sql = _resolve_sql(payload)
    max_rows = payload.get("max_rows") or settings.sql_row_limit_default
    run_explain = payload.get("run_explain", True)

    client = get_doris_client()
    explain_result: Optional[Dict[str, Any]] = None
    if run_explain and sql:
        try:
            explain_result = client.explain_sql(sql)
        except Exception as e:  # noqa: BLE001
            explain_result = {"ok": False, "error": str(e), "engine": "explain_failed"}

    if not sql:
        return {
            "ok": False,
            "columns": [],
            "rows": [],
            "row_count": 0,
            "error_code": "NO_SQL",
            "error_message": "compiled_sql 为空（compiler 失败？）",
            "explain": explain_result,
            "engine": None,
            "raw_execute": {},
        }

    raw = client.execute_sql(sql, max_rows=max_rows)
    ok = bool(raw.get("ok", True)) and not raw.get("error")
    err = raw.get("error")
    code = "DORIS_EXEC_ERROR" if not ok else None

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
    if payload.get("compiled_sql"):
        return str(payload["compiled_sql"]).strip()
    bundle = payload.get("sql_compiler") or payload.get("sql_compiler_bundle") or {}
    return str(bundle.get("sql") or "").strip()
