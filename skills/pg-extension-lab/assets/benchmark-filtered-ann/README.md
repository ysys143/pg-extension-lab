# Filtered ANN benchmark harness — worked case

Copy-ready harness for the filtered-ANN worked case
([`references/benchmarking/filtered-ann-case.md`](../../references/benchmarking/filtered-ann-case.md)).
It realizes the generic methodology
([`references/benchmarking/methodology.md`](../../references/benchmarking/methodology.md)) for
one kind of extension path: an approximate vector index queried with a filter. Selectivity ×
filter/geometry correlation is this case's adversarial axis and recall@k against exact filtered
ground truth is its quality metric; another extension path has its own axis and oracle.

Scenarios define what is measured; target adapters define how a backend performs it.
`targets/postgres_sql.py` is a config-driven adapter for SQL-callable paths and
`examples/pgvector_target.py` is a pgvector example; neither is the core abstraction.

## Adapt

1. Copy this directory to `bench/filtered-ann/`.
2. Edit `bench_config.example.toml` or copy it to `bench_config.toml`.
3. Start with one of two paths:
   - Generic SQL path: enable `targets.postgres_sql` and edit `[postgres_sql]` templates.
   - Custom path: copy `targets/adapter_template.py` and implement the target contract.
4. Write `hypothesis_template.md`, then generate a bounded parameter plan:

```bash
python design_space.py --space parameter_space.example.toml --mode scout --out scout_cells.json
python design_space.py --space parameter_space.example.toml --mode frontier --out frontier_cells.json
```

5. Validate without a database:

```bash
python run_bench.py --validate-config --config bench_config.toml
python run_bench.py --dry-run --config bench_config.toml --scenario a
python -B -m unittest discover -s tests -v
```

6. Run the database-free smoke (the shipped config compares `prefilter_exact` with the
   `postfilter_topn` model), then your own targets:

```bash
python run_bench.py --config bench_config.example.toml --output results_smoke.json
python report.py results_smoke.json > REPORT_smoke.md
python pareto.py results_smoke.json
```

For the pgvector example (needs PostgreSQL with pgvector and `psycopg`):

```bash
python run_bench.py --validate-config --config bench_config.pgvector-example.toml
python run_bench.py --config bench_config.pgvector-example.toml --scenario a
```

## Fixture and filter semantics

- A row passes when `bucket < round(selectivity * 100)` (`fixtures.synthetic.passes`).
  Selectivities must be multiples of 0.01; `--validate-config` rejects others.
- Fixtures are stratified, so the realized pass rate equals the configured selectivity to
  within one row. Every result row records `pass_rate`, and the runner warns on stderr if a
  fixture does not realize its selectivity.
