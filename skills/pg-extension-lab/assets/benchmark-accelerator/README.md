# Accelerator benchmark harness — worked case

Copy to `bench/accelerator/` when comparing CPU, GPU, SIMD, remote accelerator, or cached
execution paths. This is the accelerator worked case of the generic methodology
(`references/benchmarking/methodology.md`, `references/benchmarking/crossover-and-cost.md`). The
folder holds artifacts that should stay stable across backends: binary vector formats, exact
ground truth, recall scoring, and protocol schemas.

## Minimum flow

```bash
./run_pilot.sh
```

The pilot generates a dataset and a held-out query set (separate seed), computes exact ground
truth with `gt.py`, and — when numpy and faiss are installed — recomputes it with
`gt_faiss.py` and scores one against the other. That is the ground-truth independence check:
two independent exact implementations must agree before either one grades a backend. Without
faiss it prints `SKIP` instead of a number.

Step by step:

```bash
python gen_dataset.py --rows 1000 --dims 16 --seed 42 --out data.fbin
python gen_dataset.py --rows 100 --dims 16 --seed 43 --out queries.fbin
python gt.py --data data.fbin --queries queries.fbin --k 10 --out gt.ibin
python gt_faiss.py --data data.fbin --queries queries.fbin --k 10 --out gt_faiss.ibin
python recall.py --gt gt.ibin --results gt_faiss.ibin --k 10
```

For real runs, add backend-specific scripts that emit `<qid> <neighbor_id>` result rows and
resource CSV rows matching `protocol_schema.csv`. `recall.py` aligns result rows to ground-truth
query ids, scores a missing query as 0, and rejects ids outside the ground truth.

`sample_artifacts/` holds illustrative layouts (`EXAMPLE_*`, `example_*`), not measurements.
