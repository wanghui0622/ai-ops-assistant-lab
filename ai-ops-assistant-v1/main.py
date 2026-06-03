#!/usr/bin/env python3
"""
AI 运营助手 CLI 入口。

【学习】阅读顺序：本文件 → workflow/ops_workflow.py → agents/_camel_runtime.py
【学习】Python：argparse 子命令、if __name__ == "__main__" 脚本入口约定
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# 【学习】目录名含连字符（ai-ops-assistant-v1），不能 pip install 成包名时，
# 用 sys.path 把项目根加入模块搜索路径，才能 `from config import ...`
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import get_settings  # noqa: E402
from workflow.ops_workflow import OpsWorkflow  # noqa: E402


def main() -> None:
    # 【学习】argparse：nargs="?" 表示位置参数可选；action="store_true" 为布尔开关
    #  官网：https://docs.python.org/zh-cn/3.10/library/argparse.html
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
        help="同时打印完整 trace（JSON，不含长报告正文）",
    )
    args = parser.parse_args()

    settings = get_settings()
    print("=== AI 运营助手 ===")
    print(f"Mock Agent: {settings.use_mock_agents}")
    print(f"问题: {args.question}")
    print()

    # 【学习】编排层：业务逻辑在 OpsWorkflow.run，main 只负责 IO
    wf = OpsWorkflow()
    result = wf.run(args.question)

    print(result["markdown_report"])
    print()
    if args.json:
        # trace 含各 Agent 中间结果，便于调试；报告正文可能很长故排除
        safe = {
            k: v
            for k, v in result.items()
            if k != "markdown_report"
        }
        # ensure_ascii=False 保留中文；indent 便于人读
        print(json.dumps(safe, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
