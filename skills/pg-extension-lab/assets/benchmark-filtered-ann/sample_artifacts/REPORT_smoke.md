# Filtered ANN benchmark report

- run_id: `20261023-164425`
- profile: filtered-ann
- command: `python run_bench.py --config bench_config.example.toml --output sample_artifacts/results_smoke.json`
- scale: 1000 rows, 16 dims, 10 queries per condition, fixtures correlated, uncorrelated. Smoke scale: the report shows where recall fails and recovers, not performance or latency distributions at scale.
- recall threshold for the matched-recall operating point: 0.94

| metric | trust | why |
|---|---|---|
| recall@k vs exact filtered ground truth | SOLID | deterministic oracle, host-independent |
| realized selectivity (fixture count) | SOLID | counted from the fixture, not timed |
| qps, p95 ms | INDICATIVE | shared-host timing; qps is single-client serial over target calls only |
| buffer accesses/query (shared hit + read) | INDICATIVE | from a separate EXPLAIN (ANALYZE, BUFFERS) re-execution, not the timed call; a page touched twice counts twice |

`plan` is the EXPLAIN node path per cell, followed by the plan mode the harness requested
(`planner` lets PostgreSQL choose; `force_index` asks for the index). Check it before reading
recall as index quality: an exact path (Seq Scan or Bitmap Heap Scan, then Sort) scores 1.0 by
construction.

