"""阶段缓存（与 V2 相同）。"""

from __future__ import annotations

import hashlib
import json
from collections import OrderedDict
from typing import Any, Callable, Dict, Optional, Tuple, TypeVar

from config import Settings, get_settings

T = TypeVar("T")


def stable_hash(obj: Any) -> str:
    payload = json.dumps(obj, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class StageCache:
    def __init__(self, settings: Optional[Settings] = None) -> None:
        self._settings = settings or get_settings()
        self._store: "OrderedDict[str, Any]" = OrderedDict()

    def memo(self, stage: str, inputs: Dict[str, Any], compute: Callable[[], T]) -> Tuple[T, bool]:
        if not self._settings.workflow_cache_enabled:
            return compute(), False

        key = f"{stage}:{stable_hash(inputs)}"
        if key in self._store:
            self._store.move_to_end(key)
            return self._store[key], True

        value = compute()
        self._store[key] = value
        while len(self._store) > self._settings.workflow_cache_max_entries:
            self._store.popitem(last=False)
        return value, False
