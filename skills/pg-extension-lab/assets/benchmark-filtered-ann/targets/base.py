from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass
class QueryResult:
    ids: list[int]
    elapsed_ms: float
    extra: dict[str, Any]


class Target(Protocol):
    name: str

    def setup(self) -> None: ...

    def insert_batch(self, rows: list[tuple[int, list[float], int]]) -> None: ...

    def set_search_knob(self, value: int) -> None: ...

    def force_index_scan(self, enabled: bool) -> None: ...

    def query_filtered(self, query: list[float], filter_value: int, k: int) -> QueryResult: ...

    def explain_filtered(self, query: list[float], filter_value: int, k: int) -> dict[str, Any]: ...

    def teardown(self) -> None: ...

    def close(self) -> None: ...

