"""商城订单 Mock 数据。"""

from __future__ import annotations

from typing import Any, Dict, List

ORDER_DAILY_SUMMARY: List[Dict[str, Any]] = [
    {"dt": "2026-04-14", "orders": 9200, "gmv_cny": 486_000},
    {"dt": "2026-04-15", "orders": 9350, "gmv_cny": 492_000},
    {"dt": "2026-04-16", "orders": 9100, "gmv_cny": 478_000},
    {"dt": "2026-04-17", "orders": 9050, "gmv_cny": 471_000},
    {"dt": "2026-04-18", "orders": 8980, "gmv_cny": 465_000},
    {"dt": "2026-04-19", "orders": 8920, "gmv_cny": 459_000},
    {"dt": "2026-04-20", "orders": 8860, "gmv_cny": 452_000},
]


def table_rows(table: str) -> List[Dict[str, Any]]:
    if table == "order_daily_summary":
        return list(ORDER_DAILY_SUMMARY)
    return []
