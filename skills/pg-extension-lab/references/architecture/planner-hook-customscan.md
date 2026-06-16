# Planner hook, CustomScan, and native AM choices

Read this when the extension changes PostgreSQL planning or vector/index execution.

## Three tiers

| Tier | Shape | Use when | Main risk |
|---|---|---|---|
| Hook-only | `set_rel_pathlist_hook` / planner hook adds or biases paths | You can express the work through existing executor/index nodes | Cost model lies or hook ordering conflicts |
| CustomScan over another AM | Custom executor node drives an existing index or page layout | You need filtered/progressive behavior but can reuse storage | Version-pinned internal layout dependency |
| Native AM | Full `IndexAmRoutine` with custom pages/WAL/costing | Storage/execution cannot be represented by an existing AM | Crash safety, VACUUM/build/scan correctness |

## Protocol before code

1. Implement a hook-only prototype to prove the planner decision surface.
2. Add forced physical curves before trusting planner choices.
3. Add `EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)` regret reports: compare chosen plan against
   forced alternatives and record pages/query.
4. Freeze the cost model with a version tag before promoting to full benchmark runs.

## CustomScan dependency rule

If a CustomScan reads another extension's internal page layout, declare the supported upstream
version range and add a startup/runtime guard. Treat the layout as a private ABI: a silent
upstream change can corrupt results without crashing.

## Cost model minimum

Costing must include filter selectivity, expected candidate expansion, heap recheck cost,
random page pressure, and startup overhead. A benchmark that only compares `ef` or distance
calculations is not enough; it misses the PostgreSQL cost surface that users experience.

## Required scenarios for filtered vectors

- A: selectivity sweep with correlated and uncorrelated filters.
- B: post-filter recall failure against exact filtered ground truth.
- C: incremental/progressive recall recovery as candidate expansion increases.
- D: correlation stress, where the passing set is spatially far from the query-nearest path.

