# Testing harness asset

Copy this folder into a PostgreSQL extension repo, then move files into the repo's normal
layout. Edit bracketed placeholders before running.

## Adapt

- `Makefile.pgxs.fragment`: merge into a C/PGXS extension Makefile.
- `Makefile.pgrx.fragment`: copy commands into a pgrx project Makefile or CI job.
- `test/sql/smoke.sql` and `test/expected/smoke.out`: rename `smoke` and replace SQL calls.
- `test/specs/concurrent_insert_scan.spec`: replace table/index/function names.
- `sql/restrict_acl.sql`: replace schema and extension owner role.
- `.github/workflows/ci-cpu-reference.yml`: edit package names and PostgreSQL versions.

Keep SQL/spec files environment-agnostic. Put host, port, device, and image differences in
Makefile targets or CI environment variables.

