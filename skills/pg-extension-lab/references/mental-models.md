# Mental models for PostgreSQL extension work

This skill is not a checklist. It is a way to keep PostgreSQL extension work honest when the
system has many hidden variables: planner behavior, MVCC, C memory contexts, background
workers, external services, accelerators, noisy hosts, and stale documentation.

## 1. Evidence search beats implementation theater

The unit of progress is not "I wrote code." The unit of progress is "uncertainty got smaller."
Sometimes the best next move is a failing SQL regression test. Sometimes it is reading a source
file. Sometimes it is a tiny `EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)` run. Sometimes it is a
report that says a hypothesis failed.

Prefer actions that create durable evidence: red/green tests, config-validated benchmark plans,
exact ground truth, result JSON/CSV, EXPLAIN JSON, reports with commands and caveats, and
source-code citations that explain why docs were incomplete.

Code without evidence is just another hypothesis.

## 2. Experiments search over code, fixtures, and outputs

During exploration, the job is to generate ideas, apply them to code, and find better code. But
"better" is not directly visible. You only observe it through a designed output:

```text
candidate code + fixture/workload + measurement function => output artifact
```

That means the fixture is not a side detail. The fixture is part of the question. If the fixture
is too friendly, too synthetic, too small, or accidentally coupled to the implementation, the
output answers the wrong question and selects the wrong code.

Design fixtures as deliberately as code:

- model the real workload shape, not only the easiest unit case;
- include adversarial cases that expose the failure mode the feature claims to fix;
- make the expected output observable from outside the implementation;
- keep the fixture stable enough that competing code candidates see the same world;
- version fixture generation so a changed fixture is visible as a changed question.

In this mindset, code variants are candidates, fixtures are questions, and result artifacts are
answers. A benchmark is only useful when the question is good enough to choose between answers.

## 3. Hidden parameters often drive the result

Unexpected parameters routinely dominate PostgreSQL extension behavior: planner GUCs, cache
warmth, visibility map state, table bloat, index build order, background worker timing,
service latency, device memory pressure, client transport, concurrency, CPU features, Docker
image GLIBC, and more.

Do not pretend the visible config is the whole experiment. Actively search for the hidden
parameter space:

- when a result changes, ask which untracked state could have changed;
- when a result is too good, look for a shortcut, cache, de-indexed path, or unfair baseline;
- when a result is good for no understood reason, assume a hidden dimension may be missing from
  the experiment design;
- when a result is too noisy, isolate one layer before adding more samples;
- when two runs disagree, preserve both artifacts and explain the differing conditions.

The point of smoke runs, one-axis scouts, EXPLAIN checks, and environment capture is to discover
which hidden parameters are actually steering the system.

## 4. Docs are maps, code is terrain, execution is weather

Do not start by blindly wiring every API you can find. Start with docs because they reveal the
intended model and vocabulary. Then distrust them enough to inspect source, SQL definitions,
catalog state, tests, and runtime behavior.

| Evidence | What it is good for | What can go wrong |
|---|---|---|
| Docs | intended contract, architecture, supported usage | stale, aspirational, incomplete |
| Public API | stable integration boundary | too broad; names can imply false guarantees |
| Source code | actual behavior and edge cases | hard to interpret without runtime state |
| Tests | executable expectations | may miss production scenarios |
| Execution | real planner/runtime behavior | environment noise and accidental coupling |

When evidence disagrees, record the disagreement. Trust executable evidence for the current
decision, then fix or annotate the docs so future work does not repeat the investigation.

## 5. DB-service work needs API, fixture, and environment evidence

When PostgreSQL is joined to an external model/service, a green E2E run is ambiguous unless the
three layers have separate evidence:

- **API:** the boundary accepts the request you think you are sending and returns the shape you
  think you are parsing.
- **Fixture:** the database rows, expected answers, IDs, and oracle express the behavior you
  actually want, not merely "something came back."
- **Environment:** the effective endpoint, env vars, registry row, container image, volume
  state, dependency versions, and runtime flags match the claim.

These layers can fail independently. API-compatible calls can still answer the wrong fixture.
Correct fixtures can still run against a stale container or a blank env override. A real service
can prove compatibility while a mock remains the better correctness gate. Classify boundary
failures as API, fixture, or environment before changing code.

## 6. Parameter space is a landscape, not a grid

PostgreSQL extension benchmarks have too many axes: dataset, selectivity, k, index build knobs,
search knobs, planner knobs, memory, concurrency, hardware, service settings, and target
implementations. A full Cartesian product is usually wasteful and often dishonest because the
reader cannot tell which cells mattered.

Think in phases:

- **Scout:** one axis at a time to learn active ranges.
- **Prune:** discard dead ranges and dominated cells.
- **Refine:** spend runs near knees, cliffs, planner flips, OOM thresholds, and frontier changes.
- **Promote:** only stable, decision-changing cells move from smoke to full suite.

Pareto curves are the right answer shape because they preserve trade-offs. A single best number
usually hides which resource was spent to get it.

