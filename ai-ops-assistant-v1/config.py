"""
项目级配置：路径、模型与 Mock 开关。

【学习】Python：@dataclass(frozen=True) 生成不可变配置对象，避免运行中被误改
【学习】工程：集中 get_settings()，各模块不直接读 os.environ，便于测试注入
"""

from __future__ import annotations

import os
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv

# 【学习】python-dotenv：启动时加载 .env 到环境变量（不覆盖已存在的系统变量）
_ENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=_ENV_PATH)


@dataclass(frozen=True)
class Settings:
    """运行时配置（一次构建、全程只读）。"""

    project_root: Path
    prompts_dir: Path
    mock_data_dir: Path
    use_mock_agents: bool  # True = 不调 OpenAI，走 agents/* 里的 _mock_* 函数
    openai_api_key: Optional[str]
    model_platform: str
    model_name: str
    temperature: float  # LLM 采样温度，分析类任务宜偏低（0.1～0.3）


def get_settings() -> Settings:
    """
    从环境变量构建 Settings。

    【学习】Mock 策略：无 API Key 时强制 Mock，保证 clone 仓库即可演示。
    """
    root = Path(__file__).resolve().parent
    key = os.getenv("OPENAI_API_KEY") or os.getenv("CAMEL_API_KEY")
    use_mock = os.getenv("USE_MOCK_AGENTS", "").lower() in ("1", "true", "yes")
    if not key:
        use_mock = True
    return Settings(
        project_root=root,
        prompts_dir=root / "prompts",
        mock_data_dir=root / "mock_data",
        use_mock_agents=use_mock,
        openai_api_key=key,
        model_platform=os.getenv("CAMEL_MODEL_PLATFORM", "openai"),
        model_name=os.getenv("CAMEL_MODEL_NAME", "gpt-4o-mini"),
        temperature=float(os.getenv("CAMEL_TEMPERATURE", "0.2")),
    )
