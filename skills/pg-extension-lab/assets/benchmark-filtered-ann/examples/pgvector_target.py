from __future__ import annotations

import time
from typing import Any

import psycopg

from targets._bulk import chunks, vector_literal
from targets._explain import summarize_explain
from targets.base import QueryResult


class PgvectorExampleTarget:
    name = "pgvector-example"

    def __init__(self, config: dict[str, Any]):
        self.cfg = config["pgvector_example"]
        self.conn = psycopg.connect(self.cfg["dsn"])
        self.conn.autocommit = True

    def setup(self) -> None:
        with self.conn.cursor() as cur:
            cur.execute(self.cfg.get("extension_sql", "CREATE EXTENSION IF NOT EXISTS vector"))
            cur.execute(f"DROP TABLE IF EXISTS {self.cfg['table']}")
            cur.execute(
                f"CREATE TABLE {self.cfg['table']} ("
                f"{self.cfg['id_column']} int PRIMARY KEY, "
                f"{self.cfg['vector_column']} vector({self.cfg.get('dims', 16)}), "
                f"{self.cfg['filter_column']} int)"
            )

    def insert_batch(self, rows: list[tuple[int, list[float], int]]) -> None:
        sql = (
            f"INSERT INTO {self.cfg['table']} "
            f"({self.cfg['id_column']}, {self.cfg['vector_column']}, {self.cfg['filter_column']}) "
            "VALUES (%s, %s, %s)"
        )
        with self.conn.cursor() as cur:
            for batch in chunks(rows, 1000):
                cur.executemany(sql, [(rid, vector_literal(vec), filt) for rid, vec, filt in batch])
            if self.cfg.get("index_sql"):
                cur.execute(self.cfg["index_sql"])
            cur.execute("ANALYZE " + self.cfg["table"])

    def set_search_knob(self, value: int) -> None:
        guc = self.cfg.get("search_guc")
        if guc:
            with self.conn.cursor() as cur:
                cur.execute(f"SET {guc} = %s", (value,))

    def force_index_scan(self, enabled: bool) -> None:
        with self.conn.cursor() as cur:
            cur.execute("SET enable_seqscan = %s", ("off" if enabled else "on",))

    def _query_sql(self, explain: bool = False) -> str:
        prefix = "EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) " if explain else ""
        return (
            prefix
            + f"SELECT {self.cfg['id_column']} FROM {self.cfg['table']} "
            + f"WHERE {self.cfg['filter_column']} = %s "
            + f"ORDER BY {self.cfg['vector_column']} {self.cfg['distance_operator']} %s "
            + "LIMIT %s"
        )

    def query_filtered(self, query: list[float], filter_value: int, k: int) -> QueryResult:
        started = time.perf_counter()
        with self.conn.cursor() as cur:
            cur.execute(self._query_sql(), (filter_value, vector_literal(query), k))
            ids = [int(row[0]) for row in cur.fetchall()]
        return QueryResult(ids=ids, elapsed_ms=(time.perf_counter() - started) * 1000.0, extra={})

    def explain_filtered(self, query: list[float], filter_value: int, k: int) -> dict[str, Any]:
        with self.conn.cursor() as cur:
            cur.execute(self._query_sql(explain=True), (filter_value, vector_literal(query), k))
            return summarize_explain(cur.fetchone()[0])

    def teardown(self) -> None:
        with self.conn.cursor() as cur:
            cur.execute(f"DROP TABLE IF EXISTS {self.cfg['table']}")

    def close(self) -> None:
        self.conn.close()


def create_target(config: dict[str, Any]):
    config["pgvector_example"]["dims"] = config["dataset"]["dims"]
    return PgvectorExampleTarget(config)

