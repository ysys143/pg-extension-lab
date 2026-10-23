# Filtered ANN benchmark report

- run_id: `20261023-150644`
- profile: filtered-ann
- command: `python run_bench.py --config bench_config.pgvector-example.toml --output sample_artifacts/results_pgvector_smoke.json`
- pgvector_example: extension_version 0.8.7, postgres_version 17.11 (Debian 17.11-1.pgdg12+2)
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
| pgvector_example | correlated | a_selectivity_sweep | 0.010 | 0.010 | 10 | 20 | 1.000 | 2565.61 | 0.44 | 42.00 | Limit > Sort > Seq Scan (planner) |
| pgvector_example | correlated | a_selectivity_sweep | 0.010 | 0.010 | 10 | 40 | 1.000 | 2841.11 | 0.42 | 42.00 | Limit > Sort > Seq Scan (planner) |
| pgvector_example | correlated | a_selectivity_sweep | 0.010 | 0.010 | 10 | 80 | 1.000 | 3011.75 | 0.39 | 42.00 | Limit > Sort > Seq Scan (planner) |
| pgvector_example | correlated | a_selectivity_sweep | 0.010 | 0.010 | 10 | 160 | 1.000 | 2499.64 | 0.64 | 42.00 | Limit > Sort > Seq Scan (planner) |
| pgvector_example | correlated | a_selectivity_sweep | 0.050 | 0.050 | 10 | 20 | 1.000 | 2564.73 | 0.60 | 42.00 | Limit > Sort > Seq Scan (planner) |
| pgvector_example | correlated | a_selectivity_sweep | 0.050 | 0.050 | 10 | 40 | 1.000 | 1456.30 | 1.27 | 42.00 | Limit > Sort > Seq Scan (planner) |
| pgvector_example | correlated | a_selectivity_sweep | 0.050 | 0.050 | 10 | 80 | 1.000 | 1541.27 | 1.22 | 42.00 | Limit > Sort > Seq Scan (planner) |
| pgvector_example | correlated | a_selectivity_sweep | 0.050 | 0.050 | 10 | 160 | 1.000 | 1523.96 | 1.13 | 42.00 | Limit > Sort > Seq Scan (planner) |
| pgvector_example | correlated | a_selectivity_sweep | 0.100 | 0.100 | 10 | 20 | 1.000 | 594.65 | 5.40 | 42.00 | Limit > Sort > Seq Scan (planner) |
| pgvector_example | correlated | a_selectivity_sweep | 0.100 | 0.100 | 10 | 40 | 1.000 | 958.06 | 1.09 | 42.00 | Limit > Sort > Seq Scan (planner) |
| pgvector_example | correlated | a_selectivity_sweep | 0.100 | 0.100 | 10 | 80 | 1.000 | 1949.82 | 0.61 | 42.00 | Limit > Sort > Seq Scan (planner) |
| pgvector_example | correlated | a_selectivity_sweep | 0.100 | 0.100 | 10 | 160 | 1.000 | 2184.96 | 0.55 | 42.00 | Limit > Sort > Seq Scan (planner) |
| pgvector_example | correlated | b_postfilter_recall | 0.010 | 0.010 | 10 | 20 | 0.000 | 546.07 | 4.56 | 394.40 | Limit > Index Scan (force_index) |
| pgvector_example | correlated | b_postfilter_recall | 0.010 | 0.010 | 10 | 40 | 0.050 | 1241.37 | 1.09 | 514.60 | Limit > Index Scan (force_index) |
| pgvector_example | correlated | b_postfilter_recall | 0.010 | 0.010 | 10 | 80 | 0.080 | 460.31 | 8.87 | 725.20 | Limit > Index Scan (force_index) |
| pgvector_example | correlated | b_postfilter_recall | 0.010 | 0.010 | 10 | 160 | 0.100 | 1003.90 | 1.57 | 1154.20 | Limit > Index Scan (force_index) |
| pgvector_example | correlated | c_candidate_expansion | 0.010 | 0.010 | 10 | 20 | 0.000 | 1188.54 | 1.32 | 394.40 | Limit > Index Scan (force_index) |
| pgvector_example | correlated | c_candidate_expansion | 0.010 | 0.010 | 10 | 40 | 0.050 | 2067.33 | 0.82 | 514.60 | Limit > Index Scan (force_index) |
| pgvector_example | correlated | c_candidate_expansion | 0.010 | 0.010 | 10 | 80 | 0.080 | 1571.03 | 0.93 | 725.20 | Limit > Index Scan (force_index) |
| pgvector_example | correlated | c_candidate_expansion | 0.010 | 0.010 | 10 | 160 | 0.100 | 1313.36 | 1.46 | 1154.20 | Limit > Index Scan (force_index) |
| pgvector_example | correlated | c_candidate_expansion | 0.050 | 0.050 | 10 | 20 | 0.100 | 2203.61 | 0.55 | 392.80 | Limit > Index Scan (force_index) |
| pgvector_example | correlated | c_candidate_expansion | 0.050 | 0.050 | 10 | 40 | 0.110 | 1873.90 | 0.60 | 509.60 | Limit > Index Scan (force_index) |
| pgvector_example | correlated | c_candidate_expansion | 0.050 | 0.050 | 10 | 80 | 0.130 | 1893.48 | 0.58 | 712.60 | Limit > Index Scan (force_index) |
| pgvector_example | correlated | c_candidate_expansion | 0.050 | 0.050 | 10 | 160 | 0.200 | 1269.01 | 1.62 | 1131.20 | Limit > Index Scan (force_index) |
| pgvector_example | correlated | c_candidate_expansion | 0.100 | 0.100 | 10 | 20 | 0.160 | 1555.23 | 0.99 | 392.40 | Limit > Index Scan (force_index) |
| pgvector_example | correlated | c_candidate_expansion | 0.100 | 0.100 | 10 | 40 | 0.200 | 1665.36 | 0.82 | 506.60 | Limit > Index Scan (force_index) |
| pgvector_example | correlated | c_candidate_expansion | 0.100 | 0.100 | 10 | 80 | 0.220 | 1916.08 | 0.64 | 701.80 | Limit > Index Scan (force_index) |
| pgvector_example | correlated | c_candidate_expansion | 0.100 | 0.100 | 10 | 160 | 0.350 | 1723.40 | 0.66 | 1105.40 | Limit > Index Scan (force_index) |
| pgvector_example | correlated | d_correlation | 0.100 | 0.100 | 10 | 20 | 0.000 | 2008.50 | 0.57 | 357.60 | Limit > Index Scan (force_index) |
| pgvector_example | correlated | d_correlation | 0.100 | 0.100 | 10 | 40 | 0.000 | 1625.99 | 1.30 | 479.60 | Limit > Index Scan (force_index) |
| pgvector_example | correlated | d_correlation | 0.100 | 0.100 | 10 | 80 | 0.000 | 1819.31 | 0.65 | 695.20 | Limit > Index Scan (force_index) |
| pgvector_example | correlated | d_correlation | 0.100 | 0.100 | 10 | 160 | 0.000 | 1613.67 | 0.70 | 1117.80 | Limit > Index Scan (force_index) |
| prefilter_exact | correlated | a_selectivity_sweep | 0.010 | 0.010 | 10 | - | 1.000 | 3390.31 | 0.49 | 0.00 | python-exact (planner) |
| prefilter_exact | correlated | a_selectivity_sweep | 0.050 | 0.050 | 10 | - | 1.000 | 2510.88 | 0.47 | 0.00 | python-exact (planner) |
| prefilter_exact | correlated | a_selectivity_sweep | 0.100 | 0.100 | 10 | - | 1.000 | 3872.65 | 0.46 | 0.00 | python-exact (planner) |
| prefilter_exact | correlated | b_postfilter_recall | 0.010 | 0.010 | 10 | - | 1.000 | 22127.95 | 0.05 | 0.00 | python-exact (force_index) |
| prefilter_exact | correlated | c_candidate_expansion | 0.010 | 0.010 | 10 | - | 1.000 | 22503.52 | 0.05 | 0.00 | python-exact (force_index) |
| prefilter_exact | correlated | c_candidate_expansion | 0.050 | 0.050 | 10 | - | 1.000 | 9662.22 | 0.11 | 0.00 | python-exact (force_index) |
| prefilter_exact | correlated | c_candidate_expansion | 0.100 | 0.100 | 10 | - | 1.000 | 5662.38 | 0.18 | 0.00 | python-exact (force_index) |
| prefilter_exact | correlated | d_correlation | 0.100 | 0.100 | 10 | - | 1.000 | 5630.63 | 0.19 | 0.00 | python-exact (force_index) |
| pgvector_example | uncorrelated | a_selectivity_sweep | 0.010 | 0.010 | 10 | 20 | 1.000 | 2013.15 | 0.68 | 42.00 | Limit > Sort > Seq Scan (planner) |
| pgvector_example | uncorrelated | a_selectivity_sweep | 0.010 | 0.010 | 10 | 40 | 1.000 | 2208.44 | 0.52 | 42.00 | Limit > Sort > Seq Scan (planner) |
| pgvector_example | uncorrelated | a_selectivity_sweep | 0.010 | 0.010 | 10 | 80 | 1.000 | 2269.01 | 0.48 | 42.00 | Limit > Sort > Seq Scan (planner) |
| pgvector_example | uncorrelated | a_selectivity_sweep | 0.010 | 0.010 | 10 | 160 | 1.000 | 1545.62 | 0.88 | 42.00 | Limit > Sort > Seq Scan (planner) |
| pgvector_example | uncorrelated | a_selectivity_sweep | 0.050 | 0.050 | 10 | 20 | 1.000 | 2127.74 | 0.56 | 42.00 | Limit > Sort > Seq Scan (planner) |
| pgvector_example | uncorrelated | a_selectivity_sweep | 0.050 | 0.050 | 10 | 40 | 1.000 | 744.37 | 2.72 | 42.00 | Limit > Sort > Seq Scan (planner) |
| pgvector_example | uncorrelated | a_selectivity_sweep | 0.050 | 0.050 | 10 | 80 | 1.000 | 1819.20 | 0.77 | 42.00 | Limit > Sort > Seq Scan (planner) |
| pgvector_example | uncorrelated | a_selectivity_sweep | 0.050 | 0.050 | 10 | 160 | 1.000 | 256.56 | 14.12 | 42.00 | Limit > Sort > Seq Scan (planner) |
| pgvector_example | uncorrelated | a_selectivity_sweep | 0.100 | 0.100 | 10 | 20 | 1.000 | 1143.55 | 1.73 | 42.00 | Limit > Sort > Seq Scan (planner) |
| pgvector_example | uncorrelated | a_selectivity_sweep | 0.100 | 0.100 | 10 | 40 | 1.000 | 1670.58 | 0.72 | 42.00 | Limit > Sort > Seq Scan (planner) |
| pgvector_example | uncorrelated | a_selectivity_sweep | 0.100 | 0.100 | 10 | 80 | 1.000 | 2335.97 | 0.44 | 42.00 | Limit > Sort > Seq Scan (planner) |
| pgvector_example | uncorrelated | a_selectivity_sweep | 0.100 | 0.100 | 10 | 160 | 1.000 | 1837.39 | 0.63 | 42.00 | Limit > Sort > Seq Scan (planner) |
| pgvector_example | uncorrelated | b_postfilter_recall | 0.010 | 0.010 | 10 | 20 | 0.020 | 1257.71 | 1.18 | 809.20 | Limit > Index Scan (force_index) |
| pgvector_example | uncorrelated | b_postfilter_recall | 0.010 | 0.010 | 10 | 40 | 0.030 | 959.62 | 1.40 | 1208.00 | Limit > Index Scan (force_index) |
| pgvector_example | uncorrelated | b_postfilter_recall | 0.010 | 0.010 | 10 | 80 | 0.080 | 1340.49 | 1.13 | 1717.80 | Limit > Index Scan (force_index) |
| pgvector_example | uncorrelated | b_postfilter_recall | 0.010 | 0.010 | 10 | 160 | 0.190 | 1425.09 | 0.76 | 2372.20 | Limit > Index Scan (force_index) |
| pgvector_example | uncorrelated | c_candidate_expansion | 0.010 | 0.010 | 10 | 20 | 0.020 | 1690.83 | 0.96 | 809.20 | Limit > Index Scan (force_index) |
| pgvector_example | uncorrelated | c_candidate_expansion | 0.010 | 0.010 | 10 | 40 | 0.030 | 1470.08 | 1.07 | 1208.00 | Limit > Index Scan (force_index) |
| pgvector_example | uncorrelated | c_candidate_expansion | 0.010 | 0.010 | 10 | 80 | 0.080 | 1745.14 | 0.65 | 1717.80 | Limit > Index Scan (force_index) |
| pgvector_example | uncorrelated | c_candidate_expansion | 0.010 | 0.010 | 10 | 160 | 0.190 | 1278.49 | 0.93 | 2372.20 | Limit > Index Scan (force_index) |
| pgvector_example | uncorrelated | c_candidate_expansion | 0.050 | 0.050 | 10 | 20 | 0.060 | 1957.75 | 0.59 | 809.20 | Limit > Index Scan (force_index) |
| pgvector_example | uncorrelated | c_candidate_expansion | 0.050 | 0.050 | 10 | 40 | 0.110 | 1494.01 | 1.51 | 1208.00 | Limit > Index Scan (force_index) |
| pgvector_example | uncorrelated | c_candidate_expansion | 0.050 | 0.050 | 10 | 80 | 0.320 | 1527.52 | 0.78 | 1717.80 | Limit > Index Scan (force_index) |
| pgvector_example | uncorrelated | c_candidate_expansion | 0.050 | 0.050 | 10 | 160 | 0.750 | 1529.92 | 0.73 | 2364.20 | Limit > Index Scan (force_index) |
| pgvector_example | uncorrelated | c_candidate_expansion | 0.100 | 0.100 | 10 | 20 | 0.170 | 439.61 | 9.68 | 809.20 | Limit > Index Scan (force_index) |
| pgvector_example | uncorrelated | c_candidate_expansion | 0.100 | 0.100 | 10 | 40 | 0.360 | 1869.42 | 0.64 | 1208.00 | Limit > Index Scan (force_index) |
| pgvector_example | uncorrelated | c_candidate_expansion | 0.100 | 0.100 | 10 | 80 | 0.760 | 1639.77 | 0.71 | 1713.80 | Limit > Index Scan (force_index) |
| pgvector_example | uncorrelated | c_candidate_expansion | 0.100 | 0.100 | 10 | 160 | 1.000 | 978.67 | 1.47 | 2251.60 | Limit > Index Scan (force_index) |
| pgvector_example | uncorrelated | d_correlation | 0.100 | 0.100 | 10 | 20 | 0.190 | 1943.51 | 0.58 | 810.00 | Limit > Index Scan (force_index) |
| pgvector_example | uncorrelated | d_correlation | 0.100 | 0.100 | 10 | 40 | 0.430 | 1871.55 | 0.63 | 1186.40 | Limit > Index Scan (force_index) |
| pgvector_example | uncorrelated | d_correlation | 0.100 | 0.100 | 10 | 80 | 0.770 | 1617.83 | 0.71 | 1699.40 | Limit > Index Scan (force_index) |
| pgvector_example | uncorrelated | d_correlation | 0.100 | 0.100 | 10 | 160 | 0.980 | 1342.86 | 0.80 | 2241.00 | Limit > Index Scan (force_index) |
| prefilter_exact | uncorrelated | a_selectivity_sweep | 0.010 | 0.010 | 10 | - | 1.000 | 7752.19 | 0.19 | 0.00 | python-exact (planner) |
| prefilter_exact | uncorrelated | a_selectivity_sweep | 0.050 | 0.050 | 10 | - | 1.000 | 1428.78 | 1.60 | 0.00 | python-exact (planner) |
| prefilter_exact | uncorrelated | a_selectivity_sweep | 0.100 | 0.100 | 10 | - | 1.000 | 2013.90 | 0.51 | 0.00 | python-exact (planner) |
| prefilter_exact | uncorrelated | b_postfilter_recall | 0.010 | 0.010 | 10 | - | 1.000 | 9806.72 | 0.13 | 0.00 | python-exact (force_index) |
| prefilter_exact | uncorrelated | c_candidate_expansion | 0.010 | 0.010 | 10 | - | 1.000 | 21617.74 | 0.05 | 0.00 | python-exact (force_index) |
| prefilter_exact | uncorrelated | c_candidate_expansion | 0.050 | 0.050 | 10 | - | 1.000 | 9352.35 | 0.11 | 0.00 | python-exact (force_index) |
| prefilter_exact | uncorrelated | c_candidate_expansion | 0.100 | 0.100 | 10 | - | 1.000 | 5389.99 | 0.19 | 0.00 | python-exact (force_index) |
| prefilter_exact | uncorrelated | d_correlation | 0.100 | 0.100 | 10 | - | 1.000 | 5446.87 | 0.19 | 0.00 | python-exact (force_index) |

