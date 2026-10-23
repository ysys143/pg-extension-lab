"""Deterministic model of post-filtering with a candidate budget. Not an ANN index.

Ranks every row by exact distance, keeps the `search_value` nearest candidates regardless of the
filter, then filters and returns the first k passing ids. This isolates the failure a
post-filtered index shows: when passing rows sit far from the query, a small candidate budget
returns few or none of them. Recall rises with the budget and falls with selectivity and with
filter/geometry correlation, so the scenarios produce real curves without a database.
"""

from __future__ import annotations

import time
from typing import Any

from fixtures.synthetic import passes

from ._metric import l2
from .base import QueryResult


class PostfilterTopNTarget:
    name = "postfilter-topn"
    has_search_knob = True

    def __init__(self, config: dict[str, Any]):
        self.rows: list[tuple[int, list[float], int]] = []
        self.candidates = 0

    def setup(self) -> None:
        self.rows = []

    def insert_batch(self, rows: list[tuple[int, list[float], int]]) -> None:
        self.rows.extend(rows)

    def set_search_knob(self, value: int) -> None:
        self.candidates = int(value)

    def force_index_scan(self, enabled: bool) -> None:
        return None

    def query_filtered(self, query: list[float], filter_value: int, k: int) -> QueryResult:
        started = time.perf_counter()
        ranked = sorted((l2(query, vec), rid, bucket) for rid, vec, bucket in self.rows)
        ids = [rid for _, rid, bucket in ranked[: self.candidates] if passes(bucket, filter_value)][:k]
        return QueryResult(ids, (time.perf_counter() - started) * 1000.0, {"candidates": self.candidates})

    def explain_filtered(self, query: list[float], filter_value: int, k: int) -> dict[str, Any]:
        return {"pages_total": 0, "pages_hit": 0, "pages_read": 0, "plan_summary": f"python-postfilter-top{self.candidates}"}

    def teardown(self) -> None:
        self.rows = []

    def close(self) -> None:
        return None


def create_target(config: dict[str, Any]):
    return PostfilterTopNTarget(config)
