"""
Camel ChatAgent 运行时：模型构建、JSON 解析与单轮对话。

【学习】本文件是 V1/V2/V3 接入真实 LLM 的公共层；Mock 模式下各 Agent 不调用此处。

Camel-AI 调用链（真实 LLM 时）：
  ModelFactory.create → ChatAgent → BaseMessage.make_user_message → agent.step
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, Optional

from camel.agents import ChatAgent
from camel.messages import BaseMessage
from camel.models import ModelFactory
from camel.types import ModelPlatformType, ModelType

from config import Settings, get_settings


def load_prompt_file(settings: Settings, relative_name: str) -> str:
    """从 prompts/ 目录读取系统提示词模板（纯文本）。"""
    path = settings.prompts_dir / relative_name
    return path.read_text(encoding="utf-8")


def extract_json_object(text: str) -> Dict[str, Any]:
    """
    从模型输出中提取 JSON 对象。

    【学习】LLM 常违反「只输出 JSON」：先 json.loads 全文，失败则用正则抠 {...}。
    生产环境可改用 Camel 的 structured output / function calling（本仓库为教学简化）。
    """
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
    """
    根据配置创建 ChatAgent（OpenAI 兼容平台）。

    【学习】ModelFactory.create 参数：
      - model_platform: 如 OPENAI
      - model_type: 枚举或字符串模型名
      - model_config_dict: 传给后端的 extra（如 temperature）
      - api_key: 来自 Settings
    """
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
    # system_message 在整个对话中固定，相当于「角色设定」
    return ChatAgent(system_message=system_prompt, model=model)


def _resolve_model_type(name: str) -> ModelType | str:
    """将 .env 中的模型名映射到 Camel ModelType；未知名则原样传给 API。"""
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
    """
    单轮 ChatAgent 调用，要求模型返回 JSON dict。

    【学习】agent.step(msg) 是「一步」推理（非多轮记忆）；多轮需自行维护 history。
    【学习】user_payload 序列化为 JSON 字符串作为用户消息，便于模型解析结构化输入。
    """
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
