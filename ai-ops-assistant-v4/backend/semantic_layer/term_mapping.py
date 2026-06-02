"""业务名词 → 指标映射（语义层入口之一）。"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import yaml

from config import Settings, get_settings


class TermMetricMapper:
    """加载 term_map.yaml，支持简单子串命中（演示）。"""

    def __init__(self, terms: Dict[str, Any]) -> None:
        self._terms = terms

    def lookup_terms(self, text: str) -> Dict[str, Any]:
        """返回命中的业务词及候选指标。"""
        hits: List[str] = []
        metric_ids: Set[str] = set()
        lowered = text.lower()
        for term, payload in self._terms.items():
            if term.lower() in lowered or term in text:
                hits.append(term)
                mids = (payload or {}).get("metrics") or []
                metric_ids.update(mids)
        return {
            "matched_terms": hits,
            "candidate_metric_ids": sorted(metric_ids),
        }


_mapper: Optional[TermMetricMapper] = None


def load_term_map(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return dict(data.get("terms") or {})


def get_term_mapper(settings: Optional[Settings] = None) -> TermMetricMapper:
    global _mapper
    if _mapper is None:
        s = settings or get_settings()
        raw = load_term_map(s.semantic_layer_dir / "term_map.yaml")
        _mapper = TermMetricMapper(raw)
    return _mapper
