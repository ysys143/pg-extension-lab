"""Harness self-tests (stdlib only). Run from the harness directory:

    python -B -m unittest discover -s tests -v
"""

from __future__ import annotations

import importlib
import json
import subprocess
import sys
import tempfile
import time
import types
import unittest
from pathlib import Path
from unittest import mock

HARNESS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HARNESS))

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
from scenarios import a_selectivity_sweep, b_postfilter_recall, c_candidate_expansion, d_correlation  # noqa: E402
from scenarios.common import best_cell, recovery_point, run_selectivity_case, summarize_plans  # noqa: E402
from targets._explain import summarize_explain  # noqa: E402
from targets._metric import l2  # noqa: E402
from targets.base import QueryResult  # noqa: E402
from targets.postfilter_topn import PostfilterTopNTarget  # noqa: E402
from targets.prefilter_exact import PrefilterExactTarget  # noqa: E402

SCENARIO_MODULES = (a_selectivity_sweep, b_postfilter_recall, c_candidate_expansion, d_correlation)


def loaded(target_cls, rows):
    target = target_cls({})
    target.setup()
    target.insert_batch(rows)
    return target


def smoke_config():
    return {
        "run": {"k": 10, "recall_threshold": 0.94, "warmup_passes": 0},
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

    def test_far_query_neighborhoods_fail_every_filter(self):
        rows = make_dataset(1000, 16, 42, "correlated")
        workload = make_workload(10, 16, 42, "correlated", max_selectivity=0.10)
        widest = filter_value_for_selectivity(0.10)
        for query in workload.far_queries:
            nearest = sorted(rows, key=lambda row: l2(query, row[1]))[:10]
            self.assertFalse(any(passes(bucket, widest) for _, _, bucket in nearest))


class TargetTest(unittest.TestCase):
    def setUp(self):
        self.rows = make_dataset(1000, 16, 42, "correlated")
        self.workload = Workload("correlated", make_queries(10, 16, 42, "correlated"), [])

    def test_prefilter_exact_returns_nearest_passing_rows(self):
        exact = loaded(PrefilterExactTarget, self.rows)
        for query in self.workload.queries:
            got = exact.query_filtered(query, 5, 10).ids
            want = [rid for _, rid in sorted((l2(query, vec), rid) for rid, vec, b in self.rows if passes(b, 5))][:10]
            self.assertEqual(got, want)

    def test_postfilter_recall_is_monotone_and_non_trivial(self):
        exact = loaded(PrefilterExactTarget, self.rows)
        target = loaded(PostfilterTopNTarget, self.rows)
        expected = [exact.query_filtered(q, 5, 10).ids for q in self.workload.queries]
        recalls = [
            run_selectivity_case(target, self.workload.queries, expected, 5, 10, budget, 0)["recall_at_k"]
            for budget in (20, 80, 320, 1000)
        ]
        self.assertEqual(recalls, sorted(recalls))
        self.assertLess(recalls[0], 1.0)
        self.assertEqual(recalls[-1], 1.0)


class RecordingExact(PrefilterExactTarget):
    def __init__(self, rows):
        super().__init__({})
        self.insert_batch(rows)
        self.queries_seen: list[tuple] = []

    def query_filtered(self, query, filter_value, k):
        self.queries_seen.append(tuple(query))
        return super().query_filtered(query, filter_value, k)


class ForceRecordingTarget(PostfilterTopNTarget):
    def __init__(self, config):
        super().__init__(config)
        self.force_calls: list[bool] = []

    def force_index_scan(self, enabled):
        self.force_calls.append(enabled)


class SlowExplainTarget(PostfilterTopNTarget):
    def explain_filtered(self, query, filter_value, k):
        time.sleep(0.02)
        return super().explain_filtered(query, filter_value, k)


class InstantTarget(SlowExplainTarget):
    def query_filtered(self, query, filter_value, k):
        return QueryResult([], 0.0, {})


class CountingTarget(PostfilterTopNTarget):
    calls = 0

    def query_filtered(self, query, filter_value, k):
        self.calls += 1
        return QueryResult([], 0.0, {})


class ScenarioTest(unittest.TestCase):
    def setUp(self):
        self.rows = make_dataset(300, 8, 1, "correlated")
        self.workload = make_workload(5, 8, 1, "correlated", max_selectivity=0.10)

    def test_oracle_runs_once_per_query_set_and_filter_across_scenarios(self):
        exact = RecordingExact(self.rows)
        target = loaded(PostfilterTopNTarget, self.rows)
        for module in SCENARIO_MODULES:
            module.run(smoke_config(), target, exact, self.workload, [20, 80, 300])
        # queries x 3 selectivities (A, B, C share them) + far queries x the widest filter (D)
        self.assertEqual(len(exact.queries_seen), 5 * 3 + 5 * 1)

    def test_d_scores_far_queries(self):
        exact = RecordingExact(self.rows)
        target = loaded(PostfilterTopNTarget, self.rows)
        d_correlation.run(smoke_config(), target, exact, self.workload, [20])
        self.assertEqual(set(exact.queries_seen), {tuple(q) for q in self.workload.far_queries})
        self.assertFalse(set(exact.queries_seen) & {tuple(q) for q in self.workload.queries})

    def test_only_b_c_d_force_the_index_path(self):
        for module, expected in zip(SCENARIO_MODULES, ([], [True, False], [True, False], [True, False])):
            target = loaded(ForceRecordingTarget, self.rows)
            rows = module.run(smoke_config(), target, loaded(PrefilterExactTarget, self.rows), self.workload, [20])
            self.assertEqual(target.force_calls, expected, module.__name__)
            self.assertEqual({row["plan_mode"] for row in rows}, {"planner" if not expected else "force_index"})

    def test_c_reports_recovery_and_best_cell_per_selectivity(self):
        exact = loaded(PrefilterExactTarget, self.rows)
        target = loaded(PostfilterTopNTarget, self.rows)
        rows = c_candidate_expansion.run(smoke_config(), target, exact, self.workload, [300, 10])
        self.assertEqual({row["selectivity"] for row in rows}, {0.01, 0.05, 0.10})
        self.assertEqual([row["search_value"] for row in rows[:2]], [10, 300])  # swept upward
        for row in rows:
            self.assertEqual(row["recovery_search_value"], 300)  # budget = all rows -> exact
            self.assertEqual((row["best_search_value"], row["best_recall"]), (300, 1.0))

    def test_knobless_target_runs_each_cell_once(self):
        exact = loaded(PrefilterExactTarget, self.rows)
        values = run_bench.search_values_for({"run": {"search_values": [20, 80]}}, "prefilter_exact", exact)
        rows = a_selectivity_sweep.run(smoke_config(), exact, exact, self.workload, values)
        self.assertEqual(len(rows), 3)
        self.assertEqual({row["search_value"] for row in rows}, {None})

    def test_warmup_passes_run_before_the_timed_window(self):
        target = loaded(CountingTarget, self.rows)
        run_selectivity_case(target, self.workload.queries, [[]] * 5, 5, 10, None, warmup_passes=2)
        self.assertEqual(target.calls, 5 * 3)  # two untimed passes + one timed pass

    def test_explain_runs_outside_the_timed_window(self):
        target = loaded(InstantTarget, self.rows)
        target.set_search_knob(10)
        result = run_selectivity_case(target, self.workload.queries, [[]] * 5, 5, 10, None)
        # Inside the window, five 20 ms EXPLAIN calls would cap qps near 50.
        self.assertGreater(result["qps"], 500)

    def test_recovery_point_and_best_cell(self):
        rows = [
            {"search_value": 20, "recall_at_k": 0.5},
            {"search_value": 80, "recall_at_k": 0.95},
            {"search_value": 320, "recall_at_k": 0.95},
        ]
        self.assertEqual(recovery_point(rows, 0.94), 80)
        self.assertIsNone(recovery_point(rows[:1], 0.94))
        self.assertIsNone(recovery_point([{"search_value": None, "recall_at_k": 1.0}], 0.94))
        best = best_cell(rows)
        self.assertIsNotNone(best)
        self.assertEqual(best and best["search_value"], 80)  # lowest knob on a recall tie
        self.assertIsNone(best_cell([{"search_value": None, "recall_at_k": 1.0}]))

    def test_mixed_plans_are_not_hidden(self):
        plans = [{"plan_summary": "Limit > Index Scan"}] * 6 + [{"plan_summary": "Limit > Sort > Seq Scan"}] * 4
        self.assertEqual(summarize_plans(plans), "mixed: Limit > Index Scan x6; Limit > Sort > Seq Scan x4")
        self.assertEqual(summarize_plans(plans[:2]), "Limit > Index Scan")


class FakeConnection:
    autocommit = False
    prepare_threshold = 5  # psycopg 3's default

    def close(self):
        return None


class SqlAdapterTest(unittest.TestCase):
    """The SQL adapters must plan every execution so EXPLAIN describes the timed plan."""

    def test_sql_adapters_turn_off_auto_prepare(self):
        fake = types.ModuleType("psycopg")
        setattr(fake, "connect", lambda dsn: FakeConnection())
        config = {
            "dataset": {"dims": 4},
            "postgres_sql": {"dsn": "fake"},
            "pgvector_example": {"dsn": "fake"},
        }
        with mock.patch.dict(sys.modules, {"psycopg": fake}):
            postgres_sql = importlib.import_module("targets.postgres_sql")
            pgvector_target = importlib.import_module("examples.pgvector_target")
            for target in (postgres_sql.create_target(config), pgvector_target.create_target(config)):
                self.assertIsNone(target.conn.prepare_threshold, type(target).__name__)
                self.assertTrue(target.conn.autocommit)


class ExplainTest(unittest.TestCase):
    def test_plan_summary_shows_the_scan_below_limit(self):
        # PostgreSQL buffer counts are inclusive: each node repeats its children's pages.
        pages = {"Shared Hit Blocks": 4, "Shared Read Blocks": 1}
        plan = [{"Plan": {
            "Node Type": "Limit", **pages,
            "Plans": [{"Node Type": "Sort", **pages, "Plans": [{"Node Type": "Seq Scan", **pages}]}],
        }}]
        summary = summarize_explain(plan)
        self.assertEqual(summary["plan_summary"], "Limit > Sort > Seq Scan")
        self.assertEqual((summary["pages_hit"], summary["pages_read"], summary["pages_total"]), (4, 1, 5))


class ParetoTest(unittest.TestCase):
    def frontier_sizes(self, rows):
        return [len(group["frontier"]) for group in pareto.frontier_groups(rows)]

    def test_frontier_is_judged_per_selectivity(self):
        base = {"target": "t", "scenario": "a", "fixture": "correlated"}
        rows = [
            {**base, "selectivity": 0.01, "recall_at_k": 0.5, "qps": 10.0},
            {**base, "selectivity": 0.10, "recall_at_k": 0.9, "qps": 100.0},
        ]
        self.assertEqual(self.frontier_sizes(rows), [1, 1])

    def test_frontier_is_judged_per_fixture_and_scenario(self):
        base = {"target": "t", "selectivity": 0.05}
        rows = [
            {**base, "scenario": "a", "fixture": "correlated", "recall_at_k": 0.2, "qps": 10.0},
            {**base, "scenario": "a", "fixture": "uncorrelated", "recall_at_k": 0.9, "qps": 100.0},
            {**base, "scenario": "c", "fixture": "uncorrelated", "recall_at_k": 0.1, "qps": 5.0},
        ]
        self.assertEqual(self.frontier_sizes(rows), [1, 1, 1])


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

    def test_non_l2_pgvector_operator_is_rejected(self):
        config = self.config()
        config["targets"] = {"pgvector_example": {"module": "examples.pgvector_target", "enabled": True}}
        config["pgvector_example"] = {"distance_operator": "<=>"}
        self.assertTrue(any("distance_operator" in e for e in run_bench.validate_config(config)))

    def test_equality_filter_sql_is_rejected(self):
        config = self.config()
        config["targets"] = {"postgres_sql": {"module": "targets.postgres_sql", "enabled": True}}
        config["postgres_sql"] = {"dsn": "x", "insert_sql": "x",
                                  "query_sql": "SELECT id FROM t WHERE {filter_column} = %s LIMIT %s"}
        self.assertTrue(any("query_sql" in e for e in run_bench.validate_config(config)))
        config["postgres_sql"]["query_sql"] = "SELECT id FROM t WHERE {filter_column} < %s LIMIT %s"
        self.assertEqual(run_bench.validate_config(config), [])

    def test_each_target_sweeps_its_own_knob(self):
        knob = PostfilterTopNTarget({})
        config = {"run": {"search_values": [20, 1000]}, "postfilter_topn": {"search_values": [5]}}
        self.assertEqual(run_bench.search_values_for(config, "postfilter_topn", knob), [5])
        self.assertEqual(run_bench.search_values_for(config, "other", knob), [20, 1000])
        with self.assertRaises(SystemExit):
            run_bench.search_values_for({"run": {}}, "postfilter_topn", knob)

    def test_pass_rate_warning_fires_on_unrealized_selectivity(self):
        rows = [(i, [0.0], 0 if i < 3 else 99) for i in range(100)]  # 3% pass for every bucket < 99
        self.assertEqual(run_bench.pass_rate_warnings(rows, [0.03]), [])
        self.assertEqual(len(run_bench.pass_rate_warnings(rows, [0.10])), 1)


SMALL_CONFIG = """
[run]
seed = 3
k = 5
queries = 3
search_values = [10, 200]
warmup_passes = 0

[dataset]
name = "tiny"
rows = 200
dims = 4
selectivities = [0.05, 0.10]
fixtures = ["correlated", "uncorrelated"]

[methodology]
profile = "filtered-ann"
adversarial_axis = "selectivity x correlation"

[targets.prefilter_exact]
module = "targets.prefilter_exact"
enabled = true

[targets.postfilter_topn]
module = "targets.postfilter_topn"
enabled = true
"""


def report_row(**fields):
    row = {
        "target": "t", "fixture": "correlated", "scenario": "c_candidate_expansion", "selectivity": 0.05,
        "pass_rate": 0.05, "k": 10, "search_value": 20, "recall_at_k": 0.5, "qps": 1.0, "p95_ms": 1.0,
        "pages_total_mean": 0.0, "plan_summary": "Limit > Index Scan", "plan_mode": "force_index",
        "recovery_search_value": None, "best_search_value": None, "best_recall": None,
    }
    row.update(fields)
    return row


class ReportTest(unittest.TestCase):
    def render(self, rows):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "r.json"
            path.write_text(json.dumps({"meta": {"run_id": "x", "command": "python run_bench.py",
                                                 "profile": "filtered-ann", "recall_threshold": 0.94},
                                        "results": rows}))
            proc = subprocess.run([sys.executable, "-B", "report.py", str(path)], cwd=HARNESS,
                                  capture_output=True, text=True, check=True)
        return proc.stdout

    def recovery_line(self, text, target):
        section = text.split("## Candidate-expansion recovery")[1]
        return next(line for line in section.splitlines() if line.startswith(f"| {target} |"))

    def test_recovery_marks_exact_path_and_shows_best_cell_plan(self):
        recovered = {"recovery_search_value": 80, "best_search_value": 320, "best_recall": 1.0}
        text = self.render([
            report_row(target="t", search_value=20, recall_at_k=0.5, plan_summary="Limit > Bitmap Heap Scan", **recovered),
            report_row(target="t", search_value=80, recall_at_k=0.95, plan_summary="Limit > Sort > Seq Scan", **recovered),
            report_row(target="t", search_value=320, recall_at_k=1.0, plan_summary="Limit > Index Scan", **recovered),
            report_row(target="exact", search_value=None, recall_at_k=1.0, plan_summary="python-exact"),
        ])
        self.assertIn("| t | correlated | 0.050 | 80 (exact path) | 1.000 @ 320 | Limit > Index Scan |",
                      self.recovery_line(text, "t"))
        self.assertIn("| no knob |", self.recovery_line(text, "exact"))
        self.assertIn("| pass rate |", text)
        self.assertIn("| recall (SOLID) | qps (INDICATIVE) | p95 ms (INDICATIVE) |", text)

    def test_exact_path_means_a_sort_over_unlimited_input(self):
        report = importlib.import_module("report")
        self.assertTrue(report.is_exact_path("Limit > Sort > Seq Scan"))
        self.assertTrue(report.is_exact_path("Limit > Sort > Bitmap Heap Scan > Bitmap Index Scan"))
        self.assertTrue(report.is_exact_path("Limit > Sort > Index Scan"))  # btree feeding a sort
        self.assertFalse(report.is_exact_path("Limit > Index Scan"))
        self.assertFalse(report.is_exact_path("Limit > Sort > Subquery Scan > Limit > Index Scan"))

    def test_recovery_marks_mixed_plans_and_misses(self):
        mixed = {"recovery_search_value": 20, "best_search_value": 20, "best_recall": 1.0,
                 "plan_summary": "mixed: Limit > Index Scan x6; Limit > Sort > Seq Scan x4"}
        text = self.render([
            report_row(target="m", search_value=20, recall_at_k=1.0, **mixed),
            report_row(target="n", search_value=20, recall_at_k=0.3, best_search_value=20, best_recall=0.3),
        ])
        self.assertIn("| 20 (mixed plans) |", self.recovery_line(text, "m"))
        self.assertIn("| not reached | 0.300 @ 20 |", self.recovery_line(text, "n"))


class EndToEndTest(unittest.TestCase):
    def test_missing_knob_values_fail_before_any_load(self):
        setups = []

        class RecordingTarget(PostfilterTopNTarget):
            def setup(self):
                setups.append(self)
                super().setup()

        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp) / "c.toml"
            config.write_text(SMALL_CONFIG.replace("search_values = [10, 200]\n", ""))
            argv = ["run_bench.py", "--config", str(config), "--output", str(Path(tmp) / "o.json")]
            with mock.patch.object(sys, "argv", argv), \
                    mock.patch.object(run_bench, "create_target", lambda module, cfg: RecordingTarget(cfg)):
                with self.assertRaises(SystemExit):
                    run_bench.main()
        self.assertEqual(setups, [])

    def test_run_bench_writes_labeled_rows_for_every_fixture(self):
        with tempfile.TemporaryDirectory() as tmp:
            config, output = Path(tmp) / "c.toml", Path(tmp) / "out.json"
            config.write_text(SMALL_CONFIG)
            proc = subprocess.run(
                [sys.executable, "-B", "run_bench.py", "--config", str(config), "--output", str(output)],
                cwd=HARNESS, capture_output=True, text=True,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(proc.stderr, "")  # no pass-rate or far-query warnings
            artifact = json.loads(output.read_text())
        rows = artifact["results"]
        # per fixture: prefilter (no knob) A2 B1 C2 D1 = 6; postfilter (2 knobs) A4 B2 C4 D2 = 12
        self.assertEqual(len(rows), 2 * (6 + 12))
        self.assertEqual({row["fixture"] for row in rows}, set(FIXTURES))
        for row in rows:
            self.assertEqual((row["trust_recall"], row["trust_perf"]), ("SOLID", "INDICATIVE"))
            self.assertAlmostEqual(row["pass_rate"], float(row["selectivity"]))
            self.assertIn(row["plan_mode"], {"planner", "force_index"})
        self.assertEqual(artifact["meta"]["profile"], "filtered-ann")
        self.assertEqual(set(artifact["meta"]["targets"]), {"prefilter_exact", "postfilter_topn"})


if __name__ == "__main__":
    unittest.main()