Pareto is not only for declaring absolute superiority. More often it tells you where an option
belongs: low-memory but slower, high-recall but expensive, small-N exact, high-QPS approximate,
read-heavy, write-heavy, warm-cache, cold-cache, filtered, unfiltered. The useful output is a
map of suitability zones, not just a trophy.

## 7. Explain surprising wins as mechanism hypotheses

When one option appears to dominate another, do not stop at "pick the winner." Turn the win into
a mechanism hypothesis:

```text
Option A wins because [mechanism] under [conditions], and should stop winning when [dimension]
changes.
```

Then try to verify the mechanism. The best verification isolates that part: microbenchmark the
cache lookup, force the plan, remove the index, change only selectivity, disable the fast path,
or measure page I/O. But not every mechanism can be isolated cleanly. When isolation is not
practical, inspect the code path, source, EXPLAIN output, counters, logs, and artifact schema
until the win is at least explainable.

If a win remains unexplained, treat it as unfinished evidence. It may be real, but it may also
mean the experiment omitted a hidden dimension: cache state, planner route, exact fallback,
segment indexing threshold, data order, warmup, transport ceiling, or resource pressure.

## 8. Fairness is equalized decision conditions

Fair comparison does not mean identical knobs. `ef_search`, scan budget, batch size, GPU queue
depth, and service concurrency are not the same thing. Equalize the decision condition:

- same data and query set;
- same exact ground truth;
- same recall threshold or cost budget;
- same PostgreSQL/runtime window;
- same trust-labeling rules;
- same artifact schema;
- same opportunity to tune each engine within the declared budget.

Compare frontiers and matched operating points. If an engine loses in one region and wins in
another, the crossover is the result.

The fairness question is: did each choice get the same chance to answer the same question? If
not, the benchmark measures the setup, not the code.

## 9. Realistic fixtures before confident claims

Small fixtures are useful for fast feedback, but they are not enough for product claims. After a
candidate works on smoke fixtures, move toward realistic workload shape:

- real distributions where possible, not uniform toy data by default;
- realistic cardinality, selectivity, dimensionality, update/delete churn, and concurrency;
- representative query mixes, not only a single happy-path query;
- failure-oriented fixtures for the known hard cases;
- exact ground truth or an independently defensible oracle.

Synthetic fixtures are acceptable when they isolate a mechanism. They become misleading when
they are used to claim production behavior without a bridge to real workload evidence.

## 10. Verified performance must be stabilized from many angles

A promising result is not done. Once a code path looks better, attack it from different angles:

- correctness: exact oracle, regression tests, isolation tests, upgrade tests;
- planner behavior: forced plans, free planner choices, EXPLAIN regret, pages/query;
- performance stability: warm/cold cache, concurrency, scale, selectivity, tail latency;
- operations: restart, fallback, missing device/service, OOM, retries, observability;
- security: privileges, `search_path`, RLS/ACL, recheck boundaries;
- portability: PostgreSQL major versions, compiler flags, container/runtime versions.

Exploration finds candidates. Stabilization turns a candidate into code that can survive contact
with users and operators.

## 11. Separation is how code stays safe and robust

Code should be separated so failures are contained and feedback is sharp:

- scenario logic separated from target adapters;
- SQL-observable contract separated from implementation details;
- fixture generation separated from measurement;
- benchmark config separated from runner code;
- database state separated from external service/device state;
- table-backed truth separated from notification hints;
- privileged/security-definer code separated from caller-controlled input;
- fast checks separated from slow promotion gates.

Separation is not architecture theater. It lets you swap candidates fairly, isolate failure
causes, test hard cases without a full stack, and keep dangerous work behind smaller contracts.

## 12. Isolation makes feedback attributable

A benchmark or test that cannot explain why it changed is low-quality feedback. Isolation is how
you keep feedback attributable:

- SQL/spec files stay environment-agnostic.
- Docker/CI/env files own environment differences.
- Device and service absence are explicit skip/fail-closed paths.
- Each benchmark target runs without hidden competing indexes/services where possible.
- Seeds, configs, result artifacts, and reports are versioned together.

If a result depends on untracked local state, it is not evidence yet.

## 13. Fast loops and slow gates have different jobs

Fast loops are for thinking. Slow gates are for confidence. Do not make every question wait for
a full benchmark suite.

- Seconds: config validation, unit tests, dry-runs, SQL smoke, static checks.
- Minutes: Ring A/B correctness, exact ground-truth smoke, narrow EXPLAIN checks.
- Hours: full frontier, external comparison, accelerator/cost claims.

If the fast loop cannot catch basic mistakes, the full suite becomes an expensive debugging
tool. That is backwards.

## 14. Reports are part of the system

Reports are not presentation polish after the work. They are the memory and audit layer for the
system. A good report makes it possible to know what was tested, what changed, what failed, and
what is still unknown.

Every serious report should include hypothesis, acceptance threshold, exact command, environment,
fixture identity, raw artifact path, trust labels, caveats, and self-corrections. Generate the
report from artifacts where possible. Memory is not a reproducibility strategy.

