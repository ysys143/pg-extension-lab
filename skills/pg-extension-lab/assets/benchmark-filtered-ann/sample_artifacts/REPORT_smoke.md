# Filtered ANN benchmark report

- run_id: `20261023-145416`
- profile: filtered-ann
- command: `python run_bench.py --config bench_config.example.toml --output sample_artifacts/results_smoke.json`
- recall threshold for the matched-recall operating point: 0.94

| metric | trust | why |
|---|---|---|
| recall@k vs exact filtered ground truth | SOLID | deterministic oracle, host-independent |
| realized selectivity (fixture count) | SOLID | counted from the fixture, not timed |
| qps, p95 ms | INDICATIVE | shared-host timing; qps is single-client serial over target calls only |
| pages/query | INDICATIVE | from a separate EXPLAIN (ANALYZE, BUFFERS) re-execution, not the timed call |

`plan` is the EXPLAIN node path per cell, followed by the plan mode the harness requested
(`planner` lets PostgreSQL choose; `force_index` asks for the index). Check it before reading
recall as index quality: an exact path (Seq Scan or Bitmap Heap Scan, then Sort) scores 1.0 by
construction.

| target | fixture | scenario | sel | pass rate | k | search | recall (SOLID) | qps (INDICATIVE) | p95 ms (INDICATIVE) | pages/query (INDICATIVE) | plan |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| prefilter_exact | correlated | a_selectivity_sweep | 0.010 | 0.010 | 10 | - | 1.000 | 16759.77 | 0.06 | 0.00 | python-exact (planner) |
| prefilter_exact | correlated | a_selectivity_sweep | 0.050 | 0.050 | 10 | - | 1.000 | 8130.91 | 0.13 | 0.00 | python-exact (planner) |
| prefilter_exact | correlated | a_selectivity_sweep | 0.100 | 0.100 | 10 | - | 1.000 | 4930.66 | 0.21 | 0.00 | python-exact (planner) |
| prefilter_exact | correlated | b_postfilter_recall | 0.010 | 0.010 | 10 | - | 1.000 | 16664.33 | 0.06 | 0.00 | python-exact (force_index) |
| prefilter_exact | correlated | c_candidate_expansion | 0.010 | 0.010 | 10 | - | 1.000 | 16679.40 | 0.06 | 0.00 | python-exact (force_index) |
| prefilter_exact | correlated | c_candidate_expansion | 0.050 | 0.050 | 10 | - | 1.000 | 5088.52 | 0.32 | 0.00 | python-exact (force_index) |
| prefilter_exact | correlated | c_candidate_expansion | 0.100 | 0.100 | 10 | - | 1.000 | 4832.67 | 0.21 | 0.00 | python-exact (force_index) |
| prefilter_exact | correlated | d_correlation | 0.100 | 0.100 | 10 | - | 1.000 | 3494.37 | 0.78 | 0.00 | python-exact (force_index) |
| postfilter_topn | correlated | a_selectivity_sweep | 0.010 | 0.010 | 10 | 20 | 0.000 | 491.57 | 3.60 | 0.00 | python-postfilter-top20 (planner) |
| postfilter_topn | correlated | a_selectivity_sweep | 0.010 | 0.010 | 10 | 80 | 0.080 | 381.73 | 3.42 | 0.00 | python-postfilter-top80 (planner) |
| postfilter_topn | correlated | a_selectivity_sweep | 0.010 | 0.010 | 10 | 320 | 0.250 | 354.73 | 3.80 | 0.00 | python-postfilter-top320 (planner) |
| postfilter_topn | correlated | a_selectivity_sweep | 0.010 | 0.010 | 10 | 1000 | 1.000 | 133.57 | 20.73 | 0.00 | python-postfilter-top1000 (planner) |
| postfilter_topn | correlated | a_selectivity_sweep | 0.050 | 0.050 | 10 | 20 | 0.100 | 531.79 | 2.41 | 0.00 | python-postfilter-top20 (planner) |
| postfilter_topn | correlated | a_selectivity_sweep | 0.050 | 0.050 | 10 | 80 | 0.130 | 450.83 | 2.91 | 0.00 | python-postfilter-top80 (planner) |
| postfilter_topn | correlated | a_selectivity_sweep | 0.050 | 0.050 | 10 | 320 | 0.400 | 499.89 | 3.00 | 0.00 | python-postfilter-top320 (planner) |
| postfilter_topn | correlated | a_selectivity_sweep | 0.050 | 0.050 | 10 | 1000 | 1.000 | 485.50 | 3.73 | 0.00 | python-postfilter-top1000 (planner) |
| postfilter_topn | correlated | a_selectivity_sweep | 0.100 | 0.100 | 10 | 20 | 0.160 | 488.53 | 2.60 | 0.00 | python-postfilter-top20 (planner) |
| postfilter_topn | correlated | a_selectivity_sweep | 0.100 | 0.100 | 10 | 80 | 0.220 | 551.01 | 2.12 | 0.00 | python-postfilter-top80 (planner) |
| postfilter_topn | correlated | a_selectivity_sweep | 0.100 | 0.100 | 10 | 320 | 0.400 | 507.38 | 2.64 | 0.00 | python-postfilter-top320 (planner) |
| postfilter_topn | correlated | a_selectivity_sweep | 0.100 | 0.100 | 10 | 1000 | 1.000 | 561.88 | 1.90 | 0.00 | python-postfilter-top1000 (planner) |
| postfilter_topn | correlated | b_postfilter_recall | 0.010 | 0.010 | 10 | 20 | 0.000 | 455.63 | 3.93 | 0.00 | python-postfilter-top20 (force_index) |
| postfilter_topn | correlated | b_postfilter_recall | 0.010 | 0.010 | 10 | 80 | 0.080 | 558.59 | 1.85 | 0.00 | python-postfilter-top80 (force_index) |
| postfilter_topn | correlated | b_postfilter_recall | 0.010 | 0.010 | 10 | 320 | 0.250 | 555.65 | 2.05 | 0.00 | python-postfilter-top320 (force_index) |
| postfilter_topn | correlated | b_postfilter_recall | 0.010 | 0.010 | 10 | 1000 | 1.000 | 494.74 | 2.76 | 0.00 | python-postfilter-top1000 (force_index) |
| postfilter_topn | correlated | c_candidate_expansion | 0.010 | 0.010 | 10 | 20 | 0.000 | 551.98 | 2.28 | 0.00 | python-postfilter-top20 (force_index) |
| postfilter_topn | correlated | c_candidate_expansion | 0.010 | 0.010 | 10 | 80 | 0.080 | 421.40 | 3.33 | 0.00 | python-postfilter-top80 (force_index) |
| postfilter_topn | correlated | c_candidate_expansion | 0.010 | 0.010 | 10 | 320 | 0.250 | 547.68 | 2.45 | 0.00 | python-postfilter-top320 (force_index) |
| postfilter_topn | correlated | c_candidate_expansion | 0.010 | 0.010 | 10 | 1000 | 1.000 | 488.44 | 2.91 | 0.00 | python-postfilter-top1000 (force_index) |
| postfilter_topn | correlated | c_candidate_expansion | 0.050 | 0.050 | 10 | 20 | 0.100 | 578.12 | 1.84 | 0.00 | python-postfilter-top20 (force_index) |
| postfilter_topn | correlated | c_candidate_expansion | 0.050 | 0.050 | 10 | 80 | 0.130 | 550.48 | 2.38 | 0.00 | python-postfilter-top80 (force_index) |
| postfilter_topn | correlated | c_candidate_expansion | 0.050 | 0.050 | 10 | 320 | 0.400 | 383.30 | 5.75 | 0.00 | python-postfilter-top320 (force_index) |
| postfilter_topn | correlated | c_candidate_expansion | 0.050 | 0.050 | 10 | 1000 | 1.000 | 542.41 | 2.49 | 0.00 | python-postfilter-top1000 (force_index) |
| postfilter_topn | correlated | c_candidate_expansion | 0.100 | 0.100 | 10 | 20 | 0.160 | 581.35 | 1.73 | 0.00 | python-postfilter-top20 (force_index) |
| postfilter_topn | correlated | c_candidate_expansion | 0.100 | 0.100 | 10 | 80 | 0.220 | 573.67 | 1.85 | 0.00 | python-postfilter-top80 (force_index) |
| postfilter_topn | correlated | c_candidate_expansion | 0.100 | 0.100 | 10 | 320 | 0.400 | 580.49 | 1.74 | 0.00 | python-postfilter-top320 (force_index) |
| postfilter_topn | correlated | c_candidate_expansion | 0.100 | 0.100 | 10 | 1000 | 1.000 | 568.45 | 1.90 | 0.00 | python-postfilter-top1000 (force_index) |
| postfilter_topn | correlated | d_correlation | 0.100 | 0.100 | 10 | 20 | 0.000 | 558.60 | 2.20 | 0.00 | python-postfilter-top20 (force_index) |
| postfilter_topn | correlated | d_correlation | 0.100 | 0.100 | 10 | 80 | 0.000 | 586.23 | 1.80 | 0.00 | python-postfilter-top80 (force_index) |
| postfilter_topn | correlated | d_correlation | 0.100 | 0.100 | 10 | 320 | 0.000 | 491.52 | 4.43 | 0.00 | python-postfilter-top320 (force_index) |
| postfilter_topn | correlated | d_correlation | 0.100 | 0.100 | 10 | 1000 | 1.000 | 473.87 | 4.82 | 0.00 | python-postfilter-top1000 (force_index) |
| prefilter_exact | uncorrelated | a_selectivity_sweep | 0.010 | 0.010 | 10 | - | 1.000 | 16595.23 | 0.06 | 0.00 | python-exact (planner) |
| prefilter_exact | uncorrelated | a_selectivity_sweep | 0.050 | 0.050 | 10 | - | 1.000 | 7890.58 | 0.13 | 0.00 | python-exact (planner) |
| prefilter_exact | uncorrelated | a_selectivity_sweep | 0.100 | 0.100 | 10 | - | 1.000 | 551.38 | 11.31 | 0.00 | python-exact (planner) |
| prefilter_exact | uncorrelated | b_postfilter_recall | 0.010 | 0.010 | 10 | - | 1.000 | 8520.61 | 0.13 | 0.00 | python-exact (force_index) |
| prefilter_exact | uncorrelated | c_candidate_expansion | 0.010 | 0.010 | 10 | - | 1.000 | 6113.71 | 0.56 | 0.00 | python-exact (force_index) |
| prefilter_exact | uncorrelated | c_candidate_expansion | 0.050 | 0.050 | 10 | - | 1.000 | 3088.92 | 0.61 | 0.00 | python-exact (force_index) |
| prefilter_exact | uncorrelated | c_candidate_expansion | 0.100 | 0.100 | 10 | - | 1.000 | 4728.97 | 0.22 | 0.00 | python-exact (force_index) |
| prefilter_exact | uncorrelated | d_correlation | 0.100 | 0.100 | 10 | - | 1.000 | 2727.37 | 0.89 | 0.00 | python-exact (force_index) |
| postfilter_topn | uncorrelated | a_selectivity_sweep | 0.010 | 0.010 | 10 | 20 | 0.020 | 488.88 | 2.65 | 0.00 | python-postfilter-top20 (planner) |
| postfilter_topn | uncorrelated | a_selectivity_sweep | 0.010 | 0.010 | 10 | 80 | 0.080 | 542.48 | 2.25 | 0.00 | python-postfilter-top80 (planner) |
| postfilter_topn | uncorrelated | a_selectivity_sweep | 0.010 | 0.010 | 10 | 320 | 0.390 | 564.64 | 1.81 | 0.00 | python-postfilter-top320 (planner) |
| postfilter_topn | uncorrelated | a_selectivity_sweep | 0.010 | 0.010 | 10 | 1000 | 1.000 | 460.27 | 3.33 | 0.00 | python-postfilter-top1000 (planner) |
| postfilter_topn | uncorrelated | a_selectivity_sweep | 0.050 | 0.050 | 10 | 20 | 0.060 | 354.38 | 5.32 | 0.00 | python-postfilter-top20 (planner) |
| postfilter_topn | uncorrelated | a_selectivity_sweep | 0.050 | 0.050 | 10 | 80 | 0.320 | 548.39 | 2.04 | 0.00 | python-postfilter-top80 (planner) |
| postfilter_topn | uncorrelated | a_selectivity_sweep | 0.050 | 0.050 | 10 | 320 | 1.000 | 558.65 | 2.10 | 0.00 | python-postfilter-top320 (planner) |
| postfilter_topn | uncorrelated | a_selectivity_sweep | 0.050 | 0.050 | 10 | 1000 | 1.000 | 404.52 | 4.29 | 0.00 | python-postfilter-top1000 (planner) |
| postfilter_topn | uncorrelated | a_selectivity_sweep | 0.100 | 0.100 | 10 | 20 | 0.180 | 474.04 | 4.20 | 0.00 | python-postfilter-top20 (planner) |
| postfilter_topn | uncorrelated | a_selectivity_sweep | 0.100 | 0.100 | 10 | 80 | 0.760 | 556.99 | 2.30 | 0.00 | python-postfilter-top80 (planner) |
| postfilter_topn | uncorrelated | a_selectivity_sweep | 0.100 | 0.100 | 10 | 320 | 1.000 | 507.05 | 3.24 | 0.00 | python-postfilter-top320 (planner) |
| postfilter_topn | uncorrelated | a_selectivity_sweep | 0.100 | 0.100 | 10 | 1000 | 1.000 | 546.31 | 2.20 | 0.00 | python-postfilter-top1000 (planner) |
| postfilter_topn | uncorrelated | b_postfilter_recall | 0.010 | 0.010 | 10 | 20 | 0.020 | 568.86 | 1.82 | 0.00 | python-postfilter-top20 (force_index) |
| postfilter_topn | uncorrelated | b_postfilter_recall | 0.010 | 0.010 | 10 | 80 | 0.080 | 573.62 | 1.78 | 0.00 | python-postfilter-top80 (force_index) |
| postfilter_topn | uncorrelated | b_postfilter_recall | 0.010 | 0.010 | 10 | 320 | 0.390 | 561.66 | 1.85 | 0.00 | python-postfilter-top320 (force_index) |
| postfilter_topn | uncorrelated | b_postfilter_recall | 0.010 | 0.010 | 10 | 1000 | 1.000 | 558.63 | 1.80 | 0.00 | python-postfilter-top1000 (force_index) |
| postfilter_topn | uncorrelated | c_candidate_expansion | 0.010 | 0.010 | 10 | 20 | 0.020 | 574.76 | 1.77 | 0.00 | python-postfilter-top20 (force_index) |
| postfilter_topn | uncorrelated | c_candidate_expansion | 0.010 | 0.010 | 10 | 80 | 0.080 | 522.69 | 2.86 | 0.00 | python-postfilter-top80 (force_index) |
| postfilter_topn | uncorrelated | c_candidate_expansion | 0.010 | 0.010 | 10 | 320 | 0.390 | 562.09 | 2.03 | 0.00 | python-postfilter-top320 (force_index) |
| postfilter_topn | uncorrelated | c_candidate_expansion | 0.010 | 0.010 | 10 | 1000 | 1.000 | 557.46 | 1.81 | 0.00 | python-postfilter-top1000 (force_index) |
| postfilter_topn | uncorrelated | c_candidate_expansion | 0.050 | 0.050 | 10 | 20 | 0.060 | 541.00 | 2.20 | 0.00 | python-postfilter-top20 (force_index) |
| postfilter_topn | uncorrelated | c_candidate_expansion | 0.050 | 0.050 | 10 | 80 | 0.320 | 556.77 | 2.25 | 0.00 | python-postfilter-top80 (force_index) |
| postfilter_topn | uncorrelated | c_candidate_expansion | 0.050 | 0.050 | 10 | 320 | 1.000 | 523.25 | 2.60 | 0.00 | python-postfilter-top320 (force_index) |
| postfilter_topn | uncorrelated | c_candidate_expansion | 0.050 | 0.050 | 10 | 1000 | 1.000 | 489.32 | 3.88 | 0.00 | python-postfilter-top1000 (force_index) |
| postfilter_topn | uncorrelated | c_candidate_expansion | 0.100 | 0.100 | 10 | 20 | 0.180 | 566.64 | 1.95 | 0.00 | python-postfilter-top20 (force_index) |
| postfilter_topn | uncorrelated | c_candidate_expansion | 0.100 | 0.100 | 10 | 80 | 0.760 | 568.47 | 1.88 | 0.00 | python-postfilter-top80 (force_index) |
| postfilter_topn | uncorrelated | c_candidate_expansion | 0.100 | 0.100 | 10 | 320 | 1.000 | 554.46 | 1.96 | 0.00 | python-postfilter-top320 (force_index) |
| postfilter_topn | uncorrelated | c_candidate_expansion | 0.100 | 0.100 | 10 | 1000 | 1.000 | 554.38 | 1.86 | 0.00 | python-postfilter-top1000 (force_index) |
| postfilter_topn | uncorrelated | d_correlation | 0.100 | 0.100 | 10 | 20 | 0.190 | 573.72 | 1.77 | 0.00 | python-postfilter-top20 (force_index) |
| postfilter_topn | uncorrelated | d_correlation | 0.100 | 0.100 | 10 | 80 | 0.770 | 563.64 | 1.98 | 0.00 | python-postfilter-top80 (force_index) |
| postfilter_topn | uncorrelated | d_correlation | 0.100 | 0.100 | 10 | 320 | 1.000 | 554.25 | 1.95 | 0.00 | python-postfilter-top320 (force_index) |
| postfilter_topn | uncorrelated | d_correlation | 0.100 | 0.100 | 10 | 1000 | 1.000 | 529.11 | 2.66 | 0.00 | python-postfilter-top1000 (force_index) |

