from __future__ import annotations

import argparse
import importlib
import json
import platform
import re
import sys
import time
import tomllib
from pathlib import Path

from fixtures.synthetic import (
    BUCKETS,
    FIXTURES,
    filter_value_for_selectivity,
    make_dataset,
    make_workload,
    pass_rate,
    representable_selectivity,
)
from targets.prefilter_exact import create_target as create_exact


SCENARIOS = {
    "a": "scenarios.a_selectivity_sweep",
    "b": "scenarios.b_postfilter_recall",
    "c": "scenarios.c_candidate_expansion",
    "d": "scenarios.d_correlation",
}

# The exact oracle ranks by L2 (targets/_metric.py); a target ordering by another metric would
# score its own exact path below 1.0.
ORACLE_OPERATOR = "<->"
RANGE_FILTER = re.compile(r"\{filter_column\}\s*<\s*%s")


def load_config(path: Path) -> dict:
    with path.open("rb") as f:
        return tomllib.load(f)


def validate_config(config: dict) -> list[str]:
    errors = []
    for section in ("run", "dataset", "targets"):
        if section not in config:
            errors.append(f"missing [{section}] section")
    if not errors:
        dataset = config["dataset"]
        for key in ("rows", "dims", "selectivities"):
            if key not in dataset:
                errors.append(f"missing dataset.{key}")
        for sel in dataset.get("selectivities", []):
            if not representable_selectivity(float(sel)):
                errors.append(f"dataset.selectivities: {sel} is not a multiple of 1/{BUCKETS} in (0, 1]")
        if "correlated" in dataset:
            errors.append('dataset.correlated was replaced by dataset.fixtures = ["correlated", "uncorrelated"]')
        fixtures = dataset.get("fixtures", ["correlated"])
        unknown = [name for name in fixtures if name not in FIXTURES]
        if not fixtures or unknown:
            errors.append(f"dataset.fixtures must be a non-empty subset of {list(FIXTURES)}")
        threshold = float(config["run"].get("recall_threshold", 0.94))
        if not 0 < threshold <= 1:
            errors.append("run.recall_threshold must be in (0, 1]")
        for name, item in config["targets"].items():
            if not item.get("enabled", False):
                continue
            if "module" not in item:
                errors.append(f"missing targets.{name}.module")
            if item.get("module") == "targets.postgres_sql":
                if "postgres_sql" not in config:
                    errors.append("targets.postgres_sql enabled but [postgres_sql] is missing")
                else:
                    for key in ("dsn", "insert_sql", "query_sql"):
                        if key not in config["postgres_sql"]:
                            errors.append(f"missing postgres_sql.{key}")
                    for key in ("query_sql", "explain_sql"):
                        sql = config["postgres_sql"].get(key)
                        if sql and not RANGE_FILTER.search(sql):
                            errors.append(f"postgres_sql.{key} must filter with {{filter_column}} < %s "
                                          "(rows pass below filter_value)")
            if item.get("module") == "examples.pgvector_target":
                operator = config.get("pgvector_example", {}).get("distance_operator", ORACLE_OPERATOR)
                if operator != ORACLE_OPERATOR:
                    errors.append(f"pgvector_example.distance_operator must be {ORACLE_OPERATOR}: "
                                  "the exact oracle ranks by L2")
    return errors


def pass_rate_warnings(rows: list, selectivities: list) -> list[str]:
    """Configured vs realized selectivity. A gap means the fixture does not test what the config says."""
    warnings = []
    for sel in selectivities:
        realized = pass_rate(rows, filter_value_for_selectivity(float(sel)))
        if abs(realized - float(sel)) > max(0.1 * float(sel), 1 / len(rows)):
            warnings.append(f"selectivity {sel}: realized pass rate {realized:.4f}")
    return warnings


def search_values_for(config: dict, target_name: str, target) -> list[int | None]:
    """Each target sweeps its own knob: [<target>].search_values, else [run].search_values."""
    if not getattr(target, "has_search_knob", True):
        return [None]
    values = config.get(target_name, {}).get("search_values") or config["run"].get("search_values")
    if not values:
        raise SystemExit(f"target {target_name} has a search knob but no search_values in "
                         f"[{target_name}] or [run]")
    return [int(v) for v in values]


