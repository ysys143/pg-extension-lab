# Validation — deterministic pre-run / pre-review gates

Two small stdlib-only scripts that move methodology enforcement from agent judgment into
deterministic code. Structural validity (sections exist, SQL present) stays in each harness's
own `--validate-config`; these check a different layer: **is the plan methodologically
admissible, and is the report honest?** Run them before any benchmark run and before any
report review — a violation should be rejected *before* it costs a run or misleads a reader.

```bash
# before running: reject an inadmissible plan
python validation/check_methodology.py \
  --config bench/bench_config.toml --plan bench/parameter_space.toml

# before reviewing: reject a dishonest report
python validation/lint_report.py bench/REPORT_*.md
```

Exit codes: `0` clean, `1` warnings only, `2` errors (gate CI on `!= 2`, or on `!= 0` when
strict).

## Rule ↔ principle traceability

Every rule ID maps to a cross-cutting principle in `SKILL.md`. Prose states the why; the rule
enforces the detectable part. When a principle gains a mechanically checkable form, promote it
here instead of adding more prose.

### Generic rules — every benchmark

| Rule | Severity | Enforces (SKILL.md principle) |
|---|---|---|
| `CFG-SEED` | error | Reproducibility is non-negotiable — fix every seed |
| `CFG-OUTPUT` | warn | Version what changes the claim — results are artifacts |
| `CFG-ADVERSARIAL-AXIS` | warn | Adversarial fixture — declare `[methodology] adversarial_axis`, the input that should break the fast path |
| `CFG-PROFILE` | error | A declared `[methodology] profile` must name a known case |
| `PLAN-BUDGET` | error | Bounded parameter space — explicit cell/time budget |
| `PLAN-FRONTIER` | error | Parameter space is a landscape — declare decision-changing cells |
| `PLAN-SCOUT` | warn | One-axis scouts before multi-axis runs |
| `PLAN-GRID` | error/warn | Do not worship exhaustive grids (policy seam: `budget_verdict()`) |
| `PLAN-PRUNED` | warn | Scout must prune — locate knees/cliffs before frontier spend |
| `RPT-RUNID` | error | Feedback must remain attributable |
| `RPT-REPRO` | error | Exact reproduce commands at the bottom of every report |
| `RPT-TRUST` | error | Trust labeling — oracle-scored quality SOLID, shared-host timing INDICATIVE |
| `RPT-TRUST-SPLIT` | error | Label per metric: every timing column header (qps, p50/p95/p99, ms, latency) says INDICATIVE and not SOLID, and no recall column says INDICATIVE; a report without tables needs at least one INDICATIVE label |
| `RPT-MINMS` | error | `min_ms` is never a headline |

### Case rules — `profile = "filtered-ann"`

Applied by `check_methodology.py` when the config declares `[methodology] profile =
"filtered-ann"`, and by `lint_report.py` when the report header carries `profile: filtered-ann`
(the filtered-ANN `report.py` writes it). See
[`references/benchmarking/filtered-ann-case.md`](../../references/benchmarking/filtered-ann-case.md).

| Rule | Severity | Enforces |
|---|---|---|
| `CFG-SELECTIVITY` | error | Selectivity is this case's first-class axis |
| `CFG-ADVERSARIAL` | warn | `dataset.fixtures` includes `correlated`, this case's honest worst case |
| `RPT-PASSRATE` | error | Record measured pass rates — a result-table column for the realized selectivity (prose does not count) |
| `RPT-RECALL` | warn | Matched recall, not matched knobs — a recall column in a result table |

A new case adds one function to `PROFILE_CHECKS` in `check_methodology.py` (and, if its reports
need it, one to `lint_report.py`) instead of tightening the generic rules for everyone.

## Policy seam

`check_methodology.py::budget_verdict()` encodes *when a frontier plan is admissible* relative
to its budget and the full grid. The default is: over budget = error; frontier covering >50%
of the full grid (grid > 8) = warn. This threshold is a judgment call about your run costs —
edit that one function to tighten or loosen the gate; everything else is mechanical.

## Copy workflow

Copy `validation/` next to the benchmark harness in the target repo (e.g. `bench/validation/`)
and wire both scripts into the same CI job that runs the benchmark smoke test. A report
committed without passing `lint_report.py` should fail review by machine, not by memory.
