# Performance: resource ↔ performance trade-offs & governance

Every performance gain (recall, latency, throughput) is bought with resource (build time,
index size, RAM, cores). Read this when you are **choosing build-time vs recall/latency
trade-offs, doing build-perf optimization work, or bounding a resource at runtime.**

| File | What it covers | Read when |
|---|---|---|
| [`resource-pareto.md`](resource-pareto.md) | The measurement-first discipline: **config-Pareto before code**, the recall-QPS frontier + `pareto.py` dominance check, **lock-contention build profiling** (idle% = contention, not CPU), the lever table, profile-don't-estimate, the workflow summary. | Optimizing build time or picking knob defaults. |
| [`governance.md`](governance.md) | Bounding resources at runtime: **which knob actually binds each resource**, fail-closed ceilings + admission control, storage-layout (PLAIN vs EXTERNAL) as a build lever, regenerable-artifact placement outside `$PGDATA`, accounting-as-integrity, guide-don't-force. | Managing an off-heap/external resource or a large-value table. |

Related: the deterministic injected-OOM/eviction *tests* for these resources are in
[`../architecture/out-of-process.md`](../architecture/out-of-process.md); the cost-per-query
economics are in [`../benchmarking/crossover-and-cost.md`](../benchmarking/crossover-and-cost.md).
