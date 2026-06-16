from __future__ import annotations

import argparse
import itertools
import json
import tomllib
from pathlib import Path


def product_cells(space: dict[str, list]) -> list[dict]:
    keys = list(space)
    return [dict(zip(keys, values)) for values in itertools.product(*(space[k] for k in keys))]


def stable_key(cell: dict) -> tuple:
    return tuple(sorted((key, json.dumps(value, sort_keys=True)) for key, value in cell.items()))


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a bounded benchmark cell plan.")
    parser.add_argument("--space", default="parameter_space.example.toml")
    parser.add_argument("--mode", choices=["scout", "frontier"], default="scout")
    parser.add_argument("--out", default="-")
    args = parser.parse_args()

    config = tomllib.loads(Path(args.space).read_text())
    fixed = {k: v[0] if isinstance(v, list) and len(v) == 1 else v for k, v in config.get("fixed", {}).items()}
    axes = config[args.mode]
    max_cells = int(config.get("budget", {}).get("max_cells", 999999))

    cells = []
    if args.mode == "scout":
        for axis, values in axes.items():
            baseline = {k: values[0] for k, values in axes.items()}
            for value in values:
                cell = dict(fixed)
                cell.update(baseline)
                cell[axis] = value
                cell["phase"] = f"scout:{axis}"
                cells.append(cell)
    else:
        for cell in product_cells(axes):
            merged = dict(fixed)
            merged.update(cell)
            merged["phase"] = "frontier"
            cells.append(merged)

    deduped = []
    seen = set()
    for cell in cells:
        key = stable_key(cell)
        if key not in seen:
            seen.add(key)
            deduped.append(cell)

    if len(deduped) > max_cells:
        raise SystemExit(f"cell budget exceeded: {len(deduped)} > {max_cells}")

    payload = {"mode": args.mode, "cells": deduped, "cell_count": len(deduped), "max_cells": max_cells}
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.out == "-":
        print(text, end="")
    else:
        Path(args.out).write_text(text)
        print(args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
