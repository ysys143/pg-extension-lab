# Benchmarking an accelerated path — crossover, cost, batch, honesty

When you benchmark an "accelerated" or "alternative" path against a baseline — GPU vs CPU,
parallel vs serial, cached vs uncached, index vs seqscan, any path with **fixed overhead but
better scaling** — the honest output is a *crossover and a cost frontier*, not "X is N×
faster." This file is the companion to `methodology.md` (which covers fixtures, ground truth,
and trust labeling that still apply here).

## Contents

- [1. Crossover, not a single ratio](#1-crossover-not-a-single-ratio)
- [2. Cost-per-query and total-cost framing](#2-cost-per-query-and-total-cost-framing)
- [3. Batch vs single-query — opposite winners](#3-batch-vs-single-query--opposite-winners)
- [4. Ground-truth independence (extends methodology §2–3)](#4-ground-truth-independence)
- [5. Honest reporting of an accelerated path](#5-honest-reporting-of-an-accelerated-path)
- [6. Cost-model calibration (planner cost callback)](#6-cost-model-calibration)

---

## 1. Crossover, not a single ratio

- **Decompose latency; never report one ratio.** The headline is "where does the time go
  once the new path removes the work it was built to remove." Example: once a GPU kernel
  collapses the distance math to ~715 µs, the bottleneck *moves* to the IPC round-trip (~33%)
  and heap access — so the benchmark characterizes that *shift*, not a number.
- **Find the crossover by root-finding, because the fast path is near-flat in problem size
  and the baseline grows.** Coarse log grid (`{1K,10K,100K,1M,10M}`), compute
  `ratio = metric_new / metric_baseline` per interval, then **bisect only the interval where
  ratio crosses 1.0**. (Worked example: fast path p50 871→1228 µs across N=1K→100K while the
  baseline grows 224→8232 µs; crossover ≈ N 10K–100K.)
- **The crossover is a surface, not a point.** Secondary axes (dimension, k, concurrency,
  selectivity) move the crossover N. Measure the main axis (N) densely, then 2–3 points per
  secondary axis to learn *which direction and how far* it shifts (e.g. build advantage
  widened 9×→36× as dim went 384→1536 — higher dim favored the accelerator).
- **Report the LOSING region as plainly as the winning one.** A crossover benchmark with no
  documented loss zone is not honest. Pre-register the loss as a falsifiable hypothesis
  ("H3: a region exists where we lose") and then state it: "below ~10K the baseline wins on
  every axis — the fixed overhead isn't worth paying for a tiny workload."

## 2. Cost-per-query and total-cost framing

Latency alone hides the economics when the new path uses an expensive resource.

- **Equalize by money and energy, not by raw quantity.** Never equate one resource-GB to
  another (VRAM-GB ≠ DRAM-GB). Report `$/1M queries`, `$/sustained-QPS@p99`, `J/query`, and
  *publish the raw resource counts* so a reader can re-normalize with their own price sheet.
- **Report two baselines, because "fair" depends on the buyer's question.** (a) **same-box**:
  run the baseline on the CPU/RAM that ships with the accelerated instance ("I already own
  the box"); (b) **iso-$**: a cheaper instance at the same $/hr, which gets *more* of the
  cheap resource ("where should I spend the same dollar"). The new path winning *despite* the
  baseline getting more capacity is the real result.
- **Separate fixed cost from marginal cost; amortize one-time work over the query stream.**
  A one-time build/upload (e.g. a 4 GB index load, ~876 ms) is excluded from per-query
  accounting; per-query cost is only the marginal transfer/compute. A high fixed device $/hr
  means the accelerator only wins on `$/QPS` *above a throughput threshold* — so plot
  cost-per-query as a function of sustained QPS, never at QPS=1.

## 3. Batch vs single-query — opposite winners

- **Report both; never quote one for the other.** Per-call fixed overhead (dispatch, IPC,
  transfer) starves an accelerator at Q=1 and saturates it at Q=100. Example: a Q=100 batch
  kernel ran in ~1.27 ms — ~1.8× the Q=1 kernel for 100× the queries; on another device Q=100
  was 19× faster *per query* than Q=1.
- **Micro-batch concurrent single-query traffic into one dispatch** to convert latency-bound
  load into throughput-bound load: a short coalescing window (e.g. 100–1000 µs) gathers
  requests from many backends into one Q=N call, then splits results back.
- **Know the hardware floor and cap your claims at it.** Brute-force latency floor =
  `N×dim×bytes ÷ memory_bandwidth`; a single daemon's per-query IPC caps single-device
  throughput (~1K QPS for small/medium N here) — state it as a limitation, with sharding the
  only way past (and sharding has its own cost: +70% latency / +13% recall in one measured
  case).
- **Never pull the large intermediate across the boundary; ship only the final small
  payload.** Keep the Q×N distance matrix (400 MB at Q=100/N=1M) on-device; cross the IPC
  boundary only with Q×K results (~8 KB, ~0.4% of latency). Pulling the intermediate to the
  host made a GPU path *slower than pure CPU* (749 → 7.9 QPS) — the classic accelerator
  anti-pattern.

## 4. Ground-truth independence

(Extends `methodology.md` §2–3.)

- **Generate ground truth with an INDEPENDENT exact implementation**, to avoid circular
  validation: if the system under test is engine X, compute GT with a *different* exact
  engine (e.g. faiss-cpu/-gpu flat when the SUT is a different library). Validating an
  approximate engine against its own exact mode proves nothing.
- **GT and data generation must share one deterministic path.** A batch-size/RNG-sequence
  mismatch between the loader and the GT generator desynced the RNG and produced
  **recall = 0.0 across the board** — a silent, total-failure bug. Generate base vectors for
  GT through the *same* code path as the data load (stream from the DB via `COPY TO STDOUT`
  to avoid materializing a 72 GB fixture).
- **Iso-recall, Pareto frontier.** Sweep each engine's own recall knob to the minimum meeting
  the target; report achieved recall per row if the sweep ceiling misses; extract the
  non-dominated recall/latency frontier per engine — a single tuned point hides the trade.

## 5. Honest reporting of an accelerated path

- **Warm vs cold are separate line items.** Hold warm state constant across engines
  (accelerator daemon-resident; baseline `pg_prewarm`ed) and benchmark cold-start (e.g. VRAM
  reload at ~150 MB/s) on its own line — never mixed in.
- **Label data SOLID vs INDICATIVE by data realism.** Synthetic distributions systematically
  flatter specific algorithm families: clustered synthetic flatters IVF; uniform-random gives
  a recall=1.0 trap real high-dim embeddings never reach (distance concentration). So:
  **recall claims are forbidden on synthetic data**; anchor them to one real-embedding
  dataset. *Build-speedup* claims ARE allowed on synthetic, because they depend on N/dim/M,
  not vector content.
- **Disclose the rig's blind spots instead of papering over them** (e.g. a cloud VM exposes
  no hardware PMU → cache-miss hotspots are unmeasurable; say so, and substitute
  `task-clock` sampling / client-side `\timing` rather than an unfit bucketed server p50).
- **≥5 reps/cell, report dispersion (median + IQR), ban single measurements, pin and record
  every version** (commit, driver, instance, price, all non-default GUCs per run). NUMA-pin
  (`numactl`) the CPU baseline so a wide-vCPU engine isn't unfairly slowed. The `min_ms`
  column stays an anti-pattern (see `methodology.md` §4) — report medians.
- **Correct your own earlier estimates publicly when measurement inverts them.** Credibility
  comes from showing where your priors were wrong: a code-analysis guess of "GPU build ~10 s
  vs PG overhead ~45 s" inverted under measurement to build 82% / backend 18%; a projected
  "25–35% build saving" from a storage change corrected to ~8%. Write the correction *into*
  the report.
- **Isolate the "integration tax" with a bare-engine anchor.** Quarantine comparisons in
  rings: Ring A = in-Postgres head-to-head at iso-recall; Ring B = the same kernel with **no
  DB** (raw library) purely to bound how much the DB/MVCC/durability integration costs; Ring
  C = external systems reported separately (their 2-system + ETL + eventual-consistency cost
  makes a bare QPS number unfair to both sides); Ring D = the out-of-scope ceiling, recorded
  only as "where we don't play." A "% of raw engine" claim is only fair against Ring B.

## 6. Cost-model calibration

(When the extension installs a planner cost function that decides when to use the accelerated
path, calibrate it as its own sub-benchmark.)

- **Separate expensive physical measurement from cheap planner-decision verification**, so
  fixing the cost model doesn't invalidate the whole suite. Measure the forced per-engine
  curves **once** (an invariant asset); verify the planner's *choice* with EXPLAIN-only
  sweeps (free); freeze and version-tag the cost model before the expensive full run.
- **Pass criterion = regret + ε-band.** `regret = measured(planner's pick) −
  measured(best)`. Mark an ε-band around the crossover as a "don't-care" region where either
  choice is fine — don't demand zero misclassification where the two curves coincide.

---

For the GPU-specific worked numbers behind this file — PCIe transfer accounting, energy
J/query, faiss-gpu GT, the A100 rig — see `../accelerator/gpu-benchmarking.md`.
