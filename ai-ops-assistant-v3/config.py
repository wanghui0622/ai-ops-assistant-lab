"""V3 配置：语义层目录、指标库、Doris、缓存。"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

_ENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=_ENV_PATH)


@dataclass(frozen=True)
class Settings:
    project_root: Path
    prompts_dir: Path
    mock_data_dir: Path
    metrics_dir: Path
    semantic_layer_dir: Path

    use_mock_agents: bool
    openai_api_key: Optional[str]
    model_name: str
    temperature: float

    doris_use_mock: bool
    doris_host: Optional[str]
    doris_port: int
    doris_user: Optional[str]
    doris_password: Optional[str]
    doris_database: Optional[str]

    sql_row_limit_default: int
    sql_explain_verbose: bool

    workflow_cache_enabled: bool
    workflow_cache_max_entries: int


def get_settings() -> Settings:
    root = Path(__file__).resolve().parent
    key = os.getenv("OPENAI_API_KEY") or os.getenv("CAMEL_API_KEY")
    use_mock_llm = os.getenv("USE_MOCK_AGENTS", "").lower() in ("1", "true", "yes")
    if not key:
        use_mock_llm = True

    host = os.getenv("DORIS_HOST") or os.getenv("DORIS_FE_HOST")
    use_mock_doris = os.getenv("DORIS_USE_MOCK", "").lower() in ("1", "true", "yes")
    if not host:
        use_mock_doris = True

    return Settings(
        project_root=root,
        prompts_dir=root / "prompts",
        mock_data_dir=root / "mock_data",
        metrics_dir=root / "metrics",
        semantic_layer_dir=root / "semantic_layer",
        use_mock_agents=use_mock_llm,
        openai_api_key=key,
        model_name=os.getenv("CAMEL_MODEL_NAME", "gpt-4o-mini"),
        temperature=float(os.getenv("CAMEL_TEMPERATURE", "0.2")),
        doris_use_mock=use_mock_doris,
        doris_host=host,
        doris_port=int(os.getenv("DORIS_QUERY_PORT", os.getenv("DORIS_PORT", "9030"))),
        doris_user=os.getenv("DORIS_USER"),
        doris_password=os.getenv("DORIS_PASSWORD"),
        doris_database=os.getenv("DORIS_DATABASE") or os.getenv("DORIS_DB"),
        sql_row_limit_default=int(os.getenv("SQL_ROW_LIMIT", "5000")),
        sql_explain_verbose=os.getenv("SQL_EXPLAIN_VERBOSE", "").lower()
        in ("1", "true", "yes"),
        workflow_cache_enabled=os.getenv("WORKFLOW_CACHE", "1").lower()
        not in ("0", "false", "no"),
        workflow_cache_max_entries=int(os.getenv("WORKFLOW_CACHE_MAX", "256")),
    )
