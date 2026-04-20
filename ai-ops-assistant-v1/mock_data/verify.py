"""Mock 数据自检：用于本地快速验证「行数 / 日期区间 / 最近 N 天切片」是否与预期一致。

用法（在 `ai-ops-assistant-v1` 目录下）::

    python -m mock_data.verify
"""

from __future__ import annotations

from mock_data import game_data, order_data


def main() -> None:
    g = game_data.DATASET_META
    o = order_data.DATASET_META
    print("=== V1 Mock 数据集元信息 ===")
    print(f"game_daily_metrics: {g['row_count']} 行, {g['date_from']} ~ {g['date_to']}")
    print(f"order_daily_summary: {o['row_count']} 行, {o['date_from']} ~ {o['date_to']}")
    assert g["row_count"] == o["row_count"], "两表日期行数应对齐"
    assert g["date_from"] == o["date_from"] and g["date_to"] == o["date_to"], "日期区间应对齐"

    for n in (7, 14):
        lg = game_data.last_n_days("game_daily_metrics", n)
        lo = order_data.last_n_days("order_daily_summary", n)
        assert len(lg) == n and len(lo) == n
        print(f"最近 {n} 天切片: game 末行 dt={lg[-1]['dt']}, order 末行 dt={lo[-1]['dt']}")

    print("校验通过：可用 `python main.py \"最近14天流失情况\"` 等问法覆盖更长窗口。")


if __name__ == "__main__":
    main()
