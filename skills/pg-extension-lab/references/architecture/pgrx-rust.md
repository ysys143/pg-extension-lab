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
- [Support functions with `internal` args (parser / index AM / operator)](#support-functions-with-internal-args-parser--index-am--operator)
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

## Support functions with `internal` args (parser / index AM / operator)

Some PG support functions — text-search parser (`prsstart`/`gettoken`/`prsend`), GiST/GIN
support, operator support — take/return the `internal` SQL type and are called by PG core, not
from SQL. pgrx has no dedicated helper, but `#[pg_extern]` + `pgrx::Internal` covers them
without hand-writing fcinfo/`PG_FUNCTION_INFO_V1` (pgrx still generates the finfo, `#[pg_guard]`,
and SQL):

- `fn f(arg: Internal, n: i32) -> Internal` generates `f(internal, integer) RETURNS internal`.
- Pointer arg → bytes: `let p = arg.unwrap().unwrap().cast_mut_ptr::<u8>();` then `from_raw_parts`.
  Persistent state across calls: `arg.get_mut::<State>()`.
- Create state with **`Internal::new(state)`** — it palloc's in `CurrentMemoryContext` and
  **drops on context delete**, so there is *no leak even on `ereport`/longjmp*. This is the
  memory-safety answer; never return a Rust `Box`/reference PG would never free. Values you hand
  back (e.g. token bytes via `*t`/`*tlen`) must live in that context-managed state — PG copies them.
- Register the catalog object in `extension_sql!(r#"CREATE TEXT SEARCH PARSER …"#, requires = [f, …])`
  so it is created after the functions.

**Gotcha — the SQL return type must match what PG *validates*, not what's natural.** A TS
parser's `gettoken` must be `RETURNS internal` (PG's own `CREATE TEXT SEARCH PARSER` doc example
and `DefineTSParser` require it); returning `i32` from `#[pg_extern]` yields `RETURNS integer`
and `DefineTSParser` rejects it. Carry the token-type int *inside* an Internal instead:
`Internal::from(Some(pg_sys::Datum::from(lextype as usize)))` — PG's `DatumGetInt32` reads the
datum. Reuse `pg_catalog.prsd_lextype` / `prsd_headline`, emit the standard type ids
(2 = word, 12 = blank). Validate input is UTF-8 at the boundary → `ereport` on failure; let
`#[pg_guard]` convert panics to `ereport` (never unwind across the ABI).

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
| `[profile.*]` ignored / cargo warns (pgrx needs `panic = "unwind"`) | profile tables in a *workspace member* are ignored — only the workspace **root** applies | move `[profile.dev]`/`[profile.release]` to the root `Cargo.toml`. Note: `cargo pgrx new` inside a workspace writes them into the new member crate — relocate them and add the crate to `members` |

The DROP-then-CREATE upgrade rule is the pgrx equivalent of the C-extension
"reinstall the `.so` and reconnect" — the running backend caches the loaded library and the
catalog caches the old definition.
