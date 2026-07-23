"""Report linter: reject REPORT_*.md files that violate reporting principles BEFORE review.

Each rule ID maps to a cross-cutting principle in SKILL.md (see validation/README.md).

Usage:
    python lint_report.py REPORT_smoke.md [REPORT_other.md ...]
Exit codes: 0 ok, 1 warnings only, 2 errors.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

Finding = tuple[str, str, str]  # (severity, rule_id, message)

# The headline zone is everything before the first section break after the lead table,
# approximated as: title lines, meta bullets, and the first markdown table header row.
HEADLINE_LINES = 15


def lint(text: str, name: str) -> list[Finding]:
    findings: list[Finding] = []
    lines = text.splitlines()
    headline = "\n".join(lines[:HEADLINE_LINES]).lower()

    if not re.search(r"run[_ ]?id", text, re.IGNORECASE):
        findings.append(("error", "RPT-RUNID",
                         f"{name}: no run_id — evidence must be attributable to one run"))
    if not re.search(r"command.*`.+`|`python .*`|`make .*`", text):
        findings.append(("error", "RPT-REPRO",
                         f"{name}: no exact reproduce command — put the command that produced "
                         "the artifact in the report"))
    if not re.search(r"\b(SOLID|INDICATIVE)\b", text):
        findings.append(("error", "RPT-TRUST",
                         f"{name}: no trust labels — label recall SOLID and shared-host "
                         "latency INDICATIVE"))
    if re.search(r"\bmin[_ ]?ms\b", headline):
        findings.append(("error", "RPT-MINMS",
                         f"{name}: min_ms appears in the headline zone — min_ms is never a "
                         "headline; lead with recall and a trust-labeled percentile"))
    if not re.search(r"\brecall\b", text, re.IGNORECASE):
        findings.append(("warn", "RPT-RECALL",
                         f"{name}: no recall mentioned — engine comparisons must be at matched "
                         "recall, not matched knobs"))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Report linter for REPORT_*.md evidence files.")
    parser.add_argument("reports", nargs="+", type=Path)
    args = parser.parse_args()

    findings: list[Finding] = []
    for path in args.reports:
        findings += lint(path.read_text(encoding="utf-8"), path.name)

    for severity, rule, message in findings:
        print(f"{severity.upper()} {rule}: {message}", file=sys.stderr)
    errors = sum(1 for s, _, _ in findings if s == "error")
    warns = len(findings) - errors
    print(f"report lint: {len(args.reports)} file(s), {errors} error(s), {warns} warning(s)")
    return 2 if errors else (1 if warns else 0)


if __name__ == "__main__":
    raise SystemExit(main())
