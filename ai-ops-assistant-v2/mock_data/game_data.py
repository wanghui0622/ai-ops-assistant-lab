"""游戏侧 Mock 数据（模拟 Doris 表）。"""

from __future__ import annotations

from typing import Any, Dict, List

GAME_DAILY_METRICS: List[Dict[str, Any]] = [
    {
        "dt": "2026-04-14",
        "dau": 128_400,
        "new_users": 3_200,
        "retention_d1_pct": 42.5,
        "churn_users_7d_window": 5_100,
    },
    {
        "dt": "2026-04-15",
        "dau": 129_900,
        "new_users": 3_050,
        "retention_d1_pct": 43.1,
        "churn_users_7d_window": 4_980,
    },
    {
        "dt": "2026-04-16",
        "dau": 127_200,
        "new_users": 2_980,
        "retention_d1_pct": 41.8,
        "churn_users_7d_window": 5_240,
    },
    {
        "dt": "2026-04-17",
        "dau": 126_800,
        "new_users": 3_110,
        "retention_d1_pct": 42.0,
        "churn_users_7d_window": 5_350,
    },
    {
        "dt": "2026-04-18",
        "dau": 125_600,
        "new_users": 2_900,
        "retention_d1_pct": 40.9,
        "churn_users_7d_window": 5_520,
    },
    {
        "dt": "2026-04-19",
        "dau": 124_900,
        "new_users": 2_870,
        "retention_d1_pct": 40.5,
        "churn_users_7d_window": 5_610,
    },
    {
        "dt": "2026-04-20",
        "dau": 124_100,
        "new_users": 2_840,
        "retention_d1_pct": 40.2,
        "churn_users_7d_window": 5_680,
    },
]


def table_rows(table: str) -> List[Dict[str, Any]]:
    if table == "game_daily_metrics":
        return list(GAME_DAILY_METRICS)
    return []
