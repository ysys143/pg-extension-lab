# Reference: the Rust / pgrx realization

When the extension is written in Rust with `pgrx` (cargo-pgrx) rather than C/PGXS, the TDD
discipline and architecture shapes are unchanged — but the language brings its own
conventions, traps, and a very testable unit layer. This file is the pgrx-specific layer;
read it alongside `../testing/test-ladder.md` (the test ladder applies as-is: `cargo pgrx test` is the
unit/regression layer).

---

## Contents

- [Do I even need a compiled extension? (ADR-002 checklist)](#do-i-even-need-a-compiled-extension-adr-002-checklist)
- [The load-bearing discipline: SPI-then-network phase separation](#the-load-bearing-discipline-spi-then-network-phase-separation)
- [`#[pg_extern]` attribute discipline](#pg_extern-attribute-discipline)
- [pgrx 0.18 SPI conventions](#pgrx-018-spi-conventions-the-ones-that-bite)
- [Unit tests: minimum four per function](#unit-tests-minimum-four-per-function)
- [Two reusable patterns surfaced by pgrx code](#two-reusable-patterns-surfaced-by-pgrx-code)
- [pgrx dev-loop traps (Docker)](#pgrx-dev-loop-traps-docker)

---

## Do I even need a compiled extension? (ADR-002 checklist)

A compiled `.so` (C or pgrx) is only *required* for: GUC registration, background workers,
C-level hooks, or type-system integration (operators, access methods). If you need none of
those, plain SQL / PL/pgSQL UDFs suffice and skip the whole build. Decide this first — a
build you don't need is pure cost.

---

## The load-bearing discipline: SPI-then-network phase separation

A `#[pg_extern]` function that both touches the database (SPI) and calls out over the network
must do them in **two ordered phases** — never hold SPI open across a blocking call:

```rust
fn search_impl(query: &str, pipeline: &str) -> ReturnType {
    // Phase 1 — all SPI/catalog reads, then SPI closes
    let pipeline_cfg = lookup_pipeline(pipeline)
        .unwrap_or_else(|| error!("ai.search: unknown pipeline '{}'", pipeline));
    let (base_url, api_key_env) = lookup_endpoint(&pipeline_cfg.embed_model)
        .unwrap_or_else(|| error!("ai.search: no endpoint for model"));

    // Phase 2 — blocking HTTP, OUTSIDE any SPI scope
    let api_key = api_key_env.and_then(|k| std::env::var(k).ok());
    call_search(&base_url, api_key.as_deref(), query)
        .unwrap_or_else(|e| error!("ai.search: {}", e))
}
```

Why it matters generally: holding SPI (or a transaction snapshot) open across a slow network
call pins resources and blocks vacuum/locks for the call's full duration. Resolve all
config from the catalog first, then leave SPI before the I/O. (Applies to any extension that
calls out — C or Rust.)

---

## `#[pg_extern]` attribute discipline

```rust
#[pg_extern(name = "search", schema = "ai", volatile, parallel_unsafe, security_definer)]
```

- `security_definer` — runs with the definer's privileges so callers needn't own the
  catalog tables; **mandates** `search_path` pinning (see `security.md`).
- `parallel_unsafe` — anything doing network I/O or non-deterministic work must not run in a
  parallel worker.
- `volatile` — declare correctly; a network-calling function is never `immutable`/`stable`.
- **Every** function gets an explicit `search_path` set in the `extension_sql!` block:
  `ALTER FUNCTION ai.search(...) SET search_path = pg_catalog, public, ai, pg_temp;` and the
  impl symbol is listed in that block's `requires` array.

---

## pgrx 0.18 SPI conventions (the ones that bite)

- Use `value.into()` for SPI args, **not** `value.into_datum().into()`.
- DML needs `Spi::run_with_args` — `client.select()` is read-only and silently does nothing
  for INSERT/UPDATE.
- `pgrx::Uuid.0` is private — to embed a UUID in JSON, cast in SQL: `$1::text` inside
  `jsonb_build_object(...)`.
- `TableIterator` return type: `TableIterator<'static, (name!(col, Type), ...)>`.

---

## Unit tests: minimum four per function

`cargo pgrx test` runs `#[pg_test]` functions inside a real PG. Scaffold at least four per
new function so behavior and failure modes are both pinned:

1. `test_<name>_happy_path` — basic success.
2. `test_<name>_panics_on_missing_<dep>` — `#[should_panic]`, missing pipeline/config.
3. `test_<name>_panics_on_missing_<dep2>` — `#[should_panic]`, missing endpoint/model.
4. a **side-effect** assertion — the `ai.results` row, the `ai._outbox` row, or the exact
   return type/shape.

The failure-mode tests matter most: a `security_definer` function that errors cleanly on
misconfiguration (rather than leaking a confusing internal error) is part of its contract.

---

## Two reusable patterns surfaced by pgrx code

- **Cap at the source, not at the sink.** When a GUC bounds a result size
  (`ai.max_search_results`), clamp the requested limit *before* the HTTP/SPI call so you never
  deserialize an oversized response; keep a sink-side cap only as defense-in-depth. This
  bounds both the upstream response *and* the local heap (a Rust `Vec` lives outside
  `work_mem`, so a GUC is the only lever — see `../performance/governance.md`).
- **Identifier length budget.** PostgreSQL identifiers — including NOTIFY channel names — are
  capped at `NAMEDATALEN` (64). Any scheme that embeds an id in a channel/identifier must
  prove it fits (e.g. `"ai_" + 36-char UUID = 39 < 64`).

---

## pgrx dev-loop traps (Docker)

| Symptom | Cause | Fix |
|---|---|---|
| `cargo pgrx test` Unix-socket error | PG can't create a socket on a macOS Docker bind-mount | run as a `dev` user with `CARGO_TARGET_DIR=/home/dev/target` (off the mount) |
| `cargo pgrx test` SIGKILL / OOM | Docker Desktop memory too low | give Docker ≥ 8 GB; retry warms the cache |
| `CREATE EXTENSION IF NOT EXISTS` keeps the OLD version | `cargo pgrx install` copies files only; `IF NOT EXISTS` is a no-op on an existing extension | always `DROP EXTENSION ... CASCADE` then `CREATE EXTENSION` |
| `schema X is not a member of extension` | the schema was created outside the extension, or a leftover from a prior run | `DROP EXTENSION ... CASCADE` (drops the owned schema), then recreate |

The DROP-then-CREATE upgrade rule is the pgrx equivalent of the C-extension
"reinstall the `.so` and reconnect" — the running backend caches the loaded library and the
catalog caches the old definition.
