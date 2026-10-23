# Filtered ANN benchmark report

- run_id: `20261023-143105`
- profile: filtered-ann
- command: `python run_bench.py --config bench_config.example.toml --output sample_artifacts/results_smoke.json`
- recall threshold for the matched-recall operating point: 0.94

| metric | trust | why |
|---|---|---|
| recall@k vs exact filtered ground truth | SOLID | deterministic oracle, host-independent |
| pass rate (realized selectivity) | SOLID | counted from the fixture |
| qps, p95 ms | INDICATIVE | shared-host timing; qps is single-client serial over target calls only |
| pages/query | INDICATIVE | from a separate EXPLAIN (ANALYZE, BUFFERS) re-execution, not the timed call |

| target | fixture | scenario | sel | pass rate | k | search | recall (SOLID) | qps (INDICATIVE) | p95 ms (INDICATIVE) | pages/query (INDICATIVE) |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| prefilter_exact | correlated | a_selectivity_sweep | 0.010 | 0.010 | 10 | - | 1.000 | 10524.01 | 0.15 | 0.00 |
| prefilter_exact | correlated | a_selectivity_sweep | 0.050 | 0.050 | 10 | - | 1.000 | 7909.31 | 0.13 | 0.00 |
| prefilter_exact | correlated | a_selectivity_sweep | 0.100 | 0.100 | 10 | - | 1.000 | 4260.15 | 0.48 | 0.00 |
| prefilter_exact | correlated | b_postfilter_recall | 0.010 | 0.010 | 10 | - | 1.000 | 12144.52 | 0.13 | 0.00 |
| prefilter_exact | correlated | c_candidate_expansion | 0.050 | 0.050 | 10 | - | 1.000 | 7754.44 | 0.17 | 0.00 |
| prefilter_exact | correlated | d_correlation | 0.100 | 0.100 | 10 | - | 1.000 | 4676.45 | 0.29 | 0.00 |
| postfilter_topn | correlated | a_selectivity_sweep | 0.010 | 0.010 | 10 | 20 | 0.000 | 534.51 | 2.03 | 0.00 |
| postfilter_topn | correlated | a_selectivity_sweep | 0.010 | 0.010 | 10 | 80 | 0.080 | 478.20 | 2.54 | 0.00 |
| postfilter_topn | correlated | a_selectivity_sweep | 0.010 | 0.010 | 10 | 320 | 0.250 | 336.86 | 6.38 | 0.00 |
| postfilter_topn | correlated | a_selectivity_sweep | 0.010 | 0.010 | 10 | 1000 | 1.000 | 484.32 | 2.80 | 0.00 |
| postfilter_topn | correlated | a_selectivity_sweep | 0.050 | 0.050 | 10 | 20 | 0.100 | 566.47 | 1.92 | 0.00 |
| postfilter_topn | correlated | a_selectivity_sweep | 0.050 | 0.050 | 10 | 80 | 0.130 | 573.76 | 2.04 | 0.00 |
| postfilter_topn | correlated | a_selectivity_sweep | 0.050 | 0.050 | 10 | 320 | 0.400 | 569.73 | 1.94 | 0.00 |
| postfilter_topn | correlated | a_selectivity_sweep | 0.050 | 0.050 | 10 | 1000 | 1.000 | 552.03 | 2.04 | 0.00 |
| postfilter_topn | correlated | a_selectivity_sweep | 0.100 | 0.100 | 10 | 20 | 0.160 | 563.97 | 1.99 | 0.00 |
| postfilter_topn | correlated | a_selectivity_sweep | 0.100 | 0.100 | 10 | 80 | 0.220 | 562.61 | 2.20 | 0.00 |
| postfilter_topn | correlated | a_selectivity_sweep | 0.100 | 0.100 | 10 | 320 | 0.400 | 527.97 | 2.52 | 0.00 |
| postfilter_topn | correlated | a_selectivity_sweep | 0.100 | 0.100 | 10 | 1000 | 1.000 | 543.54 | 2.02 | 0.00 |
| postfilter_topn | correlated | b_postfilter_recall | 0.010 | 0.010 | 10 | 20 | 0.000 | 572.01 | 1.91 | 0.00 |
| postfilter_topn | correlated | b_postfilter_recall | 0.010 | 0.010 | 10 | 80 | 0.080 | 569.79 | 1.86 | 0.00 |
| postfilter_topn | correlated | b_postfilter_recall | 0.010 | 0.010 | 10 | 320 | 0.250 | 575.17 | 1.77 | 0.00 |
| postfilter_topn | correlated | b_postfilter_recall | 0.010 | 0.010 | 10 | 1000 | 1.000 | 544.46 | 2.04 | 0.00 |
| postfilter_topn | correlated | c_candidate_expansion | 0.050 | 0.050 | 10 | 20 | 0.100 | 587.81 | 1.71 | 0.00 |
| postfilter_topn | correlated | c_candidate_expansion | 0.050 | 0.050 | 10 | 80 | 0.130 | 586.93 | 1.73 | 0.00 |
| postfilter_topn | correlated | c_candidate_expansion | 0.050 | 0.050 | 10 | 320 | 0.400 | 554.92 | 2.01 | 0.00 |
| postfilter_topn | correlated | c_candidate_expansion | 0.050 | 0.050 | 10 | 1000 | 1.000 | 533.67 | 2.73 | 0.00 |
| postfilter_topn | correlated | d_correlation | 0.100 | 0.100 | 10 | 20 | 0.000 | 587.10 | 1.71 | 0.00 |
| postfilter_topn | correlated | d_correlation | 0.100 | 0.100 | 10 | 80 | 0.000 | 571.90 | 1.96 | 0.00 |
| postfilter_topn | correlated | d_correlation | 0.100 | 0.100 | 10 | 320 | 0.000 | 583.44 | 1.86 | 0.00 |
| postfilter_topn | correlated | d_correlation | 0.100 | 0.100 | 10 | 1000 | 1.000 | 569.69 | 1.80 | 0.00 |
| prefilter_exact | uncorrelated | a_selectivity_sweep | 0.010 | 0.010 | 10 | - | 1.000 | 16451.89 | 0.06 | 0.00 |
| prefilter_exact | uncorrelated | a_selectivity_sweep | 0.050 | 0.050 | 10 | - | 1.000 | 7347.32 | 0.17 | 0.00 |
| prefilter_exact | uncorrelated | a_selectivity_sweep | 0.100 | 0.100 | 10 | - | 1.000 | 4685.94 | 0.22 | 0.00 |
| prefilter_exact | uncorrelated | b_postfilter_recall | 0.010 | 0.010 | 10 | - | 1.000 | 16506.20 | 0.06 | 0.00 |
| prefilter_exact | uncorrelated | c_candidate_expansion | 0.050 | 0.050 | 10 | - | 1.000 | 7912.96 | 0.13 | 0.00 |
| prefilter_exact | uncorrelated | d_correlation | 0.100 | 0.100 | 10 | - | 1.000 | 4622.67 | 0.23 | 0.00 |
| postfilter_topn | uncorrelated | a_selectivity_sweep | 0.010 | 0.010 | 10 | 20 | 0.020 | 580.48 | 1.80 | 0.00 |
| postfilter_topn | uncorrelated | a_selectivity_sweep | 0.010 | 0.010 | 10 | 80 | 0.080 | 577.98 | 1.91 | 0.00 |
| postfilter_topn | uncorrelated | a_selectivity_sweep | 0.010 | 0.010 | 10 | 320 | 0.390 | 577.51 | 1.78 | 0.00 |
| postfilter_topn | uncorrelated | a_selectivity_sweep | 0.010 | 0.010 | 10 | 1000 | 1.000 | 554.27 | 1.91 | 0.00 |
| postfilter_topn | uncorrelated | a_selectivity_sweep | 0.050 | 0.050 | 10 | 20 | 0.060 | 563.31 | 1.94 | 0.00 |
| postfilter_topn | uncorrelated | a_selectivity_sweep | 0.050 | 0.050 | 10 | 80 | 0.320 | 577.54 | 1.73 | 0.00 |
| postfilter_topn | uncorrelated | a_selectivity_sweep | 0.050 | 0.050 | 10 | 320 | 1.000 | 573.79 | 1.74 | 0.00 |
| postfilter_topn | uncorrelated | a_selectivity_sweep | 0.050 | 0.050 | 10 | 1000 | 1.000 | 557.22 | 1.88 | 0.00 |
| postfilter_topn | uncorrelated | a_selectivity_sweep | 0.100 | 0.100 | 10 | 20 | 0.180 | 583.15 | 1.83 | 0.00 |
| postfilter_topn | uncorrelated | a_selectivity_sweep | 0.100 | 0.100 | 10 | 80 | 0.760 | 573.79 | 2.08 | 0.00 |
| postfilter_topn | uncorrelated | a_selectivity_sweep | 0.100 | 0.100 | 10 | 320 | 1.000 | 584.61 | 1.74 | 0.00 |
| postfilter_topn | uncorrelated | a_selectivity_sweep | 0.100 | 0.100 | 10 | 1000 | 1.000 | 566.99 | 1.79 | 0.00 |
| postfilter_topn | uncorrelated | b_postfilter_recall | 0.010 | 0.010 | 10 | 20 | 0.020 | 572.26 | 2.18 | 0.00 |
| postfilter_topn | uncorrelated | b_postfilter_recall | 0.010 | 0.010 | 10 | 80 | 0.080 | 572.83 | 1.80 | 0.00 |
| postfilter_topn | uncorrelated | b_postfilter_recall | 0.010 | 0.010 | 10 | 320 | 0.390 | 571.67 | 1.78 | 0.00 |
| postfilter_topn | uncorrelated | b_postfilter_recall | 0.010 | 0.010 | 10 | 1000 | 1.000 | 563.25 | 1.79 | 0.00 |
| postfilter_topn | uncorrelated | c_candidate_expansion | 0.050 | 0.050 | 10 | 20 | 0.060 | 467.39 | 2.86 | 0.00 |
| postfilter_topn | uncorrelated | c_candidate_expansion | 0.050 | 0.050 | 10 | 80 | 0.320 | 564.43 | 1.87 | 0.00 |
| postfilter_topn | uncorrelated | c_candidate_expansion | 0.050 | 0.050 | 10 | 320 | 1.000 | 567.45 | 1.79 | 0.00 |
| postfilter_topn | uncorrelated | c_candidate_expansion | 0.050 | 0.050 | 10 | 1000 | 1.000 | 568.80 | 1.84 | 0.00 |
| postfilter_topn | uncorrelated | d_correlation | 0.100 | 0.100 | 10 | 20 | 0.190 | 548.15 | 2.21 | 0.00 |
| postfilter_topn | uncorrelated | d_correlation | 0.100 | 0.100 | 10 | 80 | 0.770 | 560.12 | 1.90 | 0.00 |
| postfilter_topn | uncorrelated | d_correlation | 0.100 | 0.100 | 10 | 320 | 1.000 | 573.05 | 1.82 | 0.00 |
| postfilter_topn | uncorrelated | d_correlation | 0.100 | 0.100 | 10 | 1000 | 1.000 | 562.73 | 1.78 | 0.00 |

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
