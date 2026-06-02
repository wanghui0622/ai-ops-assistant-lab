"""V4 配置。"""

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
    skills_dir: Path
    hooks_config: Path
    audit_log_path: Path
    workflows_dir: Path
    model_provider: str
    model_name: str
    temperature: float
    use_mock_model: bool
    openai_api_key: Optional[str]
    anthropic_api_key: Optional[str]
    deepseek_api_key: Optional[str]
    deepseek_base_url: str
    gemini_api_key: Optional[str]
    doris_use_mock: bool
    doris_host: Optional[str]
    doris_port: int
    doris_user: Optional[str]
    doris_password: Optional[str]
    doris_database: Optional[str]
    sql_row_limit_default: int
    hook_audit_sink: str


def get_settings() -> Settings:
    root = Path(__file__).resolve().parent
    provider = os.getenv("MODEL_PROVIDER", "mock").lower()
    openai_key = os.getenv("OPENAI_API_KEY") or os.getenv("CAMEL_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    deepseek_key = os.getenv("DEEPSEEK_API_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY")
    use_mock = provider == "mock" or not any([openai_key, anthropic_key, deepseek_key, gemini_key])
    host = os.getenv("DORIS_HOST") or os.getenv("DORIS_FE_HOST")
    use_mock_doris = os.getenv("DORIS_USE_MOCK", "").lower() in ("1", "true", "yes") or not host
    return Settings(
        project_root=root,
        prompts_dir=root / "prompts",
        mock_data_dir=root / "mock_data",
        metrics_dir=root / "metrics",
        semantic_layer_dir=root / "semantic_layer",
        skills_dir=root / "skill_engine" / "skills",
        hooks_config=root / "hook_engine" / "hooks.yaml",
        audit_log_path=root / "logs" / "audit.jsonl",
        workflows_dir=root / "runtime" / "workflows",
        model_provider="mock" if use_mock else provider,
        model_name=os.getenv("MODEL_NAME", os.getenv("CAMEL_MODEL_NAME", "gpt-4o-mini")),
        temperature=float(os.getenv("CAMEL_TEMPERATURE", "0.2")),
        use_mock_model=use_mock,
        openai_api_key=openai_key,
        anthropic_api_key=anthropic_key,
        deepseek_api_key=deepseek_key,
        deepseek_base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
        gemini_api_key=gemini_key,
        doris_use_mock=use_mock_doris,
        doris_host=host,
        doris_port=int(os.getenv("DORIS_QUERY_PORT", os.getenv("DORIS_PORT", "9030"))),
        doris_user=os.getenv("DORIS_USER"),
        doris_password=os.getenv("DORIS_PASSWORD"),
        doris_database=os.getenv("DORIS_DATABASE") or os.getenv("DORIS_DB"),
        sql_row_limit_default=int(os.getenv("SQL_ROW_LIMIT", "5000")),
        hook_audit_sink=os.getenv("HOOK_AUDIT_SINK", "file"),
    )
