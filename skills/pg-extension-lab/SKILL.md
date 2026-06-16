---
name: pg-extension-lab
description: >-
  pg-extension-lab is a harness for developing, testing, benchmarking, and performance-tuning a
  PostgreSQL extension in an isolated, reproducible environment — validating observable behavior
  separately from the implementation, or designing tuning experiments, scenarios, and isolation
  tests for an existing one. Targets pure C/PGXS or
  Rust/pgrx extensions, optionally with an external microservice (Shape B) or a co-located daemon
  fronting a costly out-of-process resource like a GPU/accelerator, resident model, or JIT
  pool (Shape C). Covers the TDD test ladder (C unit / pg_regress golden-file /
  pg_isolation_regress concurrency), index benchmark strategy (matched-recall,
  SOLID-vs-INDICATIVE trust labeling, accelerator-vs-CPU crossover, cost-per-query),
  resource-vs-performance Pareto and governance, transactional-outbox async workers, external
  AI/LLM provider integration, and SECURITY hardening (search_path, ACL, secrets, SSRF). Use
  when adding a SQL-callable feature test-first, writing regression/isolation tests, designing
  or auditing a vector/index benchmark, tuning build-time vs recall/latency, or building an
  extension that needs a GPU/model/daemon or an external provider. Detailed EN/KO triggers are
  in the skill body. Not for general web/mobile/Python TDD with no PostgreSQL extension layer.
---

# pg-extension-lab — a harness to build, test, scenario, benchmark, and tune a PostgreSQL extension

**pg-extension-lab is a harness for validating a PostgreSQL extension's observable behavior in
an isolated, reproducible environment, separately from its implementation** — covering
**three architecture shapes** and **five reference categories**. Use it not only to build an
extension from scratch but to design tuning experiments, write scenarios, and run
isolation/regression tests against an existing one. Identify your shape, then open the category
that matches the request — each
category has a `README.md` index that links to dense, single-topic detail files (progressive
disclosure: this file → category README → detail file).

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
| **Architecture** | Shape B/C, Rust/pgrx, async outbox workers, external-provider integration, security. | [`references/architecture/README.md`](references/architecture/README.md) |
| **Accelerator (GPU)** | GPU/CUDA-specific build, ops, benchmark mechanics — a *specialization*, not a separate track. | [`references/accelerator/README.md`](references/accelerator/README.md) |

The one law that spans every category: **measure before you change, and label what you
measured by how much you trust it.** Red before green. Config-Pareto before code. Recall
(deterministic) is SOLID; absolute latency on a shared host is INDICATIVE.

## When to use (detailed triggers)

Triggers (EN): "pg extension TDD", "add SQL function test first", "pg_extern add",
"pg_regress test", "isolation test for concurrent insert/scan", "golden file test",
"benchmark the index", "recall vs latency", "pareto curve", "build perf", "matched recall",
"filtered ANN benchmark", "GPU vs CPU crossover", "cost per query", "out of process daemon",
"VRAM OOM fallback", "CPU shim for CI", "two-tier GPU CI", "pgrx extension", "SECURITY DEFINER
search_path", "transactional outbox", "NOTIFY LISTEN worker", "LLM provider integration",
"mock vs real E2E", "extension security review".

Triggers (KO): "pg extension 개발/테스트", "SQL 함수 테스트 먼저", "회귀 테스트 추가",
"동시성 테스트", "벤치마크 전략", "recall 벤치", "pareto 곡선", "빌드 성능", "리소스 대 성능",
"matched recall", "GPU CPU 크로스오버", "쿼리당 비용", "데몬 IPC", "VRAM OOM 폴백",
"CI용 CPU shim", "pgrx 확장", "search_path 고정", "아웃박스 패턴", "NOTIFY 워커",
"LLM provider 통합", "mock 테스트", "확장 보안 리뷰".

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

Full ladder, empty-golden mechanics, incremental-maintenance specs, failure table:
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
4. **Trust labeling.** Recall is deterministic → **SOLID** (the headline); absolute
   latency/throughput on a shared host are **INDICATIVE**. `min_ms` is never a headline.
5. **Crossover, not a ratio.** For an accelerated path (fixed overhead, better scaling), find
   the N where it beats the baseline by root-finding; report the losing region too; frame
   cost-per-query, not just latency.

Methodology + the crossover/cost companion:
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

- **Shape B (microservice).** SQL-assertion red→green, schema→service→extension order,
  multi-service Docker deploy matrix, schema-ownership single-authority, why-not-pg_regress
  for NOTIFY.
- **Rust/pgrx.** SPI↔HTTP phase separation (never hold SPI across a network call),
  `#[pg_extern]` attrs, 4 unit tests per function, dev-loop traps.
- **Async outbox worker.** Table-as-truth / NOTIFY-as-hint, `FOR UPDATE SKIP LOCKED` claim,
  status FSM + stale-pending reaper, deterministic worker tests, high-churn governance.
- **External provider.** Config registry in DB, provider abstraction + compat endpoints, the
  **data-contract invariant** (a violated shared invariant silently corrupts), mock-vs-real
  testing of a paid API.
- **Out-of-process (Shape C) + absent-dependency playbook.** Sidecar daemon concerns,
  reference-shim testing, injected resource-pressure tests, foreign-toolchain build, two-tier CI.
- **Security.** `SECURITY DEFINER` + `search_path` pinning, least-privilege ACL,
  secrets-by-reference, SSRF via owner-only registry.

Shape selection table + all six files: **[`references/architecture/README.md`](references/architecture/README.md)**.

---

## Cross-cutting principles

- **Reproducibility is non-negotiable.** Fix every seed, commit the result JSONs and
  `REPORT_*.md`, and put exact reproduce commands at the bottom of every report.
- **Self-correction in reports.** When an earlier draft over-claimed (e.g. led with `min_ms`),
  write the correction *into* the report with the reasoning.
- **Environment-agnostic test/bench files.** Local/Docker/VM differences live in Makefile
  targets and `.env`, never in the `.sql`/`.spec`/`.py` files.
- **Bottom-up implementation, small verifiable checkpoints.** Schema → C function / service →
  SQL wrapper. Each layer compiles/passes before the next.
- **The table is the source of truth; the event is only a hint.** For any async/DB-mediated
  job, persist state to a table; NOTIFY is a latency optimization — polling still recovers.
  ([`references/architecture/async-outbox.md`](references/architecture/async-outbox.md))
- **One DDL authority per object.** In an extension + worker split, exactly one component
  creates each table; the other is a consumer. The row/payload shape is the typed interface.
  ([`references/architecture/shape-b-microservice.md`](references/architecture/shape-b-microservice.md))
- **Couple services by a data contract, not code — and enforce it.** A shared invariant (e.g.
  embedding model/dim/metric) violated silently corrupts; bind it to a registry row, make
  changes guarded, fail loud at runtime.
  ([`references/architecture/external-service.md`](references/architecture/external-service.md))
- **Pick the in-DB vs out-of-process boundary by where the cost physically occurs.** CPU-only
  non-blocking work stays in-DB for locality; slow I/O or postmaster-crashing work goes out.
  ([`references/performance/governance.md`](references/performance/governance.md))
- **Security is not optional inside the trust boundary.** Pin `search_path` on every
  `SECURITY DEFINER` function, store secrets by reference, keep outbound-URL allowlists in an
  owner-only catalog. ([`references/architecture/security.md`](references/architecture/security.md))
