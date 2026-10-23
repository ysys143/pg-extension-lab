"""Scenario C: progressive recall recovery as candidate expansion increases, index path forced.

For every selectivity, sweeps the search knob upward and records the lowest knob reaching
`run.recall_threshold` (null when none does) and the best cell, so a miss still reports the
max-recall cell. Forcing the index keeps an exact-scan plan from posing as an operating point.
This is about candidate budget, not about inserting rows after the index is built.
"""

from __future__ import annotations

from fixtures.synthetic import filter_value_for_selectivity
from scenarios.common import best_cell, exact_ids, index_path_forced, recovery_point, run_selectivity_case


def run(config, target, exact, workload, search_values):
    rows = []
    k = config["run"]["k"]
    warmup = int(config["run"].get("warmup_passes", 1))
    threshold = float(config["run"].get("recall_threshold", 0.94))
    ordered = sorted(search_values, key=lambda v: -1 if v is None else v)
    with index_path_forced(target):
        for sel in sorted(float(s) for s in config["dataset"]["selectivities"]):
            filter_value = filter_value_for_selectivity(sel)
            expected = exact_ids(exact, workload, "queries", filter_value, k)
            cells = []
            for search_value in ordered:
                result = run_selectivity_case(target, workload.queries, expected, filter_value, k, search_value, warmup)
                result.update({
                    "scenario": "c_candidate_expansion",
                    "selectivity": sel,
                    "filter_value": filter_value,
                    "plan_mode": "force_index",
                })
                cells.append(result)
            recovery = recovery_point(cells, threshold)
            best = best_cell(cells)
            for cell in cells:
                cell.update({
                    "recall_threshold": threshold,
                    "recovery_search_value": recovery,
                    "best_search_value": best["search_value"] if best else None,
                    "best_recall": best["recall_at_k"] if best else None,
                })
            rows.extend(cells)
    return rows
