# Filtered ANN benchmark report

- run_id: `20261023-150640`
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
| prefilter_exact | correlated | a_selectivity_sweep | 0.010 | 0.010 | 10 | - | 1.000 | 16832.67 | 0.06 | 0.00 | python-exact (planner) |
| prefilter_exact | correlated | a_selectivity_sweep | 0.050 | 0.050 | 10 | - | 1.000 | 8018.17 | 0.13 | 0.00 | python-exact (planner) |
| prefilter_exact | correlated | a_selectivity_sweep | 0.100 | 0.100 | 10 | - | 1.000 | 4728.13 | 0.25 | 0.00 | python-exact (planner) |
| prefilter_exact | correlated | b_postfilter_recall | 0.010 | 0.010 | 10 | - | 1.000 | 16602.08 | 0.06 | 0.00 | python-exact (force_index) |
| prefilter_exact | correlated | c_candidate_expansion | 0.010 | 0.010 | 10 | - | 1.000 | 16688.69 | 0.06 | 0.00 | python-exact (force_index) |
| prefilter_exact | correlated | c_candidate_expansion | 0.050 | 0.050 | 10 | - | 1.000 | 7963.90 | 0.13 | 0.00 | python-exact (force_index) |
| prefilter_exact | correlated | c_candidate_expansion | 0.100 | 0.100 | 10 | - | 1.000 | 4877.95 | 0.21 | 0.00 | python-exact (force_index) |
| prefilter_exact | correlated | d_correlation | 0.100 | 0.100 | 10 | - | 1.000 | 4772.22 | 0.22 | 0.00 | python-exact (force_index) |
| postfilter_topn | correlated | a_selectivity_sweep | 0.010 | 0.010 | 10 | 20 | 0.000 | 539.83 | 2.70 | 0.00 | python-postfilter-top20 (planner) |
| postfilter_topn | correlated | a_selectivity_sweep | 0.010 | 0.010 | 10 | 80 | 0.080 | 509.01 | 2.96 | 0.00 | python-postfilter-top80 (planner) |
| postfilter_topn | correlated | a_selectivity_sweep | 0.010 | 0.010 | 10 | 320 | 0.250 | 572.67 | 1.87 | 0.00 | python-postfilter-top320 (planner) |
| postfilter_topn | correlated | a_selectivity_sweep | 0.010 | 0.010 | 10 | 1000 | 1.000 | 569.86 | 1.76 | 0.00 | python-postfilter-top1000 (planner) |
| postfilter_topn | correlated | a_selectivity_sweep | 0.050 | 0.050 | 10 | 20 | 0.100 | 569.22 | 1.88 | 0.00 | python-postfilter-top20 (planner) |
| postfilter_topn | correlated | a_selectivity_sweep | 0.050 | 0.050 | 10 | 80 | 0.130 | 568.04 | 1.78 | 0.00 | python-postfilter-top80 (planner) |
| postfilter_topn | correlated | a_selectivity_sweep | 0.050 | 0.050 | 10 | 320 | 0.400 | 558.13 | 1.86 | 0.00 | python-postfilter-top320 (planner) |
| postfilter_topn | correlated | a_selectivity_sweep | 0.050 | 0.050 | 10 | 1000 | 1.000 | 496.67 | 3.20 | 0.00 | python-postfilter-top1000 (planner) |
| postfilter_topn | correlated | a_selectivity_sweep | 0.100 | 0.100 | 10 | 20 | 0.160 | 578.11 | 1.78 | 0.00 | python-postfilter-top20 (planner) |
| postfilter_topn | correlated | a_selectivity_sweep | 0.100 | 0.100 | 10 | 80 | 0.220 | 573.45 | 1.82 | 0.00 | python-postfilter-top80 (planner) |
| postfilter_topn | correlated | a_selectivity_sweep | 0.100 | 0.100 | 10 | 320 | 0.400 | 603.55 | 1.70 | 0.00 | python-postfilter-top320 (planner) |
| postfilter_topn | correlated | a_selectivity_sweep | 0.100 | 0.100 | 10 | 1000 | 1.000 | 590.53 | 1.90 | 0.00 | python-postfilter-top1000 (planner) |
| postfilter_topn | correlated | b_postfilter_recall | 0.010 | 0.010 | 10 | 20 | 0.000 | 585.05 | 1.76 | 0.00 | python-postfilter-top20 (force_index) |
| postfilter_topn | correlated | b_postfilter_recall | 0.010 | 0.010 | 10 | 80 | 0.080 | 594.75 | 1.75 | 0.00 | python-postfilter-top80 (force_index) |
| postfilter_topn | correlated | b_postfilter_recall | 0.010 | 0.010 | 10 | 320 | 0.250 | 588.21 | 1.76 | 0.00 | python-postfilter-top320 (force_index) |
| postfilter_topn | correlated | b_postfilter_recall | 0.010 | 0.010 | 10 | 1000 | 1.000 | 567.46 | 1.80 | 0.00 | python-postfilter-top1000 (force_index) |
| postfilter_topn | correlated | c_candidate_expansion | 0.010 | 0.010 | 10 | 20 | 0.000 | 608.29 | 1.68 | 0.00 | python-postfilter-top20 (force_index) |
| postfilter_topn | correlated | c_candidate_expansion | 0.010 | 0.010 | 10 | 80 | 0.080 | 611.66 | 1.70 | 0.00 | python-postfilter-top80 (force_index) |
| postfilter_topn | correlated | c_candidate_expansion | 0.010 | 0.010 | 10 | 320 | 0.250 | 598.83 | 1.74 | 0.00 | python-postfilter-top320 (force_index) |
| postfilter_topn | correlated | c_candidate_expansion | 0.010 | 0.010 | 10 | 1000 | 1.000 | 597.53 | 1.76 | 0.00 | python-postfilter-top1000 (force_index) |
| postfilter_topn | correlated | c_candidate_expansion | 0.050 | 0.050 | 10 | 20 | 0.100 | 579.80 | 1.98 | 0.00 | python-postfilter-top20 (force_index) |
| postfilter_topn | correlated | c_candidate_expansion | 0.050 | 0.050 | 10 | 80 | 0.130 | 533.77 | 2.94 | 0.00 | python-postfilter-top80 (force_index) |
| postfilter_topn | correlated | c_candidate_expansion | 0.050 | 0.050 | 10 | 320 | 0.400 | 584.18 | 1.73 | 0.00 | python-postfilter-top320 (force_index) |
| postfilter_topn | correlated | c_candidate_expansion | 0.050 | 0.050 | 10 | 1000 | 1.000 | 463.36 | 4.19 | 0.00 | python-postfilter-top1000 (force_index) |
| postfilter_topn | correlated | c_candidate_expansion | 0.100 | 0.100 | 10 | 20 | 0.160 | 592.96 | 1.70 | 0.00 | python-postfilter-top20 (force_index) |
| postfilter_topn | correlated | c_candidate_expansion | 0.100 | 0.100 | 10 | 80 | 0.220 | 613.48 | 1.73 | 0.00 | python-postfilter-top80 (force_index) |
| postfilter_topn | correlated | c_candidate_expansion | 0.100 | 0.100 | 10 | 320 | 0.400 | 589.33 | 1.77 | 0.00 | python-postfilter-top320 (force_index) |
| postfilter_topn | correlated | c_candidate_expansion | 0.100 | 0.100 | 10 | 1000 | 1.000 | 589.94 | 1.77 | 0.00 | python-postfilter-top1000 (force_index) |
| postfilter_topn | correlated | d_correlation | 0.100 | 0.100 | 10 | 20 | 0.000 | 602.93 | 1.79 | 0.00 | python-postfilter-top20 (force_index) |
| postfilter_topn | correlated | d_correlation | 0.100 | 0.100 | 10 | 80 | 0.000 | 588.14 | 1.70 | 0.00 | python-postfilter-top80 (force_index) |
| postfilter_topn | correlated | d_correlation | 0.100 | 0.100 | 10 | 320 | 0.000 | 604.55 | 1.73 | 0.00 | python-postfilter-top320 (force_index) |
| postfilter_topn | correlated | d_correlation | 0.100 | 0.100 | 10 | 1000 | 1.000 | 576.81 | 1.74 | 0.00 | python-postfilter-top1000 (force_index) |
| prefilter_exact | uncorrelated | a_selectivity_sweep | 0.010 | 0.010 | 10 | - | 1.000 | 16576.88 | 0.06 | 0.00 | python-exact (planner) |
| prefilter_exact | uncorrelated | a_selectivity_sweep | 0.050 | 0.050 | 10 | - | 1.000 | 7833.92 | 0.13 | 0.00 | python-exact (planner) |
| prefilter_exact | uncorrelated | a_selectivity_sweep | 0.100 | 0.100 | 10 | - | 1.000 | 4996.77 | 0.23 | 0.00 | python-exact (planner) |
| prefilter_exact | uncorrelated | b_postfilter_recall | 0.010 | 0.010 | 10 | - | 1.000 | 17478.70 | 0.06 | 0.00 | python-exact (force_index) |
| prefilter_exact | uncorrelated | c_candidate_expansion | 0.010 | 0.010 | 10 | - | 1.000 | 17645.74 | 0.06 | 0.00 | python-exact (force_index) |
| prefilter_exact | uncorrelated | c_candidate_expansion | 0.050 | 0.050 | 10 | - | 1.000 | 8190.85 | 0.13 | 0.00 | python-exact (force_index) |
| prefilter_exact | uncorrelated | c_candidate_expansion | 0.100 | 0.100 | 10 | - | 1.000 | 5017.25 | 0.22 | 0.00 | python-exact (force_index) |
| prefilter_exact | uncorrelated | d_correlation | 0.100 | 0.100 | 10 | - | 1.000 | 4761.43 | 0.21 | 0.00 | python-exact (force_index) |
| postfilter_topn | uncorrelated | a_selectivity_sweep | 0.010 | 0.010 | 10 | 20 | 0.020 | 588.93 | 1.78 | 0.00 | python-postfilter-top20 (planner) |
| postfilter_topn | uncorrelated | a_selectivity_sweep | 0.010 | 0.010 | 10 | 80 | 0.080 | 593.15 | 1.75 | 0.00 | python-postfilter-top80 (planner) |
| postfilter_topn | uncorrelated | a_selectivity_sweep | 0.010 | 0.010 | 10 | 320 | 0.390 | 577.50 | 1.85 | 0.00 | python-postfilter-top320 (planner) |
| postfilter_topn | uncorrelated | a_selectivity_sweep | 0.010 | 0.010 | 10 | 1000 | 1.000 | 559.60 | 1.78 | 0.00 | python-postfilter-top1000 (planner) |
| postfilter_topn | uncorrelated | a_selectivity_sweep | 0.050 | 0.050 | 10 | 20 | 0.060 | 581.97 | 1.73 | 0.00 | python-postfilter-top20 (planner) |
| postfilter_topn | uncorrelated | a_selectivity_sweep | 0.050 | 0.050 | 10 | 80 | 0.320 | 583.57 | 1.74 | 0.00 | python-postfilter-top80 (planner) |
| postfilter_topn | uncorrelated | a_selectivity_sweep | 0.050 | 0.050 | 10 | 320 | 1.000 | 569.63 | 1.80 | 0.00 | python-postfilter-top320 (planner) |
| postfilter_topn | uncorrelated | a_selectivity_sweep | 0.050 | 0.050 | 10 | 1000 | 1.000 | 518.02 | 2.43 | 0.00 | python-postfilter-top1000 (planner) |
| postfilter_topn | uncorrelated | a_selectivity_sweep | 0.100 | 0.100 | 10 | 20 | 0.180 | 578.23 | 1.79 | 0.00 | python-postfilter-top20 (planner) |
| postfilter_topn | uncorrelated | a_selectivity_sweep | 0.100 | 0.100 | 10 | 80 | 0.760 | 594.94 | 1.70 | 0.00 | python-postfilter-top80 (planner) |
| postfilter_topn | uncorrelated | a_selectivity_sweep | 0.100 | 0.100 | 10 | 320 | 1.000 | 560.95 | 2.37 | 0.00 | python-postfilter-top320 (planner) |
| postfilter_topn | uncorrelated | a_selectivity_sweep | 0.100 | 0.100 | 10 | 1000 | 1.000 | 553.42 | 1.86 | 0.00 | python-postfilter-top1000 (planner) |
| postfilter_topn | uncorrelated | b_postfilter_recall | 0.010 | 0.010 | 10 | 20 | 0.020 | 590.68 | 1.71 | 0.00 | python-postfilter-top20 (force_index) |
| postfilter_topn | uncorrelated | b_postfilter_recall | 0.010 | 0.010 | 10 | 80 | 0.080 | 573.32 | 1.74 | 0.00 | python-postfilter-top80 (force_index) |
| postfilter_topn | uncorrelated | b_postfilter_recall | 0.010 | 0.010 | 10 | 320 | 0.390 | 568.84 | 1.77 | 0.00 | python-postfilter-top320 (force_index) |
| postfilter_topn | uncorrelated | b_postfilter_recall | 0.010 | 0.010 | 10 | 1000 | 1.000 | 567.23 | 1.77 | 0.00 | python-postfilter-top1000 (force_index) |
| postfilter_topn | uncorrelated | c_candidate_expansion | 0.010 | 0.010 | 10 | 20 | 0.020 | 539.95 | 2.40 | 0.00 | python-postfilter-top20 (force_index) |
| postfilter_topn | uncorrelated | c_candidate_expansion | 0.010 | 0.010 | 10 | 80 | 0.080 | 570.67 | 1.93 | 0.00 | python-postfilter-top80 (force_index) |
| postfilter_topn | uncorrelated | c_candidate_expansion | 0.010 | 0.010 | 10 | 320 | 0.390 | 589.41 | 1.76 | 0.00 | python-postfilter-top320 (force_index) |
| postfilter_topn | uncorrelated | c_candidate_expansion | 0.010 | 0.010 | 10 | 1000 | 1.000 | 572.63 | 1.90 | 0.00 | python-postfilter-top1000 (force_index) |
| postfilter_topn | uncorrelated | c_candidate_expansion | 0.050 | 0.050 | 10 | 20 | 0.060 | 585.16 | 1.74 | 0.00 | python-postfilter-top20 (force_index) |
| postfilter_topn | uncorrelated | c_candidate_expansion | 0.050 | 0.050 | 10 | 80 | 0.320 | 582.04 | 1.81 | 0.00 | python-postfilter-top80 (force_index) |
| postfilter_topn | uncorrelated | c_candidate_expansion | 0.050 | 0.050 | 10 | 320 | 1.000 | 483.74 | 2.67 | 0.00 | python-postfilter-top320 (force_index) |
| postfilter_topn | uncorrelated | c_candidate_expansion | 0.050 | 0.050 | 10 | 1000 | 1.000 | 532.92 | 2.55 | 0.00 | python-postfilter-top1000 (force_index) |
| postfilter_topn | uncorrelated | c_candidate_expansion | 0.100 | 0.100 | 10 | 20 | 0.180 | 460.52 | 4.20 | 0.00 | python-postfilter-top20 (force_index) |
| postfilter_topn | uncorrelated | c_candidate_expansion | 0.100 | 0.100 | 10 | 80 | 0.760 | 499.82 | 4.10 | 0.00 | python-postfilter-top80 (force_index) |
| postfilter_topn | uncorrelated | c_candidate_expansion | 0.100 | 0.100 | 10 | 320 | 1.000 | 593.93 | 1.74 | 0.00 | python-postfilter-top320 (force_index) |
| postfilter_topn | uncorrelated | c_candidate_expansion | 0.100 | 0.100 | 10 | 1000 | 1.000 | 584.31 | 1.77 | 0.00 | python-postfilter-top1000 (force_index) |
| postfilter_topn | uncorrelated | d_correlation | 0.100 | 0.100 | 10 | 20 | 0.190 | 586.24 | 1.75 | 0.00 | python-postfilter-top20 (force_index) |
| postfilter_topn | uncorrelated | d_correlation | 0.100 | 0.100 | 10 | 80 | 0.770 | 587.78 | 1.73 | 0.00 | python-postfilter-top80 (force_index) |
| postfilter_topn | uncorrelated | d_correlation | 0.100 | 0.100 | 10 | 320 | 1.000 | 578.16 | 1.74 | 0.00 | python-postfilter-top320 (force_index) |
| postfilter_topn | uncorrelated | d_correlation | 0.100 | 0.100 | 10 | 1000 | 1.000 | 566.77 | 1.80 | 0.00 | python-postfilter-top1000 (force_index) |

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
