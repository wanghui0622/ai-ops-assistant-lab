#!/usr/bin/env python3
"""AI 运营助手 V3：语义层 + 指标体系（指标驱动，不经 LLM 直连 SQL）。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import get_settings  # noqa: E402
from workflow.owl_workflow import OWLSemanticWorkflow  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="AI 运营助手 V3（Semantic + Metrics）")
    parser.add_argument(
        "question",
        nargs="?",
        default="最近7天用户流失与留存怎么样？",
        help="业务问题（自然语言）",
    )
    parser.add_argument("--json", action="store_true", help="输出结构化 trace（不含全文报告）")
    args = parser.parse_args()

    settings = get_settings()
    print("=== AI 运营助手 V3 · 语义层 + 指标体系 ===")
    print(f"Doris Mock: {settings.doris_use_mock} | Agent Mock LLM: {settings.use_mock_agents}")
    print(f"问题: {args.question}\n")

    result = OWLSemanticWorkflow().run(args.question)
    print(result["markdown_report"])

    if args.json:
        slim = {k: v for k, v in result.items() if k != "markdown_report"}
        print("\n--- JSON ---\n")
        print(json.dumps(slim, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
