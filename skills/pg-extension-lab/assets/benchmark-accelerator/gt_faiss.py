"""Exact ground truth via faiss IndexFlatL2, an implementation independent of gt.py.

Agreement between gt.py (pure Python) and this script is the ground-truth independence check
(references/benchmarking/crossover-and-cost.md). Needs numpy and faiss: `pip install faiss-cpu`,
or faiss-gpu on a device host.
"""

from __future__ import annotations

import argparse
import sys

from common import read_fbin, write_ibin


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True)
    parser.add_argument("--queries", required=True)
    parser.add_argument("--k", type=int, required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    try:
        import faiss
        import numpy as np
    except ImportError as exc:
        print(f"gt_faiss.py needs numpy and faiss ({exc}); pip install faiss-cpu", file=sys.stderr)
        return 2
    data = np.asarray(read_fbin(args.data), dtype="float32")
    queries = np.asarray(read_fbin(args.queries), dtype="float32")
    index = faiss.IndexFlatL2(data.shape[1])
    index.add(data)
    _, ids = index.search(queries, args.k)
    write_ibin(args.out, ids.tolist())
    print(args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
