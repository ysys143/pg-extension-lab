---
name: pg-extension-lab
description: >-
  Develop, test, benchmark, and operate PostgreSQL extensions with reusable harnesses and
  reference protocols. Use for C/PGXS or Rust/pgrx extension work, planner hooks, CustomScan or
  index AM design, pg_regress/pg_isolation_regress TDD, filtered ANN/vector benchmarks,
  matched-recall and pages-per-query analysis, bounded parameter-space exploration, Pareto
  curves, hypothesis/evidence/report management, accelerator-vs-CPU crossover, resource Pareto
  tuning, Shape B microservice extensions, Shape C sidecar daemons, service-boundary contracts,
  async outbox workers, and SECURITY hardening. Balances docs, code evidence, and
  execution results. Includes copy-ready test, benchmark, contract, and ops assets. Not for
  projects without a PostgreSQL extension layer.
---

# pg-extension-lab — a harness to build, test, scenario, benchmark, and tune a PostgreSQL extension

**pg-extension-lab is a harness for validating a PostgreSQL extension's observable behavior in
an isolated, reproducible environment, separately from its implementation** — covering
**three architecture shapes** and **five reference categories**. Use it not only to build an
extension from scratch but to design tuning experiments, write scenarios, and run
isolation/regression tests against an existing one. Start with the mental model, identify your shape, then open the category
that matches the request — each
category has a `README.md` index that links to dense, single-topic detail files (progressive
disclosure: this file → category README → detail file).

Core mindset: **[`references/mental-models.md`](references/mental-models.md)**.

## Architecture shapes this covers

```
Shape A — pure C / PGXS or Rust/pgrx extension (e.g. a custom index access method)
  SQL caller → access method / planner hook / pg_extern function → on-disk index pages

Shape B — DB extension + external microservice (the service OWNS data)
  sync:  PostgreSQL (SQL function) → HTTP → service (FastAPI/gRPC) → SQL → database
  async: SQL function → outbox row + NOTIFY → LISTEN worker → service → UPDATE result table

Shape C — DB extension + co-located compute sidecar (the daemon owns a costly RESOURCE, not data)
  N backends → Unix socket/shm → one long-lived daemon holding a device context / model / pool
  backend resolves returned IDs → MVCC + ACL recheck against the heap
```

Shape A is the default for index/AM/hook work (no network layer). Shape B applies when a SQL
function delegates to a separate service that owns data. Shape C applies when the extension
needs a costly, *process-bound* resource — one daemon owns it, backends are thin clients, and
the daemon holds no catalog/transaction state. The TDD discipline is the same for all three;
only the deploy/verify mechanics differ (reinstall the `.so` vs redeploy a service container
vs restart the daemon + reconcile orphaned artifacts). Shapes compose.

## Pick a category

| Category | Use when | Start here |
|---|---|---|
| **Testing** | Adding a SQL-callable feature, AM behavior, or concurrency guarantee, test-first. | [`references/testing/README.md`](references/testing/README.md) |
| **Benchmarking** | Designing/auditing a recall-latency-throughput benchmark; accelerator-vs-CPU crossover; cost-per-query. | [`references/benchmarking/README.md`](references/benchmarking/README.md) |
| **Performance** | Build-time / size / RAM vs recall / latency trade-offs; build-perf work; resource governance. | [`references/performance/README.md`](references/performance/README.md) |
| **Architecture** | Shape B/C, Rust/pgrx, async outbox workers, service-boundary contracts, security. | [`references/architecture/README.md`](references/architecture/README.md) |
| **Accelerator (GPU)** | GPU/CUDA-specific build, ops, benchmark mechanics — a *specialization*, not a separate track. | [`references/accelerator/README.md`](references/accelerator/README.md) |
| **Reusable harnesses** | Copy-ready scripts/templates for test ladders, filtered-ANN benchmarks, accelerator crossover, service-boundary contracts, release/ops. | [`references/harnesses/README.md`](references/harnesses/README.md) |

The one law that spans every category: **fast, high-quality feedback comes from isolated
tests/benchmarks and disciplined versioned artifacts.** Measure before you change, label what
you measured by trust, and keep the evidence. Red before green. Docs guide the search; code
and execution decide whether the docs are true. Config-Pareto before code. Recall
(deterministic) is SOLID; absolute latency on a shared host is INDICATIVE.

