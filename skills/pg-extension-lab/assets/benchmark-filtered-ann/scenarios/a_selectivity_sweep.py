"""Scenario A: every selectivity x knob with the planner free to choose (the EXPLAIN-regret view).

On a small table the planner may pick an exact scan; the plan column shows it, and B-D force the
index path for the index's own behavior.
"""

from __future__ import annotations

from fixtures.synthetic import filter_value_for_selectivity
from scenarios.common import exact_ids, run_selectivity_case


def run(config, target, exact, workload, search_values):
    rows = []
    k = config["run"]["k"]
    warmup = int(config["run"].get("warmup_passes", 1))
    for sel in config["dataset"]["selectivities"]:
        filter_value = filter_value_for_selectivity(float(sel))
        expected = exact_ids(exact, workload, "queries", filter_value, k)
        for search_value in search_values:
            result = run_selectivity_case(target, workload.queries, expected, filter_value, k, search_value, warmup)
            result.update({
                "scenario": "a_selectivity_sweep",
                "selectivity": sel,
                "filter_value": filter_value,
                "plan_mode": "planner",
            })
            rows.append(result)
    return rows
