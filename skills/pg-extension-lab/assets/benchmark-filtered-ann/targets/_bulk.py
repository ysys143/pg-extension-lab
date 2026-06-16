from __future__ import annotations


def vector_literal(values: list[float]) -> str:
    return "[" + ",".join(f"{v:.8f}" for v in values) + "]"


def chunks(rows, size: int):
    for i in range(0, len(rows), size):
        yield rows[i : i + size]

