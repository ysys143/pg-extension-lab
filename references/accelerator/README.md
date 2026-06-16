# Accelerator (GPU/CUDA) specifics — deep dive

The concrete, hardware-specific mechanics for a GPU/CUDA-backed extension. This is a
**specialization** of the generic tracks, not a separate one — read the hardware-agnostic
parents first, then come here only for the GPU realization:

- Architecture / build / testing / CI → [`../architecture/out-of-process.md`](../architecture/out-of-process.md)
- Benchmark methodology → [`../benchmarking/crossover-and-cost.md`](../benchmarking/crossover-and-cost.md)
- Resource governance → [`../performance/governance.md`](../performance/governance.md)

| File | What it covers |
|---|---|
| [`gpu-build-and-ops.md`](gpu-build-and-ops.md) | nvcc/CUDA under PGXS, `.c`/`.cu` float4 split, static libstdc++, `-rpath` vs the ldconfig disaster (+recovery), the CUDA-context-per-process daemon rationale, remote GPU VM workflow, cost & two-tier CI. |
| [`gpu-benchmarking.md`](gpu-benchmarking.md) | Latency decomposition, crossover numbers, the on-device-intermediate rule, batch/throughput, cost & energy framing, faiss-gpu ground truth, VRAM-as-published-result, cost-model calibration. |

> Do not generalize from the numbers here — generalize from the parent references. These files
> exist so the GPU specifics don't pollute the hardware-agnostic guidance.