## When to use (detailed triggers)

Triggers (EN): "pg extension TDD", "add SQL function test first", "pg_extern add",
"pg_regress test", "isolation test for concurrent insert/scan", "golden file test",
"benchmark the index", "recall vs latency", "pareto curve", "build perf", "matched recall",
"filtered ANN benchmark", "GPU vs CPU crossover", "cost per query", "out of process daemon",
"VRAM OOM fallback", "CPU shim for CI", "two-tier GPU CI", "pgrx extension", "SECURITY DEFINER
search_path", "transactional outbox", "NOTIFY LISTEN worker", "service-boundary contract",
"mock vs real E2E", "extension security review".

Triggers (KO): "pg extension 개발/테스트", "SQL 함수 테스트 먼저", "회귀 테스트 추가",
"동시성 테스트", "벤치마크 전략", "recall 벤치", "pareto 곡선", "빌드 성능", "리소스 대 성능",
"matched recall", "GPU CPU 크로스오버", "쿼리당 비용", "데몬 IPC", "VRAM OOM 폴백",
"CI용 CPU shim", "pgrx 확장", "search_path 고정", "아웃박스 패턴", "NOTIFY 워커",
"서비스 경계 계약", "mock 테스트", "확장 보안 리뷰".

Do **not** use for general TDD in web frameworks, mobile apps, or pure Python/JS projects with
no PostgreSQL extension layer.

---

## Testing — TDD test ladder (summary)

A PostgreSQL extension has three test levels, cheapest first. The contract you assert is what
a SQL caller actually sees — schema, catalog registration, search_path, recall — not internal
code logic.

| Level | Tool | What it proves | Command |
|---|---|---|---|
| **Unit** | standalone C binary (`test/unit/*.c`) | extracted algorithm logic, no PG running | `make unit` |
| **Regression** | `pg_regress` (`test/sql/*.sql` + `test/expected/*.out`) | deployed SQL behavior, golden-file diff | `make installcheck` |
| **Isolation** | `pg_isolation_regress` (`test/specs/*.spec`) | concurrency: interleaved insert/scan/build/evict | `make installcheck-isolation` |

**Golden-file TDD (red→green):** create `test/sql/<feature>.sql` with `\set ON_ERROR_STOP on`,
add it to the `REGRESS` list, and start with an **empty/minimal `expected/<feature>.out`**.
Run — the diff (or `function does not exist`) is your RED. Implement bottom-up, re-run, and
only then promote `test/results/<feature>.out` to the golden. Never write the golden before
the implementation passes. Concurrency belongs in isolation specs, not regression. The same
SQL/spec files run unchanged locally, in Docker, or on a VM.

Full ladder, empty-golden mechanics, incremental-maintenance specs, failure table, and copy-ready
test assets:
**[`references/testing/README.md`](references/testing/README.md)**.

---

## Benchmarking (summary)

Benchmarking an ANN/index path is where most rigor is won or lost:

1. **Adversarial fixture.** A *correlated* filter (key derived from the dominant embedding
   block → passing set is a cluster *off* the query→nearest path) is the worst case and the
   only honest test. Record measured pass rates.
2. **Exact ground truth.** Brute-force top-k over the *passing* rows, per (query, selectivity).
3. **Matched recall, NOT matched ef.** Compare engines at the lowest ef each needs to reach
   recall ≥ threshold; compare frontiers, not a shared ef.
4. **Bounded parameter space.** First sweep one axis at a time to find active ranges, then
   run fractional/frontier cells only. Do not run the full Cartesian product unless the space is
   tiny and justified.
5. **Trust labeling.** Recall is deterministic → **SOLID** (the headline); absolute
   latency/throughput on a shared host are **INDICATIVE**. `min_ms` is never a headline.
6. **Crossover, not a ratio.** For an accelerated path (fixed overhead, better scaling), find
   the N where it beats the baseline by root-finding; report the losing region too; frame
   cost-per-query, not just latency.

Methodology + the crossover/cost companion + copy-ready benchmark harnesses:
**[`references/benchmarking/README.md`](references/benchmarking/README.md)**.

