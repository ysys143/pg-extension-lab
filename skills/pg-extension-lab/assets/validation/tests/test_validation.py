"""Gate self-tests (stdlib only). Run from the validation directory:

    python -B -m unittest discover -s tests -v
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import check_methodology  # noqa: E402
import lint_report  # noqa: E402


def rules(findings, severity=None):
    return {rule for sev, rule, _ in findings if severity is None or sev == severity}


def table(*headers: str) -> str:
    return "\n| " + " | ".join(headers) + " |\n|" + "---|" * len(headers) + "\n"


class ConfigGateTest(unittest.TestCase):
    def test_generic_config_without_profile_passes(self):
        config = {
            "run": {"seed": 1, "output": "outbox_throughput.json"},
            "methodology": {"adversarial_axis": "burst size x worker crash"},
            "dataset": {"name": "outbox-burst", "rows": 100000},
        }
        self.assertEqual(check_methodology.check_config(config), [])

    def test_missing_adversarial_axis_is_a_warning(self):
        findings = check_methodology.check_config({"run": {"seed": 1, "output": "x.json"}})
        self.assertEqual(rules(findings), {"CFG-ADVERSARIAL-AXIS"})
        self.assertEqual(rules(findings, "error"), set())

    def test_filtered_ann_profile_requires_selectivities(self):
        config = {
            "run": {"seed": 1, "output": "x.json"},
            "methodology": {"profile": "filtered-ann", "adversarial_axis": "selectivity"},
            "dataset": {"fixtures": ["uncorrelated"]},
        }
        findings = check_methodology.check_config(config)
        self.assertIn("CFG-SELECTIVITY", rules(findings, "error"))
        self.assertIn("CFG-ADVERSARIAL", rules(findings, "warn"))

    def test_missing_fixtures_means_correlated_like_run_bench(self):
        config = {
            "run": {"seed": 1, "output": "x.json"},
            "methodology": {"profile": "filtered-ann", "adversarial_axis": "selectivity"},
            "dataset": {"selectivities": [0.01]},
        }
        self.assertEqual(check_methodology.check_config(config), [])

    def test_unknown_profile_is_an_error(self):
        config = {"run": {"seed": 1, "output": "x.json"}, "methodology": {"profile": "nope", "adversarial_axis": "x"}}
        self.assertEqual(rules(check_methodology.check_config(config), "error"), {"CFG-PROFILE"})


HEADER = "# Report\n\n- run_id: `20261023-000000`\n- command: `python run_bench.py --config c.toml`\n"
FILTERED = HEADER + "- profile: filtered-ann\n"


class ReportLintTest(unittest.TestCase):
    def errors(self, text):
        return rules(lint_report.lint(text, "r.md"), "error")

    def test_row_level_trust_column_fails(self):
        text = HEADER + table("recall", "qps", "p95 ms", "trust") + "| 0.95 | 100 | 3.0 | SOLID |\n"
        self.assertIn("RPT-TRUST-SPLIT", self.errors(text))

    def test_flipped_labels_fail(self):
        text = HEADER + table("recall (INDICATIVE)", "qps (SOLID)", "p95 ms (SOLID)")
        self.assertIn("RPT-TRUST-SPLIT", self.errors(text))

    def test_recall_labeled_indicative_fails(self):
        text = HEADER + table("recall (INDICATIVE)", "qps (INDICATIVE)", "p95 ms (INDICATIVE)")
        self.assertIn("RPT-TRUST-SPLIT", self.errors(text))

    def test_snake_case_headers_are_checked(self):
        for header in ("p95_ms (SOLID)", "p99_ms", "latency_ms (SOLID)", "throughput (SOLID)"):
            text = HEADER + table("recall (SOLID)", header)
            self.assertIn("RPT-TRUST-SPLIT", self.errors(text), header)
        self.assertIn("RPT-TRUST-SPLIT", self.errors(HEADER + table("recall_at_k (INDICATIVE)", "qps (INDICATIVE)")))

    def test_snake_case_filtered_ann_report_passes(self):
        text = FILTERED + table("selectivity", "pass_rate", "recall_at_k (SOLID)", "p95_ms (INDICATIVE)")
        self.assertEqual(lint_report.lint(text, "r.md"), [])

    def test_one_unlabeled_timing_column_fails(self):
        text = HEADER + table("recall (SOLID)", "qps (INDICATIVE)", "p95 ms")
        self.assertIn("RPT-TRUST-SPLIT", self.errors(text))

    def test_prose_only_report_needs_one_indicative_label(self):
        self.assertIn("RPT-TRUST-SPLIT", self.errors(HEADER + "\nrecall 0.95 SOLID, qps about 100.\n"))
        self.assertEqual(self.errors(HEADER + "\nrecall 0.95 SOLID, qps about 100 INDICATIVE.\n"), set())

    def test_filtered_ann_report_without_pass_rate_column_fails(self):
        text = FILTERED + table("sel", "recall (SOLID)", "qps (INDICATIVE)")
        self.assertIn("RPT-PASSRATE", self.errors(text))

    def test_pass_rate_in_prose_does_not_satisfy_the_column_rule(self):
        text = FILTERED + "\nThe pass rate is recorded elsewhere.\n" + table("sel", "recall (SOLID)", "qps (INDICATIVE)")
        self.assertIn("RPT-PASSRATE", self.errors(text))

    def test_generic_report_needs_no_recall(self):
        text = HEADER + table("delivered exactly once (SOLID)", "p95 ms (INDICATIVE)")
        self.assertEqual(lint_report.lint(text, "r.md"), [])

    def test_split_labeled_filtered_ann_report_passes(self):
        text = FILTERED + table("sel", "pass rate", "recall (SOLID)", "qps (INDICATIVE)", "p95 ms (INDICATIVE)")
        self.assertEqual(lint_report.lint(text, "r.md"), [])


if __name__ == "__main__":
    unittest.main()