## Candidate-expansion recovery (scenario C, index path forced)

Lowest search value reaching recall >= 0.94; when none does, the
best cell is the max-recall operating point. A recovery cell that ran an exact path
(a Sort node) or mixed plans is marked; `plan` belongs to the best cell.

| target | fixture | sel | recovery search value | best recall @ search | plan |
|---|---|---:|---:|---:|---|
| pgvector_example | correlated | 0.010 | not reached | 0.100 @ 160 | Limit > Index Scan |
| pgvector_example | correlated | 0.050 | not reached | 0.200 @ 160 | Limit > Index Scan |
| pgvector_example | correlated | 0.100 | not reached | 0.350 @ 160 | Limit > Index Scan |
| prefilter_exact | correlated | 0.010 | no knob | - | python-exact |
| prefilter_exact | correlated | 0.050 | no knob | - | python-exact |
| prefilter_exact | correlated | 0.100 | no knob | - | python-exact |
| pgvector_example | uncorrelated | 0.010 | not reached | 0.190 @ 160 | Limit > Index Scan |
| pgvector_example | uncorrelated | 0.050 | not reached | 0.750 @ 160 | Limit > Index Scan |
| pgvector_example | uncorrelated | 0.100 | 160 | 1.000 @ 160 | Limit > Index Scan |
| prefilter_exact | uncorrelated | 0.010 | no knob | - | python-exact |
| prefilter_exact | uncorrelated | 0.050 | no knob | - | python-exact |
| prefilter_exact | uncorrelated | 0.100 | no knob | - | python-exact |

## Reproduce

```bash
python run_bench.py --config bench_config.pgvector-example.toml --output sample_artifacts/results_pgvector_smoke.json
python report.py sample_artifacts/results_pgvector_smoke.json
```
