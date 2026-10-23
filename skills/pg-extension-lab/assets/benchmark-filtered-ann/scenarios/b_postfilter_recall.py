from __future__ import annotations

from fixtures.synthetic import filter_value_for_selectivity
from scenarios.common import exact_ids, run_selectivity_case, search_values_for


def run(config, target, exact, workload):
    rows = []
    k = config["run"]["k"]
    sel = min(float(s) for s in config["dataset"]["selectivities"])
    filter_value = filter_value_for_selectivity(sel)
    expected = exact_ids(exact, workload.queries, filter_value, k)
    for search_value in search_values_for(config, target):
        result = run_selectivity_case(target, workload.queries, expected, filter_value, k, search_value)
        result.update({"scenario": "b_postfilter_recall", "selectivity": sel, "filter_value": filter_value})
        rows.append(result)
    return rows
