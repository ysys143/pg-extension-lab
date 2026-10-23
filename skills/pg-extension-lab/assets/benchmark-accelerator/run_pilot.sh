#!/usr/bin/env bash
# Pilot: exercises the binary formats and runs the ground-truth independence check.
# Queries are held out (separate seed): a query copied from the data finds itself at rank 1.
set -euo pipefail

PY="${PYTHON:-python3}"
ROWS="${ROWS:-1000}"
DIMS="${DIMS:-16}"
K="${K:-10}"
QUERIES="${QUERIES:-100}"

"$PY" gen_dataset.py --rows "$ROWS" --dims "$DIMS" --seed 42 --out data.fbin
"$PY" gen_dataset.py --rows "$QUERIES" --dims "$DIMS" --seed 43 --out queries.fbin
"$PY" gt.py --data data.fbin --queries queries.fbin --k "$K" --out gt.ibin

if "$PY" -c 'import faiss, numpy' 2>/dev/null; then
  "$PY" gt_faiss.py --data data.fbin --queries queries.fbin --k "$K" --out gt_faiss.ibin
  echo "ground-truth independence (gt_faiss.py vs gt.py):"
  agreement="$("$PY" recall.py --gt gt.ibin --results gt_faiss.ibin --k "$K")"
  echo "$agreement"
  # The two oracles must agree before either one grades a backend.
  if [ "$agreement" != "recall@${K}=1.000000" ]; then
    echo "FAIL: the exact ground-truth implementations disagree" >&2
    exit 1
  fi
else
  echo "SKIP ground-truth independence check: needs numpy and faiss (pip install faiss-cpu)"
fi
