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
    target_names = [name for name, spec in config.get("targets", {}).items() if spec.get("enabled", True)]
    for name in target_names:
        values = config.get(name, {}).get("search_values")
        if values:
            return [int(v) for v in values]
    for section in ("postgres_sql", "pgvector_example"):
        values = config.get(section, {}).get("search_values")
        if values:
            return [int(v) for v in values]
    return [0]


def run_selectivity_case(target, exact, queries, filter_value: int, k: int, search_value: int) -> dict[str, Any]:
    target.set_search_knob(search_value)
    latencies = []
    recalls = []
    page_totals = []
    page_hits = []
    page_reads = []
    started = time.perf_counter()
    for query in queries:
        expected = exact.query_filtered(query, filter_value, k).ids
        observed = target.query_filtered(query, filter_value, k)
        explains = target.explain_filtered(query, filter_value, k)
        latencies.append(observed.elapsed_ms)
        recalls.append(recall_at_k(observed.ids, expected, k))
        page_totals.append(float(explains.get("pages_total", 0)))
        page_hits.append(float(explains.get("pages_hit", 0)))
        page_reads.append(float(explains.get("pages_read", 0)))
    elapsed = time.perf_counter() - started
    return {
        "search_value": search_value,
        "recall_at_k": statistics.mean(recalls),
        "qps": len(queries) / elapsed if elapsed > 0 else 0.0,
        "p50_ms": percentile(latencies, 50),
        "p95_ms": percentile(latencies, 95),
        "p99_ms": percentile(latencies, 99),
        "pages_total_mean": statistics.mean(page_totals),
        "pages_hit_mean": statistics.mean(page_hits),
        "pages_read_mean": statistics.mean(page_reads),
    }
