"""Scenario B: post-filter recall failure at the lowest selectivity, index path forced.

B's cells are the same measurement as C's lowest-selectivity cells (and, for a target that
cannot force a plan, A's). B exists so the failure point can be run and read alone
(`--scenario b`); do not sum cells across scenarios.
"""

from __future__ import annotations

from fixtures.synthetic import filter_value_for_selectivity
from scenarios.common import exact_ids, index_path_forced, run_selectivity_case


def run(config, target, exact, workload, search_values):
    rows = []
    k = config["run"]["k"]
    warmup = int(config["run"].get("warmup_passes", 1))
    sel = min(float(s) for s in config["dataset"]["selectivities"])
    filter_value = filter_value_for_selectivity(sel)
    expected = exact_ids(exact, workload, "queries", filter_value, k)
    with index_path_forced(target):
        for search_value in search_values:
            result = run_selectivity_case(target, workload.queries, expected, filter_value, k, search_value, warmup)
            result.update({
                "scenario": "b_postfilter_recall",
                "selectivity": sel,
                "filter_value": filter_value,
                "plan_mode": "force_index",
            })
            rows.append(result)
    return rows
