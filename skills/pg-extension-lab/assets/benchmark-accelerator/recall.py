from __future__ import annotations

import argparse
import sys
from collections import defaultdict

from common import read_ibin, recall_at_k


def read_results(path: str, k: int, n_queries: int) -> list[list[int]]:
    """Rows aligned to ground-truth query ids 0..n_queries-1; a query with no results scores 0."""
    by_query: dict[int, list[int]] = defaultdict(list)
    with open(path) as f:
        for line in f:
            if not line.strip() or line.startswith("#"):
                continue
            qid, nid = line.split()[:2]
            by_query[int(qid)].append(int(nid))
    unknown = sorted(qid for qid in by_query if not 0 <= qid < n_queries)
    if unknown:
        raise ValueError(f"result query ids {unknown[:5]} are outside ground truth 0..{n_queries - 1}")
    rows = []
    for qid in range(n_queries):
        row = by_query.get(qid, [])[:k]
        row.extend([-1] * (k - len(row)))
        rows.append(row)
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gt", required=True)
    parser.add_argument("--results", required=True, help="'<qid> <neighbor_id>' text, or an .ibin from gt*.py")
    parser.add_argument("--k", type=int, required=True)
    args = parser.parse_args()
    gt = read_ibin(args.gt)
    if args.results.endswith(".ibin"):
        actual = read_ibin(args.results)
    else:
        try:
            actual = read_results(args.results, args.k, len(gt))
        except ValueError as exc:
            print(exc, file=sys.stderr)
            return 2
    if len(actual) != len(gt):
        print(f"results cover {len(actual)} queries, ground truth has {len(gt)}", file=sys.stderr)
        return 2
    print(f"recall@{args.k}={recall_at_k(gt, actual, args.k):.6f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
