from __future__ import annotations

from typing import Any


def summarize_explain(plan_json: Any) -> dict[str, Any]:
    root = plan_json[0]["Plan"] if isinstance(plan_json, list) else plan_json["Plan"]
    totals = {
        "pages_hit": 0,
        "pages_read": 0,
        "pages_dirtied": 0,
        "pages_written": 0,
        "plan_summary": root.get("Node Type", "unknown"),
    }

    def walk(node: dict[str, Any]) -> None:
        totals["pages_hit"] += int(node.get("Shared Hit Blocks", 0))
        totals["pages_read"] += int(node.get("Shared Read Blocks", 0))
        totals["pages_dirtied"] += int(node.get("Shared Dirtied Blocks", 0))
        totals["pages_written"] += int(node.get("Shared Written Blocks", 0))
        for child in node.get("Plans", []):
            walk(child)

    walk(root)
    totals["pages_total"] = totals["pages_hit"] + totals["pages_read"]
    return totals

