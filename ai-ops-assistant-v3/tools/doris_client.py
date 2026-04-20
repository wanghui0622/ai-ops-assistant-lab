"""Doris 客户端（Mock 支持 SELECT ... AS 别名映射）。"""

from __future__ import annotations

import copy
import re
from typing import Any, Dict, List, Optional

from config import Settings, get_settings
from mock_data import game_data, order_data

try:
    import pymysql
    from pymysql.cursors import DictCursor
except ImportError:
    pymysql = None  # type: ignore
    DictCursor = None  # type: ignore


_KNOWN_TABLES = frozenset({"game_daily_metrics", "order_daily_summary"})


def _extract_limit(sql: str) -> Optional[int]:
    m = re.search(r"\bLIMIT\s+(\d+)\s*(?:;)?\s*$", sql.strip(), re.I | re.M)
    if m:
        return int(m.group(1))
    m2 = re.search(r"\bLIMIT\s+(\d+)\b", sql, re.I)
    if m2:
        return int(m2.group(1))
    return None


def _extract_primary_from_table(sql: str) -> Optional[str]:
    lower = sql.lower()
    idx = lower.rfind(" from ")
    if idx == -1:
        return None
    rest = sql[idx + 6 :].strip().split()[0].strip(";`\"'")
    return rest.strip("`") or None


_AS_PATTERN = re.compile(
    r"`([\w]+)`\s+AS\s+`([\w]+)`",
    re.IGNORECASE,
)


def _apply_select_aliases(rows: List[Dict[str, Any]], sql: str) -> List[Dict[str, Any]]:
    """将语义层编译 SQL 中的 `col` AS `metric_id` 映射进结果行（便于 Mock）。"""
    mappings = _AS_PATTERN.findall(sql.upper())  # wrong - pattern is case insensitive for AS
    mappings = _AS_PATTERN.findall(sql)
    if not mappings:
        return rows
    out: List[Dict[str, Any]] = []
    for row in rows:
        nr = dict(row)
        for phys, alias in mappings:
            if alias in nr:
                continue
            if phys in nr:
                nr[alias] = nr[phys]
        out.append(nr)
    return out


