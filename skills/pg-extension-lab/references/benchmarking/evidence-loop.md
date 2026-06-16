# Hypothesis, evidence, and report loop

Use this before a benchmark, performance change, planner investigation, or extension behavior
claim. The mindset behind it is in [`../mental-models.md`](../mental-models.md).

## The loop

1. **Hypothesis.** Write one falsifiable claim: "At recall >= 0.95, target A has lower
   pages/query than target B for correlated 5% filters."
2. **Validation design.** Name the smallest isolated test/benchmark that can disprove it, the
   fixed controls, and the acceptance threshold.
3. **Evidence.** Collect raw artifacts: config, seed, dataset hash, SQL, EXPLAIN JSON, result
   JSON/CSV, logs, and exact command.
4. **Report.** Generate the report from artifacts. Separate SOLID findings from INDICATIVE
   observations. Include caveats and self-corrections.
5. **Decision.** State whether the hypothesis survived, failed, or needs a narrower follow-up.

## Evidence balance

- Start with docs to learn the intended contract and available APIs.
- Inspect source code, SQL definitions, catalog state, and existing tests before accepting the
  docs as true.
- Confirm important behavior with execution: unit test, regression test, isolation test,
  `EXPLAIN`, benchmark smoke, or direct catalog query.
- If docs, API names, and code disagree, record the disagreement and trust the executable
  evidence until the docs are fixed.

## Parameter-space discipline

- Declare axes: dataset, selectivity, query count, k, build knobs, search knobs, planner knobs,
  hardware/runtime, concurrency, and target implementation.
- Mark each axis as fixed, scouted, swept, or held for follow-up.
- Scout one axis at a time to find useful ranges.
- Promote only frontier-changing cells to multi-axis runs.
- Compare Pareto curves, not isolated points: recall/QPS, recall/p95, recall/pages, and
  cost/query.
- Treat Pareto curves as suitability maps. Record where each option belongs, not only who wins.
- If an option appears absolutely dominant, turn that into a mechanism hypothesis and identify
  at least one dimension where the advantage should weaken or reverse.
- Put a hard cap on cells/runtime before running. A full Cartesian product is allowed only when
  the resulting cell count is tiny and written into the plan.

## Mechanism checks

When a result is surprisingly good, prefer an isolated verification: force the plan, toggle the
fast path, microbenchmark the cache, vary only selectivity, or measure page I/O. If isolation is
not practical, inspect source, EXPLAIN, counters, logs, and telemetry until the code path is
understood. A good result without a mechanism is provisional.

## Version-control targets

Commit or archive together:

- benchmark/test scripts and target adapters;
- configs, parameter-space plan, seeds, and fixture generation commands;
- small deterministic fixtures or dataset hashes for large fixtures;
- raw result JSON/CSV, EXPLAIN JSON samples, generated reports;
- CI/Docker/env definitions needed to reproduce the environment.

Do not commit:

- host-local caches, build artifacts, `__pycache__`, temporary result scratch files;
- large rebuildable datasets unless the dataset itself is the evidence artifact;
- device-side caches tied to a specific cluster timeline/system_identifier.

## Feedback philosophy

The scarce resource is not code; it is high-quality feedback. Prefer small isolated tests,
config validation, dry-runs, and Ring A/B smoke checks that fail in seconds. Slow full-suite
runs are promotion gates, not the main development loop.

The mental model is economic: every run spends time, attention, and machine state. A good run
buys down uncertainty. A bad run only creates numbers.
