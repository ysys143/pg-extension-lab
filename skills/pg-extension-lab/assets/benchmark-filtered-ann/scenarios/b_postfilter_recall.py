"""Scenario B: post-filter recall failure at the lowest selectivity, index path forced.

For a target that cannot force a plan (the in-memory models) these cells equal A's
lowest-selectivity cells; on a database target they differ whenever the planner would have
chosen an exact scan.
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
