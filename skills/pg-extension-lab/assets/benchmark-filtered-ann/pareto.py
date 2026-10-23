from __future__ import annotations

import json
import sys
from pathlib import Path


def dominated(a, b) -> bool:
    return b["recall_at_k"] >= a["recall_at_k"] and b["qps"] >= a["qps"] and (
        b["recall_at_k"] > a["recall_at_k"] or b["qps"] > a["qps"]
    )


def frontier_groups(rows: list[dict]) -> list[dict]:
    """One recall-QPS frontier per (target, scenario, fixture, selectivity).

    Dominance is only meaningful inside one engine at one operating condition; comparing a 1%
    point with a 10% point would drop cells that are optimal for their own selectivity.
    """
    groups: dict[tuple, list[dict]] = {}
    for row in rows:
        key = (row["target"], row["scenario"], row.get("fixture"), row.get("selectivity"))
        groups.setdefault(key, []).append(row)
    out = []
    for (target, scenario, fixture, selectivity), members in groups.items():
        frontier = [row for row in members if not any(dominated(row, other) for other in members)]
        out.append({
            "target": target,
            "scenario": scenario,
            "fixture": fixture,
            "selectivity": selectivity,
            "frontier": frontier,
        })
    return out


def main() -> int:
    artifact = json.loads(Path(sys.argv[1]).read_text())
    print(json.dumps(frontier_groups(artifact["results"]), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
