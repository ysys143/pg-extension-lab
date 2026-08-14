---
name: adversarial-review
description: >-
  Adversarial code review for PostgreSQL extension work — finds the bugs a self-review misses
  by computing the DIFF between the model the author STATED and the model that Postgres, the
  sibling code, and the downstream consumers actually ENFORCE. Use when reviewing a PR, a diff,
  or your own change before pushing; when the user says "적대적 리뷰", "리뷰해줘", "이 PR 검토",
  "코드 리뷰", "adversarial review", "review this", "self-review before push"; and for
  extension-specific review requests — extension review, C/PGXS or pgrx diff review,
  pg_regress .out diff review, isolation spec review, planner hook review, CustomScan review,
  index AM review, extension upgrade script review, GUC or shared_preload_libraries review,
  benchmark claim review. A well-documented, self-critical PR is the highest-risk case: its
  disclosed risks are the author's threat model, and the surviving bugs live outside it.
  NOT for quick lint/style passes, formatting, or generating new code.
---

# Adversarial Review (PostgreSQL extension edition)

**Thesis.** A review that shares the author's mental model only finds bugs the author could
also have found. To find the rest, stop checking whether the change is consistent with what the
PR *claims*, and instead compute the **difference** between:

- the model the author **stated** (PR body, header comments, docs, "verified" claims), and
- the model that is actually **enforced** by (1) the C/Rust as written, (2) every sibling
  implementation and the in-tree Postgres precedent, (3) the full contract the Postgres backend
  imposes (MVCC, memory contexts, locking, error handling, ABI), (4) the downstream consumers
  — the planner, the executor, the SQL-level API, other extensions.

Every probe below is that diff applied to one surface. The more rigorous and self-critical the
PR looks, the more the rigor is camouflage — "looks thorough" is not "is complete".

## Operating rules (do these, in order)

1. **Never quote the PR's stated resolution/precedence order.** Re-derive it from source. If
   the PR says a setting comes from a GUC, grep the actual resolver: is it
   `GUC > reloption > compile-time default`, and does `_PG_init` register it before anything
   reads it? The same rule applies to hook chains, cost-estimate paths, and version gates.
2. **For any "Postgres rejects X" or "this state cannot happen" gate, pull the FULL set** the
   backend enforces and diff it against what the code checks. Typical under-enumerations: a
   type's input rules (NUL bytes and lone surrogates in text, not just the numeric edge cases),
   TOAST'd vs. inline datums, `standard_conforming_strings`, non-C collations, empty vs. NULL
   arrays, `-0.0`/NaN, tuples that are `HEAPTUPLE_RECENTLY_DEAD` rather than simply live.
3. **Run it in a hostile cluster**, not a clean `make installcheck` on defaults. Vary the axes
   the extension silently assumes: PG major version, `REPEATABLE READ`/`SERIALIZABLE`,
   `max_parallel_workers_per_gather > 0`, a non-C `LC_COLLATE`/ICU, `shared_preload_libraries`
   present vs. absent, a build with `-DUSE_ASSERT_CHECKING`, and a run under valgrind or ASAN.
   Bugs that only show up live are exactly the ones the mocked test path hid.
4. **Call-graph every tested function.** Is it reached from a real SQL entry point — a
   `PG_FUNCTION_INFO_V1` symbol, a registered hook, an AM handler slot — or only from the test
   harness? Then mentally mutate it: "if I invert this condition, does a test go red?" If no,
   the test asserts the fixture, not the code.
5. **Read every doc/comment sentence as a falsifiable claim** and hunt the code that violates
   it — including future-tense traps: a comment that is correct on today's PG version but will
   mislead the next contributor who edits under a different one.
6. **Enumerate the surfaces and personas** explicitly: configuration surfaces
   (GUC / reloption / function argument / compile-time default), the persona who actually hits
   this (an existing install upgrading in place, not a fresh `CREATE EXTENSION`), and the
   symmetric partner of anything you touch (build↔scan, insert↔vacuum, cost↔execute,
   serialize↔deserialize, palloc↔pfree).