## Candidate-expansion recovery (scenario C, index path forced)

Lowest search value reaching recall >= 0.94; when none does, the
best cell is the max-recall operating point. `plan` belongs to the best cell.

| target | fixture | sel | recovery search value | best recall @ search | plan |
|---|---|---:|---:|---:|---|
| prefilter_exact | correlated | 0.010 | no knob | - | python-exact |
| prefilter_exact | correlated | 0.050 | no knob | - | python-exact |
| prefilter_exact | correlated | 0.100 | no knob | - | python-exact |
| postfilter_topn | correlated | 0.010 | 1000 | 1.000 @ 1000 | python-postfilter-top1000 |
| postfilter_topn | correlated | 0.050 | 1000 | 1.000 @ 1000 | python-postfilter-top1000 |
| postfilter_topn | correlated | 0.100 | 1000 | 1.000 @ 1000 | python-postfilter-top1000 |
| prefilter_exact | uncorrelated | 0.010 | no knob | - | python-exact |
| prefilter_exact | uncorrelated | 0.050 | no knob | - | python-exact |
| prefilter_exact | uncorrelated | 0.100 | no knob | - | python-exact |
| postfilter_topn | uncorrelated | 0.010 | 1000 | 1.000 @ 1000 | python-postfilter-top1000 |
| postfilter_topn | uncorrelated | 0.050 | 320 | 1.000 @ 320 | python-postfilter-top320 |
| postfilter_topn | uncorrelated | 0.100 | 320 | 1.000 @ 320 | python-postfilter-top320 |

## Reproduce

```bash
python run_bench.py --config bench_config.example.toml --output sample_artifacts/results_smoke.json
python report.py sample_artifacts/results_smoke.json
```
