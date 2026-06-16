# Benchmarking an index / query path

How to design and audit a benchmark whose conclusions survive a noisy host. Read this when
you are **measuring recall/latency/throughput of an index or query path**, or comparing an
accelerated path against a baseline. The governing idea: the deterministic recall comparison
is the durable result; absolute latency/throughput on a shared host are INDICATIVE.

| File | What it covers | Read when |
|---|---|---|
| [`methodology.md`](methodology.md) | Adversarial correlated fixtures, exact ground truth, **matched-recall (not matched-ef)** operating points, SOLID-vs-INDICATIVE trust labeling, the **min_ms anti-pattern**, competitor fairness, transport-bound throughput, a caveats template, the harness shape. | Any recall/latency/throughput benchmark. |
| [`crossover-and-cost.md`](crossover-and-cost.md) | Comparing a path with **fixed overhead but better scaling** (GPU vs CPU, parallel vs serial, cached vs uncached): crossover root-finding, cost-per-query / total-cost framing, batch-vs-single-query, ground-truth independence, honest accelerator reporting, planner cost-model calibration. | Whenever one side has a fixed setup cost the other lacks. |
| [`protocol.md`](protocol.md) | Forced physical curves, EXPLAIN regret, freeze/version tags, full-suite promotion, Ring A-D scenarios, iso-$ / iso-energy reporting, and portable result schemas. | When a benchmark must defend planner/cost-model or accelerator conclusions. |
| [`evidence-loop.md`](evidence-loop.md) | Hypothesis → validation → evidence → report workflow, bounded parameter spaces, Pareto comparison, doc/code/execution evidence balance, and what belongs in version control. | Before starting any non-trivial benchmark or performance investigation. |

Related: resource-vs-performance frontiers and the `pareto.py` dominance check live in
[`../performance/resource-pareto.md`](../performance/resource-pareto.md); GPU-specific worked
numbers in [`../accelerator/gpu-benchmarking.md`](../accelerator/gpu-benchmarking.md).

Copy-ready benchmark assets:
[`../../assets/benchmark-filtered-ann/`](../../assets/benchmark-filtered-ann/) for filtered ANN and
[`../../assets/benchmark-accelerator/`](../../assets/benchmark-accelerator/) for accelerator
crossover/recall work.
