"""项目级配置：路径、模型与 Mock 开关。"""

from __future__ import annotations

import os
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv

_ENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=_ENV_PATH)


@dataclass(frozen=True)
class Settings:
    """运行时配置。"""

    project_root: Path
    prompts_dir: Path
    mock_data_dir: Path
    use_mock_agents: bool
    openai_api_key: Optional[str]
    model_platform: str
    model_name: str
    temperature: float


def get_settings() -> Settings:
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
