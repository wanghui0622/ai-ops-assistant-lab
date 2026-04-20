#!/usr/bin/env python3
"""AI 运营助手入口：一键跑通「自然语言 → SQL → 分析 → Markdown 报告」。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# 包路径：目录名含连字符，作为脚本运行时加入项目根
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import get_settings  # noqa: E402
from workflow.ops_workflow import OpsWorkflow  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="AI 运营助手 MVP")
    parser.add_argument(
        "question",
        nargs="?",
        default="最近7天用户流失情况如何？",
        help="自然语言业务问题（默认演示流失）",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="同时打印完整 trace（JSON）",
    )
    args = parser.parse_args()

    settings = get_settings()
    print("=== AI 运营助手 ===")
    print(f"Mock Agent: {settings.use_mock_agents}")
    print(f"问题: {args.question}")
    print()

    wf = OpsWorkflow()
    result = wf.run(args.question)

    print(result["markdown_report"])
    print()
    if args.json:
        # trace 可能很大，默认仅开关输出
        safe = {
            k: v
            for k, v in result.items()
            if k != "markdown_report"
        }
        print(json.dumps(safe, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
