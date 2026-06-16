from __future__ import annotations

import argparse
from collections import defaultdict

from common import read_ibin, recall_at_k


def read_results(path: str, k: int) -> list[list[int]]:
    by_query: dict[int, list[int]] = defaultdict(list)
    with open(path) as f:
        for line in f:
            if not line.strip() or line.startswith("#"):
                continue
            qid, nid = line.split()[:2]
            by_query[int(qid)].append(int(nid))
    rows = []
    for qid in sorted(by_query):
        row = by_query[qid][:k]
        row.extend([-1] * (k - len(row)))
        rows.append(row)
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gt", required=True)
    parser.add_argument("--results", required=True)
    parser.add_argument("--k", type=int, required=True)
    args = parser.parse_args()
    gt = read_ibin(args.gt)
    actual = read_results(args.results, args.k)
    print(f"recall@{args.k}={recall_at_k(gt, actual, args.k):.6f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
