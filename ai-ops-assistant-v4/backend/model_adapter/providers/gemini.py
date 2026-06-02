from __future__ import annotations
from typing import List
from model_adapter.providers.base import BaseProvider
from model_adapter.types import ChatMessage, ModelResponse

class GeminiProvider(BaseProvider):
    name = "gemini"
    def __init__(self, *, api_key: str, model_name: str):
        self.api_key, self.model_name = api_key, model_name
    def chat(self, messages, *, json_mode=False, temperature=0.2):
        import google.generativeai as genai
        genai.configure(api_key=self.api_key)
        model = genai.GenerativeModel(self.model_name)
        prompt = "\n".join(f"[{m.role}] {m.content}" for m in messages)
        if json_mode: prompt += "\n\n务必只输出合法 JSON。"
        resp = model.generate_content(prompt, generation_config={"temperature": temperature})
        return ModelResponse(content=(resp.text or "").strip(), provider=self.name, model=self.model_name, raw=resp)
