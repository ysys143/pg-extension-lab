# Filtered ANN benchmark report

- run_id: `20261023-143506`
- profile: filtered-ann
- command: `python run_bench.py --config bench_config.example.toml --output sample_artifacts/results_smoke.json`
- recall threshold for the matched-recall operating point: 0.94

| metric | trust | why |
|---|---|---|
| recall@k vs exact filtered ground truth | SOLID | deterministic oracle, host-independent |
| pass rate (realized selectivity) | SOLID | counted from the fixture |
| qps, p95 ms | INDICATIVE | shared-host timing; qps is single-client serial over target calls only |
| pages/query | INDICATIVE | from a separate EXPLAIN (ANALYZE, BUFFERS) re-execution, not the timed call |

`plan` is the most common EXPLAIN node path per cell: check it before reading recall as index
quality. An exact path (Seq Scan or Bitmap Heap Scan, then Sort) scores 1.0 by construction.

| target | fixture | scenario | sel | pass rate | k | search | recall (SOLID) | qps (INDICATIVE) | p95 ms (INDICATIVE) | pages/query (INDICATIVE) | plan |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| prefilter_exact | correlated | a_selectivity_sweep | 0.010 | 0.010 | 10 | - | 1.000 | 16566.58 | 0.06 | 0.00 | python-exact |
| prefilter_exact | correlated | a_selectivity_sweep | 0.050 | 0.050 | 10 | - | 1.000 | 7885.40 | 0.14 | 0.00 | python-exact |
| prefilter_exact | correlated | a_selectivity_sweep | 0.100 | 0.100 | 10 | - | 1.000 | 4820.25 | 0.24 | 0.00 | python-exact |
| prefilter_exact | correlated | b_postfilter_recall | 0.010 | 0.010 | 10 | - | 1.000 | 16620.49 | 0.06 | 0.00 | python-exact |
| prefilter_exact | correlated | c_candidate_expansion | 0.050 | 0.050 | 10 | - | 1.000 | 7253.38 | 0.20 | 0.00 | python-exact |
| prefilter_exact | correlated | d_correlation | 0.100 | 0.100 | 10 | - | 1.000 | 4915.41 | 0.21 | 0.00 | python-exact |
| postfilter_topn | correlated | a_selectivity_sweep | 0.010 | 0.010 | 10 | 20 | 0.000 | 572.74 | 1.90 | 0.00 | python-postfilter-top20 |
| postfilter_topn | correlated | a_selectivity_sweep | 0.010 | 0.010 | 10 | 80 | 0.080 | 580.23 | 1.78 | 0.00 | python-postfilter-top80 |
| postfilter_topn | correlated | a_selectivity_sweep | 0.010 | 0.010 | 10 | 320 | 0.250 | 571.20 | 1.90 | 0.00 | python-postfilter-top320 |
| postfilter_topn | correlated | a_selectivity_sweep | 0.010 | 0.010 | 10 | 1000 | 1.000 | 571.44 | 1.75 | 0.00 | python-postfilter-top1000 |
| postfilter_topn | correlated | a_selectivity_sweep | 0.050 | 0.050 | 10 | 20 | 0.100 | 576.62 | 1.90 | 0.00 | python-postfilter-top20 |
| postfilter_topn | correlated | a_selectivity_sweep | 0.050 | 0.050 | 10 | 80 | 0.130 | 549.78 | 2.37 | 0.00 | python-postfilter-top80 |
| postfilter_topn | correlated | a_selectivity_sweep | 0.050 | 0.050 | 10 | 320 | 0.400 | 519.61 | 2.45 | 0.00 | python-postfilter-top320 |
| postfilter_topn | correlated | a_selectivity_sweep | 0.050 | 0.050 | 10 | 1000 | 1.000 | 558.14 | 2.00 | 0.00 | python-postfilter-top1000 |
| postfilter_topn | correlated | a_selectivity_sweep | 0.100 | 0.100 | 10 | 20 | 0.160 | 573.32 | 1.98 | 0.00 | python-postfilter-top20 |
| postfilter_topn | correlated | a_selectivity_sweep | 0.100 | 0.100 | 10 | 80 | 0.220 | 564.16 | 1.96 | 0.00 | python-postfilter-top80 |
| postfilter_topn | correlated | a_selectivity_sweep | 0.100 | 0.100 | 10 | 320 | 0.400 | 554.52 | 2.01 | 0.00 | python-postfilter-top320 |
| postfilter_topn | correlated | a_selectivity_sweep | 0.100 | 0.100 | 10 | 1000 | 1.000 | 553.38 | 1.98 | 0.00 | python-postfilter-top1000 |
| postfilter_topn | correlated | b_postfilter_recall | 0.010 | 0.010 | 10 | 20 | 0.000 | 533.46 | 2.41 | 0.00 | python-postfilter-top20 |
| postfilter_topn | correlated | b_postfilter_recall | 0.010 | 0.010 | 10 | 80 | 0.080 | 563.80 | 2.18 | 0.00 | python-postfilter-top80 |
| postfilter_topn | correlated | b_postfilter_recall | 0.010 | 0.010 | 10 | 320 | 0.250 | 570.83 | 1.90 | 0.00 | python-postfilter-top320 |
| postfilter_topn | correlated | b_postfilter_recall | 0.010 | 0.010 | 10 | 1000 | 1.000 | 560.15 | 1.93 | 0.00 | python-postfilter-top1000 |
| postfilter_topn | correlated | c_candidate_expansion | 0.050 | 0.050 | 10 | 20 | 0.100 | 599.01 | 1.72 | 0.00 | python-postfilter-top20 |
| postfilter_topn | correlated | c_candidate_expansion | 0.050 | 0.050 | 10 | 80 | 0.130 | 588.97 | 1.92 | 0.00 | python-postfilter-top80 |
| postfilter_topn | correlated | c_candidate_expansion | 0.050 | 0.050 | 10 | 320 | 0.400 | 587.26 | 1.77 | 0.00 | python-postfilter-top320 |
| postfilter_topn | correlated | c_candidate_expansion | 0.050 | 0.050 | 10 | 1000 | 1.000 | 540.49 | 2.11 | 0.00 | python-postfilter-top1000 |
| postfilter_topn | correlated | d_correlation | 0.100 | 0.100 | 10 | 20 | 0.000 | 583.64 | 1.79 | 0.00 | python-postfilter-top20 |
| postfilter_topn | correlated | d_correlation | 0.100 | 0.100 | 10 | 80 | 0.000 | 475.30 | 3.50 | 0.00 | python-postfilter-top80 |
| postfilter_topn | correlated | d_correlation | 0.100 | 0.100 | 10 | 320 | 0.000 | 581.16 | 1.76 | 0.00 | python-postfilter-top320 |
| postfilter_topn | correlated | d_correlation | 0.100 | 0.100 | 10 | 1000 | 1.000 | 559.62 | 2.18 | 0.00 | python-postfilter-top1000 |
| prefilter_exact | uncorrelated | a_selectivity_sweep | 0.010 | 0.010 | 10 | - | 1.000 | 16503.93 | 0.06 | 0.00 | python-exact |
| prefilter_exact | uncorrelated | a_selectivity_sweep | 0.050 | 0.050 | 10 | - | 1.000 | 7865.24 | 0.13 | 0.00 | python-exact |
| prefilter_exact | uncorrelated | a_selectivity_sweep | 0.100 | 0.100 | 10 | - | 1.000 | 3483.26 | 0.53 | 0.00 | python-exact |
| prefilter_exact | uncorrelated | b_postfilter_recall | 0.010 | 0.010 | 10 | - | 1.000 | 16618.20 | 0.06 | 0.00 | python-exact |
| prefilter_exact | uncorrelated | c_candidate_expansion | 0.050 | 0.050 | 10 | - | 1.000 | 7636.99 | 0.13 | 0.00 | python-exact |
| prefilter_exact | uncorrelated | d_correlation | 0.100 | 0.100 | 10 | - | 1.000 | 4730.65 | 0.21 | 0.00 | python-exact |
| postfilter_topn | uncorrelated | a_selectivity_sweep | 0.010 | 0.010 | 10 | 20 | 0.020 | 563.70 | 1.99 | 0.00 | python-postfilter-top20 |
| postfilter_topn | uncorrelated | a_selectivity_sweep | 0.010 | 0.010 | 10 | 80 | 0.080 | 558.71 | 2.16 | 0.00 | python-postfilter-top80 |
| postfilter_topn | uncorrelated | a_selectivity_sweep | 0.010 | 0.010 | 10 | 320 | 0.390 | 568.21 | 1.78 | 0.00 | python-postfilter-top320 |
| postfilter_topn | uncorrelated | a_selectivity_sweep | 0.010 | 0.010 | 10 | 1000 | 1.000 | 543.71 | 2.05 | 0.00 | python-postfilter-top1000 |
| postfilter_topn | uncorrelated | a_selectivity_sweep | 0.050 | 0.050 | 10 | 20 | 0.060 | 549.35 | 2.20 | 0.00 | python-postfilter-top20 |
| postfilter_topn | uncorrelated | a_selectivity_sweep | 0.050 | 0.050 | 10 | 80 | 0.320 | 545.94 | 2.39 | 0.00 | python-postfilter-top80 |
| postfilter_topn | uncorrelated | a_selectivity_sweep | 0.050 | 0.050 | 10 | 320 | 1.000 | 584.97 | 1.74 | 0.00 | python-postfilter-top320 |
| postfilter_topn | uncorrelated | a_selectivity_sweep | 0.050 | 0.050 | 10 | 1000 | 1.000 | 579.40 | 1.74 | 0.00 | python-postfilter-top1000 |
| postfilter_topn | uncorrelated | a_selectivity_sweep | 0.100 | 0.100 | 10 | 20 | 0.180 | 595.59 | 1.70 | 0.00 | python-postfilter-top20 |
| postfilter_topn | uncorrelated | a_selectivity_sweep | 0.100 | 0.100 | 10 | 80 | 0.760 | 582.71 | 1.76 | 0.00 | python-postfilter-top80 |
| postfilter_topn | uncorrelated | a_selectivity_sweep | 0.100 | 0.100 | 10 | 320 | 1.000 | 523.99 | 2.41 | 0.00 | python-postfilter-top320 |
| postfilter_topn | uncorrelated | a_selectivity_sweep | 0.100 | 0.100 | 10 | 1000 | 1.000 | 489.75 | 2.29 | 0.00 | python-postfilter-top1000 |
| postfilter_topn | uncorrelated | b_postfilter_recall | 0.010 | 0.010 | 10 | 20 | 0.020 | 558.82 | 2.06 | 0.00 | python-postfilter-top20 |
| postfilter_topn | uncorrelated | b_postfilter_recall | 0.010 | 0.010 | 10 | 80 | 0.080 | 571.84 | 1.81 | 0.00 | python-postfilter-top80 |
| postfilter_topn | uncorrelated | b_postfilter_recall | 0.010 | 0.010 | 10 | 320 | 0.390 | 565.09 | 1.95 | 0.00 | python-postfilter-top320 |
| postfilter_topn | uncorrelated | b_postfilter_recall | 0.010 | 0.010 | 10 | 1000 | 1.000 | 544.62 | 2.00 | 0.00 | python-postfilter-top1000 |
| postfilter_topn | uncorrelated | c_candidate_expansion | 0.050 | 0.050 | 10 | 20 | 0.060 | 566.32 | 1.94 | 0.00 | python-postfilter-top20 |
| postfilter_topn | uncorrelated | c_candidate_expansion | 0.050 | 0.050 | 10 | 80 | 0.320 | 545.66 | 2.46 | 0.00 | python-postfilter-top80 |
| postfilter_topn | uncorrelated | c_candidate_expansion | 0.050 | 0.050 | 10 | 320 | 1.000 | 571.20 | 1.79 | 0.00 | python-postfilter-top320 |
| postfilter_topn | uncorrelated | c_candidate_expansion | 0.050 | 0.050 | 10 | 1000 | 1.000 | 563.50 | 1.80 | 0.00 | python-postfilter-top1000 |
| postfilter_topn | uncorrelated | d_correlation | 0.100 | 0.100 | 10 | 20 | 0.190 | 587.77 | 1.73 | 0.00 | python-postfilter-top20 |
| postfilter_topn | uncorrelated | d_correlation | 0.100 | 0.100 | 10 | 80 | 0.770 | 578.66 | 1.81 | 0.00 | python-postfilter-top80 |
| postfilter_topn | uncorrelated | d_correlation | 0.100 | 0.100 | 10 | 320 | 1.000 | 561.59 | 1.87 | 0.00 | python-postfilter-top320 |
| postfilter_topn | uncorrelated | d_correlation | 0.100 | 0.100 | 10 | 1000 | 1.000 | 570.40 | 1.81 | 0.00 | python-postfilter-top1000 |

## Candidate-expansion recovery (scenario C)

Lowest search value reaching recall >= 0.94.

| target | fixture | sel | recovery search value |
|---|---|---:|---:|
| prefilter_exact | correlated | 0.050 | no knob |
| postfilter_topn | correlated | 0.050 | 1000 |
| prefilter_exact | uncorrelated | 0.050 | no knob |
| postfilter_topn | uncorrelated | 0.050 | 320 |

## Reproduce

```bash
python run_bench.py --config bench_config.example.toml --output sample_artifacts/results_smoke.json
python report.py sample_artifacts/results_smoke.json
```
