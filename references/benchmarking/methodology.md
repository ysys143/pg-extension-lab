# Benchmark methodology — fixtures, ground truth, trust labeling

Hard-won discipline from benchmarking a filtered-HNSW index against pgvector-native and
Qdrant at 100K / 1M / 10M. The headline lesson: **the deterministic recall comparison is
the durable result; absolute latency/throughput on a shared host are not.** Build the
benchmark so the trustworthy part survives even when the host is noisy.

> For comparing an *accelerated* path against a baseline (GPU vs CPU, crossover, cost-per-query,
> batch-vs-latency, honest accelerator reporting), see **`crossover-and-cost.md`**.

## Contents

- [1. Fixture design — adversarial, not friendly](#1-fixture-design--adversarial-not-friendly)
- [2. Exact ground truth](#2-exact-ground-truth)
- [3. Operating point — matched recall, NOT matched ef](#3-operating-point--matched-recall-not-matched-ef)
- [4. Metrics and trust labeling (incl. the min_ms anti-pattern)](#4-metrics-and-trust-labeling)
- [5. Competitor fairness](#5-competitor-fairness)
- [6. Throughput — transport-bound; read shape, not ceiling](#6-throughput--transport-bound-read-shape-not-ceiling)
- [7. Caveats template](#7-caveats-template-paste-into-every-report)
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
  must be auditable — a reader has to see that "sel 1%" really passes ~1%.
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

## 4. Metrics and TRUST LABELING

Label every number by how much the host can be trusted to have produced it.

| Metric | Trust | Why |
|---|---|---|
| **recall@k** | **SOLID** | deterministic, host-independent. The headline. |
| relative / qualitative ordering | **SOLID** | all engines under the *same* noise, so ordering is real |
| absolute latency (ms) | **INDICATIVE** | shared-host jitter inflates median/p95 2–7× |
| throughput (QPS) | **INDICATIVE** | concurrency noise + client transport ceiling |
| index size | **SOLID** | deterministic |
| build time | approx | partly contended on a shared host |

State this table at the top of the report. The verdict must rest on the SOLID rows.

### Latency: report `min | median`, both INDICATIVE; never headline `min`

`min_ms` is **not** a legitimate comparison basis:

- It is an **extreme order statistic** — monotonically decreasing in sample count, i.e.
  "the luckiest sample," and it trends *below* the true uncontended latency as samples grow.
- It **understates**: a measured cell showed `min` 9.4 ms while the quiet-host truth for the
  same cell was ~21.5 ms — a noisier host produced a *lower* min, proving min tracks the
  best sample, not the real warm latency.
- It **hides intrinsic engine tails** (optimizer/segment variance, buffer/MVCC) that are
  part of real performance, not noise.
- Picking the metric that most flatters noisy data is **motivated reasoning**. Name it.

So: show `min | median` both labeled INDICATIVE, read only the *shape*, and for a
trustworthy absolute run a **quiet host** (co-tenant paused), warm up, and use **median**
as primary (p95 for tail, min only as a labeled floor). On a quiet host min ≈ median, which
is the tell that the host is clean.

---

## 5. Competitor fairness

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

## 6. Throughput — transport-bound; read shape, not ceiling

- Use **multiprocessing** clients (no Python GIL cap).
- **Isolate** each engine: the orchestrator drops the other engines' indexes so each is
  measured alone on the shared cores.
- A concurrency sweep `{1,4,8,16,32}`, each cell a fixed steady-state window (e.g. 6 s),
  QPS = completed / wall time.
- **Beware the client ceiling.** An HTTP/JSON client (httpx) whose QPS *plateaus by
  concurrency 8* is client/transport-bound, not server-bound — gRPC would raise it. So a
  result like "custom AM > Qdrant QPS" in such a rig is a *rig artifact*, not an engine
  verdict. Quote the **shape** (rises then plateaus) and the in-substrate comparison
  (vs pgvector), not the cross-substrate absolute ceiling. Single-query latency on a quiet
  host is the fairer head-to-head.

---

## 7. Caveats template (paste into every report)

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
