"""Scenario D: correlation stress, where the passing set is spatially far from the query.

Uses `workload.far_queries` (neighborhoods that fail every configured filter on the correlated
fixture) at the largest selectivity, with the index path forced so a planner fallback to an exact
scan cannot hide the failure. On the uncorrelated fixture the same run is the control.
"""

from __future__ import annotations

from fixtures.synthetic import filter_value_for_selectivity
from scenarios.common import exact_ids, run_selectivity_case, search_values_for


def run(config, target, exact, workload):
    rows = []
    k = config["run"]["k"]
    sel = max(float(s) for s in config["dataset"]["selectivities"])
    filter_value = filter_value_for_selectivity(sel)
    expected = exact_ids(exact, workload.far_queries, filter_value, k)
    target.force_index_scan(True)
    try:
        for search_value in search_values_for(config, target):
            result = run_selectivity_case(target, workload.far_queries, expected, filter_value, k, search_value)
            result.update({
                "scenario": "d_correlation",
                "selectivity": sel,
                "filter_value": filter_value,
                "forced": True,
                "query_set": "far",
            })
            rows.append(result)
    finally:
        target.force_index_scan(False)
    return rows
