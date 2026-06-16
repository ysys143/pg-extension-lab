# C/PGXS internals checklist

Read this for pure C extensions, index access methods, triggers, background workers, or PGXS
build/debug work. These are PostgreSQL backend contracts, not style preferences.

## SRF and SPI memory lifetime

- For set-returning functions, prefer materialize mode unless streaming is required. Allocate
  returned tuples in the per-query context, not a transient SPI or function-call context.
- Do not keep SPI tuple/table pointers after `SPI_finish()`. Copy every Datum or text value
  that must survive the SPI scope.
- PostgreSQL catalog `name` is not `text`. Use the correct SPI input/output type or cast
  explicitly in SQL. Silent assumptions here become confusing cache/catalog bugs.

## Trigger tuple ownership

- Treat `tg_trigtuple` and `tg_newtuple` as PostgreSQL-owned. Return the correct tuple pointer
  for BEFORE triggers and never free backend-owned trigger tuples.
- If a trigger changes data, build a replacement tuple with PostgreSQL APIs and document
  whether unchanged columns preserve original Datum/isnull state.

## Background workers and network I/O

- Split worker work into three phases: claim DB work, perform network/device work outside SPI,
  then persist the result in a fresh transaction.
- Table state is the source of truth. NOTIFY, latch wakeups, and socket events are hints.
- Dynamic background-worker tests often need an integration harness; unit tests should exercise
  claim/retry/reaper logic without requiring postmaster process management.

## Index AM, WAL, and PostgreSQL version drift

- Native index AMs are C-first. pgrx can wrap SQL-callable functions well, but AM callbacks,
  WAL records, page layout, and buffer locking still require C-level PostgreSQL discipline.
- Use `GenericXLog` only after writing down the invariants for page initialization, redo safety,
  and crash-restart visibility.
- PostgreSQL major versions change AM build APIs. PostgreSQL 17's index-build scan path is a
  known compatibility checkpoint; pin supported versions and compile against all of them in CI.

## Build portability traps

- Delete stale `.o` files when changing compiler flags or PostgreSQL headers.
- Avoid `-march=native` in release or portable Docker builds; it leaks host CPU assumptions.
- Build inside the oldest supported runtime image when distributing binaries. A newer GLIBC in
  the build image can produce an extension that fails to load on the deployment host.

