"""Report Agent：V3 展示语义计划 + 编译 SQL + 结果。"""

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
        "metric_bundle": payload.get("metric_bundle"),
        "query_plan": payload.get("query_plan"),
        "sql_compiler": payload.get("sql_compiler"),
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
    sc = payload.get("sql_compiler") or {}
    qp = payload.get("query_plan") or {}
    mb = payload.get("metric_bundle") or {}
    qe = payload.get("query_execution") or {}

    sql = sc.get("sql", "—")
    lines = [
        "# 语义驱动数据分析报告（V3 · Mock）",
        "",
        f"**问题**：{q}",
        "",
        "## 指标体系",
        f"- 选中指标：`{mb.get('metric_ids', [])}`",
        "",
        "## 语义查询计划（QueryPlan）",
        "```json",
        json.dumps(qp, ensure_ascii=False, indent=2)[:3500],
        "```",
        "",
        "## 编译 SQL（仅来自 sql_compiler，不经 LLM 直接写终稿）",
        "```sql",
        sql if isinstance(sql, str) else str(sql),
        "```",
        "",
        "## 执行结果",
        f"- ok={qe.get('ok')} | rows={qe.get('row_count')} | engine=`{qe.get('engine')}`",
        "",
        "## 洞察",
        insight.get("summary", "—"),
        "",
        "### 发现",
    ]
    for x in insight.get("key_findings") or []:
        lines.append(f"- {x}")
    lines.extend(["", "### 风险", ""])
    for x in insight.get("risks") or []:
        lines.append(f"- {x}")
    lines.extend(["", "### 建议", ""])
    for x in insight.get("suggestions") or []:
        lines.append(f"- {x}")
    lines.append("\n---\n*指标与 SQL 模板见 `metrics/registry.yaml`。*")
    return "\n".join(lines)
