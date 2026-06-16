# Reference: Shape B — DB extension + microservice TDD

For the architecture where a SQL function delegates over HTTP to a separate service:

```
PostgreSQL (SQL function)
    ↓ HTTP
Service layer (FastAPI / gRPC / etc.)
    ↓ SQL
Database (schema, tables, indexes)
```

The key insight is the same as the pure-C track: **SQL-level assertions are the source of
truth.** Write them first, before any implementation exists. Each assertion maps to a
user-visible contract. The difference from Shape A is the deploy/verify mechanics (rebuild
and redeploy the service + drop volumes, vs reinstall the `.so`).

This file covers the generic HTTP-delegation flow. For the deeper realizations distilled from
a full Rust/pgrx + multi-service AI extension, see:

- **`pgrx-rust.md`** — if the extension is Rust/pgrx (SPI↔HTTP phase separation,
  `#[pg_extern]` attrs, per-function unit tests, dev-loop traps).
- **`async-outbox.md`** — if a function enqueues async work (transactional outbox +
  NOTIFY/LISTEN worker, claim/retry/reaper, deterministic worker tests).
- **`external-service.md`** — if the extension crosses a service boundary
  (registry-owned configuration, data-contract invariant, mock-vs-real testing).
- **`security.md`** — `SECURITY DEFINER` + `search_path`, ACL, secrets-by-reference,
  SSRF.

## Contents