7. **Treat a self-critical PR's "disclosed risks" as the author's threat model, then hunt
   outside it.** What the author defended is already a lost fight.

## The 20 probes (A–T)

Run these as questions against the diff.

- **A stated-vs-truth** — Does the prose describe what the code does, or what the author wished
  it did? ("index-only scan" that still visits the heap; "bounded memory" that palloc's the
  whole result set in one context.)
- **B ownership/memory** — What sibling code, in-tree Postgres precedent, or exact line settles
  this? Cite it. Read the analogous core AM/hook before accepting a novel shape.
- **C backend completeness** — What is the *complete* contract Postgres imposes, not the subset
  the author enumerated? Sweep: MVCC snapshot visibility and the lifetime of a `HeapTuple`
  after buffer unpin; memory-context lifetime (`palloc` in a per-tuple context, then read after
  reset; `pfree` of something the context already owns; missing
  `MemoryContextSwitchTo` restore); SPI re-entrancy and `SPI_connect`/`SPI_finish` pairing
  across an error path; error handling via `PG_TRY`/`PG_CATCH` and what a longjmp skips
  (unreleased locks, leaked file descriptors, a `PG_RE_THROW` that never runs); lock acquisition
  order and the deadlock it creates against an existing path; TOAST detoasting and
  `PG_GETARG_*_PP` vs. copy semantics; collation-dependent comparison; and datum lifetime across
  `ExecStoreTuple`. Enumerate what applies; do not stop at the first item.
- **D empiricism** — Have I actually run it, in the failing configuration? `make installcheck`
  against the *target* PG major, `pg_regress` with the real `.so` loaded, `isolationtester` for
  the concurrency claim, an assert-enabled build, valgrind/ASAN for the memory claim. Only
  execution evidence wins an argument; a passing CI badge is not the evidence.
- **E existence vs reachability** — This test/index/branch exists — is it *reached*? Does the
  `pg_regress` expected `.out` actually drive the new branch, or does the query fall back to a
  seqscan and produce the same output either way? Does the isolation spec's permutation truly
  interleave at the contended point, or does the blocking step complete first? Is the declared
  GUC or operator class ever chosen by any plan? Does green CI mean N>0 real assertions ran, or
  that every test skipped to exit 0?
- **F doc-as-claim** — Falsify the comment with the code. README performance claims, the `.control`
  file's `requires`, and a function header's "caller must hold the lock" all count.
- **G self-serving measurement** — Does the benchmark's blind spot coincide with the
  implementation's weak spot? A fixture with uniform selectivity hides the correlated-predicate
  collapse; a warm-cache run hides the pages-per-query regression; unmatched recall hides that
  the fast path returns fewer rows.
- **H confluence** — Evaluate the extension running *alongside* the rest of the cluster: sharing
  one `shared_buffers`, one `maintenance_work_mem` budget, one lock table, one background-worker
  slot pool, and coexisting with other extensions that install the same hook.
- **I contract triangulation** — Do N existing implementations all *coincidentally* do the same
  thing? That is a contract, not a coincidence. Classic case: a hook chain where every in-tree
  and third-party implementation calls the previous hook (`if (prev_hook) prev_hook(...); else
  standard_...()`), and this one does not — silently disabling every other extension. Same for
  C ABI signatures, `PG_MODULE_MAGIC`, and AM handler struct fields.
- **J time-axis safety** — Separate "correct today" from "won't break when a future contributor
  trusts this comment, or when the next PG major changes the struct."
- **K naming as UI** — What fraction of the implementation does the name describe? A GUC named
  for a limit that is actually a hint, or a function named `..._safe` that is not, is a defect.
- **L symmetry sweep** — Fixed one site? Auto-check its mirror: build↔scan, insert↔delete↔vacuum,
  cost estimate↔actual execution shape, serialize↔deserialize, `_PG_init`↔`_PG_fini`,
  `CREATE EXTENSION` script↔`ALTER EXTENSION ... UPDATE` script, parallel worker↔leader.