---

## Performance — resource ↔ performance (summary)

The central trade-off is **resource (build time, index size, RAM) vs performance (recall,
latency, throughput)** — a frontier, not a number.

- **Config-Pareto BEFORE code.** Sweep cheap knobs first; that sets the ROI baseline every
  code change must beat.
- **Recall-QPS frontier, dominance-marked** (`pareto.py`): compare frontiers, not ef values.
- **Profile structurally.** High idle% under many workers = *lock contention*, not CPU/IO —
  adding vCPUs does nothing; remove serialization instead.
- **Govern the ceiling.** Map each resource to the knob that actually binds it; fail closed
  and loud; storage layout (PLAIN vs EXTERNAL) and artifact placement are levers; guide via
  NOTICE/WARNING, don't force.

Pareto discipline + governance: **[`references/performance/README.md`](references/performance/README.md)**.

---

## Architecture — shapes, integration, security (summary)

- **Shape A (in-process C/PGXS or pgrx).** Planner hook / CustomScan / native AM
  trade-offs, C SRF memory context rules, SPI type traps, trigger tuple ownership,
  GenericXLog/WAL, PG17 index-build API drift, and build/container portability traps.
- **Shape B (microservice).** SQL-assertion red→green, schema→service→extension order,
  multi-service Docker deploy matrix, schema-ownership single-authority, why-not-pg_regress
  for NOTIFY.
- **Rust/pgrx.** SPI↔HTTP phase separation (never hold SPI across a network call),
  `#[pg_extern]` attrs, 4 unit tests per function, dev-loop traps.
- **Async outbox worker.** Table-as-truth / NOTIFY-as-hint, `FOR UPDATE SKIP LOCKED` claim,
  status FSM + stale-pending reaper, deterministic worker tests, high-churn governance.
- **Service-boundary contracts.** Registry-owned configuration, one authority per durable
  object, the **data-contract invariant** (a violated shared invariant silently corrupts),
  mock-vs-real verification, and explicit migration rules.
- **Out-of-process (Shape C) + absent-dependency playbook.** Sidecar daemon concerns,
  reference-shim testing, injected resource-pressure tests, foreign-toolchain build, two-tier CI.
- **Security.** `SECURITY DEFINER` + `search_path` pinning, least-privilege ACL,
  secrets-by-reference, SSRF via owner-only registry.

Shape selection table + all six files: **[`references/architecture/README.md`](references/architecture/README.md)**.

Copy-ready harness assets live under **[`assets/`](assets/)**. Start with
**[`references/harnesses/README.md`](references/harnesses/README.md)** before copying them into
another repository.

---

## Cross-cutting principles

- **The work is evidence search, not implementation theater.** Code is one way to produce
  evidence. A test, EXPLAIN plan, benchmark result, source reading, or negative result can be
  the more valuable artifact if it shrinks uncertainty faster.
- **Experiments choose code through fixtures.** You cannot know a code candidate is better
  except through the output of a workload/fixture and measurement function; design that fixture
  as carefully as the code.
- **Hidden parameters are part of the search space.** Planner state, cache warmth, data shape,
  concurrency, service/device state, and build/runtime environment can dominate results; surface
  and version the ones that steer decisions.
- **Parameter space is a landscape.** Do not worship exhaustive grids. Scout the terrain,
  locate knees/cliffs/frontiers, then spend runs where a decision can change.
- **Pareto curves are suitability maps.** They are not only for declaring a winner; use them to
  find which workload, budget, hardware, and operating region each option fits.
- **Dominance needs a mechanism.** If one option looks absolutely better, state why as a
  falsifiable mechanism hypothesis and look for the hidden dimension where it should stop being
  better.
- **Fairness means equalized decision conditions, not identical knobs.** Different engines have
  different controls; compare at matched recall, matched budget, matched data, and explicit
  trust labels.
- **Realistic fixtures before confident claims.** Smoke fixtures are for speed; production
  claims need workload shape, adversarial cases, scale, churn, and an oracle.
- **Validated code must be stabilized.** Once a path looks better, attack correctness, planner
  behavior, performance stability, operations, security, and portability before treating it as
  done.
