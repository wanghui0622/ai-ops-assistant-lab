"""Semantic Planner：将 Metric Agent 输出转为结构化 QueryPlan（不含自由文本 SQL）。"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from metrics.loader import MetricRegistry, get_metric_registry


def plan_query(
    metric_bundle: Dict[str, Any],
    understanding: Dict[str, Any],
    registry: Optional[MetricRegistry] = None,
) -> Dict[str, Any]:
    """
    输入:
        metric_bundle: metric_agent.run 输出
        understanding: intent agent 输出

    输出 QueryPlan（供 sql_compiler 唯一合法 SQL 来源）:
        version, source_table, dimensions, resolved_metrics,
        time_range_days, partition_field, order_by, limit, warnings
    """
    reg = registry or get_metric_registry()
    raw_ids: List[str] = list(metric_bundle.get("metric_ids") or [])
    if not raw_ids:
        return {
            "ok": False,
            "error": "NO_METRICS",
            "message": "metric_ids 为空",
            "valid_metric_ids": reg.list_ids(),
        }

    validation = reg.validate_ids(raw_ids)
    if not validation["valid"]:
        return {
            "ok": False,
            "error": "UNKNOWN_METRIC",
            "message": f"未知指标: {validation['unknown_ids']}",
            "valid_metric_ids": reg.list_ids(),
        }

    intent = understanding.get("intent", "")
    days = int(
        metric_bundle.get("time_range_days")
        or understanding.get("time_range_days")
        or 7
    )
    dims_request: List[str] = list(metric_bundle.get("dimensions") or ["dt"])

    resolved: List[Dict[str, Any]] = []
    tables: set = set()
    for mid in raw_ids:
        m = reg.get(mid)
        if not m:
            continue
        resolved.append(
            {
                "id": mid,
                "name": m.get("name", mid),
                "sql_template": m.get("sql_template", ""),
                "source_table": m.get("source_table"),
                "dimensions_allowed": list(m.get("dimensions") or []),
            }
        )
        tables.add(m.get("source_table"))

    warnings: List[str] = []
    if len(tables) > 1:
        resolved, dropped = _filter_metrics_single_table(resolved, intent)
        if dropped:
            warnings.append(
                f"多表指标已按意图裁剪，仅保留单表查询。移除: {dropped}"
            )
        tables = {r["source_table"] for r in resolved}

    if not resolved:
        return {
            "ok": False,
            "error": "EMPTY_PLAN",
            "message": "裁剪后无可执行指标",
        }

    if len(tables) != 1:
        return {
            "ok": False,
            "error": "MULTI_TABLE_UNSUPPORTED",
            "message": "当前语义层 MVP 仅支持单物理表查询，请拆分问题或多轮问答。",
            "tables_seen": sorted(tables),
        }

    source_table = next(iter(tables))
    merged_dims = _merge_dimensions(resolved, dims_request, warnings)

    limit = int(metric_bundle.get("sql_limit") or 5000)

    plan: Dict[str, Any] = {
        "ok": True,
        "version": "semantic_query_plan_v1",
        "source_table": source_table,
        "dimensions": merged_dims,
        "partition_field": "dt",
        "resolved_metrics": resolved,
        "time_range_days": days,
        "order_by": merged_dims[:1] if merged_dims else ["dt"],
        "limit": limit,
        "intent_context": intent,
        "warnings": warnings,
    }
    return plan


def _merge_dimensions(
    resolved: List[Dict[str, Any]],
    requested: List[str],
    warnings: List[str],
) -> List[str]:
    """维度交集 + 默认 dt。"""
    common: Optional[set] = None
    for r in resolved:
        allowed = set(r.get("dimensions_allowed") or [])
        common = allowed if common is None else common & allowed
    if not common:
        common = {"dt"}
        warnings.append("指标维度无交集，强制使用 dt。")
    out: List[str] = []
    for d in requested:
        if d in common and d not in out:
            out.append(d)
    if not out:
        out = ["dt"] if "dt" in common else sorted(common)[:1]
    return out


def _filter_metrics_single_table(
    resolved: List[Dict[str, Any]],
    intent: str,
) -> tuple:
    """按意图保留一张表上的指标。"""
    if not resolved:
        return [], []

    tables = {r["source_table"] for r in resolved}
    if len(tables) <= 1:
        return resolved, []

    if intent == "revenue_analysis":
        preferred = "order_daily_summary"
    elif intent in ("churn_analysis", "general_trend"):
        preferred = "game_daily_metrics"
    else:
        preferred = resolved[0]["source_table"]

    kept = [r for r in resolved if r["source_table"] == preferred]
    dropped = [r["id"] for r in resolved if r["source_table"] != preferred]
    if not kept:
        kept = [resolved[0]]
        dropped = [r["id"] for r in resolved[1:]]
    return kept, dropped