- **M review ledger** — Own the running list of open items; note stale threads and record
  explicit "resolved as non-actionable" verdicts with the reason.
- **N test information content** — Does each test-matrix axis correspond to a real conditional
  branch? An axis the code does not distinguish (three vector dimensions through one identical
  code path) is cost, not signal.
- **O self-defeating failure mode** — Does the recovery code fail in exactly the scenario it
  exists for? Sharpest instances here: the upgrade script (`ALTER EXTENSION ... UPDATE`) that
  works from a fresh install but fails from the *actual* prior version's catalog state; a
  version-gated `CREATE OR REPLACE` that assumes an object the old version never created;
  `_PG_init` that is not idempotent under re-entry or under a second load path; a cleanup
  callback that itself allocates in the context being reset.
- **P implicit deployment assumptions** — What deployment setting does the code silently assume?
  Isolation level, `shared_preload_libraries` membership, extension installed and at which
  version, PG major-version branch, parallel query on/off, `huge_pages`, a specific collation
  provider, superuser vs. non-superuser install. Fix it or document it.
- **Q deviation-proportional evidence** — The larger the deviation from the in-tree reference
  implementation, the more evidence required. A novel scan node needs more than a smoke test.
- **R baseline legitimacy** — When the author argues "consistent with X", ask whether X deserves
  to be the baseline at all. "The existing extension does it this way" is not a defense if that
  way is also wrong.
- **S rebuttal ships an alternative** — Do not just reject; write the working SQL, C, or spec
  permutation that proves the fix is feasible.
- **T mutation sensitivity** — For each test, mentally break the logic: does it go red? Ask
  specifically whether the `.out` expected file *constrains* the logic or merely happens to
  match (an empty result set, or output that a fallback plan produces identically), and whether
  each `Assert` checks a real invariant rather than something the type system already
  guarantees.

## Workflow

1. **Extract the stated model.** Read the PR body, header comments, and every "verified" /
   "deliberately not covered" claim. That is the author's threat model — write it down.
2. **Re-derive the enforced model from ground truth** (rules 1, 5; probes A/B/C/F): grep the
   resolvers, read the sibling and in-tree implementations, pull the backend's real rules for
   every type, lock, context, and error path the diff touches. Do not trust the stated model
   for any of this.
3. **Compute the diff.** Every gap between stated and enforced is a candidate finding.
4. **Probe reachability and execution** (rules 3, 4; probes D/E/N/T): hostile-cluster run,
   call-graph from a real SQL entry point, mutation test on the expected files. Downgrade any
   "CI green" to "N assertions ran against the loaded `.so`".
5. **Sweep symmetry and personas** (rule 6; probes G/H/I/L/O/P): mirrors, confluence with the
   rest of the cluster, the in-place upgrade persona, deployment assumptions.
6. **Triage like a maintainer** (probes M/Q/R/S): rank by severity, demand evidence
   proportional to deviation, attach a working alternative to each rejection, and record
   explicit verdicts — including what you checked and deliberately passed.
7. **Report** most-severe-first, each finding with `file:line` evidence and a concrete failure
   scenario (the query, the permutation, or the upgrade path that triggers it). If you used a
   bot or LLM as a breadth sensor, curate its output by hand — promote, reject, or mark
   false-positive; do not relay its priorities raw.

## Guardrails

- Do not claim a finding without re-deriving from source (rule 1) and without a concrete failure
  scenario. "Looks suspicious" is not a finding.
- A rejection of the author's rebuttal must carry execution evidence (D) or a legitimacy
  argument about the baseline (R). A bare value judgment loses.
- Cite exact `file:line`. If you cannot, you have not finished probe B.
- Distinguish "crashes the backend" (memory, locking, longjmp) from "returns a wrong row" from
  "is merely untidy", and say which one each finding is. In extension work the first class takes
  the whole cluster down, so it outranks everything else.
