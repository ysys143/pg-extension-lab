from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: python report.py results.json", file=sys.stderr)
        return 2
    artifact = json.loads(Path(sys.argv[1]).read_text())
    print("# Filtered ANN benchmark report\n")
    print(f"- run_id: `{artifact['meta'].get('run_id')}`")
    print(f"- command: `{artifact['meta'].get('command')}`")
    print("\n| target | scenario | sel | k | search | recall | qps | p95 ms | pages/query | trust |")
    print("|---|---|---:|---:|---:|---:|---:|---:|---:|---|")
    for row in artifact["results"]:
        print(
            f"| {row['target']} | {row['scenario']} | {row.get('selectivity', 0):.3f} | "
            f"{row['k']} | {row.get('search_value', '')} | {row['recall_at_k']:.3f} | "
            f"{row['qps']:.2f} | {row['p95_ms']:.2f} | {row['pages_total_mean']:.2f} | "
            f"{row['trust_label']} |"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

