"""SQLOptimizerAgent：结构优化（JOIN/过滤/分区裁剪/LIMIT）（第二阶段）。"""

from __future__ import annotations

import re
from typing import Any, Dict, List

from agents._camel_runtime import load_prompt_file, run_json_agent
from config import get_settings


def run(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    输入:
        sql_plan: SQLPlannerAgent 输出
        understanding, schema_context

    输出:
        optimized_sql, optimizations_applied, warnings, partition_hint
    """
    settings = get_settings()
    plan = payload.get("sql_plan") or {}
    initial = (plan.get("initial_sql") or "").strip()

    if settings.use_mock_agents:
        return _mock_optimize(initial, payload)

    system = load_prompt_file(settings, "sql_optimizer_prompt.txt")
    user_payload = {
        "initial_sql": initial,
        "understanding": payload.get("understanding"),
        "schema_context": payload.get("schema_context"),
        "estimated_scan_hint": plan.get("estimated_scan_hint"),
    }
    data = run_json_agent(system, user_payload, settings=settings)
    return _normalize(data, initial)


def _normalize(data: Dict[str, Any], fallback_sql: str) -> Dict[str, Any]:
    opt = data.get("optimized_sql") or fallback_sql
    return {
        "optimized_sql": opt.strip(),
        "optimizations_applied": list(data.get("optimizations_applied") or []),
        "warnings": list(data.get("warnings") or []),
        "partition_hint": data.get("partition_hint", ""),
    }


def _mock_optimize(initial_sql: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """确定性规则：补默认 LIMIT、强调分区谓词。"""
    settings = get_settings()
    lim = settings.sql_row_limit_default
    sql = initial_sql.rstrip().rstrip(";")
    apps: List[str] = []
    warns: List[str] = []

    if re.search(r"\blimit\b", sql, re.I):
        warns.append("已存在 LIMIT，未叠加默认行数上限。")
    else:
        sql = f"{sql}\nLIMIT {lim}"
        apps.append(f"追加 LIMIT {lim} 防止大范围扫描。")

    if not re.search(r"\bWHERE\b", sql, re.I):
        warns.append("缺少 WHERE：生产环境应对分区键加范围过滤。")
    else:
        apps.append("检测到 WHERE，利于分区裁剪（请在 catalog 校验分区键）。")

    part = "确保 dt 范围与意图天数一致"
    return {
        "optimized_sql": sql,
        "optimizations_applied": apps,
        "warnings": warns,
        "partition_hint": part,
    }
