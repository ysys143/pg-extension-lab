# Filtered ANN benchmark report

- run_id: `20261023-164427`
- profile: filtered-ann
- command: `python run_bench.py --config bench_config.pgvector-example.toml --output sample_artifacts/results_pgvector_smoke.json`
- pgvector_example: extension_version 0.8.7, postgres_version 17.11 (Debian 17.11-1.pgdg12+2)
- scale: 1000 rows, 16 dims, 10 queries per condition, fixtures correlated, uncorrelated. At this size the report shows where recall fails and recovers, not performance or latency distributions at scale.
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
| pgvector_example | correlated | a_selectivity_sweep | 0.010 | 0.010 | 10 | 20 | 1.000 | 2314.95 | 0.51 | 14.00 | Limit > Sort > Seq Scan (planner) |
| pgvector_example | correlated | a_selectivity_sweep | 0.010 | 0.010 | 10 | 40 | 1.000 | 1740.08 | 0.61 | 14.00 | Limit > Sort > Seq Scan (planner) |
| pgvector_example | correlated | a_selectivity_sweep | 0.010 | 0.010 | 10 | 80 | 1.000 | 2038.10 | 0.56 | 14.00 | Limit > Sort > Seq Scan (planner) |
| pgvector_example | correlated | a_selectivity_sweep | 0.010 | 0.010 | 10 | 160 | 1.000 | 2136.31 | 0.62 | 14.00 | Limit > Sort > Seq Scan (planner) |
| pgvector_example | correlated | a_selectivity_sweep | 0.050 | 0.050 | 10 | 20 | 1.000 | 2013.96 | 0.67 | 14.00 | Limit > Sort > Seq Scan (planner) |
| pgvector_example | correlated | a_selectivity_sweep | 0.050 | 0.050 | 10 | 40 | 1.000 | 1618.47 | 0.86 | 14.00 | Limit > Sort > Seq Scan (planner) |
| pgvector_example | correlated | a_selectivity_sweep | 0.050 | 0.050 | 10 | 80 | 1.000 | 2258.40 | 0.47 | 14.00 | Limit > Sort > Seq Scan (planner) |
| pgvector_example | correlated | a_selectivity_sweep | 0.050 | 0.050 | 10 | 160 | 1.000 | 2304.86 | 0.56 | 14.00 | Limit > Sort > Seq Scan (planner) |
| pgvector_example | correlated | a_selectivity_sweep | 0.100 | 0.100 | 10 | 20 | 1.000 | 1800.23 | 0.71 | 14.00 | Limit > Sort > Seq Scan (planner) |
| pgvector_example | correlated | a_selectivity_sweep | 0.100 | 0.100 | 10 | 40 | 1.000 | 2115.00 | 0.56 | 14.00 | Limit > Sort > Seq Scan (planner) |
| pgvector_example | correlated | a_selectivity_sweep | 0.100 | 0.100 | 10 | 80 | 1.000 | 2312.61 | 0.50 | 14.00 | Limit > Sort > Seq Scan (planner) |
| pgvector_example | correlated | a_selectivity_sweep | 0.100 | 0.100 | 10 | 160 | 1.000 | 1953.60 | 0.63 | 14.00 | Limit > Sort > Seq Scan (planner) |
| pgvector_example | correlated | b_postfilter_recall | 0.010 | 0.010 | 10 | 20 | 0.020 | 1923.69 | 0.72 | 207.00 | Limit > Index Scan (force_index) |
| pgvector_example | correlated | b_postfilter_recall | 0.010 | 0.010 | 10 | 40 | 0.060 | 1753.94 | 0.82 | 266.70 | Limit > Index Scan (force_index) |
| pgvector_example | correlated | b_postfilter_recall | 0.010 | 0.010 | 10 | 80 | 0.080 | 1443.96 | 0.93 | 376.30 | Limit > Index Scan (force_index) |
| pgvector_example | correlated | b_postfilter_recall | 0.010 | 0.010 | 10 | 160 | 0.110 | 1339.34 | 0.79 | 588.30 | Limit > Index Scan (force_index) |
| pgvector_example | correlated | c_candidate_expansion | 0.010 | 0.010 | 10 | 20 | 0.020 | 1583.30 | 0.73 | 207.00 | Limit > Index Scan (force_index) |
| pgvector_example | correlated | c_candidate_expansion | 0.010 | 0.010 | 10 | 40 | 0.060 | 2407.63 | 0.45 | 266.70 | Limit > Index Scan (force_index) |
| pgvector_example | correlated | c_candidate_expansion | 0.010 | 0.010 | 10 | 80 | 0.080 | 2108.39 | 0.52 | 376.30 | Limit > Index Scan (force_index) |
| pgvector_example | correlated | c_candidate_expansion | 0.010 | 0.010 | 10 | 160 | 0.110 | 1615.56 | 0.75 | 588.30 | Limit > Index Scan (force_index) |
| pgvector_example | correlated | c_candidate_expansion | 0.050 | 0.050 | 10 | 20 | 0.100 | 2091.36 | 0.65 | 206.50 | Limit > Index Scan (force_index) |
| pgvector_example | correlated | c_candidate_expansion | 0.050 | 0.050 | 10 | 40 | 0.100 | 945.39 | 5.26 | 264.20 | Limit > Index Scan (force_index) |
| pgvector_example | correlated | c_candidate_expansion | 0.050 | 0.050 | 10 | 80 | 0.120 | 2140.93 | 0.58 | 369.80 | Limit > Index Scan (force_index) |
| pgvector_example | correlated | c_candidate_expansion | 0.050 | 0.050 | 10 | 160 | 0.200 | 1606.60 | 0.68 | 576.80 | Limit > Index Scan (force_index) |
| pgvector_example | correlated | c_candidate_expansion | 0.100 | 0.100 | 10 | 20 | 0.190 | 1505.47 | 0.82 | 206.00 | Limit > Index Scan (force_index) |
| pgvector_example | correlated | c_candidate_expansion | 0.100 | 0.100 | 10 | 40 | 0.200 | 1787.28 | 0.72 | 261.90 | Limit > Index Scan (force_index) |
| pgvector_example | correlated | c_candidate_expansion | 0.100 | 0.100 | 10 | 80 | 0.220 | 1545.08 | 0.76 | 363.60 | Limit > Index Scan (force_index) |
| pgvector_example | correlated | c_candidate_expansion | 0.100 | 0.100 | 10 | 160 | 0.310 | 1133.12 | 1.32 | 563.50 | Limit > Index Scan (force_index) |
| pgvector_example | correlated | d_correlation | 0.100 | 0.100 | 10 | 20 | 0.000 | 1857.04 | 0.98 | 170.00 | Limit > Index Scan (force_index) |
| pgvector_example | correlated | d_correlation | 0.100 | 0.100 | 10 | 40 | 0.000 | 1934.88 | 0.77 | 236.10 | Limit > Index Scan (force_index) |
| pgvector_example | correlated | d_correlation | 0.100 | 0.100 | 10 | 80 | 0.000 | 1155.96 | 1.21 | 342.40 | Limit > Index Scan (force_index) |
| pgvector_example | correlated | d_correlation | 0.100 | 0.100 | 10 | 160 | 0.000 | 1405.97 | 0.91 | 552.00 | Limit > Index Scan (force_index) |
| prefilter_exact | correlated | a_selectivity_sweep | 0.010 | 0.010 | 10 | - | 1.000 | 8204.29 | 0.15 | 0.00 | python-exact (planner) |
| prefilter_exact | correlated | a_selectivity_sweep | 0.050 | 0.050 | 10 | - | 1.000 | 2915.95 | 0.54 | 0.00 | python-exact (planner) |
| prefilter_exact | correlated | a_selectivity_sweep | 0.100 | 0.100 | 10 | - | 1.000 | 2080.26 | 0.51 | 0.00 | python-exact (planner) |
| prefilter_exact | correlated | b_postfilter_recall | 0.010 | 0.010 | 10 | - | 1.000 | 7455.96 | 0.25 | 0.00 | python-exact (force_index) |
| prefilter_exact | correlated | c_candidate_expansion | 0.010 | 0.010 | 10 | - | 1.000 | 18373.91 | 0.06 | 0.00 | python-exact (force_index) |
| prefilter_exact | correlated | c_candidate_expansion | 0.050 | 0.050 | 10 | - | 1.000 | 8137.80 | 0.13 | 0.00 | python-exact (force_index) |
| prefilter_exact | correlated | c_candidate_expansion | 0.100 | 0.100 | 10 | - | 1.000 | 4583.13 | 0.23 | 0.00 | python-exact (force_index) |
| prefilter_exact | correlated | d_correlation | 0.100 | 0.100 | 10 | - | 1.000 | 4747.21 | 0.23 | 0.00 | python-exact (force_index) |
| pgvector_example | uncorrelated | a_selectivity_sweep | 0.010 | 0.010 | 10 | 20 | 1.000 | 1498.18 | 1.30 | 14.00 | Limit > Sort > Seq Scan (planner) |
| pgvector_example | uncorrelated | a_selectivity_sweep | 0.010 | 0.010 | 10 | 40 | 1.000 | 2122.30 | 0.59 | 14.00 | Limit > Sort > Seq Scan (planner) |
| pgvector_example | uncorrelated | a_selectivity_sweep | 0.010 | 0.010 | 10 | 80 | 1.000 | 2558.96 | 0.57 | 14.00 | Limit > Sort > Seq Scan (planner) |
| pgvector_example | uncorrelated | a_selectivity_sweep | 0.010 | 0.010 | 10 | 160 | 1.000 | 1415.14 | 1.74 | 14.00 | Limit > Sort > Seq Scan (planner) |
| pgvector_example | uncorrelated | a_selectivity_sweep | 0.050 | 0.050 | 10 | 20 | 1.000 | 1571.70 | 0.97 | 14.00 | Limit > Sort > Seq Scan (planner) |
| pgvector_example | uncorrelated | a_selectivity_sweep | 0.050 | 0.050 | 10 | 40 | 1.000 | 2500.68 | 0.49 | 14.00 | Limit > Sort > Seq Scan (planner) |
| pgvector_example | uncorrelated | a_selectivity_sweep | 0.050 | 0.050 | 10 | 80 | 1.000 | 2492.16 | 0.48 | 14.00 | Limit > Sort > Seq Scan (planner) |
| pgvector_example | uncorrelated | a_selectivity_sweep | 0.050 | 0.050 | 10 | 160 | 1.000 | 1729.63 | 0.91 | 14.00 | Limit > Sort > Seq Scan (planner) |
| pgvector_example | uncorrelated | a_selectivity_sweep | 0.100 | 0.100 | 10 | 20 | 1.000 | 1696.18 | 0.78 | 14.00 | Limit > Sort > Seq Scan (planner) |
| pgvector_example | uncorrelated | a_selectivity_sweep | 0.100 | 0.100 | 10 | 40 | 1.000 | 1842.24 | 0.83 | 14.00 | Limit > Sort > Seq Scan (planner) |
| pgvector_example | uncorrelated | a_selectivity_sweep | 0.100 | 0.100 | 10 | 80 | 1.000 | 2098.84 | 0.57 | 14.00 | Limit > Sort > Seq Scan (planner) |
| pgvector_example | uncorrelated | a_selectivity_sweep | 0.100 | 0.100 | 10 | 160 | 1.000 | 973.30 | 2.32 | 14.00 | Limit > Sort > Seq Scan (planner) |
| pgvector_example | uncorrelated | b_postfilter_recall | 0.010 | 0.010 | 10 | 20 | 0.010 | 1522.99 | 0.69 | 186.60 | Limit > Index Scan (force_index) |
| pgvector_example | uncorrelated | b_postfilter_recall | 0.010 | 0.010 | 10 | 40 | 0.010 | 1725.41 | 0.67 | 247.50 | Limit > Index Scan (force_index) |
| pgvector_example | uncorrelated | b_postfilter_recall | 0.010 | 0.010 | 10 | 80 | 0.060 | 1477.57 | 0.78 | 357.10 | Limit > Index Scan (force_index) |
| pgvector_example | uncorrelated | b_postfilter_recall | 0.010 | 0.010 | 10 | 160 | 0.110 | 1364.84 | 0.99 | 574.90 | Limit > Index Scan (force_index) |
| pgvector_example | uncorrelated | c_candidate_expansion | 0.010 | 0.010 | 10 | 20 | 0.010 | 2165.05 | 0.58 | 186.60 | Limit > Index Scan (force_index) |
| pgvector_example | uncorrelated | c_candidate_expansion | 0.010 | 0.010 | 10 | 40 | 0.010 | 2483.01 | 0.46 | 247.50 | Limit > Index Scan (force_index) |
| pgvector_example | uncorrelated | c_candidate_expansion | 0.010 | 0.010 | 10 | 80 | 0.060 | 1866.21 | 0.75 | 357.10 | Limit > Index Scan (force_index) |
| pgvector_example | uncorrelated | c_candidate_expansion | 0.010 | 0.010 | 10 | 160 | 0.110 | 1722.84 | 0.67 | 574.90 | Limit > Index Scan (force_index) |
| pgvector_example | uncorrelated | c_candidate_expansion | 0.050 | 0.050 | 10 | 20 | 0.080 | 1840.90 | 0.71 | 186.60 | Limit > Index Scan (force_index) |
| pgvector_example | uncorrelated | c_candidate_expansion | 0.050 | 0.050 | 10 | 40 | 0.140 | 1988.70 | 0.53 | 247.50 | Limit > Index Scan (force_index) |
| pgvector_example | uncorrelated | c_candidate_expansion | 0.050 | 0.050 | 10 | 80 | 0.440 | 1058.12 | 1.62 | 357.10 | Limit > Index Scan (force_index) |
| pgvector_example | uncorrelated | c_candidate_expansion | 0.050 | 0.050 | 10 | 160 | 0.770 | 1292.89 | 0.88 | 566.20 | Limit > Index Scan (force_index) |
| pgvector_example | uncorrelated | c_candidate_expansion | 0.100 | 0.100 | 10 | 20 | 0.210 | 1806.83 | 0.66 | 186.60 | Limit > Index Scan (force_index) |
| pgvector_example | uncorrelated | c_candidate_expansion | 0.100 | 0.100 | 10 | 40 | 0.370 | 1853.61 | 0.63 | 247.50 | Limit > Index Scan (force_index) |
| pgvector_example | uncorrelated | c_candidate_expansion | 0.100 | 0.100 | 10 | 80 | 0.890 | 1901.16 | 0.63 | 352.80 | Limit > Index Scan (force_index) |
| pgvector_example | uncorrelated | c_candidate_expansion | 0.100 | 0.100 | 10 | 160 | 1.000 | 1306.17 | 1.32 | 508.60 | Limit > Index Scan (force_index) |
| pgvector_example | uncorrelated | d_correlation | 0.100 | 0.100 | 10 | 20 | 0.140 | 2792.48 | 0.39 | 181.30 | Limit > Index Scan (force_index) |
| pgvector_example | uncorrelated | d_correlation | 0.100 | 0.100 | 10 | 40 | 0.390 | 2433.11 | 0.45 | 245.20 | Limit > Index Scan (force_index) |
| pgvector_example | uncorrelated | d_correlation | 0.100 | 0.100 | 10 | 80 | 0.730 | 2041.91 | 0.64 | 348.40 | Limit > Index Scan (force_index) |
| pgvector_example | uncorrelated | d_correlation | 0.100 | 0.100 | 10 | 160 | 1.000 | 960.97 | 2.44 | 512.40 | Limit > Index Scan (force_index) |
| prefilter_exact | uncorrelated | a_selectivity_sweep | 0.010 | 0.010 | 10 | - | 1.000 | 4280.75 | 0.38 | 0.00 | python-exact (planner) |
| prefilter_exact | uncorrelated | a_selectivity_sweep | 0.050 | 0.050 | 10 | - | 1.000 | 2426.84 | 0.88 | 0.00 | python-exact (planner) |
| prefilter_exact | uncorrelated | a_selectivity_sweep | 0.100 | 0.100 | 10 | - | 1.000 | 5496.27 | 0.18 | 0.00 | python-exact (planner) |
| prefilter_exact | uncorrelated | b_postfilter_recall | 0.010 | 0.010 | 10 | - | 1.000 | 20437.74 | 0.07 | 0.00 | python-exact (force_index) |
| prefilter_exact | uncorrelated | c_candidate_expansion | 0.010 | 0.010 | 10 | - | 1.000 | 21609.94 | 0.05 | 0.00 | python-exact (force_index) |
| prefilter_exact | uncorrelated | c_candidate_expansion | 0.050 | 0.050 | 10 | - | 1.000 | 8265.60 | 0.14 | 0.00 | python-exact (force_index) |
| prefilter_exact | uncorrelated | c_candidate_expansion | 0.100 | 0.100 | 10 | - | 1.000 | 4799.04 | 0.27 | 0.00 | python-exact (force_index) |
| prefilter_exact | uncorrelated | d_correlation | 0.100 | 0.100 | 10 | - | 1.000 | 4522.92 | 0.24 | 0.00 | python-exact (force_index) |

