from __future__ import annotations

import math


def l2(a: list[float], b: list[float]) -> float:
    """The oracle's metric. A target that orders by another metric (e.g. cosine) needs a matching
    oracle here first, or its exact path will score below recall 1.0."""
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))
