from __future__ import annotations

import random
from dataclasses import dataclass

BUCKETS = 100
FIXTURES = ("correlated", "uncorrelated")


@dataclass
class Workload:
    fixture: str
    queries: list[list[float]]
    far_queries: list[list[float]]


def passes(bucket: int, filter_value: int) -> bool:
    """The one filter predicate: a row passes when its bucket is below filter_value."""
    return bucket < filter_value


def filter_value_for_selectivity(selectivity: float) -> int:
    return max(1, min(BUCKETS, round(selectivity * BUCKETS)))


def representable_selectivity(selectivity: float) -> bool:
    scaled = selectivity * BUCKETS
    return 0 < selectivity <= 1 and abs(scaled - round(scaled)) < 1e-9


def pass_rate(rows: list[tuple[int, list[float], int]], filter_value: int) -> float:
    if not rows:
        return 0.0
    return sum(1 for _, _, bucket in rows if passes(bucket, filter_value)) / len(rows)


def make_dataset(rows: int, dims: int, seed: int, fixture: str) -> list[tuple[int, list[float], int]]:
    # Stratified: every row owns one slot of [0, rows), so each bucket holds rows/BUCKETS rows to
    # within one row and the realized pass rate equals the configured selectivity.
    rng = random.Random(seed)
    slots = list(range(rows))
    rng.shuffle(slots)
    out = []
    for rid in range(rows):
        if fixture == "correlated":
            base = (slots[rid] + rng.random()) / rows
            vec = [base + rng.gauss(0, 0.05) for _ in range(dims)]
            bucket = min(BUCKETS - 1, int(base * BUCKETS))
        else:
            vec = [rng.random() for _ in range(dims)]
            bucket = slots[rid] * BUCKETS // rows
        out.append((rid, vec, bucket))
    return out


def make_queries(
    count: int, dims: int, seed: int, fixture: str, base_range: tuple[float, float] = (0.0, 1.0)
) -> list[list[float]]:
    """Held-out queries drawn from the fixture's distribution, never copied from the dataset."""
    rng = random.Random(seed + 1)
    lo, hi = base_range
    out = []
    for _ in range(count):
        if fixture == "correlated":
            base = rng.uniform(lo, hi)
            out.append([base + rng.gauss(0, 0.05) for _ in range(dims)])
        else:
            out.append([rng.random() for _ in range(dims)])
    return out


def make_far_queries(count: int, dims: int, seed: int, fixture: str, max_selectivity: float) -> list[list[float]]:
    """Queries whose neighborhood fails every configured filter (correlated fixture only).

    Passing rows have base < max_selectivity; these queries sit in the upper half of the
    remaining range. On the uncorrelated fixture geometry carries no filter signal, so the same
    call yields ordinary queries and scenario D becomes its own control.
    """
    lo = (1.0 + max_selectivity) / 2
    return make_queries(count, dims, seed + 1, fixture, base_range=(lo, 1.0))


def make_workload(count: int, dims: int, seed: int, fixture: str, max_selectivity: float) -> Workload:
    return Workload(
        fixture=fixture,
        queries=make_queries(count, dims, seed, fixture),
        far_queries=make_far_queries(count, dims, seed, fixture, max_selectivity),
    )
