from __future__ import annotations

import statistics
import time
from collections import Counter
from contextlib import contextmanager
from typing import Any


def recall_at_k(actual: list[int], expected: list[int], k: int) -> float:
    if not expected:
        return 1.0 if not actual else 0.0
    return len(set(actual[:k]) & set(expected[:k])) / min(k, len(expected))


def percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = min(len(ordered) - 1, int(round((pct / 100.0) * (len(ordered) - 1))))
    return ordered[idx]


def exact_ids(exact, workload, query_set: str, filter_value: int, k: int) -> list[list[int]]:
    """Ground truth for one (fixture, query set, filter), computed once and cached on the workload
    so every target, scenario, and knob value reuses it."""
    key = (query_set, filter_value, k)
    if key not in workload.truth:
        queries = getattr(workload, query_set)
        workload.truth[key] = [exact.query_filtered(query, filter_value, k).ids for query in queries]
    return workload.truth[key]


@contextmanager
def index_path_forced(target):
    """Ask the target to use its index. The plan column shows whether it did."""
    target.force_index_scan(True)
    try:
        yield
    finally:
        target.force_index_scan(False)


def recovery_point(rows: list[dict[str, Any]], threshold: float) -> int | None:
    """Lowest search value whose recall reaches threshold: the matched-recall operating point."""
    reached = [r["search_value"] for r in rows if r["search_value"] is not None and r["recall_at_k"] >= threshold]
    return min(reached) if reached else None


def best_cell(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Highest-recall knob cell (lowest knob on ties): what to report when nothing reaches threshold."""
    knobbed = [r for r in rows if r["search_value"] is not None]
    return max(knobbed, key=lambda r: (r["recall_at_k"], -r["search_value"])) if knobbed else None


def summarize_plans(explains: list[dict[str, Any]]) -> str:
    counts = Counter(str(e.get("plan_summary", "")) for e in explains)
    if len(counts) == 1:
        return next(iter(counts))
    return "mixed: " + "; ".join(f"{plan} x{n}" for plan, n in counts.most_common())


def run_selectivity_case(
    target,
    queries: list[list[float]],
    expected: list[list[int]],
    filter_value: int,
    k: int,
    search_value: int | None,
    warmup_passes: int = 1,
) -> dict[str, Any]:
    if search_value is not None:
        target.set_search_knob(search_value)
    # Untimed passes so cell order (and the previous cell's EXPLAIN) does not decide cache warmth.
    for _ in range(warmup_passes):
        for query in queries:
            target.query_filtered(query, filter_value, k)
    # Timed window: target calls only. Scoring and EXPLAIN run after it so neither enters qps.
    observed = []
    started = time.perf_counter()
    for query in queries:
        observed.append(target.query_filtered(query, filter_value, k))
    elapsed = time.perf_counter() - started
    latencies = [result.elapsed_ms for result in observed]
    recalls = [recall_at_k(result.ids, ids, k) for result, ids in zip(observed, expected)]
    # EXPLAIN (ANALYZE) executes each query again: its buffer counts describe that re-execution,
    # not the timed call above.
    explains = [target.explain_filtered(query, filter_value, k) for query in queries]
    return {
        "search_value": search_value,
        "recall_at_k": statistics.mean(recalls),
        "qps": len(queries) / elapsed if elapsed > 0 else 0.0,
        "p50_ms": percentile(latencies, 50),
        "p95_ms": percentile(latencies, 95),
        "p99_ms": percentile(latencies, 99),
        "pages_total_mean": statistics.mean(float(e.get("pages_total", 0)) for e in explains),
        "pages_hit_mean": statistics.mean(float(e.get("pages_hit", 0)) for e in explains),
        "pages_read_mean": statistics.mean(float(e.get("pages_read", 0)) for e in explains),
        "plan_summary": summarize_plans(explains),
    }
