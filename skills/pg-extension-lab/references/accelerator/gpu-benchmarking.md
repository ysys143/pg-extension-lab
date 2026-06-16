# Reference (deep): GPU/CUDA extension — benchmarking specifics

The GPU realization of the generic crossover / cost / batch / honesty methodology in
`../benchmarking/crossover-and-cost.md`. Read that first (and `../benchmarking/methodology.md`
for fixtures/ground-truth/trust labeling). This file holds only the GPU-specific numbers,
accounting, and rig details that illustrate those generic rules.

---

## Latency decomposition (where the time goes once the kernel is fast)

Once the GPU search kernel collapses the distance math to a sub-millisecond kernel, the bottleneck moves
off arithmetic:

- **IPC round-trip ≈ 33%** of query latency (backend ↔ daemon over the Unix socket).
- **Heap access** (TID → visible tuple, MVCC recheck) becomes a real share.
- **Per-query device transfer ≈ 4.4 µs** — negligible, *because only Q×K results cross PCIe.*

The benchmark's job is characterizing this *shift*, not quoting a single speedup.

## Crossover numbers (the surface)

- Latency: GPU path p50 871→1228 µs across N=1K→100K (near-flat in the reference run); CPU graph path grows 224→8232 µs →
  **latency crossover ≈ N 10K–100K**. Below ~10K, CPU HNSW wins on every axis (IPC round-trip
  not worth it for a tiny search).
- Build: advantage widens with both N and dim — 9× at 100K×384 → 36× at 1M×1536. **Higher
  dimension favors the GPU more.** Build-speedup is allowed on synthetic data (data-independent).
- Find the crossover by log-bisection (coarse `{1K,10K,100K,1M,10M}`, bisect the interval
  where `ratio` crosses 1.0), not a dense grid.

## The on-device intermediate rule (the make-or-break for GPU)

Keep the Q×N distance matrix **on-device** (400 MB at Q=100/N=1M); cross IPC only with Q×K
(TID+distance, ~8 KB, ~0.4% of latency). **Pulling the intermediate to the host made a GPU
path slower than pure CPU (749 → 7.9 QPS).** This is the single most important GPU benchmark
correctness rule.

## Batch / throughput

- Per-call dispatch+IPC overhead is fixed → GPU starved at Q=1, saturated at Q=100 (Q=100
  batch kernel ~1.27 ms ≈ 1.8× the Q=1 kernel for 100× queries). Report single-query latency
  and batched throughput as **separate benchmarks with opposite winners.**
- Micro-batch concurrent single-query requests via a coalescing window
  (`accelerator.batch_wait_us` ~100–1000 µs) into one Q=N kernel.
- Single-device throughput ceiling ≈ ~1K QPS (small/medium N), IPC-bound; sharding is the
  only way past (+70% latency / +13% recall in one case). State it as a limitation.

## Cost & energy framing

- Report `$/1M queries`, `$/sustained-QPS@p99`, `J/query` — never VRAM-GB ≡ DRAM-GB.
- Two baselines: **same-box** (CPU engine on the GPU instance's CPU/RAM) and **iso-$** (a
  CPU-only instance at equal $/hr, which gets more RAM).
- Fixed vs marginal: the 4 GB index upload (~876 ms) is once-per-index, excluded from
  per-query cost. The GPU only wins `$/QPS` above a throughput threshold → plot cost-per-query
  vs sustained QPS, not at QPS=1.

## Ground truth & honesty (GPU specifics)

- GT with an **independent** exact engine: faiss-cpu/flat ≤1M, **faiss-gpu/flat ≥10M**
  (different implementation from the system under test → no circular validation). Stream base vectors via
  `COPY TO STDOUT` to avoid a 72 GB fbin. **GT and loader must share the same batch/RNG
  path** — a mismatch desynced the RNG and gave recall = 0.0 everywhere.
- Warm (daemon-resident, load confirmed) vs cold-start (VRAM reload ~150 MB/s) are separate
  lines.
- **Recall forbidden on synthetic** (uniform-random = recall 1.0 trap; clustered flatters
  IVF) — anchor recall to one real dataset (Cohere 1M×1024). Build-speedup OK on synthetic.
- Rig blind spots disclosed: GCP VM exposes no hardware PMU → cache-miss hotspots
  unmeasurable; use `task-clock` sampling and client-side `\timing`, not the unfit bucketed
  server p50.
- ≥5 reps/cell, median+IQR, NUMA-pin (`numactl`) the CPU baseline, pin commit/driver/instance/price.

## VRAM as a published result

The resource ceiling is a real finding, printed verbatim: "50M×384 fp32 = 73 GiB >
2×40 GB VRAM → GPU INDEX BUILD FAILED." VRAM-budget and shard-count sweeps are run *as benchmarks*
(`gpu_resources_bench.csv`), with `peak_vram_mb / gpu_s / energy_j` columns alongside latency.
See resource governance in `../performance/governance.md`.

## Cost-model calibration

The planner cost callback decides accelerated path vs seqscan/baseline index and stats a
`.stale` sidecar to force cost `1e9` when the index is stale. Calibrate per
`../benchmarking/crossover-and-cost.md` §6: measure forced curves once, verify the planner's pick by
EXPLAIN-only sweeps, pass on **regret + ε-band**.
