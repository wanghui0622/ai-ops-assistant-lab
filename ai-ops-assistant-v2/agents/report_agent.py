"""Report Agent：汇总 SQL 各阶段与洞察 → Markdown。"""

from __future__ import annotations

import json
from typing import Any, Dict

from agents._camel_runtime import build_chat_agent, load_prompt_file
from camel.messages import BaseMessage
from config import get_settings


def run(payload: Dict[str, Any]) -> Dict[str, Any]:
    settings = get_settings()
    if settings.use_mock_agents:
        return {"markdown": _mock_markdown(payload), "format": "markdown"}

    system = load_prompt_file(settings, "report_prompt.txt")
    bundle = {
        "user_question": payload.get("user_question"),
        "understanding": payload.get("understanding"),
        "sql_plan": payload.get("sql_plan"),
        "sql_optimizer": payload.get("sql_optimizer"),
        "query_execution": payload.get("query_execution"),
        "insight": payload.get("insight"),
    }
    user_text = json.dumps(bundle, ensure_ascii=False, indent=2)
    agent = build_chat_agent(system, settings)
    msg = BaseMessage.make_user_message(role_name="User", content=user_text)
    response = agent.step(msg)
    content = response.msg.content
    if not isinstance(content, str):
        content = str(content)
    return {"markdown": content.strip(), "format": "markdown"}


def _mock_markdown(payload: Dict[str, Any]) -> str:
    q = payload.get("user_question", "")
    insight = payload.get("insight") or {}
    plan = payload.get("sql_plan") or {}
    opt = payload.get("sql_optimizer") or {}
    qe = payload.get("query_execution") or {}
    rows = qe.get("rows") or []
    expl = qe.get("explain") or {}

    lines = [
        "# 运营分析报告（V2 · Mock Agent）",
        "",
        f"**用户问题**：{q}",
        "",
        "## 执行链路",
        "- Intent → SQL Plan → SQLOptimizer → Doris Execute → Insight → Report",
        "",
        "## SQL 草案",
        "### Planner（初始 SQL）",
        "```sql",
        plan.get("initial_sql", "").strip(),
        "```",
        "### Optimizer（优化后）",
        "```sql",
        opt.get("optimized_sql", "").strip(),
        "```",
        "",
        "## EXPLAIN（摘要）",
        f"- engine: `{expl.get('engine', '')}`",
        "",
        "## 查询结果",
        f"- ok: {qe.get('ok')} | rows: {qe.get('row_count')} | engine: `{qe.get('engine')}`",
        "",
        "## 洞察摘要",
        "",
        insight.get("summary", "—"),
        "",
        "### 关键发现",
    ]
    for item in insight.get("key_findings") or []:
        lines.append(f"- {item}")
    if not insight.get("key_findings"):
        lines.append("- （无）")

    lines.extend(["", "### 风险", ""])
    for r in insight.get("risks") or []:
        lines.append(f"- {r}")

    lines.extend(["", "### 建议", ""])
    for s in insight.get("suggestions") or []:
        lines.append(f"- {s}")

    lines.extend(
        [
            "",
            "---",
            "*配置 `OPENAI_API_KEY` + Doris 连接串可切换生产模式；详见 `.env.example`。*",
        ]
    )
    return "\n".join(lines)
