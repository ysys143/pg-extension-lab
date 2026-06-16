# Reference: async jobs — transactional outbox + NOTIFY/LISTEN worker

A common Shape B sub-architecture: a SQL function enqueues work, an external worker does it
asynchronously, and the caller polls (or waits) for the result. Done naively this loses jobs
and double-processes them. The durable pattern, and how to test it deterministically.

```
ai.<fn>()  --INSERT result(pending) + INSERT _outbox + pg_notify-->  PostgreSQL
worker: LISTEN channel  ──claim outbox row──>  do work  ──UPDATE result(done|error)──>  client polls result
```

---

## Contents

- [The pattern](#the-pattern)
- [The async-kickoff SQL gotchas](#the-async-kickoff-sql-gotchas)
- [Two-step retention for high-churn queue tables](#two-step-retention-for-high-churn-queue-tables)
- [Testing the worker deterministically](#testing-the-worker-deterministically-no-db-no-network-no-paid-api)
- [Worker resource levers (outside PG's standard knobs)](#worker-resource-levers-outside-pgs-standard-knobs)

---

## The pattern

- **The result table is the single source of truth; NOTIFY is only a hint.** Persist job
  state to `ai.results` (status `pending`); use `pg_notify` purely as a latency optimization.
  If the signal is lost (worker was down, connection dropped), the row still exists and the
  worker recovers it by polling. This also makes the system PgBouncer-transaction-mode
  compatible (LISTEN needs a persistent connection; polling does not) and lets clients choose
  NOTIFY *or* polling freely.
- **Transactional outbox.** The enqueue writes the `ai._outbox` row in the *same transaction*
  as the result row, so the job can never be "notified but not durably recorded." The NOTIFY
  fires after commit.
- **Atomic claim with `FOR UPDATE SKIP LOCKED`** — the canonical concurrent-safe queue claim,
  many workers, no double-processing, no lock waiting:
  ```sql
  UPDATE ai._outbox SET taken_at = now()
  WHERE id = (SELECT id FROM ai._outbox WHERE taken_at IS NULL
              ORDER BY created_at LIMIT 1 FOR UPDATE SKIP LOCKED)
  RETURNING ...;
  ```
  `taken_at IS NULL` is the unclaimed predicate.
- **Status state machine: `pending → done | error`,** with `finished_at` set on the terminal
  transition. Capture the error **as data**, not just a log line: wrap the handler in
  try/except and write `str(exc)` into `ai.results.error_msg`, so failures are queryable
  through the same table clients already poll.
- **Stale-pending reaper.** Every job row gets a deadline column —
  `pending_timeout_at timestamptz NOT NULL DEFAULT now() + interval '5 minutes'` — plus a
  **partial index** `WHERE status='pending'` so the reaper scan is cheap. A crashed/lost task
  can't stay pending forever: the cleanup pass flips expired rows to `error`.
- **Recovery-on-restart is structural, not coded.** Because NOTIFY is only a hint and the
  outbox row persists with `taken_at IS NULL`, a worker that was down during the NOTIFY just
  claims the unclaimed row on its next poll — no separate replay path. The LISTEN loop
  auto-reconnects with a backoff.
- **Fail loud on contract drift.** On startup the worker checks the existing
  `ai.chunks.embedding` width via `pg_attribute` and *raises* if it differs from the
  configured dimension — because `CREATE TABLE IF NOT EXISTS` would silently skip and later
  INSERTs would fail confusingly. Runtime-enforce the invariants that DDL idempotency hides.

---

## The async-kickoff SQL gotchas

- **Per-database NOTIFY.** `NOTIFY`/`LISTEN` channels are scoped to a *database*. This breaks
  `pg_regress`-based E2E: `pg_regress` creates an isolated `contrib_regression` DB, but the
  worker LISTENs on the app DB — the NOTIFY never arrives, the test hangs. Run the async E2E
  with `psql -f` against the *real* DB the worker listens on (a Makefile `run-*` target), not
  `pg_regress`. (See `shape-b-microservice.md`.)
- **COMMIT inside a `DO`/PL block.** A `DO` block is one transaction; an enqueue INSERT that
  isn't committed is invisible to the worker. Emit an explicit `COMMIT;` right after the
  kickoff (PostgreSQL 11+) so the worker can see the row.
- **psql `:'var'` substitution does not reach inside `$$ ... $$`.** Receive function return
  values with a PL/pgSQL `DECLARE` instead of psql variable interpolation inside the block.

---

## Two-step retention for high-churn queue tables

`ai._outbox` and `ai.results` are high-churn. Govern them:

- **Tune autovacuum per-table** (e.g. `autovacuum_vacuum_scale_factor = 0.01`) — the global
  default leaves dead tuples to pile up on a hot queue.
- **Run a cleanup loop** on an interval: (1) expire timed-out `pending` rows to `error`, then
  (2) delete old terminal rows past a retention window. Order matters and is intentional:
  PL/pgSQL DMLs run sequentially, so step 2 sees step 1's transitions — and freshly-expired
  rows survive until the retention window elapses (don't delete what you just transitioned in
  the same pass).

---

## Testing the worker deterministically (no DB, no network, no paid API)

The worker is the hardest part to test; these patterns make it ordinary unit tests.

- **Stub the heavy runtime in `conftest` before import.** The service reads env and imports
  clients at module top-level, so the test must pre-seed them:
  ```python
  for name in ("psycopg", "fastapi", "openai", "httpx", "pdf_lib"):
      sys.modules.setdefault(name, MagicMock())
  os.environ["DATABASE_URL"] = "postgres://test"   # before `import main`
  ```
- **Extract one iteration out of every infinite loop.** A `while True: ...` loop delegates to
  a `_run_once()` pass. Tests drive it by **monkeypatching `asyncio.sleep` to raise
  `CancelledError` on the Nth call** — turning an unbounded loop into a counted, deterministic
  one. Reusable for any poller/reaper/listener.
- **Test loop-survives-error explicitly.** First pass raises, second succeeds, third cancels
  → assert the loop did not die. A background loop must catch-log-continue on per-iteration
  errors (only `CancelledError` breaks); prove a transient failure doesn't kill the daemon.
- **Test the concurrency bound with an instrumented fake + peak counter.** Replace the handler
  with a fake that increments an `active` counter, records `peak`, sleeps to force overlap;
  assert `peak <= limit` and `done == N`. To prove the semaphore is *released on failure*
  (no deadlock), use a **1-slot** semaphore and a handler that always raises — the second
  call can only complete if the first released despite raising.
- **Test batching for every edge:** call-count = `ceil(N/B)`, order preserved across batches,
  exact-multiple boundary, empty input = zero calls, correct slice per call. If the code does
  a function-local import (`from embedder import embed` inside the function), patch
  `sys.modules['embedder']`, not the symbol.
- **Fake the async DB connection as an async context manager** (`__aenter__/__aexit__` with
  `AsyncMock` `execute`/`commit`); assert specific SQL substrings appear in
  `execute.call_args_list` and that `commit` was awaited exactly once — the reusable shape for
  "prove this path committed."

---

## Worker resource levers (outside PG's standard knobs)

The worker runs outside the PG backend, so PG's `work_mem`/`max_connections` don't bound it —
give it dedicated env levers and document them next to `postgresql.conf`:

- **Semaphore backpressure** (`MAX_CONCURRENT_TASKS`): the worker has no connection pool, so a
  NOTIFY burst would open unbounded connections and exhaust `max_connections`. A semaphore
  caps concurrent events; the excess waits (backpressure).
- **Batch streaming** (`EMBED_BATCH_SIZE`): stream embed→insert in batches so peak memory is
  `batch_size × dim × 4 bytes` *independent of document length*, not the whole document.
- **Cleanup interval** (`CLEANUP_INTERVAL_SECONDS`): how often the retention loop runs.
