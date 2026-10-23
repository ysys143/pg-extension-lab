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
| `targets/postfilter_topn.py` | Deterministic model of post-filtering with a candidate budget (`search_value` nearest rows, then filter). Not an ANN index; it lets the scenarios show real recall curves without a database. |
| `targets/postgres_sql.py` | SQL templates from `[postgres_sql]`. Has a knob only when `set_search_knob_sql` is set. |
| `examples/pgvector_target.py` | pgvector HNSW example; knob = `search_guc`. |

## Scenarios

| Key | File | Measures |
|---|---|---|
| A | `scenarios/a_selectivity_sweep.py` | recall/latency across every selectivity × knob, on correlated and uncorrelated fixtures |
| B | `scenarios/b_postfilter_recall.py` | post-filter recall failure at the lowest selectivity |
| C | `scenarios/c_candidate_expansion.py` | progressive recall recovery as candidate expansion grows; records the lowest knob reaching `run.recall_threshold` |
| D | `scenarios/d_correlation.py` | correlation stress: queries whose neighborhood fails the filter, index path forced; the uncorrelated fixture is the control |

## What the numbers mean

- Ground truth is computed once per (fixture, query set, filter), outside timing.
- `qps` is single-client serial throughput over target calls only. Recall scoring and EXPLAIN
  run after the timed window. Real throughput needs multiprocessing clients (methodology §7).
- `pages_*` come from a separate `EXPLAIN (ANALYZE, BUFFERS)` execution, not from the timed call.
- Each row carries `trust_recall = SOLID` and `trust_perf = INDICATIVE`; the report labels
  every column.
- Targets with `has_search_knob = False` run each cell once with `search_value = null`.

`sample_artifacts/` holds a real run of the shipped config; regenerate it with the commands in
its `REPORT_smoke.md`.

## Target adapter contract

Targets expose `setup`, `query_filtered`, `explain_filtered`, `force_index_scan`,
`set_search_knob`, `insert_batch`, `teardown`, `close`, and the `has_search_knob` attribute
(see `targets/base.py`).

Do not expand target APIs just because dependency APIs exist. Use docs to find the intended
contract, inspect code/schema/tests to confirm the real contract, then add only the adapter
methods the benchmark scenario needs.

## Generic SQL adapter

`targets/postgres_sql.py` executes SQL templates from `[postgres_sql]`. Use `{name}` placeholders
for identifiers controlled by `[postgres_sql.context]`; use bind parameters for runtime values.
`insert_params` and `query_params` define bind order using `id`, `query_vector`, `filter_value`,
and `k`. The query must filter with `{filter_column} < %s`. This keeps extension-specific SQL in
config until custom Python is genuinely needed.
