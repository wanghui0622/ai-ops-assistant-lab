"""Report Agent：聚合上下文 → Markdown 报告（Camel 或模板兜底）。"""

from __future__ import annotations

import json
from typing import Any, Dict

from agents._camel_runtime import load_prompt_file, build_chat_agent
from camel.messages import BaseMessage
from config import get_settings


def run(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    输入:
        user_question, understanding, sql_bundle, query_tool_result, analysis

    输出:
        markdown: 完整报告正文
        format: "markdown"
    """
    settings = get_settings()
    if settings.use_mock_agents:
        md = _mock_markdown(payload)
        return {"markdown": md, "format": "markdown"}

    system = load_prompt_file(settings, "report_prompt.txt")
    bundle = {
        "user_question": payload.get("user_question"),
        "understanding": payload.get("understanding"),
        "sql_bundle": payload.get("sql_bundle"),
        "query_tool_result": payload.get("query_tool_result"),
        "analysis": payload.get("analysis"),
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
    """无 LLM 时的可读报告。"""
    q = payload.get("user_question", "")
    analysis = payload.get("analysis") or {}
    sql_b = payload.get("sql_bundle") or {}
    tool = payload.get("query_tool_result") or {}
    qr = (tool.get("query_result") or {}).get("rows") or []

    lines = [
        "# 运营分析简报（Mock 模式）",
        "",
        f"**用户问题**：{q}",
        "",
        "## 数据概况",
        f"- 返回行数：{len(qr)}",
        "",
        "## 关键发现",
    ]
    for item in analysis.get("key_findings") or []:
        lines.append(f"- {item}")
    if not analysis.get("key_findings"):
        lines.append("- （无）")
    lines.extend(["", "## 摘要", "", analysis.get("summary", "—"), "", "## 风险与波动"])
    for r in analysis.get("risks") or []:
        lines.append(f"- {r}")
    lines.extend(["", "## 建议"])
    for s in analysis.get("suggestions") or []:
        lines.append(f"- {s}")
    lines.extend(
        [
            "",
            "## 附录：SQL 草案",
            "",
            "```sql",
            sql_b.get("sql", "").strip(),
            "```",
            "",
            "*本报告由 AI 运营助手 MVP 生成；配置 `OPENAI_API_KEY` 并关闭 `USE_MOCK_AGENTS` 可启用大模型撰写。*",
        ]
    )
    return "\n".join(lines)
