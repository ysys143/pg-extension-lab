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

# Timing figures that a shared host cannot make SOLID.
PERF_PATTERN = r"\bqps\b|\bp(?:50|95|99)|\blatency\b|_ms\b|\bms\b"
TIMING_CELL = re.compile(r"\bqps\b|\bp(?:50|95|99)\b|\blatency\b|\bms\b", re.IGNORECASE)
SEPARATOR_ROW = re.compile(r"^\s*\|[\s:|-]+\|\s*$")


def table_header_cells(text: str) -> list[str]:
    """Header cells of every markdown table (a pipe row followed by a separator row)."""
    lines = text.splitlines()
    cells: list[str] = []
    for line, following in zip(lines, lines[1:]):
        if line.strip().startswith("|") and SEPARATOR_ROW.match(following):
            cells += [cell.strip() for cell in line.strip().strip("|").split("|")]
    return cells


def lint(text: str, name: str) -> list[Finding]:
    findings: list[Finding] = []
    lines = text.splitlines()
    headline = "\n".join(lines[:HEADLINE_LINES]).lower()
    headers = table_header_cells(text)
    timing_cells = [cell for cell in headers if TIMING_CELL.search(cell)]

    if not re.search(r"run[_ ]?id", text, re.IGNORECASE):
        findings.append(("error", "RPT-RUNID",
                         f"{name}: no run_id — evidence must be attributable to one run"))
    if not re.search(r"command.*`.+`|`python .*`|`make .*`", text):
        findings.append(("error", "RPT-REPRO",
                         f"{name}: no exact reproduce command — put the command that produced "
                         "the artifact in the report"))
    if not re.search(r"\b(SOLID|INDICATIVE)\b", text):
        findings.append(("error", "RPT-TRUST",
                         f"{name}: no trust labels — label oracle-scored quality SOLID and "
                         "shared-host timing INDICATIVE"))
    else:
        # Per metric: each timing column is labeled INDICATIVE in its own header, never SOLID,
        # and a quality column is never INDICATIVE. Prose-only reports fall back to one label.
        mislabeled = [cell for cell in timing_cells if "INDICATIVE" not in cell or "SOLID" in cell]
        mislabeled += [cell for cell in headers if re.search(r"\brecall\b", cell, re.IGNORECASE)
                       and "INDICATIVE" in cell]
        if mislabeled:
            findings.append(("error", "RPT-TRUST-SPLIT",
                             f"{name}: columns with the wrong trust label {mislabeled} — timing "
                             "columns INDICATIVE, oracle-scored quality SOLID, per column"))
        elif (not timing_cells and re.search(PERF_PATTERN, text, re.IGNORECASE)
              and not re.search(r"\bINDICATIVE\b", text)):
            findings.append(("error", "RPT-TRUST-SPLIT",
                             f"{name}: latency/throughput figures carry no INDICATIVE label — label "
                             "per metric, not per row"))
    if re.search(r"\bmin[_ ]?ms\b", headline):
        findings.append(("error", "RPT-MINMS",
                         f"{name}: min_ms appears in the headline zone — min_ms is never a "
                         "headline; lead with the quality metric and a trust-labeled percentile"))
    if re.search(r"profile:\s*filtered-ann", text, re.IGNORECASE):
        findings += lint_filtered_ann(headers, name)
    return findings


def lint_filtered_ann(headers: list[str], name: str) -> list[Finding]:
    """PROFILE — reports whose header declares `profile: filtered-ann`. Checks the result-table
    columns, not prose, so boilerplate cannot satisfy them."""
    findings: list[Finding] = []
    if not any(re.search(r"pass[ _]rate", cell, re.IGNORECASE) for cell in headers):
        findings.append(("error", "RPT-PASSRATE",
                         f"{name}: filtered-ann report without a measured pass-rate column — show "
                         "the realized selectivity next to the configured one"))
    if not any(re.search(r"\brecall\b", cell, re.IGNORECASE) for cell in headers):
        findings.append(("warn", "RPT-RECALL",
                         f"{name}: no recall column — engine comparisons must be at matched "
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
