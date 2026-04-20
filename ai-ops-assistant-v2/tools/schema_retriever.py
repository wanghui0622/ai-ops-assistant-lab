"""Schema Awareness：合并语义目录 catalog.yaml 与 Doris DESCRIBE 结果。"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from config import Settings, get_settings
from tools.doris_client import DorisClient, get_doris_client


class SchemaRetriever:
    """提供表结构、字段说明与指标定义，供 SQL Agent 与用户问题对齐。"""

    def __init__(
        self,
        settings: Optional[Settings] = None,
        doris: Optional[DorisClient] = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._doris = doris or get_doris_client()
        self._catalog = self._load_catalog(self._settings.schema_dir / "catalog.yaml")

    def _load_catalog(self, path: Path) -> Dict[str, Any]:
        if not path.exists():
            return {"tables": {}, "metrics": {}}
        with path.open(encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def list_tables(self) -> List[str]:
        tables = self._catalog.get("tables") or {}
        return list(tables.keys())

    def get_metric_definitions(self) -> Dict[str, Any]:
        return dict(self._catalog.get("metrics") or {})

    def fetch_table_semantic(self, table: str) -> Dict[str, Any]:
        """catalog 中的表级元数据。"""
        t = (self._catalog.get("tables") or {}).get(table)
        if not t:
            return {"table": table, "found": False}
        return {"table": table, "found": True, **t}

    def fetch_schema(self, table: str) -> Dict[str, Any]:
        """DESCRIBE + 语义合并。"""
        physical = self._doris.fetch_schema(table)
        semantic = self.fetch_table_semantic(table)
        merged_columns: List[Dict[str, Any]] = []
        sem_cols = (semantic.get("columns") if semantic.get("found") else {}) or {}

        for row in physical.get("columns") or []:
            name = row.get("Field") or row.get("field")
            extra = sem_cols.get(name, {}) if isinstance(sem_cols, dict) else {}
            merged_columns.append(
                {
                    "name": name,
                    "physical": row,
                    "semantic": extra if isinstance(extra, dict) else {},
                }
            )

        return {
            "table": table,
            "physical_ok": physical.get("ok"),
            "semantic_found": semantic.get("found", False),
            "table_description": semantic.get("description") if semantic.get("found") else None,
            "partition_by": semantic.get("partition_by"),
            "columns": merged_columns,
            "describe_error": physical.get("error"),
        }

    def build_prompt_context(self, tables: List[str]) -> str:
        """注入 LLM 的拼接文本。"""
        lines: List[str] = []
        metrics = self.get_metric_definitions()
        if metrics:
            lines.append("### 指标定义（metrics）")
            for name, meta in metrics.items():
                desc = meta.get("definition") if isinstance(meta, dict) else meta
                lines.append(f"- **{name}**: {desc}")
        for t in tables:
            sch = self.fetch_schema(t)
            lines.append(f"\n### 表 `{t}`")
            if sch.get("table_description"):
                lines.append(f"- 描述: {sch['table_description']}")
            if sch.get("partition_by"):
                lines.append(f"- 分区字段: {sch['partition_by']}")
            lines.append("- 字段:")
            for c in sch.get("columns") or []:
                nm = c.get("name")
                sem = c.get("semantic") or {}
                desc = sem.get("description") if isinstance(sem, dict) else ""
                phys = c.get("physical") or {}
                dtype = phys.get("Type") or phys.get("type")
                lines.append(f"  - `{nm}` ({dtype}): {desc}")
        return "\n".join(lines)


def infer_tables_from_intent(intent: Dict[str, Any]) -> List[str]:
    """由意图推断候选表（可替换为向量检索）。"""
    name = intent.get("intent", "")
    if name == "revenue_analysis":
        return ["order_daily_summary"]
    if name == "churn_analysis":
        return ["game_daily_metrics"]
    return ["game_daily_metrics"]
