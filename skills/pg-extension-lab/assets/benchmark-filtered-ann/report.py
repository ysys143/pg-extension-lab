from __future__ import annotations

import json
import sys
from pathlib import Path

TRUST_TABLE = """| metric | trust | why |
|---|---|---|
| recall@k vs exact filtered ground truth | SOLID | deterministic oracle, host-independent |
| realized selectivity (fixture count) | SOLID | counted from the fixture, not timed |
| qps, p95 ms | INDICATIVE | shared-host timing; qps is single-client serial over target calls only |
| pages/query | INDICATIVE | from a separate EXPLAIN (ANALYZE, BUFFERS) re-execution, not the timed call |

`plan` is the EXPLAIN node path per cell, followed by the plan mode the harness requested
(`planner` lets PostgreSQL choose; `force_index` asks for the index). Check it before reading
recall as index quality: an exact path (Seq Scan or Bitmap Heap Scan, then Sort) scores 1.0 by
construction."""


def fmt_search(value) -> str:
    return "-" if value is None else str(value)


def recovery_label(row: dict) -> str:
    if row["search_value"] is None:
        return "no knob"
    value = row.get("recovery_search_value")
    return "not reached" if value is None else str(value)


def best_label(row: dict) -> str:
    if row.get("best_search_value") is None:
        return "-"
    return f"{row['best_recall']:.3f} @ {row['best_search_value']}"


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
    for name, info in meta.get("targets", {}).items():
        if info:
            print(f"- {name}: " + ", ".join(f"{key} {value}" for key, value in sorted(info.items())))
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
            f"{row['pages_total_mean']:.2f} | {row.get('plan_summary', '')} ({row.get('plan_mode', '')}) |"
        )

    recovery_rows: dict[tuple, dict] = {}
    for row in rows:
        if row["scenario"] == "c_candidate_expansion":
            key = (row["target"], row["fixture"], row["selectivity"])
            if row.get("best_search_value") is not None and row["search_value"] == row["best_search_value"]:
                recovery_rows[key] = row
            else:
                recovery_rows.setdefault(key, row)
    if recovery_rows:
        print("\n## Candidate-expansion recovery (scenario C, index path forced)\n")
        print(f"Lowest search value reaching recall >= {meta.get('recall_threshold')}; when none does, the")
        print("best cell is the max-recall operating point. `plan` belongs to the best cell.\n")
        print("| target | fixture | sel | recovery search value | best recall @ search | plan |")
        print("|---|---|---:|---:|---:|---|")
        for (target, fixture, sel), row in recovery_rows.items():
            print(
                f"| {target} | {fixture} | {float(sel):.3f} | {recovery_label(row)} | {best_label(row)} | "
                f"{row.get('plan_summary', '')} |"
            )

    print("\n## Reproduce\n")
    print("```bash")
    print(meta.get("command"))
    print(f"python report.py {sys.argv[1]}")
    print("```")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