- `dataset.fixtures` lists `correlated` (filter key follows the vector's position) and/or
  `uncorrelated` (filter key independent of geometry). Every scenario runs on every fixture.
- Queries are held out: drawn from the fixture's distribution, never copied from the data.

## Targets

| Target | Role |
|---|---|
| `targets/prefilter_exact.py` | Exact filtered top-k. The ground-truth oracle, and a baseline with recall 1.0 by construction. No search knob. |
| `targets/postfilter_topn.py` | Deterministic model of post-filtering with a candidate budget (`search_value` nearest rows, then filter). Not an ANN index; it lets the scenarios show real recall curves without a database. Its recall is meaningful, its timing is not: it ranks every row whatever the budget, so qps stays flat. |
| `targets/postgres_sql.py` | SQL templates from `[postgres_sql]`. Has a knob only when `set_search_knob_sql` is set. |
| `examples/pgvector_target.py` | pgvector HNSW example; knob = `search_guc`. |

## Scenarios

Every scenario runs on every fixture. `plan_mode` records what the harness asked for; the
report's `plan` column records what EXPLAIN says actually ran.

| Key | File | Plan mode | Measures |
|---|---|---|---|
| A | `scenarios/a_selectivity_sweep.py` | `planner` | every selectivity × knob with PostgreSQL free to choose (the EXPLAIN-regret view) |
| B | `scenarios/b_postfilter_recall.py` | `force_index` | post-filter recall failure at the lowest selectivity |
| C | `scenarios/c_candidate_expansion.py` | `force_index` | for every selectivity, recall recovering as candidate expansion grows: the lowest knob reaching `run.recall_threshold`, and the best cell when none does |
| D | `scenarios/d_correlation.py` | `force_index` | correlation stress: queries whose neighborhood fails the filter; the uncorrelated fixture is the control |

B's cells are the same measurement as C's lowest-selectivity cells, and on a target that cannot
force a plan (the in-memory models) also as A's. B exists so the failure point can be run and
read alone (`--scenario b`). Do not sum cells across scenarios.

## What the numbers mean

- Ground truth is computed once per (fixture, query set, filter), outside timing, and shared by
  every target, scenario, and knob value.
- The exact oracle ranks by L2 (`targets/_metric.py`). Targets must order by L2 too;
  `--validate-config` rejects a pgvector `distance_operator` other than `<->`.
- Each cell runs `run.warmup_passes` untimed passes (default 1), so cell order does not decide
  cache warmth.
- `qps` is single-client serial throughput over target calls only. Recall scoring and EXPLAIN
  run after the timed window. Real throughput needs multiprocessing clients (methodology §7).
- `pages_*` come from a separate `EXPLAIN (ANALYZE, BUFFERS)` execution, not from the timed call.
  `plan_summary` is the node path; a cell whose queries took different plans reads `mixed: …`.
- Each row carries `trust_recall = SOLID` and `trust_perf = INDICATIVE`; the report labels
  every column.
- Each target sweeps its own knob: `[<target>].search_values`, else `[run].search_values`.
  Targets with `has_search_knob = False` run each cell once with `search_value = null`.
- A target's optional `describe()` (PostgreSQL and extension versions for the SQL targets) is
  copied into `meta.targets`.

`sample_artifacts/` holds real runs, each regenerated with the commands at the bottom of its
report:

- `REPORT_smoke.md` — the shipped config, no database.
- `REPORT_pgvector_smoke.md` — `bench_config.pgvector-example.toml` against
  `docker run -d --rm -e POSTGRES_PASSWORD=postgres -p 5432:5432 pgvector/pgvector:pg17`
  (pgvector 0.8.7, PostgreSQL 17.11).
  - A: at 1,000 rows the planner picks `Seq Scan > Sort`, so its recall of 1.0 is the exact path.
  - B, C, D force the HNSW `Index Scan`. At 1% selectivity, B's post-filter recall is 0.00 → 0.10
    over `ef` 20 → 160 on the correlated fixture.
  - C never reaches 0.94 on the correlated fixture; its best cells are 0.10 / 0.20 / 0.35 at
    `ef` 160. The uncorrelated fixture reaches 0.94 only at 10% (`ef` 160).
  - D gives 0.0 at every `ef` on correlated far queries, while the uncorrelated control climbs
    from 0.19 to 0.98.

## Target adapter contract

Targets expose `setup`, `query_filtered`, `explain_filtered`, `force_index_scan`,
`set_search_knob`, `insert_batch`, `teardown`, `close`, the `has_search_knob` attribute, and
optionally `describe()` (see `targets/base.py`).

Do not expand target APIs just because dependency APIs exist. Use docs to find the intended
contract, inspect code/schema/tests to confirm the real contract, then add only the adapter
methods the benchmark scenario needs.

## Generic SQL adapter

`targets/postgres_sql.py` executes SQL templates from `[postgres_sql]`. Use `{name}` placeholders
for identifiers controlled by `[postgres_sql.context]`; use bind parameters for runtime values.
`insert_params` and `query_params` define bind order using `id`, `query_vector`, `filter_value`,
and `k`. The query must filter with `{filter_column} < %s`. This keeps extension-specific SQL in
config until custom Python is genuinely needed.
