# Benchmark protocol for planner and accelerator claims

Use this when the benchmark needs to defend a planner, cost-model, GPU/accelerator, or
filtered-index conclusion.

## Stages

1. **Evidence intake.** Read the docs to identify intended contracts, then inspect source/code
   paths, catalog shape, or existing tests to find the executable contract. Do not start from
   API surface alone.
2. **Forced physical curves.** Force each candidate path and sweep the physical knobs. This
   answers what each implementation can do independent of planner choice.
3. **EXPLAIN regret.** Let PostgreSQL choose freely, then compare the chosen plan with forced
   alternatives at the same query/selectivity point. Record the performance gap and page I/O.
4. **Freeze/version.** Pin extension version, PostgreSQL version, dataset hash, GUCs, hardware,
   planner knobs, and cost constants. Retune only in a new versioned run.
5. **Full suite.** Run the broad scenario suite only after the first three stages are stable.

## Rings

| Ring | Purpose | Promotion gate |
|---|---|---|
| A | Tiny smoke, no device required where possible | scripts compile, config validates, report schema writes |
| B | Single-machine deterministic correctness | exact ground truth and recall match expectations |
| C | Realistic size/perf | stable frontier and pages/query metrics |
| D | External comparison or accelerator claim | cost-per-query and reproducibility artifacts complete |

## Result schema

Every row should carry at least the core fields:

```text
run_id, stage, ring, dataset, dataset_hash, postgres_version, extension_version,
target, scenario, k, recall_at_k (or the case's oracle-scored quality metric),
qps, p50_ms, p95_ms, p99_ms, trust_recall, trust_perf,
hardware, cost_model_version, command
```

Each worked case adds the fields that describe its conditions:

- filtered ANN: `fixture, selectivity, filter_value, pass_rate, search_value,
  pages_total_mean, pages_hit_mean, pages_read_mean, plan_summary`
- accelerator: `rows, dims, search_value, device, host, cost_usd_per_hour, energy_j_per_query`

Label trust per metric: `trust_recall = SOLID` for oracle-scored quality and `trust_perf =
INDICATIVE` for shared-host latency, throughput, and page counts. A single row-level label
cannot say both. Do not headline `min_ms`.

## Cost and energy

For accelerator comparisons, report same-box latency and either iso-dollar or iso-energy
normalization. If one path has fixed setup overhead and better scaling, report the crossover
point and the losing region, not only the best ratio.

## Combinatorial control

Use ring promotion plus Pareto pruning to prevent combinatorial explosion. Ring A validates
scripts and schemas. Ring B sweeps one axis at a time. Ring C runs only cells that can affect
the frontier or planner flip points. Ring D repeats the already-selected cells for external
comparison, not the full grid.

Version the parameter-space plan before execution. If a cell is added after seeing results,
mark it as exploratory in the report so it cannot masquerade as the predeclared comparison.
