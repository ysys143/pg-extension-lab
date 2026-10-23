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


def is_exact_path(plan: str) -> bool:
    """A Sort over unlimited input computes the distance order exactly over the filtered rows; a
    Sort over a Limit (an index's candidate set re-sorted) does not."""
    nodes = plan.split(" > ")
    return "Sort" in nodes and "Limit" not in nodes[nodes.index("Sort") + 1:]


def recovery_label(cells: list[dict]) -> str:
    if cells[0]["search_value"] is None:
        return "no knob"
    value = cells[0].get("recovery_search_value")
    if value is None:
        return "not reached"
    plan = next(str(c.get("plan_summary", "")) for c in cells if c["search_value"] == value)
    if plan.startswith("mixed:"):
        return f"{value} (mixed plans)"
    return f"{value} (exact path)" if is_exact_path(plan) else str(value)


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

    groups: dict[tuple, list[dict]] = {}
    for row in rows:
        if row["scenario"] == "c_candidate_expansion":
            groups.setdefault((row["target"], row["fixture"], row["selectivity"]), []).append(row)
    if groups:
        print("\n## Candidate-expansion recovery (scenario C, index path forced)\n")
        print(f"Lowest search value reaching recall >= {meta.get('recall_threshold')}; when none does, the")
        print("best cell is the max-recall operating point. A recovery cell that ran an exact path")
        print("(a Sort node) or mixed plans is marked; `plan` belongs to the best cell.\n")
        print("| target | fixture | sel | recovery search value | best recall @ search | plan |")
        print("|---|---|---:|---:|---:|---|")
        for (target, fixture, sel), cells in groups.items():
            best = next((c for c in cells if c["search_value"] is not None
                         and c["search_value"] == c.get("best_search_value")), cells[0])
            print(
                f"| {target} | {fixture} | {float(sel):.3f} | {recovery_label(cells)} | {best_label(best)} | "
                f"{best.get('plan_summary', '')} |"
            )

    print("\n## Reproduce\n")
    print("```bash")
    print(meta.get("command"))
    print(f"python report.py {sys.argv[1]}")
    print("```")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
