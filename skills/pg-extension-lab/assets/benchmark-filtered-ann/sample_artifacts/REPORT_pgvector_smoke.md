# Filtered ANN benchmark report

- run_id: `20261023-143529`
- profile: filtered-ann
- command: `python run_bench.py --config bench_config.pgvector-example.toml --output sample_artifacts/results_pgvector_smoke.json`
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
| pgvector_example | correlated | a_selectivity_sweep | 0.010 | 0.010 | 10 | 20 | 1.000 | 978.95 | 2.26 | 42.00 | Limit > Sort > Seq Scan |
| pgvector_example | correlated | a_selectivity_sweep | 0.010 | 0.010 | 10 | 40 | 1.000 | 1569.95 | 0.75 | 42.00 | Limit > Sort > Seq Scan |
| pgvector_example | correlated | a_selectivity_sweep | 0.010 | 0.010 | 10 | 80 | 1.000 | 1384.41 | 0.91 | 42.00 | Limit > Sort > Seq Scan |
| pgvector_example | correlated | a_selectivity_sweep | 0.010 | 0.010 | 10 | 160 | 1.000 | 2293.60 | 0.53 | 42.00 | Limit > Sort > Seq Scan |
| pgvector_example | correlated | a_selectivity_sweep | 0.050 | 0.050 | 10 | 20 | 1.000 | 2178.00 | 0.59 | 42.00 | Limit > Sort > Seq Scan |
| pgvector_example | correlated | a_selectivity_sweep | 0.050 | 0.050 | 10 | 40 | 1.000 | 1954.97 | 0.80 | 42.00 | Limit > Sort > Seq Scan |
| pgvector_example | correlated | a_selectivity_sweep | 0.050 | 0.050 | 10 | 80 | 1.000 | 2090.43 | 0.58 | 42.00 | Limit > Sort > Seq Scan |
| pgvector_example | correlated | a_selectivity_sweep | 0.050 | 0.050 | 10 | 160 | 1.000 | 2232.91 | 0.70 | 42.00 | Limit > Sort > Seq Scan |
| pgvector_example | correlated | a_selectivity_sweep | 0.100 | 0.100 | 10 | 20 | 1.000 | 2300.28 | 0.50 | 42.00 | Limit > Sort > Seq Scan |
| pgvector_example | correlated | a_selectivity_sweep | 0.100 | 0.100 | 10 | 40 | 1.000 | 2089.46 | 0.68 | 42.00 | Limit > Sort > Seq Scan |
| pgvector_example | correlated | a_selectivity_sweep | 0.100 | 0.100 | 10 | 80 | 1.000 | 2084.65 | 0.57 | 42.00 | Limit > Sort > Seq Scan |
| pgvector_example | correlated | a_selectivity_sweep | 0.100 | 0.100 | 10 | 160 | 1.000 | 2183.96 | 0.49 | 42.00 | Limit > Sort > Seq Scan |
| pgvector_example | correlated | b_postfilter_recall | 0.010 | 0.010 | 10 | 20 | 1.000 | 2331.55 | 0.56 | 42.00 | Limit > Sort > Seq Scan |
| pgvector_example | correlated | b_postfilter_recall | 0.010 | 0.010 | 10 | 40 | 1.000 | 2218.18 | 0.52 | 42.00 | Limit > Sort > Seq Scan |
| pgvector_example | correlated | b_postfilter_recall | 0.010 | 0.010 | 10 | 80 | 1.000 | 1643.64 | 1.26 | 42.00 | Limit > Sort > Seq Scan |
| pgvector_example | correlated | b_postfilter_recall | 0.010 | 0.010 | 10 | 160 | 1.000 | 2484.86 | 0.43 | 42.00 | Limit > Sort > Seq Scan |
| pgvector_example | correlated | c_candidate_expansion | 0.050 | 0.050 | 10 | 20 | 1.000 | 1960.64 | 0.67 | 42.00 | Limit > Sort > Seq Scan |
| pgvector_example | correlated | c_candidate_expansion | 0.050 | 0.050 | 10 | 40 | 1.000 | 2083.39 | 0.62 | 42.00 | Limit > Sort > Seq Scan |
| pgvector_example | correlated | c_candidate_expansion | 0.050 | 0.050 | 10 | 80 | 1.000 | 2277.34 | 0.49 | 42.00 | Limit > Sort > Seq Scan |
| pgvector_example | correlated | c_candidate_expansion | 0.050 | 0.050 | 10 | 160 | 1.000 | 2387.42 | 0.48 | 42.00 | Limit > Sort > Seq Scan |
| pgvector_example | correlated | d_correlation | 0.100 | 0.100 | 10 | 20 | 0.000 | 2477.27 | 0.53 | 359.20 | Limit > Index Scan |
| pgvector_example | correlated | d_correlation | 0.100 | 0.100 | 10 | 40 | 0.000 | 2249.19 | 0.54 | 479.00 | Limit > Index Scan |
| pgvector_example | correlated | d_correlation | 0.100 | 0.100 | 10 | 80 | 0.000 | 1657.16 | 0.88 | 694.60 | Limit > Index Scan |
| pgvector_example | correlated | d_correlation | 0.100 | 0.100 | 10 | 160 | 0.000 | 1591.24 | 1.00 | 1117.20 | Limit > Index Scan |
| prefilter_exact | correlated | a_selectivity_sweep | 0.010 | 0.010 | 10 | - | 1.000 | 21488.05 | 0.05 | 0.00 | python-exact |
| prefilter_exact | correlated | a_selectivity_sweep | 0.050 | 0.050 | 10 | - | 1.000 | 8539.71 | 0.17 | 0.00 | python-exact |
| prefilter_exact | correlated | a_selectivity_sweep | 0.100 | 0.100 | 10 | - | 1.000 | 5367.33 | 0.23 | 0.00 | python-exact |
| prefilter_exact | correlated | b_postfilter_recall | 0.010 | 0.010 | 10 | - | 1.000 | 21778.62 | 0.05 | 0.00 | python-exact |
| prefilter_exact | correlated | c_candidate_expansion | 0.050 | 0.050 | 10 | - | 1.000 | 9610.00 | 0.11 | 0.00 | python-exact |
| prefilter_exact | correlated | d_correlation | 0.100 | 0.100 | 10 | - | 1.000 | 5663.45 | 0.18 | 0.00 | python-exact |
| pgvector_example | uncorrelated | a_selectivity_sweep | 0.010 | 0.010 | 10 | 20 | 1.000 | 1816.20 | 0.93 | 42.00 | Limit > Sort > Seq Scan |
| pgvector_example | uncorrelated | a_selectivity_sweep | 0.010 | 0.010 | 10 | 40 | 1.000 | 1995.29 | 0.65 | 42.00 | Limit > Sort > Seq Scan |
| pgvector_example | uncorrelated | a_selectivity_sweep | 0.010 | 0.010 | 10 | 80 | 1.000 | 1950.25 | 0.70 | 42.00 | Limit > Sort > Seq Scan |
| pgvector_example | uncorrelated | a_selectivity_sweep | 0.010 | 0.010 | 10 | 160 | 1.000 | 2043.77 | 0.90 | 42.00 | Limit > Sort > Seq Scan |
| pgvector_example | uncorrelated | a_selectivity_sweep | 0.050 | 0.050 | 10 | 20 | 1.000 | 2216.82 | 0.49 | 42.00 | Limit > Sort > Seq Scan |
| pgvector_example | uncorrelated | a_selectivity_sweep | 0.050 | 0.050 | 10 | 40 | 1.000 | 2170.71 | 0.92 | 42.00 | Limit > Sort > Seq Scan |
| pgvector_example | uncorrelated | a_selectivity_sweep | 0.050 | 0.050 | 10 | 80 | 1.000 | 1475.74 | 1.08 | 42.00 | Limit > Sort > Seq Scan |
| pgvector_example | uncorrelated | a_selectivity_sweep | 0.050 | 0.050 | 10 | 160 | 1.000 | 2426.30 | 0.47 | 42.00 | Limit > Sort > Seq Scan |
| pgvector_example | uncorrelated | a_selectivity_sweep | 0.100 | 0.100 | 10 | 20 | 1.000 | 1570.81 | 1.03 | 42.00 | Limit > Sort > Seq Scan |
| pgvector_example | uncorrelated | a_selectivity_sweep | 0.100 | 0.100 | 10 | 40 | 1.000 | 2487.28 | 0.43 | 42.00 | Limit > Sort > Seq Scan |
| pgvector_example | uncorrelated | a_selectivity_sweep | 0.100 | 0.100 | 10 | 80 | 1.000 | 2190.88 | 0.75 | 42.00 | Limit > Sort > Seq Scan |
| pgvector_example | uncorrelated | a_selectivity_sweep | 0.100 | 0.100 | 10 | 160 | 1.000 | 2074.35 | 0.63 | 42.00 | Limit > Sort > Seq Scan |
| pgvector_example | uncorrelated | b_postfilter_recall | 0.010 | 0.010 | 10 | 20 | 1.000 | 1878.83 | 0.76 | 42.00 | Limit > Sort > Seq Scan |
| pgvector_example | uncorrelated | b_postfilter_recall | 0.010 | 0.010 | 10 | 40 | 1.000 | 2108.98 | 0.52 | 42.00 | Limit > Sort > Seq Scan |
| pgvector_example | uncorrelated | b_postfilter_recall | 0.010 | 0.010 | 10 | 80 | 1.000 | 2150.15 | 0.53 | 42.00 | Limit > Sort > Seq Scan |
| pgvector_example | uncorrelated | b_postfilter_recall | 0.010 | 0.010 | 10 | 160 | 1.000 | 2264.83 | 0.46 | 42.00 | Limit > Sort > Seq Scan |
| pgvector_example | uncorrelated | c_candidate_expansion | 0.050 | 0.050 | 10 | 20 | 1.000 | 2220.39 | 0.47 | 42.00 | Limit > Sort > Seq Scan |
| pgvector_example | uncorrelated | c_candidate_expansion | 0.050 | 0.050 | 10 | 40 | 1.000 | 2268.41 | 0.46 | 42.00 | Limit > Sort > Seq Scan |
| pgvector_example | uncorrelated | c_candidate_expansion | 0.050 | 0.050 | 10 | 80 | 1.000 | 2772.07 | 0.40 | 42.00 | Limit > Sort > Seq Scan |
| pgvector_example | uncorrelated | c_candidate_expansion | 0.050 | 0.050 | 10 | 160 | 1.000 | 2294.74 | 0.46 | 42.00 | Limit > Sort > Seq Scan |
| pgvector_example | uncorrelated | d_correlation | 0.100 | 0.100 | 10 | 20 | 0.190 | 1800.30 | 0.69 | 806.20 | Limit > Index Scan |
| pgvector_example | uncorrelated | d_correlation | 0.100 | 0.100 | 10 | 40 | 0.430 | 1891.73 | 0.61 | 1180.60 | Limit > Index Scan |
| pgvector_example | uncorrelated | d_correlation | 0.100 | 0.100 | 10 | 80 | 0.770 | 1784.37 | 0.58 | 1695.00 | Limit > Index Scan |
| pgvector_example | uncorrelated | d_correlation | 0.100 | 0.100 | 10 | 160 | 0.980 | 1564.77 | 0.65 | 2235.60 | Limit > Index Scan |
| prefilter_exact | uncorrelated | a_selectivity_sweep | 0.010 | 0.010 | 10 | - | 1.000 | 8149.96 | 0.15 | 0.00 | python-exact |
| prefilter_exact | uncorrelated | a_selectivity_sweep | 0.050 | 0.050 | 10 | - | 1.000 | 3980.76 | 0.25 | 0.00 | python-exact |
| prefilter_exact | uncorrelated | a_selectivity_sweep | 0.100 | 0.100 | 10 | - | 1.000 | 1614.79 | 2.05 | 0.00 | python-exact |
| prefilter_exact | uncorrelated | b_postfilter_recall | 0.010 | 0.010 | 10 | - | 1.000 | 8104.27 | 0.21 | 0.00 | python-exact |
| prefilter_exact | uncorrelated | c_candidate_expansion | 0.050 | 0.050 | 10 | - | 1.000 | 1794.54 | 3.16 | 0.00 | python-exact |
| prefilter_exact | uncorrelated | d_correlation | 0.100 | 0.100 | 10 | - | 1.000 | 5172.64 | 0.22 | 0.00 | python-exact |

## Candidate-expansion recovery (scenario C)

Lowest search value reaching recall >= 0.94.

| target | fixture | sel | recovery search value |
|---|---|---:|---:|
| pgvector_example | correlated | 0.050 | 20 |
| prefilter_exact | correlated | 0.050 | no knob |
| pgvector_example | uncorrelated | 0.050 | 20 |
| prefilter_exact | uncorrelated | 0.050 | no knob |

## Reproduce

```bash
python run_bench.py --config bench_config.pgvector-example.toml --output sample_artifacts/results_pgvector_smoke.json
python report.py sample_artifacts/results_pgvector_smoke.json
```
