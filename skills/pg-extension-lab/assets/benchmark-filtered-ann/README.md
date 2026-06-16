# Filtered ANN benchmark harness

Portable harness for filtered vector/index benchmarks. It preserves the protocol from the
reference projects while keeping extension-specific behavior behind target adapters.

The core harness is generic. `targets/postgres_sql.py` is a config-driven adapter for ordinary
SQL-callable extension paths. `examples/pgvector_target.py` is a worked example, not the core
abstraction.

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
```

6. Run a smoke benchmark against a database:

```bash
python run_bench.py --config bench_config.toml --scenario a --output results_smoke.json
python report.py results_smoke.json > REPORT_smoke.md
```

For a pgvector-specific worked example, use:

```bash
python run_bench.py --validate-config --config bench_config.pgvector-example.toml
python run_bench.py --config bench_config.pgvector-example.toml --scenario a
```

## Target adapter contract

Targets expose `setup`, `query_filtered`, `explain_filtered`, `force_index_scan`,
`set_search_knob`, `insert_batch`, `teardown`, and `close`. Scenarios define what is measured;
targets define how a backend performs that measurement.

Do not expand target APIs just because dependency APIs exist. Use docs to find the intended
contract, inspect code/schema/tests to confirm the real contract, then add only the adapter
methods the benchmark scenario needs.

## Generic SQL adapter

`targets/postgres_sql.py` executes SQL templates from `[postgres_sql]`. Use `{name}` placeholders
for identifiers controlled by `[postgres_sql.context]`; use bind parameters for runtime values.
`insert_params` and `query_params` define bind order using `id`, `query_vector`, `filter_value`,
and `k`. This keeps extension-specific SQL in config until custom Python is genuinely needed.