## Candidate-expansion recovery (scenario C, index path forced)

Lowest search value reaching recall >= 0.94; when none does, the
best cell is the max-recall operating point. A recovery cell that ran an exact path
(a Sort node) or mixed plans is marked; `plan` belongs to the best cell.

| target | fixture | sel | recovery search value | best recall @ search | plan |
|---|---|---:|---:|---:|---|
| pgvector_example | correlated | 0.010 | not reached | 0.110 @ 160 | Limit > Index Scan |
| pgvector_example | correlated | 0.050 | not reached | 0.200 @ 160 | Limit > Index Scan |
| pgvector_example | correlated | 0.100 | not reached | 0.310 @ 160 | Limit > Index Scan |
| prefilter_exact | correlated | 0.010 | no knob | - | python-exact |
| prefilter_exact | correlated | 0.050 | no knob | - | python-exact |
| prefilter_exact | correlated | 0.100 | no knob | - | python-exact |
| pgvector_example | uncorrelated | 0.010 | not reached | 0.110 @ 160 | Limit > Index Scan |
| pgvector_example | uncorrelated | 0.050 | not reached | 0.770 @ 160 | Limit > Index Scan |
| pgvector_example | uncorrelated | 0.100 | 160 | 1.000 @ 160 | Limit > Index Scan |
| prefilter_exact | uncorrelated | 0.010 | no knob | - | python-exact |
| prefilter_exact | uncorrelated | 0.050 | no knob | - | python-exact |
| prefilter_exact | uncorrelated | 0.100 | no knob | - | python-exact |

## Reproduce

```bash
python run_bench.py --config bench_config.pgvector-example.toml --output sample_artifacts/results_pgvector_smoke.json
python report.py sample_artifacts/results_pgvector_smoke.json
```
