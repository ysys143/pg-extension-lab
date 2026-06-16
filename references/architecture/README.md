# Architecture shapes & cross-cutting concerns

How the extension is structured, and the language/integration/security concerns that follow
from the shape. Start by identifying your **shape**, then read the matching files.

## Pick your shape

| Shape | The extension… | Deploy/verify | Primary files |
|---|---|---|---|
| **A — pure in-process** | is a `.so` doing everything in the backend (custom AM, hooks, `pg_extern`) | reinstall `.so`, reconnect | (testing + performance categories; pgrx if Rust) |
| **B — extension + microservice** | delegates over HTTP to a service that **owns data** | rebuild/redeploy service, drop volumes | [`shape-b-microservice.md`](shape-b-microservice.md), [`async-outbox.md`](async-outbox.md), [`external-service.md`](external-service.md) |
| **C — extension + sidecar daemon** | fronts a costly **process-bound resource** (GPU context, resident model, JIT pool); daemon owns the resource, **not data** | restart daemon, reconcile orphans | [`out-of-process.md`](out-of-process.md) |

Shapes compose: a Rust/pgrx Shape-B extension with an async worker uses `pgrx-rust.md` +
`shape-b-microservice.md` + `async-outbox.md` + `external-service.md` + `security.md`.

## Files

| File | What it covers |
|---|---|
| [`shape-b-microservice.md`](shape-b-microservice.md) | Shape B TDD: SQL-assertion red→green, schema→service→extension order, multi-service Docker deploy matrix, verification ladder with skip conditions, schema-ownership single-authority, why-not-pg_regress for NOTIFY. |
| [`pgrx-rust.md`](pgrx-rust.md) | Rust/pgrx realization: SPI↔HTTP phase separation, `#[pg_extern]` attrs, SPI conventions, 4-unit-tests-per-function, dev-loop traps, "do I need a compiled extension." |
| [`async-outbox.md`](async-outbox.md) | Transactional outbox + NOTIFY/LISTEN worker: table-as-truth, `FOR UPDATE SKIP LOCKED`, status FSM, stale-pending reaper, deterministic worker testing, high-churn governance. |
| [`external-service.md`](external-service.md) | Calling a paid/external provider: config registry, provider abstraction + compat endpoints, the **data-contract invariant**, mock-vs-real testing, RAG/LLM benchmark methodology. |
| [`out-of-process.md`](out-of-process.md) | Shape C + the absent-dependency playbook: sidecar daemon concerns, reference-shim testing, injected resource-pressure tests, foreign-toolchain build, two-tier CI. |
| [`security.md`](security.md) | `SECURITY DEFINER` + `search_path` pinning, least-privilege ACL, secrets-by-reference, SSRF via owner-only registry, documented threat model. |
