"""Scenario D: correlation stress, where the passing set is spatially far from the query.

Uses `workload.far_queries` (neighborhoods that fail every configured filter on the correlated
fixture) at the largest selectivity, with the index path forced so the planner cannot switch to
an exact scan and hide the failure. On the uncorrelated fixture the same run is the control.
"""

from __future__ import annotations

from fixtures.synthetic import filter_value_for_selectivity
from scenarios.common import exact_ids, index_path_forced, run_selectivity_case


def run(config, target, exact, workload, search_values):
    rows = []
    k = config["run"]["k"]
    warmup = int(config["run"].get("warmup_passes", 1))
    sel = max(float(s) for s in config["dataset"]["selectivities"])
    filter_value = filter_value_for_selectivity(sel)
    expected = exact_ids(exact, workload, "far_queries", filter_value, k)
    with index_path_forced(target):
        for search_value in search_values:
            result = run_selectivity_case(target, workload.far_queries, expected, filter_value, k, search_value, warmup)
            result.update({
                "scenario": "d_correlation",
                "selectivity": sel,
                "filter_value": filter_value,
                "plan_mode": "force_index",
                "query_set": "far",
            })
            rows.append(result)
    return rows
