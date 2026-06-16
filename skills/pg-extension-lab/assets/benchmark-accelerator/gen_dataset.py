from __future__ import annotations

import argparse
import random

from common import write_fbin


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", type=int, required=True)
    parser.add_argument("--dims", type=int, required=True)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    rng = random.Random(args.seed)
    data = [[rng.gauss(0.0, 1.0) for _ in range(args.dims)] for _ in range(args.rows)]
    write_fbin(args.out, data)
    print(args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
