#!/usr/bin/env python3
"""AI 运营助手 V2：自然语言 → Intent → SQL 规划/优化 → Doris → Insight → Report。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import get_settings  # noqa: E402
from workflow.owl_workflow import OWLWorkflow  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="AI 运营助手 V2（Doris + OWL Workflow）")
    parser.add_argument(
        "question",
        nargs="?",
        default="最近7天用户流失情况如何？",
        help="自然语言问题",
    )
    parser.add_argument("--json", action="store_true", help="打印 JSON trace（不含长 markdown）")
    args = parser.parse_args()

    settings = get_settings()
    print("=== AI 运营助手 V2 ===")
    print(f"Doris Mock: {settings.doris_use_mock} | Agent Mock LLM: {settings.use_mock_agents}")
    print(f"Workflow cache: {settings.workflow_cache_enabled}")
    print(f"问题: {args.question}\n")

    result = OWLWorkflow().run(args.question)
    print(result["markdown_report"])

    if args.json:
        slim = {k: v for k, v in result.items() if k != "markdown_report"}
        slim["markdown_report_length"] = len(result.get("markdown_report", ""))
        print("\n--- JSON ---\n")
        print(json.dumps(slim, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
