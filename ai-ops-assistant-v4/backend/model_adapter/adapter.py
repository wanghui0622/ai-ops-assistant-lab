from __future__ import annotations
import json, re
from typing import Any, Dict, Iterator, List, Optional
from config import Settings, get_settings
from model_adapter.providers.anthropic import AnthropicProvider
from model_adapter.providers.gemini import GeminiProvider
from model_adapter.providers.mock import MockProvider
from model_adapter.providers.openai import OpenAICompatibleProvider
from model_adapter.types import ChatMessage, ModelChunk, ModelResponse

def extract_json_object(text: str) -> Dict[str, Any]:
    text = text.strip()
    try: return json.loads(text)
    except json.JSONDecodeError: pass
    m = re.search(r"\{[\s\S]*\}", text)
    if not m: raise ValueError(f"无法解析 JSON：{text[:500]}")
    return json.loads(m.group(0))

class ModelAdapter:
    def __init__(self, settings: Optional[Settings] = None) -> None:
        self.settings = settings or get_settings()
        self._provider = self._build_provider()
    @property
    def provider_name(self) -> str: return self._provider.name
    @property
    def model_name(self) -> str: return self.settings.model_name
    def _build_provider(self):
        s = self.settings
        if s.use_mock_model or s.model_provider == "mock": return MockProvider(s.model_name)
        if s.model_provider == "anthropic" and s.anthropic_api_key: return AnthropicProvider(api_key=s.anthropic_api_key, model_name=s.model_name)
        if s.model_provider == "gemini" and s.gemini_api_key: return GeminiProvider(api_key=s.gemini_api_key, model_name=s.model_name)
        if s.model_provider == "deepseek" and s.deepseek_api_key:
            return OpenAICompatibleProvider(api_key=s.deepseek_api_key, model_name=s.model_name, base_url=s.deepseek_base_url, provider_label="deepseek")
        if s.openai_api_key: return OpenAICompatibleProvider(api_key=s.openai_api_key, model_name=s.model_name, provider_label="openai")
        return MockProvider(s.model_name)
    def chat(self, messages, *, json_mode=False, temperature=None):
        return self._provider.chat(messages, json_mode=json_mode, temperature=temperature if temperature is not None else self.settings.temperature)
    def chat_json(self, system_prompt, user_payload, *, temperature=None):
        hint = "\n\n务必只输出一个合法 JSON 对象，不要 Markdown 围栏或解释性文字。"
        messages = [ChatMessage(role="system", content=system_prompt + hint), ChatMessage(role="user", content=json.dumps(user_payload, ensure_ascii=False, indent=2))]
        return extract_json_object(self.chat(messages, json_mode=True, temperature=temperature).content)
    def stream(self, messages, *, temperature=None) -> Iterator[ModelChunk]:
        yield from self._provider.stream(messages, temperature=temperature if temperature is not None else self.settings.temperature)
