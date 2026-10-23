"""Methodology validator: reject benchmark plans that violate skill principles BEFORE any run.

Structural validity (sections exist, SQL present) is `run_bench.py --validate-config`'s job.
This script checks a different layer: whether the plan is *methodologically* admissible.
Each rule ID maps to a cross-cutting principle in SKILL.md (see validation/README.md).

Usage:
    python check_methodology.py --config bench_config.toml --plan parameter_space.toml
Exit codes: 0 ok, 1 warnings only, 2 errors.
"""

from __future__ import annotations

import argparse
import math
import sys
import tomllib
from pathlib import Path

# (severity, rule_id, message); severity is "error" or "warn"
Finding = tuple[str, str, str]


def load_toml(path: Path) -> dict:
    with path.open("rb") as f:
        return tomllib.load(f)


def check_config(config: dict) -> list[Finding]:
    """Generic rules apply to every benchmark; case rules apply only under [methodology] profile."""
    findings: list[Finding] = []
    run = config.get("run", {})
    methodology = config.get("methodology", {})

    if "seed" not in run:
        findings.append(("error", "CFG-SEED",
                         "run.seed missing — fix every seed (Reproducibility is non-negotiable)"))
    if "output" not in run:
        findings.append(("warn", "CFG-OUTPUT",
                         "run.output missing — result JSON must be a versioned artifact, not stdout"))
    if not methodology.get("adversarial_axis"):
        findings.append(("warn", "CFG-ADVERSARIAL-AXIS",
                         "methodology.adversarial_axis missing — name the input distribution that "
                         "should break the fast path (Adversarial fixture)"))

    profile = methodology.get("profile")
    if profile is not None:
        check = PROFILE_CHECKS.get(profile)
        if check is None:
            findings.append(("error", "CFG-PROFILE",
                             f"unknown methodology.profile {profile!r} — known: {sorted(PROFILE_CHECKS)}"))
        else:
            findings += check(config)
    return findings


def check_filtered_ann(config: dict) -> list[Finding]:
    """PROFILE — the filtered-ANN worked case (references/benchmarking/filtered-ann-case.md)."""
    findings: list[Finding] = []
    dataset = config.get("dataset", {})
    if not dataset.get("selectivities"):
        findings.append(("error", "CFG-SELECTIVITY",
                         "filtered-ann: dataset.selectivities missing/empty — selectivity is this "
                         "case's first-class axis"))
    if "correlated" not in dataset.get("fixtures", []):
        findings.append(("warn", "CFG-ADVERSARIAL",
                         "filtered-ann: dataset.fixtures lacks \"correlated\" — a correlated filter is "
                         "this case's honest worst case; justify its absence in the hypothesis doc"))
    return findings


# Case rules keyed by [methodology] profile. Add a case by adding one function here.
PROFILE_CHECKS = {"filtered-ann": check_filtered_ann}


def budget_verdict(frontier_cells: int, max_cells: int, full_grid: int) -> tuple[str, str]:
    """POLICY SEAM — when is a frontier plan admissible relative to its budget and the full grid?

    Default policy: over budget is an error; a frontier covering more than half of the full
    Cartesian product looks like an unpruned grid and gets a warning ("Do not worship
    exhaustive grids"). Tighten or loosen to taste.
    Returns (severity, message) or ("ok", "").
    """
    if frontier_cells > max_cells:
        return ("error",
                f"frontier plans {frontier_cells} cells > budget.max_cells={max_cells} — prune "
                "axes or raise the budget explicitly")
    if full_grid > 0 and frontier_cells > 0.5 * full_grid and full_grid > 8:
        return ("warn",
                f"frontier ({frontier_cells} cells) covers >50% of the full grid ({full_grid}) — "
                "looks like an exhaustive sweep; scout one axis at a time first")
    return ("ok", "")


def check_plan(plan: dict) -> list[Finding]:
    findings: list[Finding] = []
    budget = plan.get("budget", {})
    scout = plan.get("scout", {})
    frontier = plan.get("frontier", {})

    for key in ("max_cells", "max_minutes"):
        if key not in budget:
            findings.append(("error", "PLAN-BUDGET",
                             f"budget.{key} missing — bounded parameter-space exploration requires "
                             "an explicit budget"))
    if not scout:
        findings.append(("warn", "PLAN-SCOUT",
                         "[scout] missing — sweep one axis at a time before frontier cells"))
    if not frontier:
        findings.append(("error", "PLAN-FRONTIER",
                         "[frontier] missing — declare which cells can change a decision"))

    if frontier and "max_cells" in budget:
        frontier_cells = math.prod(len(v) for v in frontier.values() if isinstance(v, list)) or 0
        full_grid = math.prod(len(v) for v in scout.values() if isinstance(v, list)) if scout else 0
        severity, message = budget_verdict(frontier_cells, int(budget["max_cells"]), full_grid)
        if severity != "ok":
            findings.append((severity, "PLAN-GRID", message))

    if scout and frontier:
        unpruned = [axis for axis, values in frontier.items()
                    if axis in scout and sorted(scout[axis]) == sorted(values)]
        if unpruned and len(unpruned) == len(frontier):
            findings.append(("warn", "PLAN-PRUNED",
                             "every frontier axis equals its scout axis — the scout produced no "
                             "pruning; locate knees/cliffs before spending frontier runs"))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Methodology validator for benchmark configs and parameter-space plans.")
    parser.add_argument("--config", type=Path, help="bench_config.toml to check")
    parser.add_argument("--plan", type=Path, help="parameter_space.toml to check")
    args = parser.parse_args()
    if not args.config and not args.plan:
        parser.error("pass --config and/or --plan")

    findings: list[Finding] = []
    if args.config:
        findings += check_config(load_toml(args.config))
    if args.plan:
        findings += check_plan(load_toml(args.plan))

    for severity, rule, message in findings:
        print(f"{severity.upper()} {rule}: {message}", file=sys.stderr)
    errors = sum(1 for s, _, _ in findings if s == "error")
    warns = len(findings) - errors
    print(f"methodology check: {errors} error(s), {warns} warning(s)")
    return 2 if errors else (1 if warns else 0)


if __name__ == "__main__":
    raise SystemExit(main())
