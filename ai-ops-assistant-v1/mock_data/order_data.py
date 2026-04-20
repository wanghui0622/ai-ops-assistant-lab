"""商城订单 Mock 数据（模拟 Doris 表 `order_daily_summary`）。

与 `game_data` 使用相同日期区间（14 天），便于对照「活跃 vs 付费」叙事验证。
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

ORDER_DAILY_SUMMARY: List[Dict[str, Any]] = [
    {"dt": "2026-04-07", "orders": 9450, "gmv_cny": 498_000},
    {"dt": "2026-04-08", "orders": 9420, "gmv_cny": 495_500},
    {"dt": "2026-04-09", "orders": 9380, "gmv_cny": 493_000},
    {"dt": "2026-04-10", "orders": 9350, "gmv_cny": 491_000},
    {"dt": "2026-04-11", "orders": 9320, "gmv_cny": 489_500},
    {"dt": "2026-04-12", "orders": 9280, "gmv_cny": 488_000},
    {"dt": "2026-04-13", "orders": 9240, "gmv_cny": 487_000},
    {"dt": "2026-04-14", "orders": 9200, "gmv_cny": 486_000},
    {"dt": "2026-04-15", "orders": 9350, "gmv_cny": 492_000},
    {"dt": "2026-04-16", "orders": 9100, "gmv_cny": 478_000},
    {"dt": "2026-04-17", "orders": 9050, "gmv_cny": 471_000},
    {"dt": "2026-04-18", "orders": 8980, "gmv_cny": 465_000},
    {"dt": "2026-04-19", "orders": 8920, "gmv_cny": 459_000},
    {"dt": "2026-04-20", "orders": 8860, "gmv_cny": 452_000},
]

DATASET_META: Dict[str, Any] = {
    "table": "order_daily_summary",
    "row_count": len(ORDER_DAILY_SUMMARY),
    "date_from": ORDER_DAILY_SUMMARY[0]["dt"],
    "date_to": ORDER_DAILY_SUMMARY[-1]["dt"],
    "notes": "Mock；gmv_cny 为当日商城 GMV（人民币），orders 为订单笔数",
}


def table_rows(table: str) -> List[Dict[str, Any]]:
    if table == "order_daily_summary":
        return list(ORDER_DAILY_SUMMARY)
    return []


def last_n_days(table: str, n: int) -> List[Dict[str, Any]]:
    rows = table_rows(table)
    if not rows:
        return []
    k = max(1, min(int(n), len(rows)))
    return rows[-k:]


def date_range() -> Tuple[str, str]:
    if not ORDER_DAILY_SUMMARY:
        return ("", "")
    return (ORDER_DAILY_SUMMARY[0]["dt"], ORDER_DAILY_SUMMARY[-1]["dt"])
