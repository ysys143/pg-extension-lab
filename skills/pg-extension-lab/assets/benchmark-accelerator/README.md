# Accelerator benchmark harness

Copy to `bench/accelerator/` when comparing CPU, GPU, SIMD, remote accelerator, or cached
execution paths. This folder focuses on artifacts that should stay stable across backends:
binary vector formats, exact ground truth, recall scoring, and protocol schemas.

## Minimum flow

```bash
python gen_dataset.py --rows 1000 --dims 16 --out data.fbin
python gt.py --data data.fbin --queries data.fbin --k 10 --out gt.ibin
python recall.py --gt gt.ibin --results sample_results.txt --k 10
```

For real runs, add backend-specific scripts that emit `<qid> <neighbor_id>` result rows and
resource CSV rows matching `protocol_schema.csv`.

