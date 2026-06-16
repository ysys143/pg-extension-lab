from __future__ import annotations

import argparse

from common import exact_l2, read_fbin, write_ibin


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True)
    parser.add_argument("--queries", required=True)
    parser.add_argument("--k", type=int, required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    gt = exact_l2(read_fbin(args.data), read_fbin(args.queries), args.k)
    write_ibin(args.out, gt)
    print(args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

