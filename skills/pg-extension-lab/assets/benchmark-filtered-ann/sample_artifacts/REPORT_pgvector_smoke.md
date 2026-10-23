# Filtered ANN benchmark report

- run_id: `20261023-145558`
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
| pgvector_example | correlated | a_selectivity_sweep | 0.010 | 0.010 | 10 | 20 | 1.000 | 2278.60 | 0.58 | 42.00 | Limit > Sort > Seq Scan (planner) |
| pgvector_example | correlated | a_selectivity_sweep | 0.010 | 0.010 | 10 | 40 | 1.000 | 1338.68 | 1.23 | 42.00 | Limit > Sort > Seq Scan (planner) |
| pgvector_example | correlated | a_selectivity_sweep | 0.010 | 0.010 | 10 | 80 | 1.000 | 538.44 | 4.59 | 42.00 | Limit > Sort > Seq Scan (planner) |
| pgvector_example | correlated | a_selectivity_sweep | 0.010 | 0.010 | 10 | 160 | 1.000 | 2138.05 | 1.01 | 42.00 | Limit > Sort > Seq Scan (planner) |
| pgvector_example | correlated | a_selectivity_sweep | 0.050 | 0.050 | 10 | 20 | 1.000 | 2011.60 | 0.80 | 42.00 | Limit > Sort > Seq Scan (planner) |
| pgvector_example | correlated | a_selectivity_sweep | 0.050 | 0.050 | 10 | 40 | 1.000 | 2328.67 | 0.83 | 42.00 | Limit > Sort > Seq Scan (planner) |
| pgvector_example | correlated | a_selectivity_sweep | 0.050 | 0.050 | 10 | 80 | 1.000 | 2234.80 | 0.71 | 42.00 | Limit > Sort > Seq Scan (planner) |
| pgvector_example | correlated | a_selectivity_sweep | 0.050 | 0.050 | 10 | 160 | 1.000 | 2731.21 | 0.47 | 42.00 | Limit > Sort > Seq Scan (planner) |
| pgvector_example | correlated | a_selectivity_sweep | 0.100 | 0.100 | 10 | 20 | 1.000 | 2282.76 | 0.51 | 42.00 | Limit > Sort > Seq Scan (planner) |
| pgvector_example | correlated | a_selectivity_sweep | 0.100 | 0.100 | 10 | 40 | 1.000 | 1652.01 | 1.09 | 42.00 | Limit > Sort > Seq Scan (planner) |
| pgvector_example | correlated | a_selectivity_sweep | 0.100 | 0.100 | 10 | 80 | 1.000 | 1868.31 | 1.29 | 42.00 | Limit > Sort > Seq Scan (planner) |
| pgvector_example | correlated | a_selectivity_sweep | 0.100 | 0.100 | 10 | 160 | 1.000 | 2521.88 | 0.54 | 42.00 | Limit > Sort > Seq Scan (planner) |
| pgvector_example | correlated | b_postfilter_recall | 0.010 | 0.010 | 10 | 20 | 0.000 | 2793.78 | 0.42 | 373.60 | Limit > Index Scan (force_index) |
| pgvector_example | correlated | b_postfilter_recall | 0.010 | 0.010 | 10 | 40 | 0.050 | 2197.88 | 0.48 | 498.60 | Limit > Index Scan (force_index) |
| pgvector_example | correlated | b_postfilter_recall | 0.010 | 0.010 | 10 | 80 | 0.080 | 2046.94 | 0.53 | 711.20 | Limit > Index Scan (force_index) |
| pgvector_example | correlated | b_postfilter_recall | 0.010 | 0.010 | 10 | 160 | 0.100 | 1270.26 | 1.71 | 1140.20 | Limit > Index Scan (force_index) |
| pgvector_example | correlated | c_candidate_expansion | 0.010 | 0.010 | 10 | 20 | 0.000 | 2056.82 | 1.00 | 373.60 | Limit > Index Scan (force_index) |
| pgvector_example | correlated | c_candidate_expansion | 0.010 | 0.010 | 10 | 40 | 0.050 | 1999.92 | 0.64 | 498.60 | Limit > Index Scan (force_index) |
| pgvector_example | correlated | c_candidate_expansion | 0.010 | 0.010 | 10 | 80 | 0.080 | 1482.95 | 0.90 | 711.20 | Limit > Index Scan (force_index) |
| pgvector_example | correlated | c_candidate_expansion | 0.010 | 0.010 | 10 | 160 | 0.100 | 1156.52 | 1.73 | 1140.20 | Limit > Index Scan (force_index) |
| pgvector_example | correlated | c_candidate_expansion | 0.050 | 0.050 | 10 | 20 | 0.100 | 1798.22 | 0.93 | 372.00 | Limit > Index Scan (force_index) |
| pgvector_example | correlated | c_candidate_expansion | 0.050 | 0.050 | 10 | 40 | 0.110 | 1774.50 | 0.71 | 493.60 | Limit > Index Scan (force_index) |
| pgvector_example | correlated | c_candidate_expansion | 0.050 | 0.050 | 10 | 80 | 0.130 | 1641.25 | 0.82 | 698.60 | Limit > Index Scan (force_index) |
| pgvector_example | correlated | c_candidate_expansion | 0.050 | 0.050 | 10 | 160 | 0.200 | 1260.23 | 1.00 | 1117.20 | Limit > Index Scan (force_index) |
| pgvector_example | correlated | c_candidate_expansion | 0.100 | 0.100 | 10 | 20 | 0.160 | 2265.28 | 0.54 | 371.60 | Limit > Index Scan (force_index) |
| pgvector_example | correlated | c_candidate_expansion | 0.100 | 0.100 | 10 | 40 | 0.200 | 2349.51 | 0.49 | 490.60 | Limit > Index Scan (force_index) |
| pgvector_example | correlated | c_candidate_expansion | 0.100 | 0.100 | 10 | 80 | 0.220 | 1983.21 | 0.64 | 687.80 | Limit > Index Scan (force_index) |
| pgvector_example | correlated | c_candidate_expansion | 0.100 | 0.100 | 10 | 160 | 0.350 | 1516.31 | 0.93 | 1091.40 | Limit > Index Scan (force_index) |
| pgvector_example | correlated | d_correlation | 0.100 | 0.100 | 10 | 20 | 0.000 | 2729.13 | 0.40 | 360.00 | Limit > Index Scan (force_index) |
| pgvector_example | correlated | d_correlation | 0.100 | 0.100 | 10 | 40 | 0.000 | 1680.26 | 1.81 | 483.40 | Limit > Index Scan (force_index) |
| pgvector_example | correlated | d_correlation | 0.100 | 0.100 | 10 | 80 | 0.000 | 2131.40 | 0.59 | 699.00 | Limit > Index Scan (force_index) |
| pgvector_example | correlated | d_correlation | 0.100 | 0.100 | 10 | 160 | 0.000 | 1518.35 | 0.83 | 1121.60 | Limit > Index Scan (force_index) |
| prefilter_exact | correlated | a_selectivity_sweep | 0.010 | 0.010 | 10 | - | 1.000 | 7449.02 | 0.26 | 0.00 | python-exact (planner) |
| prefilter_exact | correlated | a_selectivity_sweep | 0.050 | 0.050 | 10 | - | 1.000 | 2824.39 | 0.46 | 0.00 | python-exact (planner) |
| prefilter_exact | correlated | a_selectivity_sweep | 0.100 | 0.100 | 10 | - | 1.000 | 1865.90 | 0.69 | 0.00 | python-exact (planner) |
| prefilter_exact | correlated | b_postfilter_recall | 0.010 | 0.010 | 10 | - | 1.000 | 8482.06 | 0.13 | 0.00 | python-exact (force_index) |
| prefilter_exact | correlated | c_candidate_expansion | 0.010 | 0.010 | 10 | - | 1.000 | 20838.76 | 0.05 | 0.00 | python-exact (force_index) |
| prefilter_exact | correlated | c_candidate_expansion | 0.050 | 0.050 | 10 | - | 1.000 | 9628.11 | 0.11 | 0.00 | python-exact (force_index) |
| prefilter_exact | correlated | c_candidate_expansion | 0.100 | 0.100 | 10 | - | 1.000 | 5573.75 | 0.19 | 0.00 | python-exact (force_index) |
| prefilter_exact | correlated | d_correlation | 0.100 | 0.100 | 10 | - | 1.000 | 5739.15 | 0.18 | 0.00 | python-exact (force_index) |
| pgvector_example | uncorrelated | a_selectivity_sweep | 0.010 | 0.010 | 10 | 20 | 1.000 | 2552.11 | 0.41 | 42.00 | Limit > Sort > Seq Scan (planner) |
| pgvector_example | uncorrelated | a_selectivity_sweep | 0.010 | 0.010 | 10 | 40 | 1.000 | 1860.57 | 1.34 | 42.00 | Limit > Sort > Seq Scan (planner) |
| pgvector_example | uncorrelated | a_selectivity_sweep | 0.010 | 0.010 | 10 | 80 | 1.000 | 2448.83 | 0.49 | 42.00 | Limit > Sort > Seq Scan (planner) |
| pgvector_example | uncorrelated | a_selectivity_sweep | 0.010 | 0.010 | 10 | 160 | 1.000 | 2638.93 | 0.42 | 42.00 | Limit > Sort > Seq Scan (planner) |
| pgvector_example | uncorrelated | a_selectivity_sweep | 0.050 | 0.050 | 10 | 20 | 1.000 | 2585.37 | 0.44 | 42.00 | Limit > Sort > Seq Scan (planner) |
| pgvector_example | uncorrelated | a_selectivity_sweep | 0.050 | 0.050 | 10 | 40 | 1.000 | 2309.20 | 0.55 | 42.00 | Limit > Sort > Seq Scan (planner) |
| pgvector_example | uncorrelated | a_selectivity_sweep | 0.050 | 0.050 | 10 | 80 | 1.000 | 2488.88 | 0.42 | 42.00 | Limit > Sort > Seq Scan (planner) |
| pgvector_example | uncorrelated | a_selectivity_sweep | 0.050 | 0.050 | 10 | 160 | 1.000 | 1390.76 | 1.15 | 42.00 | Limit > Sort > Seq Scan (planner) |
| pgvector_example | uncorrelated | a_selectivity_sweep | 0.100 | 0.100 | 10 | 20 | 1.000 | 2378.92 | 0.52 | 42.00 | Limit > Sort > Seq Scan (planner) |
| pgvector_example | uncorrelated | a_selectivity_sweep | 0.100 | 0.100 | 10 | 40 | 1.000 | 2117.77 | 0.67 | 42.00 | Limit > Sort > Seq Scan (planner) |
| pgvector_example | uncorrelated | a_selectivity_sweep | 0.100 | 0.100 | 10 | 80 | 1.000 | 2159.38 | 0.57 | 42.00 | Limit > Sort > Seq Scan (planner) |
| pgvector_example | uncorrelated | a_selectivity_sweep | 0.100 | 0.100 | 10 | 160 | 1.000 | 2303.53 | 0.50 | 42.00 | Limit > Sort > Seq Scan (planner) |
| pgvector_example | uncorrelated | b_postfilter_recall | 0.010 | 0.010 | 10 | 20 | 0.020 | 1906.71 | 0.59 | 802.80 | Limit > Index Scan (force_index) |
| pgvector_example | uncorrelated | b_postfilter_recall | 0.010 | 0.010 | 10 | 40 | 0.030 | 2116.36 | 0.59 | 1200.60 | Limit > Index Scan (force_index) |
| pgvector_example | uncorrelated | b_postfilter_recall | 0.010 | 0.010 | 10 | 80 | 0.080 | 1814.50 | 0.67 | 1708.40 | Limit > Index Scan (force_index) |
| pgvector_example | uncorrelated | b_postfilter_recall | 0.010 | 0.010 | 10 | 160 | 0.190 | 435.67 | 6.33 | 2361.60 | Limit > Index Scan (force_index) |
| pgvector_example | uncorrelated | c_candidate_expansion | 0.010 | 0.010 | 10 | 20 | 0.020 | 181.16 | 15.77 | 802.80 | Limit > Index Scan (force_index) |
| pgvector_example | uncorrelated | c_candidate_expansion | 0.010 | 0.010 | 10 | 40 | 0.030 | 2072.95 | 0.62 | 1200.60 | Limit > Index Scan (force_index) |
| pgvector_example | uncorrelated | c_candidate_expansion | 0.010 | 0.010 | 10 | 80 | 0.080 | 1681.91 | 0.75 | 1708.40 | Limit > Index Scan (force_index) |
| pgvector_example | uncorrelated | c_candidate_expansion | 0.010 | 0.010 | 10 | 160 | 0.190 | 1538.76 | 0.81 | 2361.60 | Limit > Index Scan (force_index) |
| pgvector_example | uncorrelated | c_candidate_expansion | 0.050 | 0.050 | 10 | 20 | 0.060 | 2077.08 | 0.68 | 802.80 | Limit > Index Scan (force_index) |
| pgvector_example | uncorrelated | c_candidate_expansion | 0.050 | 0.050 | 10 | 40 | 0.110 | 1921.74 | 0.69 | 1200.60 | Limit > Index Scan (force_index) |
| pgvector_example | uncorrelated | c_candidate_expansion | 0.050 | 0.050 | 10 | 80 | 0.320 | 1470.97 | 1.00 | 1708.40 | Limit > Index Scan (force_index) |
| pgvector_example | uncorrelated | c_candidate_expansion | 0.050 | 0.050 | 10 | 160 | 0.750 | 1443.24 | 0.79 | 2353.60 | Limit > Index Scan (force_index) |
| pgvector_example | uncorrelated | c_candidate_expansion | 0.100 | 0.100 | 10 | 20 | 0.170 | 2136.12 | 0.60 | 802.80 | Limit > Index Scan (force_index) |
| pgvector_example | uncorrelated | c_candidate_expansion | 0.100 | 0.100 | 10 | 40 | 0.360 | 1990.43 | 0.70 | 1200.60 | Limit > Index Scan (force_index) |
| pgvector_example | uncorrelated | c_candidate_expansion | 0.100 | 0.100 | 10 | 80 | 0.760 | 692.51 | 2.12 | 1704.40 | Limit > Index Scan (force_index) |
| pgvector_example | uncorrelated | c_candidate_expansion | 0.100 | 0.100 | 10 | 160 | 1.000 | 1594.19 | 0.67 | 2241.00 | Limit > Index Scan (force_index) |
| pgvector_example | uncorrelated | d_correlation | 0.100 | 0.100 | 10 | 20 | 0.190 | 2093.91 | 0.57 | 805.20 | Limit > Index Scan (force_index) |
| pgvector_example | uncorrelated | d_correlation | 0.100 | 0.100 | 10 | 40 | 0.430 | 182.07 | 10.61 | 1179.60 | Limit > Index Scan (force_index) |
| pgvector_example | uncorrelated | d_correlation | 0.100 | 0.100 | 10 | 80 | 0.770 | 1965.04 | 0.60 | 1698.80 | Limit > Index Scan (force_index) |
| pgvector_example | uncorrelated | d_correlation | 0.100 | 0.100 | 10 | 160 | 0.980 | 1651.25 | 0.66 | 2240.40 | Limit > Index Scan (force_index) |
| prefilter_exact | uncorrelated | a_selectivity_sweep | 0.010 | 0.010 | 10 | - | 1.000 | 8829.70 | 0.12 | 0.00 | python-exact (planner) |
| prefilter_exact | uncorrelated | a_selectivity_sweep | 0.050 | 0.050 | 10 | - | 1.000 | 3921.82 | 0.28 | 0.00 | python-exact (planner) |
| prefilter_exact | uncorrelated | a_selectivity_sweep | 0.100 | 0.100 | 10 | - | 1.000 | 5303.28 | 0.20 | 0.00 | python-exact (planner) |
| prefilter_exact | uncorrelated | b_postfilter_recall | 0.010 | 0.010 | 10 | - | 1.000 | 20648.70 | 0.07 | 0.00 | python-exact (force_index) |
| prefilter_exact | uncorrelated | c_candidate_expansion | 0.010 | 0.010 | 10 | - | 1.000 | 21794.42 | 0.05 | 0.00 | python-exact (force_index) |
| prefilter_exact | uncorrelated | c_candidate_expansion | 0.050 | 0.050 | 10 | - | 1.000 | 8788.96 | 0.16 | 0.00 | python-exact (force_index) |
| prefilter_exact | uncorrelated | c_candidate_expansion | 0.100 | 0.100 | 10 | - | 1.000 | 5265.12 | 0.22 | 0.00 | python-exact (force_index) |
| prefilter_exact | uncorrelated | d_correlation | 0.100 | 0.100 | 10 | - | 1.000 | 5400.05 | 0.19 | 0.00 | python-exact (force_index) |

## Candidate-expansion recovery (scenario C, index path forced)

Lowest search value reaching recall >= 0.94; when none does, the
best cell is the max-recall operating point. `plan` belongs to the best cell.

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
