# Resource governance & ops levers

The flip side of `resource-pareto.md`: once you know the trade-off, you have to *bound* the
resource at runtime — decide which knob actually binds each resource, what happens at the
ceiling, and which layout/placement choices are levers. Most of this matters whether or not
the extension touches an accelerator.

## Contents

- [Storage layout is a build/scan lever](#storage-layout-is-a-buildscan-lever-large-value-extensions)
- [Place regenerable derived artifacts outside the backup tree](#place-regenerable-derived-artifacts-outside-the-backup-tree)
- [Resource governance — the ceiling is a first-class concern](#resource-governance--the-ceiling-is-a-first-class-concern)
- [Guide, don't force](#guide-dont-force)

---

## Storage layout is a build/scan lever (large-value extensions)

For an extension over large column values (high-dim vectors, big JSON/blobs), the row
**storage mode** is a real resource↔performance lever, because the build/scan path pays a
**detoast** cost for every out-of-line value:

- PostgreSQL's default for a large type is often `EXTERNAL`/`EXTENDED` → values past the
  TOAST threshold (~2 KB) go out-of-line → each heap scan in a build detoasts them.
- `SET STORAGE PLAIN` keeps values inline → no detoast, faster build, ~10% faster INSERT,
  smaller *total* disk (TOAST table disappears) — **but** the main heap bloats massively
  (one measured case: 58 MB → 7.8 GB, ~134×), so other columns' scans slow down.
- Therefore PLAIN is a win **only for a dedicated single-purpose table** (the vector-only
  table), not a shared one. And it is impossible when a row can't fit a page (very high dim).
- The right move is to **measure the detoast fraction** for your dim and decide, and to
  **emit a build-time NOTICE** when a column is toasted at that dimension so the operator can
  choose — guide, don't force (below).

## Place regenerable derived artifacts outside the backup tree

If the extension writes large *regenerable* derived files (index artifacts, caches), where
they live is a resource decision with two **orthogonal** axes:

- **Locality** (a fast local volume — for build/serve speed) and
- **Backup membership** (inside vs outside the `$PGDATA` tree).

Defaulting them under `$PGDATA` means `pg_basebackup` copies multi-GB regenerable data into
every backup and every new standby (backup bloat, worse RTO). Put them on a **sibling
directory on the same fast disk but outside `$PGDATA`** — locality kept, backups slim. Emit
a WARNING if the configured path resolves under `$PGDATA`.

## Resource governance — the ceiling is a first-class concern

When the extension manages an off-heap or external resource (device memory, a shm corpus, a
process pool), standard PostgreSQL knobs **silently do not govern it** — and a silent
non-enforcement is a correctness and benchmark-integrity hazard.

- **Map every resource to the knob that actually binds it.** `maintenance_work_mem` is
  silently ignored for an off-heap build; `temp_file_limit` can't see a memfd/shm corpus;
  `shared_buffers`/tablespace don't apply to device memory. Maintain a per-resource "real
  enforcement" table: PG-internal → standard GUCs; host RAM → **OS/cgroup `MemoryMax`** (the
  extension GUC is only a clean-error soft cap); external/device → reactive evict-and-retry +
  a pool cap. Document which lever is real for each. (A worked in-backend-vs-worker lever map:
  a GUC like `ai.max_search_results` bounds a Rust `Vec` that lives *outside* `work_mem`.)
- **At the ceiling, fail closed and loud — never silently corrupt or silently degrade.**
  Admission control = a soft floor inside the app (reservation counter + LRU eviction;
  build-OOM triggers evict-then-retry-once) plus a hard wall at the OS/cgroup. Publish the
  ceiling as a real result, verbatim: "50M×384 fp32 = 73 GiB > 2×40 GB VRAM → BUILD FAILED."
- **Record every knob/reloption/flag per result row**, exactly as a CPU benchmark records
  `work_mem` — a `params_json` column plus resource columns (`peak_mem`, `device_s`,
  `energy_j`). Run budget/shard sweeps *as benchmarks*, not as one-off checks.
- **Accounting bugs are benchmark-integrity bugs.** If your resource accounting is wrong,
  your resource-vs-performance numbers are fiction. Confirm accounting/eviction bugs by root
  cause (build under AddressSanitizer in CI), never a guess-patch. Write a discriminating
  before/after test (see `../architecture/out-of-process.md`).

## Guide, don't force

Prefer build-time `NOTICE`/`WARNING` that recommend a better setting (PLAIN storage,
index_dir placement, a supported dependency-version range) over silently changing the user's
configuration. Pin a dependency's on-disk-format version range and WARN outside it; re-verify
the format constants on every major bump of that dependency.
