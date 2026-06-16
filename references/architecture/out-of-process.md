# Reference: extensions whose core needs something the host/CI may not have

A PostgreSQL extension often depends on a resource that is *not* an ordinary in-process C
library: a GPU/accelerator context, a large loaded model, a JIT/compiler pool, a remote
service, a licensed SDK. This reference is the hardware-agnostic playbook for building,
testing, and structuring such extensions. The lessons were distilled from a GPU extension
but **none of them are GPU-specific** — they apply to any extension with a costly,
process-bound, or absent-at-build-time dependency. (The concrete GPU mechanics live in
`../accelerator/`.)

## Contents

- [1. Architecture Shape C — the out-of-process sidecar daemon](#1-architecture-shape-c--the-out-of-process-sidecar-daemon)
- [2. Testing a core that depends on an absent device/SDK — the reference shim](#2-testing-a-core-that-depends-on-an-absent-devicesdk--the-reference-implementation-shim)
- [3. Making an external/bounded resource deterministically testable](#3-making-an-externalbounded-resource-deterministically-testable)
- [4. Build-system lessons for a foreign toolchain under PGXS](#4-build-system-lessons-for-a-foreign-toolchain-under-pgxs)
- [5. CI strategy when the runner lacks the dependency](#5-ci-strategy-when-the-runner-lacks-the-dependency)
- [6. Two meta-lessons worth lifting verbatim](#6-two-meta-lessons-worth-lifting-verbatim)

---

## 1. Architecture Shape C — the out-of-process sidecar daemon

Beyond Shape A (pure in-process C) and Shape B (extension → external microservice that owns
data), there is a third shape:

```
Shape C — extension + co-located compute sidecar (owns a costly process-bound resource, NOT data)
  N PostgreSQL backends  →  Unix socket / shm  →  one long-lived daemon
                                                    holds the costly context + resident state
  backend resolves returned IDs → MVCC / ACL recheck against the heap
```

**When to reach for it.** When the expensive resource has *process-bound lifetime or
setup cost* that cannot be paid per backend: a device context (creating one is expensive and
per-process), a multi-GB model or index resident in memory, a warm JIT/compiler cache.
Every short-lived PG backend connecting as a thin client shares the one resident copy.

**The invariant that defines the shape:** *backends never create the costly context.* One
daemon owns it; backends are clients.

**Critically: the sidecar holds NO catalog/transaction state — it is a pure compute cache.**
This is what separates Shape C from Shape B. The daemon returns *candidate row-IDs +
scores only*; the backend resolves them to visible heap tuples and runs the MVCC snapshot
check and ACL recheck. "The accelerator never owns heap tuples." Keeping all
catalog/visibility logic in the backend is what lets the daemon stay a dumb, restartable
cache.

### What Shape C forces you to handle (each is a first-class concern, not an afterthought)

| Concern | Why it arises | Mechanism |
|---|---|---|
| **Orphan reconciliation** | the daemon can't see a `DROP` (no catalog) | a GC function + startup scan reconcile artifacts left by a DROP that happened while the daemon was down; e.g. `..._gc_orphans()` |
| **Fail-closed validation** | a restarted daemon may load stale/corrupt artifacts | every artifact load checks a CRC'd header / manifest hash / version / relfilenode and **rejects** rather than serving stale data |
| **Interruptible cross-process waits** | a blocking `recv` breaks PG's `statement_timeout`/cancel contract | replace blocking recv with a `poll()` loop that calls `CHECK_FOR_INTERRUPTS()`; the daemon ignores `SIGPIPE` to survive a client disconnecting mid-reply |
| **Wire-ABI pinning** | a struct/padding drift between client and daemon is silent corruption | force a rebuild of **all** objects on **any** shared-header change (`$(OBJS): $(wildcard src/*.h)`) — PGXS's implicit rule does not track header deps |
| **Fault-injectable test build** | failure paths (persist/serialize/rename failure) can't be triggered normally | a parallel `_test`-suffixed daemon binary built with `-DTEST_HOOKS`; env-var-gated fault points (`fault("RENAME_X")`); never installed over the production binary |

---

## 2. Testing a core that depends on an absent device/SDK — the reference-implementation shim

The dev laptop and the free CI runner usually lack the special hardware/SDK. Do **not** let
that mean "the extension is untestable without the device." Build a swappable reference
implementation.

- **Funnel every device/SDK call through ONE header.** All access to the foreign backend
  goes through a single boundary header (e.g. `wrapper.h`). No other source line touches the
  SDK.
- **Provide a CPU-only translation unit implementing every symbol in that header.** A build
  flag swaps the real object for the shim (`make CPU_SHIM=1` → swaps `WRAPPER_OBJ`). Nothing
  else in the tree changes.
- **Make the shim toolkit-free.** Stub the SDK's leaked types (`typedef void *deviceStream_t;`)
  and realize opaque handles as plain host structs. Zero SDK headers/libs on the boundary
  path — otherwise you lose the free-runner advantage.
- **Make the reference EXACT, so it doubles as ground truth.** If the real backend is
  *approximate* (an ANN index), have the shim compute the *exact* answer (brute-force kNN,
  recall = 1.0). Then the SQL correctness assertions — written with `>=` thresholds — pass
  on the shim while still exercising all the glue (SQL plumbing, IPC, ID encoding, MVCC
  recheck). One reference impl serves both "runs without the device" and "is the oracle."
- **Document precisely what the shim CANNOT catch.** The shim is exact, so it is blind to:
  real SDK integration (API misuse, dtype/stream bugs), *approximate-quality regression*
  (graph recall loss is invisible against an exact oracle), real resource (VRAM/mempool)
  behavior, and true latency. Write this false-confidence boundary down — a green run on the
  shim must not be read as "the device path works."

---

## 3. Making an external/bounded resource deterministically testable

A device's real memory exhaustion is non-deterministic (pool caching, fragmentation). Do not
try to provoke real OOM. Instead, **inject** the failure so OOM / eviction / fallback become
ordinary regression tests that run on CPU CI. This generalizes to *any* bounded resource — a
RAM budget, a connection pool, a disk quota, a cache size.

- **Fake counter + injectable failure.** Expose a virtual resource counter the test can move
  (`eat_vram(n)` / `free_vram(n)`) and an injector that arms exactly N consecutive synthetic
  failures (`inject_build_oom(n)`).
- **Test the eviction POLICY, not just "it errors."** Stage ≥2 resident victims, arm 2
  OOMs, then assert the next build *still succeeds* (it evicted to fit) and `evictions >=
  e0+2`. This distinguishes "evict-once-then-fail" from "evict-to-fit loop." Run it for both
  the single-process and the parallel-worker paths.
- **Self-account the resource, and write a discriminating before/after test.** Device APIs
  under-report freed memory; your own `Σ per-object estimate` is the only stable number.
  Snapshot accounted usage before vs after forcing an allocation and assert it *grew by the
  expected size* — this catches uncounted allocations.
- **Detect reservation leaks by asserting return-to-baseline after DROP.** `base := used;
  build; DROP; assert used <= base`.
- **Counters are cumulative/daemon-lifetime — snapshot a baseline, assert deltas**, never
  absolute values (`SELECT evictions AS e0 \gset` … `evictions > :e0`).
- **Size fixtures above the observability granularity.** If the stat view reports MB, make
  the test object ≥ a couple MB or the signal rounds to zero.

(Resource *governance* — which knob actually binds each resource, admission control, the
ceiling-as-published-result — is in `../performance/governance.md`.)

---

## 4. Build-system lessons for a foreign toolchain under PGXS

PGXS only understands `.c → .o`. Teaching it about a foreign object (a `.cu`, a `.cpp`, a
Rust staticlib) has two separate obligations and several traps. The *principles* are
hardware-agnostic; the concrete `nvcc` invocation is in `../accelerator/`.

- **Custom pattern rule AND list the object in `OBJS`.** The rule builds the foreign object;
  adding it to `OBJS` is what makes the `.so` link it. Both are required.
- **Emit a stub bitcode for the JIT step.** PGXS's JIT path emits LLVM bitcode per `.c`; a
  non-C source breaks it. Generate a tiny `void foo_jit_stub(void){}` `.bc` for the foreign
  TU.
- **Statically link (or pin) a conflicting C++ runtime.** When the host C runtime and the
  SDK's C++ runtime disagree, link the stdlib statically:
  `-Wl,-Bstatic -lstdc++ -Wl,-Bdynamic`. Avoids ABI/version skew at load time in the
  postmaster.
- **Embed the library path with `-rpath`, do NOT pollute system `ldconfig`.** Use
  `-Wl,-rpath,<libdir>` so the postmaster finds a non-system shared lib without
  `LD_LIBRARY_PATH`. Registering a packaged env's `lib/` into `/etc/ld.so.conf.d` is a
  *system-bricking* mistake — that directory also contains alternate `libssl`/`libdbus`
  that the system's own sshd/dbus will then load, ABI-clash, and die on next boot. If system
  registration is truly needed, symlink the *one* specific `.so`, never the whole directory.
- **Build an out-of-process daemon completely outside PGXS.** It must not pull PG headers;
  give it its own `CC`/`CFLAGS`/`LDFLAGS`. Sources shared between the `.so` and the daemon
  are compiled **twice** under distinct object names (`ipc.o` for the extension, `ipc_server.o`
  for the daemon).
- **Parameterize the SDK root/arch via env so the build is portable** (`SDK_PREFIX ?=
  $(CONDA_PREFIX)`, `ARCH ?= ...`). Expose a sanitizer hook (`EXTRA_CFLAGS`) — see §6.
- **Sync rules must exclude artifacts compiled with the *remote* toolchain.** If you edit on
  a laptop and build on a remote target, `rsync --exclude 'src/*.o' --exclude '*.so'
  --exclude 'src/*.bc'` — pushing laptop objects over correctly-built remote objects breaks
  the link silently.

---

## 5. CI strategy when the runner lacks the dependency

- **Two tiers.** Tier 1: free, unlimited, every PR, on the **reference/shim build** — proves
  plumbing, contracts, correctness, fail-closed gates. Tier 2: the real device, **on-demand
  only** (`workflow_dispatch`) — proves kernels, approximate recall, real-resource behavior,
  latency. The justification is empirical: most real bugs are *glue* (IPC serialization,
  routing, fail-closed, mode labels), all reproducible device-free.
- **Encode the tiering in the build as one source of truth.** A single `REGRESS` list minus
  a `TIER2_ONLY` filter: `REGRESS_TIER1 = $(filter-out $(REGRESS_TIER2_ONLY),$(REGRESS))`,
  with an `installcheck-tier1` target. Don't maintain two hand-kept lists.
- **Drive the paid runner start→test→stop from a hosted job, gated by human approval.** A
  3-job workflow: `start-vm` (hosted, boots the device VM) → `gpu-test`
  (`[self-hosted, …]`) → `stop-vm` (`if: always()`). Put the boot behind an
  `environment:` with required reviewers so cost is only incurred on a deliberate click. The
  self-hosted runner is online *only* while a triggered run holds the VM up → no standing
  attack surface. **Never** auto-trigger the device job from a comment/label — a fork PR
  could then run arbitrary code on your hardware.
- **Authenticate the cloud with keyless, repo-scoped federation** (OIDC / Workload Identity),
  not a long-lived secret in CI; least-privilege (start/stop/get one instance), bound to one
  repo.
- **State the honesty caveat next to the green badge.** "CI Tier 1 verifies
  plumbing/contracts/correctness on the CPU reference; device-kernel correctness, approximate
  recall, and real resource behavior are verified in on-demand Tier-2 runs." A badge that
  implies more than the cheap tier checked is itself a false-done.

---

## 6. Two meta-lessons worth lifting verbatim

- **Bidirectional false-done prevention.** Both failure modes are real: "claimed done but
  unimplemented," *and* "claimed undone but actually wired." Completion means verifying the
  *normal path actually runs* — not grepping that the code exists. (A real case: a remapping
  built only on the load path silently degraded freshly-built indexes to a post-filter
  path — it passed a grep for the code, and failed reality. Only running the normal path
  caught it.)
- **Fail-closed as a tested contract, everywhere.** Every artifact gate — CRC, geometry,
  version skew, manifest hash, relfilenode match — must *reject* rather than degrade, and
  each rejection must have a regression test that feeds it a corrupted input. This converts
  "trust the data" into a tested invariant. Use AddressSanitizer (build the daemon under
  `-fsanitize=address` in CI) to confirm accounting/memory bugs by root cause, never a
  guess-patch — a wrong accounting number makes every resource-vs-performance figure fiction.
