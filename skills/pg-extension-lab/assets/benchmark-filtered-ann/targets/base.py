from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass
class QueryResult:
    ids: list[int]
    elapsed_ms: float
    extra: dict[str, Any]


class Target(Protocol):
    """Backend adapter contract.

    Filter semantics: a row passes when its filter column is below `filter_value`
    (`fixtures.synthetic.passes`). `query_filtered` returns the ids of the k nearest passing rows.
    Set `has_search_knob = False` when `set_search_knob` is a no-op; scenarios then run once
    instead of repeating identical cells for every knob value. Order results by L2 distance: the
    exact oracle does (`targets/_metric.py`). An optional `describe()` returns version facts
    (e.g. postgres_version, extension_version) that the runner copies into the artifact.

    Lifecycle: the runner creates one instance per run. For each fixture it calls `setup`,
    `insert_batch`, the scenarios, then `teardown`, on that same instance; `close` runs once at
    the end. Session state such as GUCs carries across fixtures, so apply knobs per cell.

    SQL adapters must plan every execution (psycopg 3: `conn.prepare_threshold = None`). EXPLAIN
    is always planned afresh, but an auto-prepared query can reuse a cached generic plan that
    ignores `force_index_scan`, so the plan label and the timed run would differ.
    """

    name: str
    has_search_knob: bool

    def setup(self) -> None: ...

    def insert_batch(self, rows: list[tuple[int, list[float], int]]) -> None: ...

    def set_search_knob(self, value: int) -> None: ...

    def force_index_scan(self, enabled: bool) -> None: ...

    def query_filtered(self, query: list[float], filter_value: int, k: int) -> QueryResult: ...

    def explain_filtered(self, query: list[float], filter_value: int, k: int) -> dict[str, Any]: ...

    def teardown(self) -> None: ...

    def close(self) -> None: ...