def enabled_targets(config: dict) -> list[tuple[str, str]]:
    out = []
    for name, item in config["targets"].items():
        if item.get("enabled", False):
            out.append((name, item["module"]))
    return out


def create_target(module_name: str, config: dict):
    module = importlib.import_module(module_name)
    return module.create_target(config)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="bench_config.example.toml")
    parser.add_argument("--scenario", choices=["all", *SCENARIOS], default="all")
    parser.add_argument("--output")
    parser.add_argument("--validate-config", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    config = load_config(Path(args.config))
    errors = validate_config(config)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 2
    if args.validate_config:
        print("config ok")
        return 0

    dataset = config["dataset"]
    rows_n, dims, seed = int(dataset["rows"]), int(dataset["dims"]), int(config["run"]["seed"])
    fixtures = dataset.get("fixtures", ["correlated"])
    selectivities = dataset["selectivities"]
    k = config["run"]["k"]
    scenario_keys = list(SCENARIOS) if args.scenario == "all" else [args.scenario]
    target_specs = enabled_targets(config)

    if args.dry_run:
        print(json.dumps({
            "scenarios": scenario_keys,
            "targets": [name for name, _ in target_specs],
            "fixtures": fixtures,
            "rows": rows_n,
        }))
        return 0

    max_selectivity = max(float(s) for s in selectivities)
    if "d" in scenario_keys and "correlated" in fixtures and max_selectivity > 0.5:
        print("WARN far-queries: max selectivity > 0.5 leaves too little room above the passing "
              "range; scenario D will not stress correlation", file=sys.stderr)
    results = []
    started = time.time()
    # Create every target and resolve its knob sweep before loading anything, so a missing
    # search_values fails before any load and each target keeps one connection for all fixtures.
    opened = []
    targets = []
    try:
        for target_name, module_name in target_specs:
            target = create_target(module_name, config)
            opened.append(target)
            targets.append((target_name, target, search_values_for(config, target_name, target)))
        target_info: dict[str, dict] = {}
        for fixture in fixtures:
            rows = make_dataset(rows_n, dims, seed, fixture)
            for warning in pass_rate_warnings(rows, selectivities):
                print(f"WARN pass-rate [{fixture}] {warning}", file=sys.stderr)
            workload = make_workload(int(config["run"]["queries"]), dims, seed, fixture, max_selectivity)
            exact = create_exact(config)
            try:
                exact.setup()
                exact.insert_batch(rows)
                for target_name, target, search_values in targets:
                    try:
                        target.setup()
                        target.insert_batch(rows)
                        if target_name not in target_info:
                            target_info[target_name] = getattr(target, "describe", dict)()
                        for key in scenario_keys:
                            scenario = importlib.import_module(SCENARIOS[key])
                            for row in scenario.run(config, target, exact, workload, search_values):
                                row.update({
                                    "target": target_name,
                                    "dataset": dataset["name"],
                                    "fixture": fixture,
                                    "pass_rate": pass_rate(rows, row["filter_value"]),
                                    "k": k,
                                    "trust_recall": "SOLID",
                                    "trust_perf": "INDICATIVE",
                                })
                                results.append(row)
                    finally:
                        target.teardown()
            finally:
                exact.close()
    finally:
        for target in opened:
            target.close()

    artifact = {
        "meta": {
            "run_id": time.strftime("%Y%m%d-%H%M%S"),
            "command": " ".join(["python", *sys.argv]),
            "python": platform.python_version(),
            "elapsed_s": time.time() - started,
            "profile": config.get("methodology", {}).get("profile"),
            "recall_threshold": float(config["run"].get("recall_threshold", 0.94)),
            "targets": target_info,
        },
        "results": results,
    }
    output = Path(args.output or config["run"].get("output", "results.json"))
    output.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
