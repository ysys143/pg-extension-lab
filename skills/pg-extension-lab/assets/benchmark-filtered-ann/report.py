from __future__ import annotations

import json
import sys
from pathlib import Path

TRUST_TABLE = """| metric | trust | why |
|---|---|---|
| recall@k vs exact filtered ground truth | SOLID | deterministic oracle, host-independent |
| pass rate (realized selectivity) | SOLID | counted from the fixture |
| qps, p95 ms | INDICATIVE | shared-host timing; qps is single-client serial over target calls only |
| pages/query | INDICATIVE | from a separate EXPLAIN (ANALYZE, BUFFERS) re-execution, not the timed call |

`plan` is the most common EXPLAIN node path per cell: check it before reading recall as index
quality. An exact path (Seq Scan or Bitmap Heap Scan, then Sort) scores 1.0 by construction."""


def fmt_search(value) -> str:
    return "-" if value is None else str(value)


def recovery_label(row: dict) -> str:
    if row["search_value"] is None:
        return "no knob"
    value = row.get("recovery_search_value")
    return "not reached" if value is None else str(value)


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: python report.py results.json", file=sys.stderr)
        return 2
    artifact = json.loads(Path(sys.argv[1]).read_text())
    meta = artifact["meta"]
    rows = artifact["results"]
    print("# Filtered ANN benchmark report\n")
    print(f"- run_id: `{meta.get('run_id')}`")
    print(f"- profile: {meta.get('profile') or 'none'}")
    print(f"- command: `{meta.get('command')}`")
    print(f"- recall threshold for the matched-recall operating point: {meta.get('recall_threshold')}\n")
    print(TRUST_TABLE)
    print(
        "\n| target | fixture | scenario | sel | pass rate | k | search | recall (SOLID) | "
        "qps (INDICATIVE) | p95 ms (INDICATIVE) | pages/query (INDICATIVE) | plan |"
    )
    print("|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|")
    for row in rows:
        print(
            f"| {row['target']} | {row['fixture']} | {row['scenario']} | {float(row['selectivity']):.3f} | "
            f"{row['pass_rate']:.3f} | {row['k']} | {fmt_search(row['search_value'])} | "
            f"{row['recall_at_k']:.3f} | {row['qps']:.2f} | {row['p95_ms']:.2f} | "
            f"{row['pages_total_mean']:.2f} | {row.get('plan_summary', '')} |"
        )

    recovery_rows = {}
    for row in rows:
        if row["scenario"] == "c_candidate_expansion":
            recovery_rows.setdefault((row["target"], row["fixture"], row["selectivity"]), row)
    if recovery_rows:
        print("\n## Candidate-expansion recovery (scenario C)\n")
        print(f"Lowest search value reaching recall >= {meta.get('recall_threshold')}.\n")
        print("| target | fixture | sel | recovery search value |")
        print("|---|---|---:|---:|")
        for (target, fixture, sel), row in recovery_rows.items():
            print(f"| {target} | {fixture} | {float(sel):.3f} | {recovery_label(row)} |")

    print("\n## Reproduce\n")
    print("```bash")
    print(meta.get("command"))
    print(f"python report.py {sys.argv[1]}")
    print("```")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
