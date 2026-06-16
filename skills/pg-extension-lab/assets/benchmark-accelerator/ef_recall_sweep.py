from __future__ import annotations

import argparse
import csv
import subprocess


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--values", required=True, help="comma-separated search knob values")
    parser.add_argument("--command-template", required=True, help="use {value} and {results}")
    parser.add_argument("--recall-command-template", required=True, help="use {results}")
    parser.add_argument("--out", default="sweep.csv")
    args = parser.parse_args()
    with open(args.out, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["search_value", "results_file", "recall_output"])
        writer.writeheader()
        for value in [v.strip() for v in args.values.split(",") if v.strip()]:
            results = f"results_{value}.txt"
            subprocess.run(args.command_template.format(value=value, results=results), shell=True, check=True)
            recall = subprocess.check_output(
                args.recall_command_template.format(results=results), shell=True, text=True
            ).strip()
            writer.writerow({"search_value": value, "results_file": results, "recall_output": recall})
    print(args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