- [Phase A — Red (test first)](#phase-a--red-test-first)
- [Phase B — Green (implement, bottom-up)](#phase-b--green-implement-bottom-up)
- [Phase C — Verify](#phase-c--verify)
- [Failure modes (Shape B)](#failure-modes-shape-b)
- [Design principles](#design-principles)

---

## Phase A — Red (test first)

### 1. Identify the SQL contract

```sql
SELECT ai.search('query', 'pipeline', 5, '{"category": "db"}');
-- → TABLE of (chunk_id, content, score, source, metadata)
```

### 2. Write the SQL test file

`<test-dir>/<feature>.sql`, `\set ON_ERROR_STOP on` at the top. Every file the same shape:

```sql
\set ON_ERROR_STOP on

-- Setup: fixtures (pipelines, data)
-- Wait loop if async ingestion is involved:
DO $$ ... LOOP ... END $$;

-- ASSERTION 1: function exists
SELECT EXISTS(SELECT 1 FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
  WHERE n.nspname='<schema>' AND p.proname='<function>') AS function_exists;

-- ASSERTION 2: returns expected rows/values
SELECT COUNT(*) > 0 AS returns_rows FROM <schema>.<function>(...);

-- ASSERTION 3: edge case
SELECT ... AS edge_case_ok;

-- Cleanup (idempotent)
DELETE FROM ... WHERE ...;
SELECT '<feature> TDD test complete — all assertions passed' AS result;
```

Principles: one boolean `SELECT` per assertion; descriptive column names
(`filter_db_returns_row`, not `result`); cleanup at the end; `ON_ERROR_STOP` so the first
failure aborts with the exact error.

### 3. Add a runner entry point

The runner just reaches a running DB + service, executes the SQL, exits non-zero on failure.

```makefile
run-<feature>-real:
	@test -n "$(API_KEY)" || (echo "ERROR: API_KEY not set"; exit 1)
	$(START_SERVICES)
	$(BOOTSTRAP)
	$(WAIT_READY)
	$(call RUN_TEST,<feature>.sql)
```

Remote: `psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f test/sql/<feature>.sql`.
CI: the same psql line as a GitHub Actions step with `DATABASE_URL` from secrets.
The `.sql` file never changes — only how it is invoked.

### 4. Run red — confirm failure

Expected: `function <schema>.<function> does not exist` or an assertion returning `f`.
**Do not proceed to Phase B until red is confirmed.**

---

## Phase B — Green (implement, bottom-up)

| Layer | What changes | Example |
|---|---|---|
| **Schema** | tables, columns, indexes, pure SQL functions | `ADD COLUMN`, `CREATE OR REPLACE FUNCTION` |
| **Service** | HTTP endpoint, business logic | FastAPI `@app.post("/feature")` |
| **Extension API** | DB function that calls the service | `#[pg_extern]` / PL/pgSQL wrapper |
| **Client** | HTTP client | Rust `call_feature()` / `requests.post()` |

One layer at a time; each compiles/type-checks before the next.

- **Schema:** `IF NOT EXISTS` columns (idempotent), indexes alongside; test with
  `psql -c "SELECT ..."` before wiring the service.
- **Service:** request/response models first; new endpoint next to similar ones; run
  `pyright`/`mypy`.
- **Extension API:** match the exact signature the SQL test calls; defaults must match
  `ALTER FUNCTION` defaults; add to the `SET search_path` block; unit-test happy path +
  missing config + edge.

### Deploy to the test target

After changing any layer, the running environment must pick up the new code.

```bash
# Local Docker Compose
docker compose build <service>
docker compose down -v          # REQUIRED when schema changes — named volumes copy from
make run-<feature>-real         # the image only on first creation, so old schema persists

# Remote (SSH)
rsync -az src/ user@host:/app/src/ && ssh user@host "systemctl restart <service>"
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f test/sql/<feature>.sql

# CI (push-to-deploy)
git push origin feature-branch  # triggers CD; wait, then run the test
```

Regardless of target: the SQL test file is environment-agnostic; all environment wiring
lives in the runner.

---

### Multi-service deploy matrix

With several containers (pg + builder + worker + service + mock), what you rebuild depends on
what changed — rebuilding everything every time is slow and rebuilding too little serves
stale code:

| Changed | Action |
|---|---|
| extension Rust/C | `cargo pgrx install` (or `make install`) in the builder → `DROP EXTENSION … CASCADE; CREATE EXTENSION` → restart the worker (it recreates its schema on boot) |
| service `.py` | `docker compose build <service>` → `up -d --force-recreate <service>` (force-recreate so it picks up changed env) |
| SQL schema | `docker compose down -v` (drop named volumes — they copy schema from the image only on first creation) |
| docs only | nothing |

### Schema ownership — exactly one DDL authority per object

In an extension + worker split, decide who *creates* each table and never blur it:

- The **extension** owns its namespace: `CREATE EXTENSION` creates schema `ai` and the
  registry/queue tables via `extension_sql!` with ordered `requires =` deps, and registers
  each with `pg_extension_config_dump(...)` so its *data* survives `pg_dump`. Verify with an
  automated `pg_dump`/restore round-trip test.
- The **worker** creates only its *own* artifact tables (`documents`, `chunks`) and is a
  *consumer/updater* of the extension's tables (`ai.results`, `ai._outbox`) — never their
  creator. This removes DDL races and divergent definitions; the only coupling between the two
  languages becomes the **row/payload shapes** (the typed interface).
- The worker must NOT `CREATE SCHEMA ai` — that produces `schema ai is not a member of
  extension`. A standalone-mode fallback (no extension installed) lives in a *separate*
  migration file so it can't blur ownership.

## Phase C — Verify

```bash
make run-<feature>-real 2>&1 | tail -10     # all assertions 't'; final "complete" line
make run-<main-e2e>-real 2>&1 | grep complete  # regression: original E2E still passes
pyright && cargo check --lib                 # type check: zero errors before commit
```

### Verification ladder with change-type skip conditions

A full verification is build → unit → type-check → mock-E2E. Skip the stages a change can't
affect, so the dev loop stays fast:

| Changed | Run |
|---|---|
| only docs | nothing |
| only `services/*.py` | type-check + mock-E2E (skip Rust build + unit) |
| only `extension/*.rs` | build + unit + mock-E2E (skip Python type-check) |
| schema / cross-cutting | the whole ladder |

Stop on first failure. The mock-E2E (no API cost) is the gate for "safe to commit"; one real
run is an optional final sanity check.

### Why the async E2E does NOT use pg_regress

`pg_regress` creates an isolated `contrib_regression` database, but the worker `LISTEN`s on
the application database — and **NOTIFY is per-database**, so the signal never arrives and the
test hangs. Run the async E2E with `psql -f <feature>.sql` against the real app DB (a Makefile
`run-*` target). See `async-outbox.md`.

---

## Failure modes (Shape B)

| Error | Cause | Fix |
|---|---|---|
| `function does not exist` in green | service rebuilt but not extension | rebuild extension + drop volumes |
| `column does not exist` | schema change not picked up | `docker compose down -v` |
| `different vector dimensions` | new embedding dim, old index | drop index, recreate with new dim |
| `variable conflict` | PL/pgSQL OUT param vs column name | `#variable_conflict use_column` |
| missing protocol error | `BASE_URL=""` instead of unset | strip empty env vars at startup |
| named volume serving old `.so` | image rebuilt, volume not refreshed | `docker compose down -v` |

---

## Design principles

- **Why SQL assertions, not unit tests of the code?** The contract is what SQL callers see.
  A mocked unit test proves logic; a SQL assertion proves deployed behavior — schema,
  security definer, search_path, type coercions.
- **Why bottom-up?** Each layer depends on the one below; bottom-up gives small verifiable
  checkpoints instead of "nothing works until the last layer."
- **Why `docker compose down -v`?** Named volumes copy from the image on first creation;
  after rebuilding, old volume content is stale. Dropping volumes forces a fresh copy.
- **Why `DEFAULT '{}'` for optional JSONB params?** Backward compatibility — existing
  callers that omit the param keep working; `metadata @> '{}'` is always true (a natural
  "no filter" sentinel).
