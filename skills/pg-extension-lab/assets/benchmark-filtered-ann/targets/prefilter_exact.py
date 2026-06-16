from __future__ import annotations

import math
import time
from typing import Any

from .base import QueryResult


class PrefilterExactTarget:
    name = "prefilter-exact"

    def __init__(self, config: dict[str, Any]):
        self.rows: list[tuple[int, list[float], int]] = []

    def setup(self) -> None:
        self.rows = []

    def insert_batch(self, rows: list[tuple[int, list[float], int]]) -> None:
        self.rows.extend(rows)

    def set_search_knob(self, value: int) -> None:
        return None

    def force_index_scan(self, enabled: bool) -> None:
        return None

    def query_filtered(self, query: list[float], filter_value: int, k: int) -> QueryResult:
        started = time.perf_counter()
        scored = []
        for rid, vec, filt in self.rows:
            if filt == filter_value:
                dist = math.sqrt(sum((a - b) ** 2 for a, b in zip(query, vec)))
                scored.append((dist, rid))
        scored.sort()
        return QueryResult([rid for _, rid in scored[:k]], (time.perf_counter() - started) * 1000.0, {})

    def explain_filtered(self, query: list[float], filter_value: int, k: int) -> dict[str, Any]:
        return {"pages_total": 0, "pages_hit": 0, "pages_read": 0, "plan_summary": "python-exact"}

    def teardown(self) -> None:
        self.rows = []

    def close(self) -> None:
        return None


def create_target(config: dict[str, Any]):
    return PrefilterExactTarget(config)

