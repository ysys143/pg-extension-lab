"""Harness self-tests (stdlib only). Run from the harness directory:

    python -B -m unittest discover -s tests -v
"""

from __future__ import annotations

import sys
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pareto  # noqa: E402
import run_bench  # noqa: E402
from fixtures.synthetic import (  # noqa: E402
    FIXTURES,
    Workload,
    filter_value_for_selectivity,
    make_dataset,
    make_queries,
    make_workload,
    pass_rate,
    passes,
    representable_selectivity,
)
from scenarios import a_selectivity_sweep  # noqa: E402
from scenarios.common import exact_ids, recovery_point, run_selectivity_case  # noqa: E402
from targets._explain import summarize_explain  # noqa: E402
from targets._metric import l2  # noqa: E402
from targets.base import QueryResult  # noqa: E402
from targets.postfilter_topn import PostfilterTopNTarget  # noqa: E402
from targets.prefilter_exact import PrefilterExactTarget  # noqa: E402


def loaded(target_cls, rows):
    target = target_cls({})
    target.setup()
    target.insert_batch(rows)
    return target


def smoke_config(search_values):
    return {
        "run": {"k": 10, "search_values": search_values, "recall_threshold": 0.94},
        "dataset": {"selectivities": [0.01, 0.05, 0.10]},
    }


class FixtureTest(unittest.TestCase):
    def test_realized_pass_rate_matches_configured_selectivity(self):
        for rows_n in (1000, 999, 5000):
            for fixture in FIXTURES:
                rows = make_dataset(rows_n, 4, 7, fixture)
                for sel in (0.01, 0.05, 0.10, 0.37):
                    realized = pass_rate(rows, filter_value_for_selectivity(sel))
                    self.assertLessEqual(abs(realized - sel), 1 / rows_n, (rows_n, fixture, sel, realized))

    def test_filter_value_rounds_instead_of_truncating(self):
        self.assertEqual(filter_value_for_selectivity(0.29), 29)  # int(0.29 * 100) == 28
        self.assertTrue(representable_selectivity(0.29))
        self.assertFalse(representable_selectivity(0.015))
        self.assertFalse(representable_selectivity(1.5))
        self.assertFalse(representable_selectivity(0.0))

    def test_queries_are_held_out(self):
        for fixture in FIXTURES:
            rows = make_dataset(500, 8, 3, fixture)
            vectors = {tuple(vec) for _, vec, _ in rows}
            for query in make_queries(50, 8, 3, fixture):
                self.assertNotIn(tuple(query), vectors)

    def test_far_queries_sit_outside_every_passing_set(self):
        workload = make_workload(20, 8, 3, "correlated", max_selectivity=0.10)
        for query in workload.far_queries:
            self.assertGreater(sum(query) / len(query), 0.4)


class TargetTest(unittest.TestCase):
    def setUp(self):
        self.rows = make_dataset(1000, 16, 42, "correlated")
        self.queries = make_queries(10, 16, 42, "correlated")

    def test_prefilter_exact_returns_nearest_passing_rows(self):
        exact = loaded(PrefilterExactTarget, self.rows)
        for query in self.queries:
            got = exact.query_filtered(query, 5, 10).ids
            want = [rid for _, rid in sorted((l2(query, vec), rid) for rid, vec, b in self.rows if passes(b, 5))][:10]
            self.assertEqual(got, want)

    def test_postfilter_recall_is_monotone_and_non_trivial(self):
        exact = loaded(PrefilterExactTarget, self.rows)
        target = loaded(PostfilterTopNTarget, self.rows)
        expected = exact_ids(exact, self.queries, 5, 10)
        recalls = [
            run_selectivity_case(target, self.queries, expected, 5, 10, budget)["recall_at_k"]
            for budget in (20, 80, 320, 1000)
        ]
        self.assertEqual(recalls, sorted(recalls))
        self.assertLess(recalls[0], 1.0)
        self.assertEqual(recalls[-1], 1.0)


class CountingExact(PrefilterExactTarget):
    def __init__(self, rows):
        super().__init__({})
        self.insert_batch(rows)
        self.calls = 0

    def query_filtered(self, query, filter_value, k):
        self.calls += 1
        return super().query_filtered(query, filter_value, k)


class SlowExplainTarget(PostfilterTopNTarget):
    def explain_filtered(self, query, filter_value, k):
        time.sleep(0.02)
        return super().explain_filtered(query, filter_value, k)


