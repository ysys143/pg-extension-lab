from __future__ import annotations

from typing import Any


def summarize_explain(plan_json: Any) -> dict[str, Any]:
    root = plan_json[0]["Plan"] if isinstance(plan_json, list) else plan_json["Plan"]
    # Buffer counts accumulate up the tree: the root's numbers cover the whole query, including
    # InitPlans, SubPlans, CTEs, and parallel workers. Lower nodes repeat or overlap those counts,
    # so summing nodes (or a node's children) over-counts.
    totals: dict[str, Any] = {
        "pages_hit": int(root.get("Shared Hit Blocks", 0)),
        "pages_read": int(root.get("Shared Read Blocks", 0)),
        "pages_dirtied": int(root.get("Shared Dirtied Blocks", 0)),
        "pages_written": int(root.get("Shared Written Blocks", 0)),
    }
    # The node path, not just the root (always Limit here), shows whether the index ran.
    nodes: list[str] = []

    def walk(node: dict[str, Any]) -> None:
        nodes.append(node.get("Node Type", "unknown"))
        for child in node.get("Plans", []):
            walk(child)

    walk(root)
    totals["plan_summary"] = " > ".join(nodes)
    totals["pages_total"] = totals["pages_hit"] + totals["pages_read"]
    return totals
