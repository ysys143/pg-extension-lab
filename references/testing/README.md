# Testing a PostgreSQL extension

How to test an extension test-first, across the three levels PostgreSQL gives you, locally or
on remote/Docker hardware. Read this when you are **adding a SQL-callable feature, an access-
method behavior, or a concurrency guarantee** and want the red→green discipline.

| File | What it covers |
|---|---|
| [`test-ladder.md`](test-ladder.md) | The full ladder: standalone **C unit tests** → **pg_regress** golden-file regression (the red→green core) → **pg_isolation_regress** concurrency specs (incl. incremental-maintenance patterns). Plus the absent-device testing playbook pointer, false-done / fail-closed meta-rules, and the local/Docker/VM runner matrix + failure table. |

Related, in other categories:
- Rust/pgrx unit-test conventions (4 per function) — [`../architecture/pgrx-rust.md`](../architecture/pgrx-rust.md)
- Deterministic worker/async tests (outbox, semaphore, loop) — [`../architecture/async-outbox.md`](../architecture/async-outbox.md)
- Testing a core that needs absent hardware (reference shim, injected OOM, two-tier CI) — [`../architecture/out-of-process.md`](../architecture/out-of-process.md)
- Mock-vs-real E2E for a paid external API — [`../architecture/external-service.md`](../architecture/external-service.md)
