"""运营向报告构建：问题摘要、指标说明、图表数据、建议（不含 SQL）。"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from metrics.loader import get_metric_registry


def build_business_report(payload: Dict[str, Any]) -> Dict[str, Any]:
    """从分析上下文生成运营可读报告（markdown + charts）。"""
    question = payload.get("user_question", "")
    understanding = payload.get("understanding") or {}
    mb = payload.get("metric_bundle") or {}
    qe = payload.get("query_execution") or {}
    insight = payload.get("insight") or {}
    rows = list(qe.get("rows") or [])
    metric_ids: List[str] = list(mb.get("metric_ids") or [])

    reg = get_metric_registry()
    metric_cards = _metric_cards(metric_ids, reg)
    charts = _build_charts(rows, metric_ids, reg)
    time_range = int(mb.get("time_range_days") or understanding.get("time_range_days") or 7)

    md = _render_markdown(
        question=question,
        intent_label=understanding.get("intent_label", "数据分析"),
        time_range=time_range,
        summary=insight.get("summary", ""),
        metric_cards=metric_cards,
        charts=charts,
        key_findings=list(insight.get("key_findings") or []),
        risks=list(insight.get("risks") or []),
        suggestions=list(insight.get("suggestions") or []),
        row_count=qe.get("row_count", len(rows)),
    )
    return {
        "markdown": md,
        "format": "markdown",
        "charts": charts,
        "metric_cards": metric_cards,
    }


def _metric_cards(metric_ids: List[str], reg) -> List[Dict[str, str]]:
    cards = []
    for mid in metric_ids:
        m = reg.get(mid) or {}
        cards.append({
            "id": mid,
            "name": m.get("name", mid),
            "description": m.get("description", mid),
        })
    return cards


def _build_charts(rows: List[Dict[str, Any]], metric_ids: List[str], reg) -> List[Dict[str, Any]]:
    if not rows:
        return []
    date_key = "dt" if "dt" in rows[0] else next(iter(rows[0].keys()), "dt")
    charts: List[Dict[str, Any]] = []
    for mid in metric_ids:
        if mid not in rows[0]:
            continue
        m = reg.get(mid) or {}
        series = []
        for r in rows:
            val = r.get(mid)
            if val is None:
                continue
            series.append({"date": str(r.get(date_key, "")), "value": float(val)})
        if not series:
            continue
        unit = _guess_unit(mid, m.get("description", ""))
        charts.append({
            "title": m.get("description", mid).split("，")[0],
            "metric_id": mid,
            "metric_label": m.get("description", mid),
            "unit": unit,
            "series": series,
        })
    return charts


def _guess_unit(metric_id: str, description: str) -> str:
    if "率" in description or "pct" in metric_id or "rate" in metric_id:
        return "%"
    if "金额" in description or "gmv" in metric_id or "amount" in metric_id:
        return "元"
    if "用户" in description or "user" in metric_id:
        return "人"
    if "订单" in description or "order" in metric_id:
        return "笔"
    return ""


def _fmt_value(value: float, unit: str) -> str:
    if unit == "%":
        return f"{value:.1f}%"
    if unit == "元":
        if value >= 10000:
            return f"{value / 10000:.2f} 万"
        return f"{value:,.0f}"
    if value >= 10000:
        return f"{value:,.0f}"
    return f"{value:,.0f}"


def _render_markdown(
    *,
    question: str,
    intent_label: str,
    time_range: int,
    summary: str,
    metric_cards: List[Dict[str, str]],
    charts: List[Dict[str, Any]],
    key_findings: List[str],
    risks: List[str],
    suggestions: List[str],
    row_count: int,
) -> str:
    lines = [
        "# 运营数据分析报告",
        "",
        "## 一、问题与结论",
        "",
        f"**分析问题**：{question}",
        "",
        f"**分析主题**：{intent_label}  ",
        f"**观察周期**：最近 {time_range} 天（共 {row_count} 个数据点）",
        "",
        f"**核心结论**：{summary or '见下方数据解读与建议。'}",
        "",
        "## 二、使用指标",
        "",
        "本次分析基于以下业务指标：",
        "",
    ]
    for card in metric_cards:
        lines.append(f"- **{card['name']}**：{card['description']}")
    lines.append("")

    lines.extend(["## 三、数据概览", ""])
    if charts:
        for chart in charts:
            series = chart.get("series") or []
            if not series:
                continue
            unit = chart.get("unit", "")
            first, last = series[0]["value"], series[-1]["value"]
            delta = last - first
            pct = (delta / first * 100) if first else 0
            trend = "上升" if pct > 2 else ("下降" if pct < -2 else "平稳")
            lines.append(f"### {chart['title']}")
            lines.append("")
            lines.append(
                f"- 期初：{_fmt_value(first, unit)} → 期末：{_fmt_value(last, unit)}（{trend}，变化 {pct:+.1f}%）"
            )
            lines.append("")
            lines.append("| 日期 | 数值 |")
            lines.append("| --- | --- |")
            for pt in series:
                lines.append(f"| {pt['date']} | {_fmt_value(pt['value'], unit)} |")
            lines.append("")
    else:
        lines.append("_暂无可用图表数据，请确认指标与查询结果。_")
        lines.append("")

    lines.extend(["## 四、关键发现", ""])
    if key_findings:
        for item in key_findings:
            lines.append(f"- {item}")
    else:
        lines.append("- 数据已拉取，建议结合图表进一步解读。")
    lines.append("")

    if risks:
        lines.extend(["## 五、风险提示", ""])
        for item in risks:
            lines.append(f"- {item}")
        lines.append("")

    lines.extend(["## 六、运营建议", ""])
    if suggestions:
        for item in suggestions:
            lines.append(f"- {item}")
    else:
        lines.append("- 持续跟踪核心指标波动，必要时拆分渠道/版本做下钻分析。")
        lines.append("- 若指标异常，同步产品与市场同学排查活动与版本影响。")
    lines.append("")
    lines.append("---")
    lines.append("*本报告面向运营同学，已隐藏 SQL 等技术细节。*")

    return "\n".join(lines)