class InstantTarget(SlowExplainTarget):
    def query_filtered(self, query, filter_value, k):
        return QueryResult([], 0.0, {})


class ScenarioTest(unittest.TestCase):
    def setUp(self):
        self.rows = make_dataset(300, 8, 1, "correlated")
        self.workload = Workload("correlated", make_queries(5, 8, 1, "correlated"), [])

    def test_ground_truth_is_computed_once_per_query_and_filter(self):
        exact = CountingExact(self.rows)
        target = loaded(PostfilterTopNTarget, self.rows)
        a_selectivity_sweep.run(smoke_config([20, 80, 320]), target, exact, self.workload)
        self.assertEqual(exact.calls, len(self.workload.queries) * 3)

    def test_knobless_target_runs_each_cell_once(self):
        exact = loaded(PrefilterExactTarget, self.rows)
        rows = a_selectivity_sweep.run(smoke_config([20, 80, 320]), exact, exact, self.workload)
        self.assertEqual(len(rows), 3)
        self.assertEqual({row["search_value"] for row in rows}, {None})

    def test_explain_runs_outside_the_timed_window(self):
        target = loaded(InstantTarget, self.rows)
        target.set_search_knob(10)
        result = run_selectivity_case(target, self.workload.queries, [[]] * 5, 5, 10, None)
        # Inside the window, five 20 ms EXPLAIN calls would cap qps near 50.
        self.assertGreater(result["qps"], 500)

    def test_recovery_point_is_lowest_knob_reaching_threshold(self):
        rows = [
            {"search_value": 20, "recall_at_k": 0.5},
            {"search_value": 80, "recall_at_k": 0.95},
            {"search_value": 320, "recall_at_k": 1.0},
        ]
        self.assertEqual(recovery_point(rows, 0.94), 80)
        self.assertIsNone(recovery_point(rows[:1], 0.94))
        self.assertIsNone(recovery_point([{"search_value": None, "recall_at_k": 1.0}], 0.94))


class ExplainTest(unittest.TestCase):
    def test_plan_summary_shows_the_scan_below_limit(self):
        plan = [{"Plan": {
            "Node Type": "Limit", "Shared Hit Blocks": 1,
            "Plans": [{"Node Type": "Sort", "Plans": [{"Node Type": "Seq Scan", "Shared Read Blocks": 4}]}],
        }}]
        summary = summarize_explain(plan)
        self.assertEqual(summary["plan_summary"], "Limit > Sort > Seq Scan")
        self.assertEqual(summary["pages_total"], 5)


class ParetoTest(unittest.TestCase):
    def test_frontier_is_judged_per_selectivity(self):
        base = {"target": "t", "scenario": "a", "fixture": "correlated"}
        rows = [
            {**base, "selectivity": 0.01, "recall_at_k": 0.5, "qps": 10.0},
            {**base, "selectivity": 0.10, "recall_at_k": 0.9, "qps": 100.0},
        ]
        groups = pareto.frontier_groups(rows)
        self.assertEqual(len(groups), 2)
        self.assertTrue(all(len(group["frontier"]) == 1 for group in groups))


class ConfigTest(unittest.TestCase):
    def config(self, **dataset):
        return {
            "run": {"seed": 1, "k": 10},
            "dataset": {"rows": 100, "dims": 4, "selectivities": [0.05], **dataset},
            "targets": {},
        }

    def test_valid_config_passes(self):
        self.assertEqual(run_bench.validate_config(self.config(fixtures=["correlated"])), [])

    def test_unrepresentable_selectivity_is_rejected(self):
        for sel in (0.015, 1.5):
            errors = run_bench.validate_config(self.config(selectivities=[sel]))
            self.assertTrue(any("selectivities" in error for error in errors), (sel, errors))

    def test_legacy_correlated_flag_is_rejected(self):
        errors = run_bench.validate_config(self.config(correlated=True))
        self.assertTrue(any("dataset.fixtures" in error for error in errors), errors)

    def test_pass_rate_warning_fires_on_unrealized_selectivity(self):
        rows = [(i, [0.0], 0 if i < 3 else 99) for i in range(100)]  # 3% pass for every bucket < 99
        self.assertEqual(run_bench.pass_rate_warnings(rows, [0.03]), [])
        self.assertEqual(len(run_bench.pass_rate_warnings(rows, [0.10])), 1)


if __name__ == "__main__":
    unittest.main()
