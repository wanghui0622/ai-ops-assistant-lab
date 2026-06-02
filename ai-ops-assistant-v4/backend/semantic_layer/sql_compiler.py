"""SQL Compiler：仅将 QueryPlan 编译为 Doris SQL（禁止由 LLM 直接写 SQL）。"""

from __future__ import annotations

import re
from typing import Any, Dict, List


_IDENTIFIER = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")


def compile_query_plan(plan: Dict[str, Any]) -> Dict[str, Any]:
    """将 QueryPlan 编译为唯一可执行 SQL。"""
    if not plan.get("ok"):
        return {
            "ok": False,
            "sql": "",
            "compilation_method": "semantic_sql_compiler_v3",
            "error": plan.get("error") or plan.get("message"),
            "plan_echo": plan,
        }

    table = plan["source_table"]
    if not _safe_ident(table):
        return _reject("INVALID_TABLE_NAME")

    dims: List[str] = plan["dimensions"]
    for d in dims:
        if not _safe_ident(d):
            return _reject(f"INVALID_DIMENSION:{d}")

    metrics: List[Dict[str, Any]] = plan["resolved_metrics"]
    select_parts: List[str] = []

    for d in dims:
        select_parts.append(f"`{d}`")

    used_aliases = set(dims)
    for m in metrics:
        raw_expr = (m.get("sql_template") or "").strip()
        mid = m.get("id", "metric")
        if not _safe_ident(mid):
            return _reject(f"INVALID_METRIC_ID:{mid}")
        if not _safe_sql_expression(raw_expr):
            return _reject(f"INVALID_METRIC_EXPRESSION:{mid}")

        if _safe_ident(raw_expr):
            expr_sql = f"`{raw_expr}`"
        else:
            expr_sql = raw_expr

        alias = mid
        if alias in used_aliases:
            alias = f"{mid}_m"
        select_parts.append(f"{expr_sql} AS `{alias}`")
        used_aliases.add(alias)

    days = int(plan.get("time_range_days", 7))
    pf = plan.get("partition_field") or "dt"
    if not _safe_ident(pf):
        return _reject("INVALID_PARTITION_FIELD")

    order_by = plan.get("order_by") or dims[:1]
    order_sql = ", ".join(f"`{o}`" for o in order_by if _safe_ident(o))
    limit = max(1, min(int(plan.get("limit", 5000)), 100_000))

    select_clause = ", ".join(select_parts)

    sql = (
        f"SELECT {select_clause}\n"
        f"FROM `{table}`\n"
        f"WHERE `{pf}` >= DATE_SUB(CURRENT_DATE(), INTERVAL {days} DAY)\n"
        f"ORDER BY {order_sql}\n"
        f"LIMIT {limit}"
    )

    return {
        "ok": True,
        "sql": sql.strip(),
        "compilation_method": "semantic_sql_compiler_v3",
        "plan_echo": plan,
        "notes": [
            "SQL 仅由 metrics/registry.yaml 模板与 QueryPlan 拼装，不经 LLM 产出终稿。",
        ],
    }


def _safe_ident(name: str) -> bool:
    return bool(name and _IDENTIFIER.match(name))


def _safe_sql_expression(expr: str) -> bool:
    if not expr or len(expr) > 512:
        return False
    if ";" in expr or "--" in expr or "/*" in expr:
        return False
    allowed = set(
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_+-*/().% "
    )
    for ch in expr:
        if ch not in allowed:
            return False
    return True


def _reject(reason: str) -> Dict[str, Any]:
    return {
        "ok": False,
        "sql": "",
        "compilation_method": "semantic_sql_compiler_v3",
        "error": reason,
        "plan_echo": {},
    }