- **Separation is safety.** Separate scenarios from target adapters, fixtures from measurement,
  configs from runners, DB truth from hints, and privileged code from caller-controlled input.
- **Representative evidence beats convenient evidence.** Assert the execution mode/codepath and
  cover fresh-build, reload, restart, eviction, and upgrade states before calling a feature done.
- **Caches and sidecars are hints, not authority.** Derived state must miss, reload, or fail
  closed; heap/catalog/WAL-backed state remains the source of truth.
- **Cost models are controllers.** Separate forced physical curves from planner-auto decisions,
  measure regret, freeze versions, and keep auto modes regret-averse.
- **Competitor results need codepath proof.** Verify whether the other system used exact scan,
  graph search, indexed segments, payload-aware path, or a fallback before interpreting recall.
- **Strategy depends on the denominator.** Cost per vector, cost per query, p99, Joules/query,
  and operator complexity imply different architectures and different no-go decisions.
- **Test doubles verify contracts, not physics.** CPU shims and fake services catch plumbing
  and fail-closed bugs; real hardware still owns approximate recall, memory pressure, and
  latency truth.
- **Docs are maps, code is terrain, execution is weather.** Read docs to orient, inspect code to
  see the real shape, and run minimal checks because runtime behavior can still differ.
- **Feedback quality × feedback speed is the core product.** A slow uncertain loop is worse
  than a small sharp loop. Isolate environments and version artifacts so feedback remains
  attributable.
- **Reproducibility is non-negotiable.** Fix every seed, commit the result JSONs and
  `REPORT_*.md`, and put exact reproduce commands at the bottom of every report.
- **Hypothesis → validation → evidence → report is the unit of work.** Start with a falsifiable
  hypothesis, name the acceptance threshold, run the smallest isolated check that can disprove
  it, commit the raw evidence, then write the report from the artifact rather than memory.
- **Do not trust docs or APIs alone.** Read docs first to find the intended contract, then verify
  against source code, catalog shape, `EXPLAIN`, tests, or a minimal execution. If docs and code
  disagree, record the disagreement and trust the executable evidence.
- **DB-service boundaries need triple confirmation.** Verify API contract, fixture semantics,
  and effective environment separately; a green E2E run can hide failure in any one of the
  three.
- **Self-correction in reports.** When an earlier draft over-claimed (e.g. led with `min_ms`),
  write the correction *into* the report with the reasoning.
- **Environment-agnostic test/bench files.** Local/Docker/VM differences live in Makefile
  targets and `.env`, never in the `.sql`/`.spec`/`.py` files.
- **Version what changes the claim.** Track benchmark configs, seeds, fixtures, result JSON/CSV,
  generated reports, schema/extension SQL, Docker/CI environment, and scripts. Do not commit
  host-local caches, generated device state, or large rebuildable datasets unless they are the
  evidence artifact under review.
- **Bottom-up implementation, small verifiable checkpoints.** Schema → C function / service →
  SQL wrapper. Each layer compiles/passes before the next.
- **The table is the source of truth; the event is only a hint.** For any async/DB-mediated
  job, persist state to a table; NOTIFY is a latency optimization — polling still recovers.
  ([`references/architecture/async-outbox.md`](references/architecture/async-outbox.md))
- **One DDL authority per object.** In an extension + worker split, exactly one component
  creates each table; the other is a consumer. The row/payload shape is the typed interface.
  ([`references/architecture/shape-b-microservice.md`](references/architecture/shape-b-microservice.md))
- **Couple services by a data contract, not code — and enforce it.** A shared invariant
  violated silently corrupts; bind it to a registry row, make changes guarded, fail loud at
  runtime.
  ([`references/architecture/external-service.md`](references/architecture/external-service.md))
- **Pick the in-DB vs out-of-process boundary by where the cost physically occurs.** CPU-only
  non-blocking work stays in-DB for locality; slow I/O or postmaster-crashing work goes out.
  ([`references/performance/governance.md`](references/performance/governance.md))
- **Security is not optional inside the trust boundary.** Pin `search_path` on every
  `SECURITY DEFINER` function, store secrets by reference, keep outbound-URL allowlists in an
  owner-only catalog. ([`references/architecture/security.md`](references/architecture/security.md))
