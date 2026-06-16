from __future__ import annotations

import json
import sys
from pathlib import Path


def dominated(a, b) -> bool:
    return b["recall_at_k"] >= a["recall_at_k"] and b["qps"] >= a["qps"] and (
        b["recall_at_k"] > a["recall_at_k"] or b["qps"] > a["qps"]
    )


def main() -> int:
    artifact = json.loads(Path(sys.argv[1]).read_text())
    rows = artifact["results"]
    frontier = [row for row in rows if not any(dominated(row, other) for other in rows)]
    print(json.dumps(frontier, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

