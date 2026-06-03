"""
中间结果缓存：按阶段 + 输入摘要键；LRU 淘汰。

【学习】对应 LEARNING.md 阶段 3。解决重复 LLM 调用贵、慢的问题。
【学习】Python：
  - TypeVar("T")：泛型，让 memo 返回值类型与 compute() 一致
  - Callable[[], T]：无参可调用对象，常用 lambda: agent.run(...)
  - OrderedDict.move_to_end / popitem(last=False)：LRU 经典写法
"""

from __future__ import annotations

import hashlib
import json
from collections import OrderedDict
from typing import Any, Callable, Dict, Optional, Tuple, TypeVar

from config import Settings, get_settings

T = TypeVar("T")


def stable_hash(obj: Any) -> str:
    """
    确定性哈希（用于缓存键）。

    【学习】sort_keys=True 保证 dict 键顺序不同仍得到同一 hash；
    default=str 处理不可 JSON 序列化的对象（如 datetime）。
    """
    payload = json.dumps(obj, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class StageCache:
    """OWL 工作流中间态缓存；由 owl_workflow 在各阶段调用 memo。"""

    def __init__(self, settings: Optional[Settings] = None) -> None:
        self._settings = settings or get_settings()
        self._store: "OrderedDict[str, Any]" = OrderedDict()

    def memo(self, stage: str, inputs: Dict[str, Any], compute: Callable[[], T]) -> Tuple[T, bool]:
        """
        记忆化：命中缓存则不调 compute。

        返回 (value, cache_hit)。cache_hit=True 表示跳过 LLM/重计算。
        环境变量 WORKFLOW_CACHE=0 可关闭（见 config.workflow_cache_enabled）。
        """
        if not self._settings.workflow_cache_enabled:
            return compute(), False

        key = f"{stage}:{stable_hash(inputs)}"
        if key in self._store:
            self._store.move_to_end(key)  # 最近使用
            return self._store[key], True

        value = compute()
        self._store[key] = value
        while len(self._store) > self._settings.workflow_cache_max_entries:
            self._store.popitem(last=False)  # 淘汰最久未用
        return value, False
