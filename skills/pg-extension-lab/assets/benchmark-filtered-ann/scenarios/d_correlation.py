from __future__ import annotations

from fixtures.synthetic import filter_value_for_selectivity
from scenarios.common import configured_search_values, run_selectivity_case


def run(config, target, exact, queries):
    rows = []
    sel = max(float(s) for s in config["dataset"]["selectivities"])
    filter_value = filter_value_for_selectivity(sel)
    target.force_index_scan(True)
    try:
        for search_value in configured_search_values(config):
            result = run_selectivity_case(target, exact, queries, filter_value, config["run"]["k"], int(search_value))
            result.update({"scenario": "d_correlation", "selectivity": sel, "filter_value": filter_value, "forced": True})
            rows.append(result)
    finally:
        target.force_index_scan(False)
    return rows