## 15. Representative evidence beats convenient evidence

Completion evidence must come from the state users will actually hit, not the easiest state to
measure. A feature can look done because the test exercised a restart/load path while the fresh
build path is broken, because a benchmark did not assert the chosen execution mode, or because
the comparison used stale results from an older binary.

Use representative-state guards:

- assert the mode/codepath, not only the output;
- test fresh build, reload, restart, eviction, and upgrade paths separately;
- compare current binary to current binary, not current competitor to stale local results;
- keep negative corrections in the report instead of overwriting the story;
- add a regression guard for the exact false-done mechanism that fooled you.

The mindset: evidence is only as strong as the state it represents.

## 16. Hints, caches, and sidecars must never become authority

Many extension optimizations are derived state: shared-memory code caches, resident GPU indexes,
LRU slots, sidecar artifacts, NOTIFY events, object-store snapshots, and warmup registries. They
are valuable only while the durable source of truth remains elsewhere.

The authority rule:

- heap/catalog/WAL-backed state decides correctness;
- caches accelerate but must miss/fallback safely;
- sidecar artifacts need manifest, checksum, version, and cluster identity;
- object-store or disk artifacts must fail closed when heap compatibility is unknown;
- NOTIFY and background warmup are hints, never the only record of work.

If deleting a cache changes the answer instead of only changing latency, the cache has become
an unsafe authority.

## 17. Cost models are control systems, not comments

A PostgreSQL cost model is not documentation for an algorithm. It is a controller that changes
which code runs. A small wrong constant can route users onto a worse path even if the algorithm
itself is good.

Treat cost work as a control loop:

- separate forced physical curves from planner-auto results;
- use EXPLAIN regret to compare planner choice against measured best choice;
- define an epsilon band where either choice is acceptable;
- freeze and version cost constants before running expensive auto suites;
- prefer regret-averse defaults: explicit opt-in beats automatic misrouting.

Do not promote an auto mode until the regret cells are gone or consciously accepted.

## 18. Competitor benchmarks require codepath proof

External systems often have internal planners, thresholds, optimizers, exact fallbacks, and
background indexing. A benchmark can accidentally measure a different algorithm than the one
named in the report.

Before trusting a competitor result:

- inspect docs and source for threshold semantics;
- verify runtime status counters or telemetry;
- wait for background indexing/optimization to settle;
- force or label exact-vs-approximate paths;
- record the codepath proof beside the latency/recall numbers.

If a reported HNSW result actually used exact brute force, the recall result is not wrong, but
the interpretation is.

## 19. Strategy depends on the denominator

Performance strategy changes when the denominator changes. A system optimized for cost per
stored vector is different from one optimized for cost per query, p99 latency, Joules/query, or
operator complexity.

Use denominator discipline:

- name the economic denominator before choosing the architecture;
- do not chase workloads whose denominator structurally favors another system;
- let competitor evidence refute positioning, then update the roadmap;
- distinguish "north-star" work from marginal work hidden behind a wall-clock floor;
- keep no-go decisions as useful outputs when the denominator says the idea is wrong.

Hardware changes the algorithm too: CPU graph traversal, GPU brute force, NVMe rerank, and
integrated-memory GPUs create different optimal shapes. The right algorithm is conditional on
the resource surface.

## 20. Test doubles verify contracts, not physics

CPU shims, fake devices, fake object stores, and deterministic service doubles are powerful because
most bugs are glue bugs: serialization drift, routing mistakes, fail-closed gaps, mode labels,
manifest contracts, and recovery paths. They should run constantly.

But a test double must be labeled honestly:

- Tier 1 shims verify contracts, plumbing, state machines, and deterministic correctness;
- Tier 2 real hardware verifies physical behavior, approximate recall, memory pressure, and
  latency;
- green shim CI must never be presented as green GPU CI;
- tests should say which bug class they can and cannot catch.

The double is a lens, not the real world.

## 21. Experimental paths should be explicit until proven safe

When evidence says a path is promising but conditional, keep it behind an explicit switch or
experimental mode. Preserve the code when it may become valuable under different hardware or
workload assumptions, but do not let it silently enter auto-routing.

Graduation rule:

- explicit `on` is acceptable with caveats;
- `auto` requires regret analysis and representative workloads;
- default-on requires correctness, stability, observability, rollback, and cost evidence;
- deprecation/no-go is valid when the denominator or hardware surface makes the path wrong.

This keeps learning alive without making users pay for unfinished bets.

## 22. PostgreSQL-specific humility

PostgreSQL extension work has traps that look like ordinary programming until they fail:
backend memory contexts decide object lifetime; SPI scope decides pointer validity; MVCC means
returned IDs still need heap visibility/security rechecks; planner choices can dominate
algorithmic wins; WAL/recovery rules decide whether a custom index is real; background workers
and NOTIFY need table-backed truth; `SECURITY DEFINER` makes `search_path` correctness-critical.

This is why the harness emphasizes observable SQL behavior, isolation tests, EXPLAIN/page I/O,
and versioned artifacts. The database is the runtime, not just a library.
