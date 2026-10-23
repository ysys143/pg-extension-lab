from __future__ import annotations

import random
from dataclasses import dataclass, field

BUCKETS = 100
FIXTURES = ("correlated", "uncorrelated")


@dataclass
class Workload:
    fixture: str
    queries: list[list[float]]
    far_queries: list[list[float]]
    # Ground truth keyed by (query set, filter_value, k), shared by every target and scenario.
    truth: dict = field(default_factory=dict)


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
    """Both fixtures share the same vectors; only the bucket assignment differs, so a
    correlated-vs-uncorrelated gap measures the filter/geometry correlation and nothing else.

    Stratified: every row owns one slot of [0, rows), so each bucket holds rows/BUCKETS rows to
    within one row and the realized pass rate equals the configured selectivity.
    """
    rng = random.Random(seed)
    slots = list(range(rows))
    rng.shuffle(slots)
    bases = [(slots[rid] + rng.random()) / rows for rid in range(rows)]
    vectors = [[base + rng.gauss(0, 0.05) for _ in range(dims)] for base in bases]
    if fixture == "correlated":
        # The bucket follows the vector's position along the data's main axis.
        buckets = [min(BUCKETS - 1, int(base * BUCKETS)) for base in bases]
    else:
        # Same stratified counts, assigned by an independent permutation: no geometric signal.
        independent = list(range(rows))
        random.Random(seed + 1_000_003).shuffle(independent)
        buckets = [independent[rid] * BUCKETS // rows for rid in range(rows)]
    return [(rid, vectors[rid], buckets[rid]) for rid in range(rows)]


def make_queries(count: int, dims: int, seed: int, base_range: tuple[float, float] = (0.0, 1.0)) -> list[list[float]]:
    """Held-out queries from the data's distribution, never copied from the dataset. Both fixtures
    get the same queries, because they share the same vectors."""
    rng = random.Random(seed + 1)
    lo, hi = base_range
    out = []
    for _ in range(count):
        base = rng.uniform(lo, hi)
        out.append([base + rng.gauss(0, 0.05) for _ in range(dims)])
    return out


def make_far_queries(count: int, dims: int, seed: int, max_selectivity: float) -> list[list[float]]:
    """Queries in the part of the space whose rows fail every filter on the correlated fixture.

    Passing rows have base < max_selectivity there; these queries sit in the upper half of the
    remaining range. On the uncorrelated fixture the same queries see passing rows at the
    configured rate around them, so scenario D's uncorrelated run is a control that differs from
    the correlated run only in bucket assignment.
    """
    lo = (1.0 + max_selectivity) / 2
    return make_queries(count, dims, seed + 1, base_range=(lo, 1.0))


def make_workload(count: int, dims: int, seed: int, fixture: str, max_selectivity: float) -> Workload:
    return Workload(
        fixture=fixture,
        queries=make_queries(count, dims, seed),
        far_queries=make_far_queries(count, dims, seed, max_selectivity),
    )
