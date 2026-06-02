from __future__ import annotations
from typing import List, Optional
from model_adapter.providers.base import BaseProvider
from model_adapter.types import ChatMessage, ModelResponse

class OpenAICompatibleProvider(BaseProvider):
    def __init__(self, *, api_key: str, model_name: str, base_url: Optional[str] = None, provider_label: str = "openai"):
        self.api_key, self.model_name, self.base_url, self.name = api_key, model_name, base_url, provider_label
    def chat(self, messages, *, json_mode=False, temperature=0.2):
        from openai import OpenAI
        client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        payload = [{"role": m.role, "content": m.content} for m in messages]
        kwargs = {"model": self.model_name, "messages": payload, "temperature": temperature}
        if json_mode: kwargs["response_format"] = {"type": "json_object"}
        resp = client.chat.completions.create(**kwargs)
        content = resp.choices[0].message.content or ""
        usage = {}
        if resp.usage: usage = {"prompt_tokens": resp.usage.prompt_tokens, "completion_tokens": resp.usage.completion_tokens}
        return ModelResponse(content=content, provider=self.name, model=self.model_name, usage=usage, raw=resp)
