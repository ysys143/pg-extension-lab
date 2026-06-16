# Reusable harnesses

These assets are meant to be copied into another PostgreSQL extension repository and adapted
there. They are intentionally small: the goal is to preserve the hard-won thinking model and
protocol, not to vendor every result file from the reference projects.

## Copy workflow

1. Pick one asset folder under `../../assets/`.
2. Copy it into the target repo, usually under `bench/`, `test/`, `tools/`, or `docs/ops/`.
3. Edit only the declared configuration seams first:
   extension name, schema/table names, vector/filter columns, index DDL, search GUCs,
   service-boundary contracts, and dataset paths.
4. Run `--validate-config` or `--dry-run` before touching a live database/device.
5. Write a hypothesis and parameter-space plan before broad runs; use one-axis scouts and
   Pareto/frontier pruning before any multi-axis run.
6. Commit the config, result JSON/CSV, and generated report together. Never commit a report
   without the exact command and environment that produced it.

## Asset index

| Asset | Copy to | Use for | First command |
|---|---|---|---|
| `assets/testing/` | repo root or `test-harness/` | PGXS/pgrx test ladder, ACL audit, CI skeleton | `make installcheck` after editing `EXTENSION` |
| `assets/benchmark-filtered-ann/` | `bench/filtered-ann/` | filtered vector/index benchmarks with pages-per-query | `python run_bench.py --validate-config --config bench_config.example.toml` |
| `assets/benchmark-accelerator/` | `bench/accelerator/` | CPU/GPU or accelerator crossover, exact ground truth, recall scoring | `python gt.py --help` |
| `assets/operations/` | `docs/ops/` | release checklist, capacity plan, replica/bootstrap runbooks | copy then fill bracketed fields |

## Adaptation rule

Prefer adding a new target adapter over editing a scenario. Scenarios define what is measured;
targets define how a specific extension executes that measurement. If a benchmark conclusion
changes when a target adapter is renamed, the benchmark was coupled to the implementation and
needs to be split again.

## Evidence rule

Do not start by wiring every API exposed by a dependency. Read docs to locate the intended
contract, inspect code/schema/tests to find the real contract, then verify with the smallest
execution that can prove it. Reports must say which evidence source supports each claim.

## Mindset rule

Treat each harness as a feedback machine. If copying a script makes feedback slower, noisier,
or less attributable, adapt the harness before adding benchmark cells. The point is not more
automation; the point is sharper evidence.
