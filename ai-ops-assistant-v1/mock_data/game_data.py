"""游戏侧 Mock 数据（模拟 Doris 表 `game_daily_metrics` 查询结果）。

设计目标：14 个自然日、趋势易读（DAU 缓降、7 日流失窗口缓升、次留缓降），
方便用「最近7天 / 最近14天」等问法在 **无真实 Doris** 时做手工/自动化验证。
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

# 14 行：2026-04-07 ～ 2026-04-20（与 order 表日期对齐，便于联合分析）
GAME_DAILY_METRICS: List[Dict[str, Any]] = [
    {
        "dt": "2026-04-07",
        "dau": 130_200,
        "new_users": 3_350,
        "retention_d1_pct": 44.1,
        "churn_users_7d_window": 4_680,
    },
    {
        "dt": "2026-04-08",
        "dau": 129_950,
        "new_users": 3_310,
        "retention_d1_pct": 43.9,
        "churn_users_7d_window": 4_730,
    },
    {
        "dt": "2026-04-09",
        "dau": 129_700,
        "new_users": 3_290,
        "retention_d1_pct": 43.6,
        "churn_users_7d_window": 4_790,
    },
    {
        "dt": "2026-04-10",
        "dau": 129_450,
        "new_users": 3_260,
        "retention_d1_pct": 43.4,
        "churn_users_7d_window": 4_840,
    },
    {
        "dt": "2026-04-11",
        "dau": 129_150,
        "new_users": 3_230,
        "retention_d1_pct": 43.2,
        "churn_users_7d_window": 4_910,
    },
    {
        "dt": "2026-04-12",
        "dau": 128_950,
        "new_users": 3_210,
        "retention_d1_pct": 43.0,
        "churn_users_7d_window": 4_970,
    },
    {
        "dt": "2026-04-13",
        "dau": 128_650,
        "new_users": 3_220,
        "retention_d1_pct": 42.8,
        "churn_users_7d_window": 5_030,
    },
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

DATASET_META: Dict[str, Any] = {
    "table": "game_daily_metrics",
    "row_count": len(GAME_DAILY_METRICS),
    "date_from": GAME_DAILY_METRICS[0]["dt"],
    "date_to": GAME_DAILY_METRICS[-1]["dt"],
    "notes": "Mock；列含义：dau=日活，retention_d1_pct=次日留存%，churn_users_7d_window=7日流失窗口人数",
}


def table_rows(table: str) -> List[Dict[str, Any]]:
    if table == "game_daily_metrics":
        return list(GAME_DAILY_METRICS)
    return []


def last_n_days(table: str, n: int) -> List[Dict[str, Any]]:
    """取最近 n 条（按时间序已在列表末尾为最新）。"""
    rows = table_rows(table)
    if not rows:
        return []
    k = max(1, min(int(n), len(rows)))
    return rows[-k:]


def date_range() -> Tuple[str, str]:
    """返回 (首日期, 末日期)，便于断言。"""
    if not GAME_DAILY_METRICS:
        return ("", "")
    return (GAME_DAILY_METRICS[0]["dt"], GAME_DAILY_METRICS[-1]["dt"])
