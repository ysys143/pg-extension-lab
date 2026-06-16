from __future__ import annotations

import time
from typing import Any

import psycopg

from ._bulk import chunks, vector_literal
from ._explain import summarize_explain
from .base import QueryResult


def render(sql: str, context: dict[str, Any]) -> str:
    return sql.format(**context)


def as_list(value: str | list[str] | None) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    return value


def bind_params(names: list[str], rid: int | None, query: list[float] | None, filter_value: int, k: int | None) -> tuple:
    values = {
        "id": rid,
        "query_vector": vector_literal(query or []),
        "filter_value": filter_value,
        "k": k,
    }
    return tuple(values[name] for name in names)


class PostgresSqlTarget:
    """Config-driven PostgreSQL target.

    The scenario contract is fixed, but all extension-specific SQL lives in the config.
    Default query parameters: filter_value, query_vector, k.
    Default insert parameters: id, query_vector, filter_value.
    """

    name = "postgres-sql"

    def __init__(self, config: dict[str, Any]):
        self.cfg = config["postgres_sql"]
        self.context = dict(self.cfg.get("context", {}))
        self.context.setdefault("dims", config["dataset"]["dims"])
        self.conn = psycopg.connect(self.cfg["dsn"])
        self.conn.autocommit = True

    def setup(self) -> None:
        with self.conn.cursor() as cur:
            for sql in as_list(self.cfg.get("setup_sql")):
                cur.execute(render(sql, self.context))

    def insert_batch(self, rows: list[tuple[int, list[float], int]]) -> None:
        insert_sql = render(self.cfg["insert_sql"], self.context)
        param_names = self.cfg.get("insert_params", ["id", "query_vector", "filter_value"])
        with self.conn.cursor() as cur:
            for batch in chunks(rows, int(self.cfg.get("batch_size", 1000))):
                cur.executemany(insert_sql, [bind_params(param_names, rid, vec, filt, None) for rid, vec, filt in batch])
            for sql in as_list(self.cfg.get("after_load_sql")):
                cur.execute(render(sql, self.context))

    def set_search_knob(self, value: int) -> None:
        sql = self.cfg.get("set_search_knob_sql")
        if sql:
            with self.conn.cursor() as cur:
                cur.execute(render(sql, self.context), (value,))

    def force_index_scan(self, enabled: bool) -> None:
        key = "force_plan_sql" if enabled else "clear_force_plan_sql"
        with self.conn.cursor() as cur:
            for sql in as_list(self.cfg.get(key)):
                cur.execute(render(sql, self.context))

    def query_filtered(self, query: list[float], filter_value: int, k: int) -> QueryResult:
        started = time.perf_counter()
        param_names = self.cfg.get("query_params", ["filter_value", "query_vector", "k"])
        with self.conn.cursor() as cur:
            cur.execute(render(self.cfg["query_sql"], self.context), bind_params(param_names, None, query, filter_value, k))
            ids = [int(row[0]) for row in cur.fetchall()]
        return QueryResult(ids=ids, elapsed_ms=(time.perf_counter() - started) * 1000.0, extra={})

    def explain_filtered(self, query: list[float], filter_value: int, k: int) -> dict[str, Any]:
        explain_sql = self.cfg.get("explain_sql")
        if not explain_sql:
            explain_sql = "EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) " + self.cfg["query_sql"]
        param_names = self.cfg.get("query_params", ["filter_value", "query_vector", "k"])
        with self.conn.cursor() as cur:
            cur.execute(render(explain_sql, self.context), bind_params(param_names, None, query, filter_value, k))
            return summarize_explain(cur.fetchone()[0])

    def teardown(self) -> None:
        with self.conn.cursor() as cur:
            for sql in as_list(self.cfg.get("teardown_sql")):
                cur.execute(render(sql, self.context))

    def close(self) -> None:
        self.conn.close()


def create_target(config: dict[str, Any]):
    return PostgresSqlTarget(config)
