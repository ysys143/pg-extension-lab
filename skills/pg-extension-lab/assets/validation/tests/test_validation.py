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

    def test_unknown_profile_is_an_error(self):
        config = {"run": {"seed": 1, "output": "x.json"}, "methodology": {"profile": "nope", "adversarial_axis": "x"}}
        self.assertEqual(rules(check_methodology.check_config(config), "error"), {"CFG-PROFILE"})


HEADER = "# Report\n\n- run_id: `20261023-000000`\n- command: `python run_bench.py --config c.toml`\n"


class ReportLintTest(unittest.TestCase):
    def test_all_solid_report_with_timing_fails(self):
        text = HEADER + "\n| recall | qps | p95 ms | trust |\n|---|---|---|---|\n| 0.95 | 100 | 3.0 | SOLID |\n"
        self.assertIn("RPT-TRUST-SPLIT", rules(lint_report.lint(text, "r.md"), "error"))

    def test_filtered_ann_report_without_pass_rate_fails(self):
        text = HEADER + "- profile: filtered-ann\n\n| sel | recall (SOLID) | qps (INDICATIVE) |\n"
        self.assertIn("RPT-PASSRATE", rules(lint_report.lint(text, "r.md"), "error"))

    def test_generic_report_needs_no_recall(self):
        text = HEADER + "\n| delivered exactly once (SOLID) | p95 ms (INDICATIVE) |\n"
        self.assertEqual(lint_report.lint(text, "r.md"), [])

    def test_split_labeled_filtered_ann_report_passes(self):
        text = HEADER + (
            "- profile: filtered-ann\n\n"
            "| sel | pass rate | recall (SOLID) | qps (INDICATIVE) | p95 ms (INDICATIVE) |\n"
        )
        self.assertEqual(lint_report.lint(text, "r.md"), [])


if __name__ == "__main__":
    unittest.main()
