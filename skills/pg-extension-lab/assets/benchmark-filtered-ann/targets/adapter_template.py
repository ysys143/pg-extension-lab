from __future__ import annotations

from typing import Any

from .base import QueryResult


class MyExtensionTarget:
    name = "my-extension"

    def __init__(self, config: dict[str, Any]):
        self.config = config

    def setup(self) -> None:
        raise NotImplementedError

    def insert_batch(self, rows: list[tuple[int, list[float], int]]) -> None:
        raise NotImplementedError

    def set_search_knob(self, value: int) -> None:
        raise NotImplementedError

    def force_index_scan(self, enabled: bool) -> None:
        raise NotImplementedError

    def query_filtered(self, query: list[float], filter_value: int, k: int) -> QueryResult:
        raise NotImplementedError

    def explain_filtered(self, query: list[float], filter_value: int, k: int) -> dict[str, Any]:
        raise NotImplementedError

    def teardown(self) -> None:
        raise NotImplementedError

    def close(self) -> None:
        raise NotImplementedError


def create_target(config: dict[str, Any]):
    return MyExtensionTarget(config)

