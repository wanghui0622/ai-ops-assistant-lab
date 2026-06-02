from __future__ import annotations
from typing import Any, Dict
from semantic_layer.semantic_planner import plan_query as semantic_plan
from semantic_layer.sql_compiler import compile_query_plan
from config import get_settings
from tools.doris_client import get_doris_client

def plan_query(ctx, inp):
    mb = inp.get("metric_bundle") or ctx.data.get("metric_bundle") or {}
    understanding = inp.get("understanding") or inp.get("intent") or ctx.data.get("understanding") or {}
    qp = semantic_plan(mb, understanding)
    ctx.data["query_plan"] = qp
    return {"query_plan": qp}

def compile_sql(ctx, inp):
    qp = inp.get("query_plan") or ctx.data.get("query_plan") or {}
    sc = compile_query_plan(qp)
    ctx.data["sql_compiler"] = sc
    return {"sql_compiler": sc}

def execute_query(ctx, inp):
    settings = get_settings()
    sc = inp.get("sql_compiler") or ctx.data.get("sql_compiler") or {}
    sql = str(sc.get("sql") or "").strip()
    client = get_doris_client()
    explain = None
    if sql:
        try: explain = client.explain_sql(sql)
        except Exception as e: explain = {"ok": False, "error": str(e)}
    if not sql:
        qe = {"ok": False, "columns": [], "rows": [], "row_count": 0, "error_code": "NO_SQL", "error_message": "compiled_sql 为空", "explain": explain, "engine": None}
    else:
        raw = client.execute_sql(sql, max_rows=settings.sql_row_limit_default)
        ok = bool(raw.get("ok", True)) and not raw.get("error")
        qe = {"ok": ok, "columns": raw.get("columns") or [], "rows": raw.get("rows") or [], "row_count": raw.get("row_count", 0), "error_code": "DORIS_EXEC_ERROR" if not ok else None, "error_message": raw.get("error"), "explain": explain, "engine": raw.get("engine"), "raw_execute": raw}
    ctx.data["query_execution"] = qe
    mb = inp.get("metric_bundle") or ctx.data.get("metric_bundle") or {}
    return {"query_execution": qe, "metric_bundle": mb}
