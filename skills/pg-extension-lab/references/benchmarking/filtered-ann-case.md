# Worked case — filtered ANN index benchmark

This is a **worked case** of the generic principles in [`methodology.md`](methodology.md), not
the template every benchmark must copy. It shows what those principles become for one kind of
extension path: an approximate vector index queried with a filter. Here the adversarial axis is
selectivity × filter/geometry correlation, the oracle is exact top-k over the passing rows, and
the operating point is matched recall at the lowest `ef`. Another extension path has its own
axis and oracle. Generalize from the parent principles, not from the numbers here.

Hard-won discipline from benchmarking a filtered index against both in-PostgreSQL and
external-engine baselines at 100K / 1M / 10M. The headline lesson: **the deterministic recall
comparison is the durable result; absolute latency/throughput on a shared host are not.** Build
the benchmark so the trustworthy part survives even when the host is noisy.

Section numbers match the principles in `methodology.md`; §4 and §5 have no case-specific
content beyond what is stated there.

## Scenarios and the copy-ready harness

[`../../assets/benchmark-filtered-ann/`](../../assets/benchmark-filtered-ann/) implements the
case. Its config declares `[methodology] profile = "filtered-ann"`, which turns on this case's
gate rules (`CFG-SELECTIVITY`, `CFG-ADVERSARIAL`, `RPT-PASSRATE`, `RPT-RECALL`).

| Scenario | Harness file | Measures |
|---|---|---|
| A — selectivity sweep | `scenarios/a_selectivity_sweep.py` | every selectivity × knob, on correlated and uncorrelated fixtures, planner free to choose |
| B — post-filter recall failure | `scenarios/b_postfilter_recall.py` | recall against exact filtered ground truth at the lowest selectivity, index path forced |
| C — candidate-expansion recovery | `scenarios/c_candidate_expansion.py` | per selectivity, index path forced: progressive recall recovery as candidate expansion grows; the lowest knob reaching the recall threshold, or the best cell when none does (§3) |
| D — correlation stress | `scenarios/d_correlation.py` | queries whose neighborhood fails the filter, index path forced; the uncorrelated fixture is the control |

The harness's pgvector sample (`sample_artifacts/REPORT_pgvector_smoke.md`, pgvector 0.8.7)
reproduces the case in miniature. It is smoke scale (1,000 rows, 16 dims, 10 queries per
condition): read it as a reproduction of failure and recovery under synthetic conditions, not as
evidence about performance at scale. The two fixtures share vectors and queries and differ only
in bucket assignment, so their gap is the correlation effect.

- A: left to itself, the planner chose `Seq Scan > Sort` at that size, so A's 1.0 is the exact
  path.
- B–D: with the HNSW index forced, B's 1% post-filter recall stays at or below 0.11 on both
  fixtures. At this size 1% is exactly k = 10 rows, so recall is capped near ef/1,000 whatever the
  geometry; the 1% cell does not separate selectivity from correlation.
- C separates the fixtures: the correlated one never reaches the 0.94 recall threshold (best 0.31
  at `ef` 160 for 10%), while the uncorrelated one crosses it at 10% with recall 1.000.
- D's correlated far queries get recall 0.0 at every `ef` from 20 to 160, while the
  uncorrelated control on the same queries climbs from 0.14 to 1.0.

The report's `plan` column is what tells the exact path from the index path. The adapter turns
off psycopg's auto-prepare: a cached generic plan ignored `enable_seqscan` and ran an exact
plan under an EXPLAIN that said `Index Scan`.

## Contents

