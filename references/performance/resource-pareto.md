# Resource ↔ performance Pareto

For an index extension, every gain in performance (recall, latency, throughput) is bought
with resource (build time, index size, RAM, cores). There is no single "fast" — there is a
frontier. This reference is the discipline for finding and moving that frontier.

> Resource *governance* (which knob binds each resource, fail-closed ceilings, storage-layout
> levers, derived-artifact placement, guide-don't-force) is in **`governance.md`**.

## Contents

- [The governing rule: measure before you change, config before code](#the-governing-rule-measure-before-you-change-config-before-code)
- [Recall-QPS frontier (the performance side)](#recall-qps-frontier-the-performance-side)
- [Profiling the resource bottleneck (build-time case)](#profiling-the-resource-bottleneck-the-build-time-case)
- [Lever table — direction of each knob](#lever-table--direction-of-each-knob)
- [Profile, don't estimate](#profile-dont-estimate)
- [Workflow summary](#workflow-summary)

---

## The governing rule: measure before you change, config before code

Two gates, in order, before any optimization code is written:

1. **Config-Pareto gate.** Sweep the cheap configuration knobs and measure the trade-off.
   This tells you how much of the problem is already solvable by turning a knob — and sets
   the **ROI baseline** that every code change must beat.
2. **Profile gate.** Identify *where* the resource actually goes (CPU? IO? lock wait?).
   Optimize the real bottleneck, not the assumed one.

Skipping the config gate is the classic failure: you write a clever optimization, it helps,
and you never learn that `payload_m=32` would have given the same build-time win for free.

### Config-Pareto recipe

Pick the 2–3 knobs that trade resource for performance and grid them:

```
payload_m ∈ {16, 32, 64}   ×   max_parallel_maintenance_workers ∈ {16, 30}
```

For each cell record **build time + index size + filtered recall at sel {1,10}%**. Read it
as a frontier:

- Hypothesis form: "workers=16 ties or beats 30 (less contention) → make 16 the default."
- Hypothesis form: "payload_m=32 cuts build ~30% with negligible recall loss → reconsider
  the default."

Each accepted hypothesis is a free win that shrinks the remaining work for code. With a 1M
fixture preloaded, each build is ~5–8 min, so the whole grid is an afternoon.

---

## Recall-QPS frontier (the performance side)

For each selectivity, sweep `ef_search` and plot (recall, QPS). A point is **Pareto-optimal**
iff no other point of the *same engine* has both ≥ recall AND ≥ QPS (with at least one
strictly greater). `bench/pareto.py` computes and marks exactly this:

```python
def _pareto_flags(points):  # points: [(ef, recall, qps, p99), ...]
    flags = []
    for i, (_, r_i, q_i, _) in enumerate(points):
        dominated = any(
            r_j >= r_i and q_j >= q_i and (r_j > r_i or q_j > q_i)
            for j, (_, r_j, q_j, _) in enumerate(points) if i != j)
        flags.append(not dominated)
    return flags
```

```
python bench/pareto.py bench/results_100k_low.json --selectivity 1
```

Compare **frontiers** between engines, never a single ef value. An engine wins if its
frontier dominates — higher recall at equal QPS, or higher QPS at equal recall, across the
operating range you care about.

---

## Profiling the resource bottleneck (the build-time case)

When build time is the cost, find out *why* before touching the algorithm:

- `pg_stat_progress_create_index` → `tuples_done` rate (throughput of the build).
- `top` during the build → the CPU picture.

**The key diagnostic:** high **idle %** under many workers means **lock contention**, not a
CPU or IO bound. Measured: at 30 workers a 10M build sat at **88% CPU idle** (user ~0%,
sys ~8%) — workers were waiting on locks, not computing. Consequences:

- **Adding vCPUs does nothing** until the contention is removed (build saturated ~16 cores;
  16→30 workers gave identical wall-time). vCPU increase is a non-lever here.
- The real levers are *removing serialization*:
  - per-worker arena/id chunks instead of a global allocator lock taken per node
    (N allocations → O(N/chunk) lock acquisitions);
  - shortening a global entry-point lock's critical section (atomic snapshot read + release
    instead of holding shared across the whole insert);
  - a **two-pass build** that separates the extension-specific cost (payload edges) from the
    base-graph build so the base pass parallelizes like stock pgvector and the payload pass
    becomes node-independent (embarrassingly parallel).

Verify each contention fix the same way you found the problem: idle % should drop and
`tuples_done` rate should rise; wall-time shortens. Gate structural changes behind a GUC so
the old path stays measurable side-by-side.

---

## Lever table — direction of each knob

| Lever | Resource cost | Performance effect | Notes |
|---|---|---|---|
| `payload_m` (payload neighbors/node) | build time ↑, index size ↑ | filtered recall ↑ | the dominant build-cost lever; up to ~3× neighbors vs base graph |
| `acorn_gamma` (candidate-queue width) | build time ↑ | recall ↑ (keeps filter-failing bridge nodes) | the mechanism that beats filter-blind HNSW |
| inline vs non-inline vectors | index size ↑↑ (4 GB vs 0.3 GB seen) | latency ↓ (vectors co-located, fewer fetches) | a latency play, not a footprint play |
| `ef_construction` | build time ↑ | recall ↑ | standard HNSW knob |
| `maintenance_work_mem` | RAM ↑ | avoids spill → build time ↓ | size to keep the build in memory |
| parallel workers | cores | build time ↓ **only until lock contention saturates** | non-lever past ~16 here; fix contention first |

---

## Profile, don't estimate

Code-reading estimates of where resource goes are routinely wrong by multiples — always
profile before optimizing, and **publish the correction** when measurement inverts a prior.
Measured examples: a "GPU build ~10 s vs PG overhead ~45 s" code-analysis guess inverted to
build 82% / backend 18%; a detoast cost estimated at "~25–35% of build" measured at ~8%; a
projected "25–35% build saving" from a storage change came out ~8%. The discipline: every
"this is the bottleneck" claim is a hypothesis until a profiler (`pg_stat_progress_*`,
`perf`/`task-clock`, before/after time deltas) confirms it.

---

## Workflow summary

```
1. Config-Pareto sweep        → free wins + ROI baseline   (no code yet)
2. Profile (progress + top)   → is it CPU / IO / lock?
3. If lock-bound:             → remove serialization (arena, lock scope, two-pass), behind a GUC
4. Re-measure same way        → idle% ↓, tuples_done rate ↑, wall-time ↓
5. Recall-QPS frontier        → confirm performance side didn't regress (pareto.py)
6. Fix seeds, commit JSON + REPORT_*.md, write reproduce commands
```

Priority order, mirroring a "measurement-first" roadmap: **config-Pareto → contention fixes
(measure) → structural change (measure)**. Never reorder; never skip a measurement gate.