class DorisClient:
    def __init__(self, settings: Optional[Settings] = None) -> None:
        self._settings = settings or get_settings()

    def execute_sql(
        self,
        sql: str,
        *,
        max_rows: Optional[int] = None,
    ) -> Dict[str, Any]:
        lim = max_rows if max_rows is not None else self._settings.sql_row_limit_default
        sql = sql.strip().rstrip(";")

        if self._settings.doris_use_mock or pymysql is None:
            return self._execute_mock(sql, lim)

        err: Optional[str] = None
        rows: List[Dict[str, Any]] = []
        columns: List[str] = []
        try:
            conn = self._connect()
            try:
                with conn.cursor(DictCursor) as cur:  # type: ignore[misc]
                    cur.execute(sql)
                    if cur.description:
                        columns = [d[0] for d in cur.description]
                    rows = list(cur.fetchmany(lim))
            finally:
                conn.close()
        except Exception as e:  # noqa: BLE001
            err = str(e)

        return {
            "ok": err is None,
            "sql": sql,
            "columns": columns,
            "rows": rows,
            "row_count": len(rows),
            "max_rows_applied": lim,
            "error": err,
            "engine": "doris",
        }

    def fetch_schema(self, table: str) -> Dict[str, Any]:
        table = table.strip("`")
        if self._settings.doris_use_mock or pymysql is None:
            return self._mock_schema(table)

        rows: List[Dict[str, Any]] = []
        err: Optional[str] = None
        try:
            conn = self._connect()
            try:
                with conn.cursor(DictCursor) as cur:  # type: ignore[misc]
                    cur.execute(f"DESCRIBE `{table}`")
                    rows = list(cur.fetchall())
            finally:
                conn.close()
        except Exception as e:  # noqa: BLE001
            err = str(e)

        return {
            "ok": err is None,
            "table": table,
            "columns": rows,
            "error": err,
            "engine": "doris",
        }

    def explain_sql(self, sql: str) -> Dict[str, Any]:
        sql = sql.strip().rstrip(";")
        if self._settings.doris_use_mock or pymysql is None:
            return self._mock_explain(sql)

        expl = f"EXPLAIN {sql}"
        if self._settings.sql_explain_verbose:
            expl = f"EXPLAIN VERBOSE {sql}"

        plan_rows: List[Any] = []
        err: Optional[str] = None
        try:
            conn = self._connect()
            try:
                with conn.cursor(DictCursor) as cur:  # type: ignore[misc]
                    cur.execute(expl)
                    plan_rows = list(cur.fetchall())
            finally:
                conn.close()
        except Exception as e:  # noqa: BLE001
            err = str(e)

        return {
            "ok": err is None,
            "sql": sql,
            "explain_statement": expl,
            "plan_rows": plan_rows,
            "error": err,
            "engine": "doris",
        }

    def _connect(self):
        if pymysql is None:
            raise RuntimeError("未安装 pymysql")
        s = self._settings
        return pymysql.connect(
            host=s.doris_host,
            port=s.doris_port,
            user=s.doris_user or "",
            password=s.doris_password or "",
            database=s.doris_database or "",
            charset="utf8mb4",
            connect_timeout=30,
            read_timeout=120,
        )

    def _execute_mock(self, sql: str, lim: int) -> Dict[str, Any]:
        table = _extract_primary_from_table(sql)
        rows: List[Dict[str, Any]] = []
        if table == "game_daily_metrics":
            rows = [copy.deepcopy(r) for r in game_data.table_rows(table)]
        elif table == "order_daily_summary":
            rows = [copy.deepcopy(r) for r in order_data.table_rows(table)]
        elif table in _KNOWN_TABLES:
            rows = []

        rows = _apply_select_aliases(rows, sql)

        limit_val = _extract_limit(sql)
        cap = min(lim, limit_val) if limit_val is not None else lim
        rows = rows[:cap]

        columns = list(rows[0].keys()) if rows else []
        return {
            "ok": True,
            "sql": sql,
            "columns": columns,
            "rows": rows,
            "row_count": len(rows),
            "max_rows_applied": cap,
            "error": None,
            "engine": "mock_doris",
        }

    def _mock_schema(self, table: str) -> Dict[str, Any]:
        if table == "game_daily_metrics":
            cols = [
                {"Field": "dt", "Type": "date", "Null": "YES", "Key": "true"},
                {"Field": "dau", "Type": "bigint", "Null": "YES", "Key": "false"},
                {"Field": "new_users", "Type": "bigint", "Null": "YES", "Key": "false"},
                {"Field": "retention_d1_pct", "Type": "double", "Null": "YES", "Key": "false"},
                {"Field": "churn_users_7d_window", "Type": "bigint", "Null": "YES", "Key": "false"},
            ]
        elif table == "order_daily_summary":
            cols = [
                {"Field": "dt", "Type": "date", "Null": "YES", "Key": "true"},
                {"Field": "orders", "Type": "bigint", "Null": "YES", "Key": "false"},
                {"Field": "gmv_cny", "Type": "double", "Null": "YES", "Key": "false"},
            ]
        else:
            cols = []
        return {
            "ok": bool(cols),
            "table": table,
            "columns": cols,
            "error": None if cols else f"未知表（Mock）：{table}",
            "engine": "mock_doris",
        }

    def _mock_explain(self, sql: str) -> Dict[str, Any]:
        tbl = _extract_primary_from_table(sql) or "unknown"
        nodes = [
            {"operator": "OLAP_SCAN", "table": tbl, "detail": "partition prune (mock)"},
            {"operator": "PROJECT", "detail": "metric aliases from semantic compiler"},
        ]
        return {
            "ok": True,
            "sql": sql,
            "explain_statement": f"EXPLAIN {sql}",
            "plan_rows": nodes,
            "error": None,
            "engine": "mock_doris",
        }


_client: Optional[DorisClient] = None


def get_doris_client() -> DorisClient:
    global _client
    if _client is None:
        _client = DorisClient()
    return _client