- [1. Fixture design — adversarial, not friendly](#1-fixture-design--adversarial-not-friendly)
- [2. Exact ground truth](#2-exact-ground-truth)
- [3. Operating point — matched recall, NOT matched ef](#3-operating-point--matched-recall-not-matched-ef)
- [6. Competitor fairness](#6-competitor-fairness)
- [7. Throughput — transport-bound; read shape, not ceiling](#7-throughput--transport-bound-read-shape-not-ceiling)
- [8. Caveats template](#8-caveats-template-paste-into-every-report)
- [Harness shape](#harness-shape-reference)

---

## 1. Fixture design — adversarial, not friendly

A benchmark is only as honest as its hardest case.

- **Correlated filter.** Derive the filter key from the data's own geometry, so the passing
  set is a *spatial cluster off the query→nearest path*. Concretely: `bucket = argmax block
  of the embedding`, filter `bucket < sel`. This is the worst case for filtered HNSW —
  greedy descent toward the query meets mostly *failing* rows, and the true top-k passing
  rows sit at a large distance-rank. A **random** filter is easy and hides the failure that
  matters. Always test the correlated case; report the random case separately if at all.
- **Record measured pass rates.** e.g. `<1%`=0.97%, `<5%`=4.83%, `<10%`=9.66%. The fixture
  must be auditable — a reader has to see that "sel 1%" really passes ~1%. The harness filters
  with `bucket < round(sel * 100)` over stratified buckets, so its smoke fixture passes exactly
  the configured share and writes `pass_rate` on every result row.
- **Real embeddings.** Use a real corpus (e.g. Cohere wikipedia 1024-dim, unit-norm,
  cosine) at multiple N, with a fixed held-out query set. Synthetic gaussians understate the
  clustering that makes filtered ANN hard.
- **Byte-identical data across engines.** pgvector and the custom AM share the *same* table;
  the external engine holds the same vectors with a deterministic id mapping (`point id =
  i+1`). Any data difference invalidates the comparison.

---

## 2. Exact ground truth

Per (query, selectivity): brute-force top-k by the real metric (cosine) over **only the
passing rows**, in numpy. This is the denominator for recall@k. Without exact truth you are
measuring agreement between two approximate engines, which is not recall.

---

## 3. Operating point — matched recall, NOT matched ef

Engines have different knobs; comparing at a shared `ef` is meaningless. Instead:

- Sweep each engine's own knob (ef_search, ef, scan budget).
- For each engine × selectivity, pick the **matched-recall cell**: the *lowest* ef that
  reaches recall ≥ threshold (0.94). If none reaches it, report the max-recall cell and say
  so.
- Each engine traces its own recall-vs-knob frontier; you compare frontiers. This is the
  apples-to-apples view.

An exact path (e.g. pgvector prefilter = bitmap + exact Sort) has recall = 1.0 by
construction — note it; it is the slow-but-correct baseline, not a tuning win.

---

## 6. Competitor fairness

- **Let external engines settle.** After load, a forced-HNSW optimizer churns (saw 114%
  CPU); the first run gave garbage (p95 1100 ms / 12 QPS). Wait for status `green` +
  `indexed_vectors_count == N` + CPU idle before measuring. **Do not** raise
  `indexing_threshold` to silence it — that de-indexes segments back to exact search and
  silently changes what you are measuring.
- **Configure the baseline fairly, then let it fail honestly.** pgvector `iterative_scan`
  needs `strict_order` + a raised `max_scan_tuples` to have any chance; with the defaults it
  collapses further (a rigged cripple). Give it the fair config — then its
  correlated-filter failure (recall capped ~0.2–0.5 at any ef) is a *real* finding you can
  stand behind.

---

## 7. Throughput — transport-bound; read shape, not ceiling

- Use **multiprocessing** clients (no Python GIL cap).
- **Isolate** each engine: the orchestrator drops the other engines' indexes so each is
  measured alone on the shared cores.
- A concurrency sweep `{1,4,8,16,32}`, each cell a fixed steady-state window (e.g. 6 s),
  QPS = completed / wall time.
- **Beware the client ceiling.** An HTTP/JSON client (httpx) whose QPS *plateaus by
  concurrency 8* is client/transport-bound, not server-bound — gRPC would raise it. So a
  result like "custom AM > external engine QPS" in such a rig is a *rig artifact*, not an engine
  verdict. Quote the **shape** (rises then plateaus) and the in-substrate comparison
  (vs pgvector), not the cross-substrate absolute ceiling. Single-query latency on a quiet
  host is the fairer head-to-head.
- The copy-ready harness does not implement this rig: its `qps` is single-client serial over
  target calls only. Add multiprocessing clients before making a throughput claim.

---

## 8. Caveats template (paste into every report)

1. **Matched recall, not matched ef** — engines compared at lowest ef reaching ≥ threshold.
2. **The fixture is deliberately hard** (correlated filter) — a random filter narrows gaps.
3. **Storage/transport are not equal** — in-PostgreSQL (MVCC, shared buffers, libpq, TOAST)
   vs a purpose-built in-memory engine over HTTP/JSON. Absolute latency is not
   apples-to-apples.
4. **Throughput is INDICATIVE and transport-bound** — client and server share cores; HTTP
   client plateaus early.
5. **Build does not scale past ~N cores** (measured idle %); build time is a floor for the
   index class.
6. **Scope** — one host, one fixture family, a small query set, one dim. Treat absolutes as
   indicative; the **scaling trend and the recall/latency trade-offs** are the takeaway.
   p99/min are extreme order statistics — read median/p95 as primary.

---

## Harness shape (reference)

The reference campaign's scripts (not shipped; the copy-ready harness maps each stage to a file
in `assets/benchmark-filtered-ann/` — see the harness shape table in `methodology.md`):

| Stage | File (example) | Does |
|---|---|---|
| fixture | `cohere_prep.py` | build correlated buckets, held-out queries |
| load + truth | `scale_load.py` | binary COPY into PG + upload to external engine + exact top-k |
| measure | `scalebench.py` / `bench3way_*.py` | recall sweep + latency dist + multiprocessing QPS |
| per-scale driver | `run_scale.sh` | build index, run measure, dump JSON |
| report | `scale_report.py` / `bench3way_report.py` | extract tables from result JSON |
| frontier | `pareto.py` | recall-QPS Pareto (see `../performance/resource-pareto.md`) |

Commit the result JSONs and the `REPORT_*.md`; put exact reproduce commands at the bottom of
every report. Fix all seeds.
