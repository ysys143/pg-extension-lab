"""Scenario C: progressive recall recovery as candidate expansion increases.

Sweeps the search knob upward at the median selectivity and records the lowest knob value that
reaches `run.recall_threshold` (null when none does). This is about candidate budget, not about
inserting rows after the index is built.
"""

from __future__ import annotations

from fixtures.synthetic import filter_value_for_selectivity
from scenarios.common import exact_ids, recovery_point, run_selectivity_case, search_values_for


def run(config, target, exact, workload):
    rows = []
    k = config["run"]["k"]
    threshold = float(config["run"].get("recall_threshold", 0.94))
    sels = sorted(float(s) for s in config["dataset"]["selectivities"])
    sel = sels[len(sels) // 2]
    filter_value = filter_value_for_selectivity(sel)
    expected = exact_ids(exact, workload.queries, filter_value, k)
    for search_value in sorted(search_values_for(config, target), key=lambda v: -1 if v is None else v):
        result = run_selectivity_case(target, workload.queries, expected, filter_value, k, search_value)
        result.update({"scenario": "c_candidate_expansion", "selectivity": sel, "filter_value": filter_value})
        rows.append(result)
    recovery = recovery_point(rows, threshold)
    for row in rows:
        row.update({"recall_threshold": threshold, "recovery_search_value": recovery})
    return rows