| target | fixture | scenario | sel | pass rate | k | search | recall (SOLID) | qps (INDICATIVE) | p95 ms (INDICATIVE) | buffer accesses/query (INDICATIVE) | plan |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| prefilter_exact | correlated | a_selectivity_sweep | 0.010 | 0.010 | 10 | - | 1.000 | 16780.86 | 0.06 | 0.00 | python-exact (planner) |
| prefilter_exact | correlated | a_selectivity_sweep | 0.050 | 0.050 | 10 | - | 1.000 | 7144.35 | 0.15 | 0.00 | python-exact (planner) |
| prefilter_exact | correlated | a_selectivity_sweep | 0.100 | 0.100 | 10 | - | 1.000 | 4382.92 | 0.32 | 0.00 | python-exact (planner) |
| prefilter_exact | correlated | b_postfilter_recall | 0.010 | 0.010 | 10 | - | 1.000 | 15357.04 | 0.07 | 0.00 | python-exact (force_index) |
| prefilter_exact | correlated | c_candidate_expansion | 0.010 | 0.010 | 10 | - | 1.000 | 15046.08 | 0.07 | 0.00 | python-exact (force_index) |
| prefilter_exact | correlated | c_candidate_expansion | 0.050 | 0.050 | 10 | - | 1.000 | 7126.74 | 0.25 | 0.00 | python-exact (force_index) |
| prefilter_exact | correlated | c_candidate_expansion | 0.100 | 0.100 | 10 | - | 1.000 | 4714.39 | 0.23 | 0.00 | python-exact (force_index) |
| prefilter_exact | correlated | d_correlation | 0.100 | 0.100 | 10 | - | 1.000 | 4717.35 | 0.25 | 0.00 | python-exact (force_index) |
| postfilter_topn | correlated | a_selectivity_sweep | 0.010 | 0.010 | 10 | 20 | 0.020 | 562.14 | 1.89 | 0.00 | python-postfilter-top20 (planner) |
| postfilter_topn | correlated | a_selectivity_sweep | 0.010 | 0.010 | 10 | 80 | 0.080 | 538.09 | 2.13 | 0.00 | python-postfilter-top80 (planner) |
| postfilter_topn | correlated | a_selectivity_sweep | 0.010 | 0.010 | 10 | 320 | 0.280 | 503.85 | 2.43 | 0.00 | python-postfilter-top320 (planner) |
| postfilter_topn | correlated | a_selectivity_sweep | 0.010 | 0.010 | 10 | 1000 | 1.000 | 467.44 | 2.99 | 0.00 | python-postfilter-top1000 (planner) |
| postfilter_topn | correlated | a_selectivity_sweep | 0.050 | 0.050 | 10 | 20 | 0.100 | 438.19 | 3.48 | 0.00 | python-postfilter-top20 (planner) |
| postfilter_topn | correlated | a_selectivity_sweep | 0.050 | 0.050 | 10 | 80 | 0.120 | 447.23 | 2.73 | 0.00 | python-postfilter-top80 (planner) |
| postfilter_topn | correlated | a_selectivity_sweep | 0.050 | 0.050 | 10 | 320 | 0.400 | 401.88 | 3.73 | 0.00 | python-postfilter-top320 (planner) |
| postfilter_topn | correlated | a_selectivity_sweep | 0.050 | 0.050 | 10 | 1000 | 1.000 | 509.24 | 2.60 | 0.00 | python-postfilter-top1000 (planner) |
| postfilter_topn | correlated | a_selectivity_sweep | 0.100 | 0.100 | 10 | 20 | 0.190 | 554.51 | 2.01 | 0.00 | python-postfilter-top20 (planner) |
| postfilter_topn | correlated | a_selectivity_sweep | 0.100 | 0.100 | 10 | 80 | 0.220 | 453.07 | 3.79 | 0.00 | python-postfilter-top80 (planner) |
| postfilter_topn | correlated | a_selectivity_sweep | 0.100 | 0.100 | 10 | 320 | 0.400 | 548.10 | 2.02 | 0.00 | python-postfilter-top320 (planner) |
| postfilter_topn | correlated | a_selectivity_sweep | 0.100 | 0.100 | 10 | 1000 | 1.000 | 543.32 | 1.99 | 0.00 | python-postfilter-top1000 (planner) |
| postfilter_topn | correlated | b_postfilter_recall | 0.010 | 0.010 | 10 | 20 | 0.020 | 525.91 | 2.40 | 0.00 | python-postfilter-top20 (force_index) |
| postfilter_topn | correlated | b_postfilter_recall | 0.010 | 0.010 | 10 | 80 | 0.080 | 548.83 | 2.00 | 0.00 | python-postfilter-top80 (force_index) |
| postfilter_topn | correlated | b_postfilter_recall | 0.010 | 0.010 | 10 | 320 | 0.280 | 550.07 | 1.90 | 0.00 | python-postfilter-top320 (force_index) |
| postfilter_topn | correlated | b_postfilter_recall | 0.010 | 0.010 | 10 | 1000 | 1.000 | 457.99 | 2.59 | 0.00 | python-postfilter-top1000 (force_index) |
| postfilter_topn | correlated | c_candidate_expansion | 0.010 | 0.010 | 10 | 20 | 0.020 | 517.86 | 2.03 | 0.00 | python-postfilter-top20 (force_index) |
| postfilter_topn | correlated | c_candidate_expansion | 0.010 | 0.010 | 10 | 80 | 0.080 | 529.19 | 2.03 | 0.00 | python-postfilter-top80 (force_index) |
| postfilter_topn | correlated | c_candidate_expansion | 0.010 | 0.010 | 10 | 320 | 0.280 | 550.38 | 1.97 | 0.00 | python-postfilter-top320 (force_index) |
| postfilter_topn | correlated | c_candidate_expansion | 0.010 | 0.010 | 10 | 1000 | 1.000 | 533.75 | 2.00 | 0.00 | python-postfilter-top1000 (force_index) |
| postfilter_topn | correlated | c_candidate_expansion | 0.050 | 0.050 | 10 | 20 | 0.100 | 550.03 | 1.91 | 0.00 | python-postfilter-top20 (force_index) |
| postfilter_topn | correlated | c_candidate_expansion | 0.050 | 0.050 | 10 | 80 | 0.120 | 563.77 | 1.91 | 0.00 | python-postfilter-top80 (force_index) |
| postfilter_topn | correlated | c_candidate_expansion | 0.050 | 0.050 | 10 | 320 | 0.400 | 542.08 | 2.15 | 0.00 | python-postfilter-top320 (force_index) |
| postfilter_topn | correlated | c_candidate_expansion | 0.050 | 0.050 | 10 | 1000 | 1.000 | 552.58 | 1.99 | 0.00 | python-postfilter-top1000 (force_index) |
| postfilter_topn | correlated | c_candidate_expansion | 0.100 | 0.100 | 10 | 20 | 0.190 | 528.29 | 1.97 | 0.00 | python-postfilter-top20 (force_index) |
| postfilter_topn | correlated | c_candidate_expansion | 0.100 | 0.100 | 10 | 80 | 0.220 | 562.49 | 1.85 | 0.00 | python-postfilter-top80 (force_index) |
| postfilter_topn | correlated | c_candidate_expansion | 0.100 | 0.100 | 10 | 320 | 0.400 | 558.46 | 1.90 | 0.00 | python-postfilter-top320 (force_index) |
| postfilter_topn | correlated | c_candidate_expansion | 0.100 | 0.100 | 10 | 1000 | 1.000 | 539.87 | 2.06 | 0.00 | python-postfilter-top1000 (force_index) |
| postfilter_topn | correlated | d_correlation | 0.100 | 0.100 | 10 | 20 | 0.000 | 568.30 | 1.85 | 0.00 | python-postfilter-top20 (force_index) |
| postfilter_topn | correlated | d_correlation | 0.100 | 0.100 | 10 | 80 | 0.000 | 414.57 | 2.98 | 0.00 | python-postfilter-top80 (force_index) |
| postfilter_topn | correlated | d_correlation | 0.100 | 0.100 | 10 | 320 | 0.000 | 514.74 | 2.06 | 0.00 | python-postfilter-top320 (force_index) |
| postfilter_topn | correlated | d_correlation | 0.100 | 0.100 | 10 | 1000 | 1.000 | 569.69 | 1.87 | 0.00 | python-postfilter-top1000 (force_index) |
| prefilter_exact | uncorrelated | a_selectivity_sweep | 0.010 | 0.010 | 10 | - | 1.000 | 15738.74 | 0.09 | 0.00 | python-exact (planner) |
| prefilter_exact | uncorrelated | a_selectivity_sweep | 0.050 | 0.050 | 10 | - | 1.000 | 7950.96 | 0.13 | 0.00 | python-exact (planner) |
| prefilter_exact | uncorrelated | a_selectivity_sweep | 0.100 | 0.100 | 10 | - | 1.000 | 4841.05 | 0.21 | 0.00 | python-exact (planner) |
| prefilter_exact | uncorrelated | b_postfilter_recall | 0.010 | 0.010 | 10 | - | 1.000 | 16423.73 | 0.06 | 0.00 | python-exact (force_index) |
| prefilter_exact | uncorrelated | c_candidate_expansion | 0.010 | 0.010 | 10 | - | 1.000 | 16192.13 | 0.07 | 0.00 | python-exact (force_index) |
| prefilter_exact | uncorrelated | c_candidate_expansion | 0.050 | 0.050 | 10 | - | 1.000 | 7755.95 | 0.17 | 0.00 | python-exact (force_index) |
| prefilter_exact | uncorrelated | c_candidate_expansion | 0.100 | 0.100 | 10 | - | 1.000 | 4454.42 | 0.26 | 0.00 | python-exact (force_index) |
| prefilter_exact | uncorrelated | d_correlation | 0.100 | 0.100 | 10 | - | 1.000 | 4527.11 | 0.26 | 0.00 | python-exact (force_index) |
| postfilter_topn | uncorrelated | a_selectivity_sweep | 0.010 | 0.010 | 10 | 20 | 0.010 | 570.52 | 1.85 | 0.00 | python-postfilter-top20 (planner) |
| postfilter_topn | uncorrelated | a_selectivity_sweep | 0.010 | 0.010 | 10 | 80 | 0.060 | 573.04 | 1.75 | 0.00 | python-postfilter-top80 (planner) |
| postfilter_topn | uncorrelated | a_selectivity_sweep | 0.010 | 0.010 | 10 | 320 | 0.340 | 561.48 | 1.87 | 0.00 | python-postfilter-top320 (planner) |
| postfilter_topn | uncorrelated | a_selectivity_sweep | 0.010 | 0.010 | 10 | 1000 | 1.000 | 520.01 | 2.33 | 0.00 | python-postfilter-top1000 (planner) |
| postfilter_topn | uncorrelated | a_selectivity_sweep | 0.050 | 0.050 | 10 | 20 | 0.080 | 571.92 | 1.77 | 0.00 | python-postfilter-top20 (planner) |
| postfilter_topn | uncorrelated | a_selectivity_sweep | 0.050 | 0.050 | 10 | 80 | 0.440 | 495.28 | 2.37 | 0.00 | python-postfilter-top80 (planner) |
| postfilter_topn | uncorrelated | a_selectivity_sweep | 0.050 | 0.050 | 10 | 320 | 1.000 | 425.05 | 2.96 | 0.00 | python-postfilter-top320 (planner) |
| postfilter_topn | uncorrelated | a_selectivity_sweep | 0.050 | 0.050 | 10 | 1000 | 1.000 | 505.86 | 2.31 | 0.00 | python-postfilter-top1000 (planner) |
| postfilter_topn | uncorrelated | a_selectivity_sweep | 0.100 | 0.100 | 10 | 20 | 0.210 | 502.87 | 2.94 | 0.00 | python-postfilter-top20 (planner) |
| postfilter_topn | uncorrelated | a_selectivity_sweep | 0.100 | 0.100 | 10 | 80 | 0.890 | 392.29 | 5.79 | 0.00 | python-postfilter-top80 (planner) |
| postfilter_topn | uncorrelated | a_selectivity_sweep | 0.100 | 0.100 | 10 | 320 | 1.000 | 437.57 | 2.41 | 0.00 | python-postfilter-top320 (planner) |
| postfilter_topn | uncorrelated | a_selectivity_sweep | 0.100 | 0.100 | 10 | 1000 | 1.000 | 464.02 | 2.46 | 0.00 | python-postfilter-top1000 (planner) |
| postfilter_topn | uncorrelated | b_postfilter_recall | 0.010 | 0.010 | 10 | 20 | 0.010 | 490.30 | 2.43 | 0.00 | python-postfilter-top20 (force_index) |
| postfilter_topn | uncorrelated | b_postfilter_recall | 0.010 | 0.010 | 10 | 80 | 0.060 | 527.27 | 2.21 | 0.00 | python-postfilter-top80 (force_index) |
| postfilter_topn | uncorrelated | b_postfilter_recall | 0.010 | 0.010 | 10 | 320 | 0.340 | 566.90 | 1.80 | 0.00 | python-postfilter-top320 (force_index) |
| postfilter_topn | uncorrelated | b_postfilter_recall | 0.010 | 0.010 | 10 | 1000 | 1.000 | 535.86 | 2.08 | 0.00 | python-postfilter-top1000 (force_index) |
| postfilter_topn | uncorrelated | c_candidate_expansion | 0.010 | 0.010 | 10 | 20 | 0.010 | 485.33 | 2.12 | 0.00 | python-postfilter-top20 (force_index) |
| postfilter_topn | uncorrelated | c_candidate_expansion | 0.010 | 0.010 | 10 | 80 | 0.060 | 550.37 | 2.02 | 0.00 | python-postfilter-top80 (force_index) |
| postfilter_topn | uncorrelated | c_candidate_expansion | 0.010 | 0.010 | 10 | 320 | 0.340 | 562.21 | 1.83 | 0.00 | python-postfilter-top320 (force_index) |
| postfilter_topn | uncorrelated | c_candidate_expansion | 0.010 | 0.010 | 10 | 1000 | 1.000 | 517.91 | 3.59 | 0.00 | python-postfilter-top1000 (force_index) |
| postfilter_topn | uncorrelated | c_candidate_expansion | 0.050 | 0.050 | 10 | 20 | 0.080 | 521.99 | 2.28 | 0.00 | python-postfilter-top20 (force_index) |
| postfilter_topn | uncorrelated | c_candidate_expansion | 0.050 | 0.050 | 10 | 80 | 0.440 | 564.13 | 1.96 | 0.00 | python-postfilter-top80 (force_index) |
| postfilter_topn | uncorrelated | c_candidate_expansion | 0.050 | 0.050 | 10 | 320 | 1.000 | 563.30 | 1.83 | 0.00 | python-postfilter-top320 (force_index) |
| postfilter_topn | uncorrelated | c_candidate_expansion | 0.050 | 0.050 | 10 | 1000 | 1.000 | 558.23 | 1.82 | 0.00 | python-postfilter-top1000 (force_index) |
| postfilter_topn | uncorrelated | c_candidate_expansion | 0.100 | 0.100 | 10 | 20 | 0.210 | 547.70 | 2.06 | 0.00 | python-postfilter-top20 (force_index) |
| postfilter_topn | uncorrelated | c_candidate_expansion | 0.100 | 0.100 | 10 | 80 | 0.890 | 541.62 | 2.00 | 0.00 | python-postfilter-top80 (force_index) |
| postfilter_topn | uncorrelated | c_candidate_expansion | 0.100 | 0.100 | 10 | 320 | 1.000 | 453.34 | 4.08 | 0.00 | python-postfilter-top320 (force_index) |
| postfilter_topn | uncorrelated | c_candidate_expansion | 0.100 | 0.100 | 10 | 1000 | 1.000 | 484.91 | 2.72 | 0.00 | python-postfilter-top1000 (force_index) |
| postfilter_topn | uncorrelated | d_correlation | 0.100 | 0.100 | 10 | 20 | 0.140 | 532.97 | 2.07 | 0.00 | python-postfilter-top20 (force_index) |
| postfilter_topn | uncorrelated | d_correlation | 0.100 | 0.100 | 10 | 80 | 0.730 | 379.39 | 3.88 | 0.00 | python-postfilter-top80 (force_index) |
| postfilter_topn | uncorrelated | d_correlation | 0.100 | 0.100 | 10 | 320 | 1.000 | 542.75 | 2.02 | 0.00 | python-postfilter-top320 (force_index) |
| postfilter_topn | uncorrelated | d_correlation | 0.100 | 0.100 | 10 | 1000 | 1.000 | 558.70 | 1.99 | 0.00 | python-postfilter-top1000 (force_index) |

## Candidate-expansion recovery (scenario C, index path forced)

Lowest search value reaching recall >= 0.94; when none does, the
best cell is the max-recall operating point. A recovery cell that ran an exact path
(a Sort node) or mixed plans is marked; `plan` belongs to the best cell.

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
