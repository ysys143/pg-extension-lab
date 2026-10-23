# Benchmark methodology — generic principles

Principles for benchmarking any extension path: an index access method, a planner hook, a SQL
function backed by a service, an outbox worker, an accelerated path. Each principle is stated
without assuming a particular metric. The worked cases show what a principle becomes in practice.

| Worked case | Where | Adversarial axis | Oracle | Quality metric |
|---|---|---|---|---|
| Filtered ANN index | [`filtered-ann-case.md`](filtered-ann-case.md), harness `assets/benchmark-filtered-ann/` | selectivity × filter/geometry correlation | exact top-k over passing rows | recall@k |
| Accelerator vs CPU | [`crossover-and-cost.md`](crossover-and-cost.md), harness `assets/benchmark-accelerator/` | N (fixed overhead vs better scaling) | independent exact ground truth | recall@k, crossover N |

> Generalize from the principles, not from a case's axes or numbers. Selectivity is a
> first-class axis *for filtered ANN*; an outbox worker's might be burst size and crash timing.

## Contents

- [1. Adversarial fixture — the input that breaks the fast path](#1-adversarial-fixture--the-input-that-breaks-the-fast-path)
- [2. Exact oracle](#2-exact-oracle)
- [3. Operating point — matched quality, NOT matched knobs](#3-operating-point--matched-quality-not-matched-knobs)
- [4. Parameter space — bounded exploration, not Cartesian explosion](#4-parameter-space--bounded-exploration-not-cartesian-explosion)
- [5. Metrics and trust labeling (incl. the min_ms anti-pattern)](#5-metrics-and-trust-labeling)
- [6. Fairness — equalized conditions, not identical knobs](#6-fairness--equalized-conditions-not-identical-knobs)
- [7. Timing windows and throughput](#7-timing-windows-and-throughput)
- [8. Caveats template](#8-caveats-template-paste-into-every-report)
- [Harness shape](#harness-shape)

---

## 1. Adversarial fixture — the input that breaks the fast path

A benchmark is only as honest as its hardest case.

- **Name the input under which the fast path should fail** and test it first. A friendly
  fixture hides the failure that matters. Declare it as `[methodology] adversarial_axis`;
  `check_methodology.py` warns when it is missing.
- **Record the realized condition next to the configured one.** If the config says "1%
  selectivity", "N = 1M", or "burst of 10k", the artifact must show what the fixture actually
  produced. A configured condition the fixture does not realize is a silent bug: every
  number downstream describes a different experiment.
- **Hold queries out of the loaded data** unless the scenario is about self-lookup. A query
  copied from the data finds itself first.
- **Real data before confident claims.** Synthetic fixtures are for speed; production claims
  need real distributions at multiple scales.
- **Identical data across compared systems.** Any data difference invalidates the comparison.

Filtered ANN: correlated filter buckets with measured pass rates (case §1).

---

## 2. Exact oracle

Score quality against a deterministic reference computed independently of the system under
test. Without it you measure agreement between two systems, not correctness.

- Compute it once per (query, condition), outside the timed window, and reuse it for every
  knob value.
- Prefer two independent oracle implementations that agree (ground-truth independence; see
  `crossover-and-cost.md`).

Filtered ANN: brute-force top-k over only the passing rows (case §2).

---

## 3. Operating point — matched quality, NOT matched knobs

Systems have different knobs; comparing at a shared knob value is meaningless.

- Sweep each system's own knob.
- For each system × condition, pick the **matched-quality cell**: the cheapest setting that
  reaches a predeclared quality threshold. If none reaches it, report the best cell and say so.
- Compare frontiers, not single points.

An exact path has maximum quality by construction. Note it: it is the slow-but-correct
baseline, not a tuning win.

Filtered ANN: lowest `ef` reaching recall ≥ 0.94 (case §3). The harness's scenario C records it
per selectivity with the index path forced, so an exact-scan plan cannot pose as the operating
point.

---

## 4. Parameter space — bounded exploration, not Cartesian explosion

Fair comparison is not "run every combination." That explodes and usually hides the conclusion.
Use staged exploration:

1. **Declare axes and fixed controls.** Separate dataset axes, query axes, planner knobs,
   physical knobs, hardware/runtime knobs, and reporting thresholds.
2. **Freeze fairness controls.** Same data, same query set, same quality threshold, same
   PostgreSQL version, same hardware window, same warmup, same result schema.
3. **One-axis scouts.** Sweep each uncertain knob against a stable baseline to find active
   ranges and dead ranges. Drop dead ranges before multi-axis work.
4. **Frontier cells.** Keep cells that can change the Pareto frontier, the crossover, or the
   suitability map. Neighboring dominated cells are sampled sparsely for sanity, not exhaustively.
5. **Refine around knees.** Spend budget near quality knees, latency cliffs, memory limits, and
   planner flip points.
6. **Cap the budget before running.** A benchmark plan must name max cells, max runtime, and
   promotion gates. If the budget is exceeded, shrink the space; do not silently add cells.

Compare Pareto frontiers (quality/QPS, quality/p95, quality/pages, cost/query where relevant)
within one system at one condition. Use them to find suitability zones, not only absolute
winners. A dominated option may still be the right choice under an omitted axis such as memory
budget, write rate, cold-start behavior, operator complexity, or hardware availability. Do not
compare a single flattering point unless it is the predeclared operating point.

If one option dominates across the measured space, write the mechanism hypothesis that explains
why and name the dimension where the dominance should break. Verify that mechanism by isolating
the component if possible; otherwise confirm the code path through source, EXPLAIN, counters, or
logs. An unexplained win is a prompt to search for hidden parameters, not a reason to stop.

---

## 5. Metrics and TRUST LABELING

Label every number by how much the host can be trusted to have produced it. Label each
**metric**, not each row: one result row carries both SOLID and INDICATIVE numbers, and a
single row-level label cannot say both.

| Metric kind | Trust | Why |
|---|---|---|
| **quality against a deterministic oracle** (recall@k, exactness, delivered-once counts) | **SOLID** | deterministic, host-independent. The headline. |
| realized fixture condition (pass rate, actual N) | **SOLID** | counted, not timed |
| relative / qualitative ordering | **SOLID** | all systems under the *same* noise, so ordering is real |
| absolute latency (ms) | **INDICATIVE** | shared-host jitter inflates median/p95 2–7× |
| throughput (QPS) | **INDICATIVE** | concurrency noise + client transport ceiling |
| deterministic sizes (index, artifact) | **SOLID** | deterministic |
| build time | approx | partly contended on a shared host |

State this table at the top of the report. The verdict must rest on the SOLID rows.
`lint_report.py` rejects a report whose timing figures carry no INDICATIVE label
(`RPT-TRUST-SPLIT`).

### Latency: report `min | median`, both INDICATIVE; never headline `min`

`min_ms` is **not** a legitimate comparison basis:

- It is an **extreme order statistic** — monotonically decreasing in sample count, i.e.
  "the luckiest sample," and it trends *below* the true uncontended latency as samples grow.
- It **understates**: in the filtered-ANN campaign a measured cell showed `min` 9.4 ms while
  the quiet-host truth for the same cell was ~21.5 ms — a noisier host produced a *lower* min,
  proving min tracks the best sample, not the real warm latency.
- It **hides intrinsic engine tails** (optimizer/segment variance, buffer/MVCC) that are
  part of real performance, not noise.
- Picking the metric that most flatters noisy data is **motivated reasoning**. Name it.

So: show `min | median` both labeled INDICATIVE, read only the *shape*, and for a
trustworthy absolute run a **quiet host** (co-tenant paused), warm up, and use **median**
as primary (p95 for tail, min only as a labeled floor). On a quiet host min ≈ median, which
is the tell that the host is clean.

---

## 6. Fairness — equalized conditions, not identical knobs

- **Configure each baseline fairly, then let it fail honestly.** A crippled baseline makes
  the win meaningless; a fairly configured baseline's failure is a finding you can defend.
- **Let systems settle before measuring.** Background indexing, compaction, or optimizer
  churn after load produces garbage numbers; wait for the system's own "ready" signal.
- **Verify the codepath.** Confirm whether each system used its index, an exact scan, or a
  fallback path before interpreting quality or latency.

Filtered ANN: external-engine settling and pgvector `iterative_scan` configuration (case §6).

---

## 7. Timing windows and throughput

- **Time only the system under test.** Oracle computation, quality scoring, and diagnostics
  (EXPLAIN, counters) run outside the timed window, or the reported speed includes the harness.
- **Warm each cell before timing it**, or cell order (and the previous cell's diagnostics)
  decides cache warmth and biases the frontier.
- `EXPLAIN (ANALYZE)` executes the query again. Its buffer counts describe that re-execution
  (usually warmer), not the timed call; label them that way.
- **Name what a QPS number is.** Serial single-client QPS is the inverse of latency, not
  throughput. Real throughput needs multiprocessing clients (no GIL cap), each system isolated
  on the shared cores, a concurrency sweep, and fixed steady-state windows
  (QPS = completed / wall time).
- **Beware the client ceiling.** A client whose QPS plateaus early is transport-bound; a
  cross-substrate "A beats B on QPS" from such a rig is a rig artifact. Quote the shape and the
  in-substrate comparison.

Filtered ANN: an httpx client plateau at concurrency 8 (case §7).

---

## 8. Caveats template (paste into every report)

1. **Operating point** — systems compared at matched quality, not matched knobs.
2. **Fixture difficulty** — which adversarial axis, and the realized condition next to the
   configured one.
3. **Substrate differences** — storage, transport, and process model are not equal; absolute
   latency is not apples-to-apples across substrates.
4. **Throughput is INDICATIVE** — and say how it was measured (serial or multiprocessing).
5. **Scope** — hosts, fixture families, query-set size, scales. Treat absolutes as indicative;
   the trends and trade-offs are the takeaway. p99/min are extreme order statistics — read
   median/p95 as primary.

Case-specific caveats: filtered ANN case §8; accelerator in `crossover-and-cost.md`.

---

## Harness shape

| Stage | Does | Filtered-ANN harness file |
|---|---|---|
| fixture | build data and held-out queries; record realized conditions | `fixtures/synthetic.py` |
| oracle | exact reference, once per condition | `targets/prefilter_exact.py`, `scenarios/common.py::exact_ids` |
| measure | time target calls only; score and diagnose after the window | `scenarios/common.py::run_selectivity_case` |
| report | tables from the artifact, trust per metric, reproduce command at the bottom | `report.py` |
| frontier | Pareto within one (target, condition) group | `pareto.py` |
| gates | methodology before the run, report honesty before review | `assets/validation/` |

Commit the result artifacts and the `REPORT_*.md`; put exact reproduce commands at the bottom of
every report. Fix all seeds.
