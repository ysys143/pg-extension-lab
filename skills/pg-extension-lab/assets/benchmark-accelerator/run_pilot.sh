#!/usr/bin/env bash
set -euo pipefail

python gen_dataset.py --rows "${ROWS:-1000}" --dims "${DIMS:-16}" --out data.fbin
python gt.py --data data.fbin --queries data.fbin --k "${K:-10}" --out gt.ibin
printf '0 0\n0 1\n0 2\n0 3\n0 4\n0 5\n0 6\n0 7\n0 8\n0 9\n' > sample_results.txt
python recall.py --gt gt.ibin --results sample_results.txt --k "${K:-10}"

