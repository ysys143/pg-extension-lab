from __future__ import annotations

import argparse
import importlib
import json
import platform
import sys
import time
import tomllib
from pathlib import Path

from fixtures.synthetic import make_dataset, make_queries
from targets.prefilter_exact import create_target as create_exact


SCENARIOS = {
    "a": "scenarios.a_selectivity_sweep",
    "b": "scenarios.b_postfilter_recall",
    "c": "scenarios.c_incremental_recall",
    "d": "scenarios.d_correlation",
}


def load_config(path: Path) -> dict:
    with path.open("rb") as f:
        return tomllib.load(f)


def validate_config(config: dict) -> list[str]:
    errors = []
    for section in ("run", "dataset", "targets"):
        if section not in config:
            errors.append(f"missing [{section}] section")
    if not errors:
        for key in ("rows", "dims", "selectivities"):
            if key not in config["dataset"]:
                errors.append(f"missing dataset.{key}")
        for name, item in config["targets"].items():
            if item.get("enabled", False) and "module" not in item:
                errors.append(f"missing targets.{name}.module")
            if item.get("enabled", False) and item.get("module") == "targets.postgres_sql":
                if "postgres_sql" not in config:
                    errors.append("targets.postgres_sql enabled but [postgres_sql] is missing")
                else:
                    for key in ("dsn", "insert_sql", "query_sql"):
                        if key not in config["postgres_sql"]:
                            errors.append(f"missing postgres_sql.{key}")
    return errors


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

    rows = make_dataset(
        int(config["dataset"]["rows"]),
        int(config["dataset"]["dims"]),
        int(config["run"]["seed"]),
        bool(config["dataset"].get("correlated", True)),
    )
    queries = make_queries(rows, int(config["run"]["queries"]), int(config["run"]["seed"]))
    scenario_keys = list(SCENARIOS) if args.scenario == "all" else [args.scenario]
    target_specs = enabled_targets(config)

    if args.dry_run:
        print(json.dumps({"scenarios": scenario_keys, "targets": [name for name, _ in target_specs], "rows": len(rows)}))
        return 0

    exact = create_exact(config)
    exact.setup()
    exact.insert_batch(rows)
    results = []
    started = time.time()
    for target_name, module_name in target_specs:
        target = create_target(module_name, config)
        target.setup()
        target.insert_batch(rows)
        try:
            for key in scenario_keys:
                scenario = importlib.import_module(SCENARIOS[key])
                for row in scenario.run(config, target, exact, queries):
                    row.update({
                        "target": target_name,
                        "dataset": config["dataset"]["name"],
                        "k": config["run"]["k"],
                        "trust_label": "SOLID" if row.get("recall_at_k") is not None else "INDICATIVE",
                    })
                    results.append(row)
        finally:
            target.teardown()
            target.close()
    exact.close()

    artifact = {
        "meta": {
            "run_id": time.strftime("%Y%m%d-%H%M%S"),
            "command": " ".join(sys.argv),
            "python": platform.python_version(),
            "elapsed_s": time.time() - started,
        },
        "results": results,
    }
    output = Path(args.output or config["run"].get("output", "results.json"))
    output.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
