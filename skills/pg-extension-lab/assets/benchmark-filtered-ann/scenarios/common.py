from __future__ import annotations

import statistics
import time
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


def configured_search_values(config: dict[str, Any]) -> list[int]:
    if "search_values" in config.get("run", {}):
        return [int(v) for v in config["run"]["search_values"]]
    for name, spec in config.get("targets", {}).items():
        if spec.get("enabled", False):
            values = config.get(name, {}).get("search_values")
            if values:
                return [int(v) for v in values]
    return [0]


def search_values_for(config: dict[str, Any], target) -> list[int | None]:
    if not getattr(target, "has_search_knob", True):
        return [None]
    values: list[int | None] = list(configured_search_values(config))
    return values


def exact_ids(exact, queries: list[list[float]], filter_value: int, k: int) -> list[list[int]]:
    """Ground truth for one (query set, filter), computed once and reused for every knob value."""
    return [exact.query_filtered(query, filter_value, k).ids for query in queries]


def recovery_point(rows: list[dict[str, Any]], threshold: float) -> int | None:
    """Lowest search value whose recall reaches threshold: the matched-recall operating point."""
    reached = [r["search_value"] for r in rows if r["search_value"] is not None and r["recall_at_k"] >= threshold]
    return min(reached) if reached else None


def run_selectivity_case(
    target, queries: list[list[float]], expected: list[list[int]], filter_value: int, k: int, search_value: int | None
) -> dict[str, Any]:
    if search_value is not None:
        target.set_search_knob(search_value)
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
    }
