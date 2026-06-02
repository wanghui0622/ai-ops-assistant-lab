from __future__ import annotations
from typing import List
from model_adapter.providers.base import BaseProvider
from model_adapter.types import ChatMessage, ModelResponse

class AnthropicProvider(BaseProvider):
    name = "anthropic"
    def __init__(self, *, api_key: str, model_name: str):
        self.api_key, self.model_name = api_key, model_name
    def chat(self, messages, *, json_mode=False, temperature=0.2):
        import anthropic
        system, conv = "", []
        for m in messages:
            if m.role == "system": system = m.content
            else: conv.append({"role": m.role, "content": m.content})
        if json_mode: system += "\n\n务必只输出合法 JSON。"
        client = anthropic.Anthropic(api_key=self.api_key)
        resp = client.messages.create(model=self.model_name, max_tokens=4096, system=system, messages=conv, temperature=temperature)
        content = "".join(getattr(b, "text", "") for b in resp.content)
        return ModelResponse(content=content.strip(), provider=self.name, model=self.model_name, raw=resp)
