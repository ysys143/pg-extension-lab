# Benchmarking an extension path

How to design and audit a benchmark whose conclusions survive a noisy host. Read this when
you are **measuring the quality, latency, or throughput of an index, query path, or other
extension path**, or comparing an accelerated path against a baseline. The governing idea: the
quality comparison against a deterministic oracle is the durable result; absolute
latency/throughput on a shared host are INDICATIVE.

The principles are generic. Two worked cases show them applied: a filtered ANN index and an
accelerator-vs-CPU crossover. Generalize from the principles, not from a case's axes.

| File | What it covers | Read when |
|---|---|---|
| [`methodology.md`](methodology.md) | Generic principles: adversarial fixtures with realized conditions recorded, exact oracles, **matched-quality (not matched-knob)** operating points, bounded parameter space, per-metric SOLID/INDICATIVE trust labeling, the **min_ms anti-pattern**, fairness, timing windows and throughput, a caveats template, the harness shape. | Any benchmark of an extension path. |
| [`filtered-ann-case.md`](filtered-ann-case.md) | Worked case — filtered ANN index: correlated-filter fixtures with measured pass rates, exact filtered ground truth, matched recall vs `ef`, scenarios A–D, competitor fairness and transport ceilings from a 100K–10M campaign. | Benchmarking a filtered vector/index path, or as an example of the principles applied. |
| [`crossover-and-cost.md`](crossover-and-cost.md) | Worked case — a path with **fixed overhead but better scaling** (GPU vs CPU, parallel vs serial, cached vs uncached): crossover root-finding, cost-per-query / total-cost framing, batch-vs-single-query, ground-truth independence, honest accelerator reporting, planner cost-model calibration. | Whenever one side has a fixed setup cost the other lacks. |
| [`protocol.md`](protocol.md) | Forced physical curves, EXPLAIN regret, freeze/version tags, full-suite promotion, Ring A-D scenarios, iso-$ / iso-energy reporting, and portable result schemas. | When a benchmark must defend planner/cost-model or accelerator conclusions. |
| [`evidence-loop.md`](evidence-loop.md) | Hypothesis → validation → evidence → report workflow, bounded parameter spaces, Pareto comparison, doc/code/execution evidence balance, and what belongs in version control. | Before starting any non-trivial benchmark or performance investigation. |

Related: resource-vs-performance frontiers and the `pareto.py` dominance check live in
[`../performance/resource-pareto.md`](../performance/resource-pareto.md); GPU-specific worked
numbers in [`../accelerator/gpu-benchmarking.md`](../accelerator/gpu-benchmarking.md).

Copy-ready benchmark assets, one per worked case:
[`../../assets/benchmark-filtered-ann/`](../../assets/benchmark-filtered-ann/) for filtered ANN and
[`../../assets/benchmark-accelerator/`](../../assets/benchmark-accelerator/) for accelerator
crossover/recall work. Both are checked by the generic gates in
[`../../assets/validation/`](../../assets/validation/README.md); case-specific gate rules turn on
through `[methodology] profile`.
