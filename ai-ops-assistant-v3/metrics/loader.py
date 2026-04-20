"""指标解析：加载 registry.yaml，校验 ID，提供查询接口。"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from config import Settings, get_settings


class MetricRegistry:
    """内存中的指标注册表。"""

    def __init__(self, raw: Dict[str, Any]) -> None:
        self._metrics: Dict[str, Dict[str, Any]] = dict(raw.get("metrics") or {})

    def list_ids(self) -> List[str]:
        return sorted(self._metrics.keys())

    def get(self, metric_id: str) -> Optional[Dict[str, Any]]:
        return self._metrics.get(metric_id)

    def validate_ids(self, ids: List[str]) -> Dict[str, Any]:
        unknown = [i for i in ids if i not in self._metrics]
        return {"valid": not unknown, "unknown_ids": unknown}

    def as_prompt_summary(self) -> str:
        """供 Metric Agent 只从白名单选 ID。"""
        lines: List[str] = []
        for mid, m in sorted(self._metrics.items()):
            lines.append(
                f"- `{mid}`: {m.get('description', '')} "
                f"[表:{m.get('source_table')}] "
                f"维度:{','.join(m.get('dimensions') or [])}"
            )
        return "\n".join(lines)


_registry: Optional[MetricRegistry] = None


def load_registry_file(path: Path) -> Dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def get_metric_registry(settings: Optional[Settings] = None) -> MetricRegistry:
    global _registry
    if _registry is None:
        s = settings or get_settings()
        data = load_registry_file(s.metrics_dir / "registry.yaml")
        _registry = MetricRegistry(data)
    return _registry


def reload_registry(settings: Optional[Settings] = None) -> MetricRegistry:
    global _registry
    _registry = None
    return get_metric_registry(settings)
