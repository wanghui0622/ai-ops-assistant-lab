from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Iterator, List
from model_adapter.types import ChatMessage, ModelChunk, ModelResponse

class BaseProvider(ABC):
    name: str
    @abstractmethod
    def chat(self, messages: List[ChatMessage], *, json_mode: bool = False, temperature: float = 0.2) -> ModelResponse: ...
    def stream(self, messages: List[ChatMessage], *, temperature: float = 0.2) -> Iterator[ModelChunk]:
        resp = self.chat(messages, temperature=temperature)
        yield ModelChunk(content=resp.content, done=True)
