from __future__ import annotations

import random


def make_dataset(rows: int, dims: int, seed: int, correlated: bool) -> list[tuple[int, list[float], int]]:
    rng = random.Random(seed)
    out = []
    for rid in range(rows):
        base = rng.random()
        vec = [base + rng.gauss(0, 0.05) for _ in range(dims)] if correlated else [rng.random() for _ in range(dims)]
        bucket = int(max(0, min(99, base * 100))) if correlated else rng.randrange(100)
        out.append((rid, vec, bucket))
    return out


def make_queries(rows: list[tuple[int, list[float], int]], count: int, seed: int) -> list[list[float]]:
    rng = random.Random(seed + 1)
    return [list(rng.choice(rows)[1]) for _ in range(count)]


def filter_value_for_selectivity(selectivity: float) -> int:
    return int(max(0, min(99, selectivity * 100)))

