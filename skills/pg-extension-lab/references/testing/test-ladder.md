# Reference: the PostgreSQL-extension test ladder

Three levels, cheapest first. Run them as a ladder: a unit failure is faster to diagnose
than a regression failure, which is faster than an isolation failure. Wire all three into
`make` so one command runs each level.

```
make unit                      # standalone C binaries, no PG server
make installcheck              # pg_regress: golden-file SQL diff
make installcheck-isolation   # pg_isolation_regress: concurrency interleavings
```

> **pgrx variant.** With cargo-pgrx the same ladder maps to: pure-Rust `cargo test` (unit, no PG)
> → `cargo pgrx test pgNN` (the regression layer — `#[pg_test]` assertions run in a real PG, each
> in a rolled-back transaction) → isolation specs. The red→green move is **assertion-based, not
> golden-file**: write a `#[pg_test]` asserting the SQL-visible behavior of a *not-yet-created*
> object (RED), implement via `extension_sql!` (GREEN) — there is no `.out` to promote. Golden-file
> diffs remain available via the `tests/pg_regress/` dir that `cargo pgrx new` scaffolds. Details:
> `../architecture/pgrx-rust.md`.

---

## Contents

- [Level 1 — Unit tests (standalone C)](#level-1--unit-tests-standalone-c)
- [Level 2 — Regression tests (pg_regress, golden-file)](#level-2--regression-tests-pg_regress-golden-file)
- [Level 3 — Isolation tests (pg_isolation_regress, concurrency)](#level-3--isolation-tests-pg_isolation_regress-concurrency)
- [Cores that need an absent device, deterministic resource tests, CI tiering](#cores-that-need-an-absent-device-deterministic-resource-tests-and-ci-tiering)
- [Remote / Docker execution](#remote--docker-execution)
- [Failure-mode table](#failure-mode-table-extension-testing)

---

## Level 1 — Unit tests (standalone C)

Extract the pure algorithm logic (distance kernels, neighbor selection, ID/arena math)
into self-contained `test/unit/*.c` files that **do not link PostgreSQL**. Stub the few PG
types you need. This catches logic bugs in milliseconds without a running cluster.

```makefile
.PHONY: unit
unit:
	$(CC) $(CFLAGS) -o test/unit/test_index_scan  test/unit/test_index_scan.c
	$(CC) $(CFLAGS) -o test/unit/test_index_build test/unit/test_index_build.c
	test/unit/test_index_scan
	test/unit/test_index_build
```

Use unit tests for anything you can isolate from `palloc`/buffer manager/catalog. If a
function is too entangled with PG internals to unit-test, that is often a sign it should be
split.

---

## Level 2 — Regression tests (pg_regress, golden-file)

`pg_regress` runs each `test/sql/<name>.sql` through `psql` and **diffs stdout against
`test/expected/<name>.out`**. Identical = pass; any diff = fail. The actual output is
written to `test/results/<name>.out`.

### The red→green golden-file cycle (the core TDD move)

1. **Write the SQL test.** `test/sql/<feature>.sql`, starting with `\set ON_ERROR_STOP on`.
   Assert what a SQL caller sees: catalog registration, GUC existence, row counts, recall
   thresholds, error messages on edge cases.
   ```sql
   \set ON_ERROR_STOP on
   CREATE EXTENSION my_extension;
   -- AM registered?
   SELECT amname FROM pg_am WHERE amname = 'my_index_am';
   -- GUC exists?
   SHOW my_extension.enable_hook;
   -- behavior:
   SELECT count(*) > 0 AS returns_rows FROM ... ORDER BY embedding <-> '[...]' LIMIT 10;
   ```
2. **Register it.** Add `<feature>` to the `REGRESS` list in the Makefile (order matters —
   keep the tier order: `smoke` → `tier1_*` → `tier2_*` → `recall_*` → `no_regression`).
3. **Start with an EMPTY / minimal golden.** Create `test/expected/<feature>.out` empty (or
   with only a leading comment). Run `make installcheck`. The diff (or the
   `... does not exist` error) is your RED. **Confirm red before implementing.**
4. **Implement** (bottom-up — see SKILL.md cross-cutting principles).
5. **Promote the golden.** Once the behavior is correct, copy `test/results/<feature>.out`
   to `test/expected/<feature>.out`. Re-run — now GREEN. Inspect the promoted golden by eye;
   a golden file is only as trustworthy as the run that produced it.

> Never write the expected `.out` by hand before the implementation passes. The empty-start
> discipline is what makes this real TDD rather than after-the-fact snapshotting.

### Tier conventions

| Tier | Scope | Examples |
|---|---|---|
| `smoke` | extension loads, objects exist | AM in `pg_am`, GUCs present, `CREATE EXTENSION` |
| `tier1_*` | one behavior in isolation | a single hook fires |
| `tier2_*` | one feature surface | auxiliary edges, code cache (+ DML, + evict), build params (memory, parallel, two-pass), search budget, auto tuning, scan stats, inline payloads, diversify, emission order |
| `recall_*` | quality gates | `recall_filter`, `recall_bridge_width`, `recall_insert` |
| `no_regression` | catch-all guard | behaviors that must never change |

---

## Level 3 — Isolation tests (pg_isolation_regress, concurrency)

Concurrency bugs do not appear in single-session regression tests. A `.spec` declares
multiple sessions and the steps to interleave; `pg_isolation_regress` permutes them and
diffs against a golden `.out`.

```
# test/specs/concurrent_insert_scan.spec
setup    { CREATE EXTENSION ...; CREATE TABLE ...; CREATE INDEX ... USING my_index_am ...; }
teardown { DROP TABLE ... CASCADE; }

session "scanner"
step "begin_scan" { BEGIN; }
step "run_scan"   { SELECT count(*) FROM ( SELECT id FROM t WHERE bucket < 3
                    ORDER BY embedding <-> '[...]' LIMIT 10 ) s; }
step "commit"     { COMMIT; }

session "writer"
step "insert_match" { INSERT INTO t(bucket, embedding) VALUES (1, '[...]'); }
```

Register specs in the `ISOLATION` Makefile list. Use isolation tests for: scan consistency
under concurrent insert (snapshot semantics — a row inserted before the scan's snapshot
must appear, after must not), build under concurrent DML, cache insert/evict racing a scan,
concurrent auxiliary-structure build. The golden `.out` captures the *expected* result of every
permutation, including which steps block.

---

### Incremental-maintenance correctness patterns

If the extension supports incremental maintenance (delta/pending buffers, tombstones,
compaction, concurrent reindex), these correctness properties live in isolation specs — a
single-session golden file cannot express them. Patterns worth copying:

- **Test BOTH orderings of maintenance vs. the operation** — each exercises a different code
  path. e.g. `reindex_concurrent_delete`: perm A = DELETE+compact *then* REINDEX (dead row
  excluded at build time) vs perm B = REINDEX *then* DELETE+compact (tombstone-filter +
  heap-recheck path). Don't assume one permutation covers the feature.
- **Verify MVCC visibility *through* the path, not just "delete works".** A committed DELETE
  must vanish for a NEW snapshot yet remain visible to an OLDER `REPEATABLE READ` snapshot
  opened before the commit. Spec: s1 opens RR + reads (fixes snapshot) → s2 DELETE+VACUUM →
  s1 re-reads (must STILL see the row) → s3 fresh read (must NOT). This proves the candidate
  pipeline respects snapshots; the heap recheck is the load-bearing filter.
- **Make the probe deterministic despite an approximate index** by planting the target at a
  unique distance extremum (`[9,9,9,9]`, far from the base cluster) so the returned id is
  independent of graph approximation and the golden file is stable. Force the index path with
  `SET enable_seqscan = off` so you're testing the index, not a seqscan.
- **Test the failure→fallback handoff end-to-end.** Inject a maintenance failure → assert the
  write falls back to a correctness-preserving path (e.g. INSERT lands in a `.delta` buffer;
  `extend_count = 0`) → assert search still finds *both* the delta'd row and the original
  index rows (no corruption, no silent demotion) → assert recovery clears it
  (`REINDEX CONCURRENTLY` absorbs the delta; `delta_rows = 0`).
- **Encode "fall back to a correct path on staleness" as a planner-cost test PLUS a
  correctness test.** A stale index must be routed away by cost (the cost function stats a
  `.stale` sidecar and returns a huge cost so the planner avoids it) AND must still return
  the right top-k via the fallback (`enable_<ext> = off` routes to the baseline and the
  results are correct).

---

## Cores that need an absent device, deterministic resource tests, and CI tiering

When the extension's core depends on hardware/SDK the dev machine or CI runner lacks, the
testing strategy (a swappable exact reference implementation that doubles as ground truth;
injectable resource-pressure tests for OOM/eviction/accounting that run on CPU CI; two-tier
CI with the cheap tier on the reference build) is its own playbook:
**`../architecture/out-of-process.md`** (hardware-agnostic). GPU-specific mechanics are one
level deeper in `../accelerator/`.

Two meta-rules from that playbook apply to *all* extension testing:

- **Bidirectional false-done prevention** — verify the *normal path actually runs*, don't
  grep that the code exists. Both "claimed done but unimplemented" and "claimed undone but
  actually wired" are real failure modes.
- **Fail-closed as a tested contract** — every artifact gate (CRC, version skew, geometry,
  relfilenode) must *reject* corrupt input, and each rejection must have a regression test
  that feeds it corruption.

---

## Remote / Docker execution

The SQL and spec files are environment-agnostic. Only the runner changes.

| Target | Command | Notes |
|---|---|---|
| Local | `make installcheck` / `make installcheck-isolation` | needs `PG_CONFIG` on PATH |
| Docker | `make docker-test` (`docker-build` → regress + isolation in container) | pinned PostgreSQL + extension dependencies image |
| Docker unit | `make docker-unit` | C unit tests, no PG needed |
| VM | `make vm-test` (regress), `make vm-test-all` (unit→regress→isolation) | over SSH; `PG_CONFIG_REMOTE` |
| VM full cycle | `make vm-cycle` | sync → build → install → test in one shot |

When a schema change does not seem to take effect on Docker, the named volume is serving
the old image content — `docker compose down -v` forces a fresh copy. (This and the rest of
the Shape-B deploy mechanics are in `../architecture/shape-b-microservice.md`.)

---

## Failure-mode table (extension testing)

| Symptom | Cause | Fix |
|---|---|---|
| `function/operator does not exist` at green | `.so` not reinstalled after edit | `make install` (and reconnect; the backend caches the loaded library) |
| regression diff in whitespace/row order only | unordered query | add `ORDER BY`; never rely on heap/scan order in a golden |
| golden passes locally, fails on VM | PG minor version / locale / dependency version differs | pin versions; keep the Docker image and VM in lockstep |
| isolation test hangs | a session left a txn open with no matching `commit`/`teardown` | every `BEGIN` needs a terminating step in the permutation |
| recall test flaky | unfixed build seed | fix the build seed; recall must be deterministic to be a gate |
| `column does not exist` (Shape B) | schema change not picked up | `docker compose down -v` (named volume copies schema once) |
