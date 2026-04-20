"""Camel ChatAgent 运行时：模型构建与 JSON 解析。"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, Optional, Union

from camel.agents import ChatAgent
from camel.messages import BaseMessage
from camel.models import ModelFactory
from camel.types import ModelPlatformType, ModelType

from config import Settings, get_settings


def load_prompt_file(settings: Settings, relative_name: str) -> str:
    path = settings.prompts_dir / relative_name
    return path.read_text(encoding="utf-8")


def extract_json_object(text: str) -> Dict[str, Any]:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    m = re.search(r"\{[\s\S]*\}", text)
    if not m:
        raise ValueError(f"无法从模型输出解析 JSON：{text[:500]}")
    return json.loads(m.group(0))


def build_chat_agent(system_prompt: str, settings: Settings) -> ChatAgent:
    if settings.use_mock_agents:
        raise RuntimeError("mock 模式不应调用 build_chat_agent")
    model = ModelFactory.create(
        model_platform=ModelPlatformType.OPENAI,
        model_type=_resolve_model_type(settings.model_name),
        model_config_dict={
            "temperature": settings.temperature,
        },
        api_key=settings.openai_api_key,
    )
    return ChatAgent(system_message=system_prompt, model=model)


def _resolve_model_type(name: str) -> Union[ModelType, str]:
    mapping = {
        "gpt-4o-mini": ModelType.GPT_4O_MINI,
        "gpt-4o": ModelType.GPT_4O,
        "gpt-4-turbo": ModelType.GPT_4_TURBO,
        "gpt-3.5-turbo": ModelType.GPT_3_5_TURBO,
    }
    return mapping.get(name, name)


def run_json_agent(
    system_prompt: str,
    user_payload: Dict[str, Any],
    *,
    settings: Optional[Settings] = None,
) -> Dict[str, Any]:
    s = settings or get_settings()
    schema_hint = (
        "\n\n务必只输出一个合法 JSON 对象，不要 Markdown 代码围栏或解释性文字。"
    )
    user_text = json.dumps(user_payload, ensure_ascii=False, indent=2)
    agent = build_chat_agent(system_prompt + schema_hint, s)
    msg = BaseMessage.make_user_message(role_name="User", content=user_text)
    response = agent.step(msg)
    content = response.msg.content
    if not isinstance(content, str):
        content = str(content)
    return extract_json_object(content)
