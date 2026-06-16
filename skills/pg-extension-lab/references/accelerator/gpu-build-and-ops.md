# Reference (deep): GPU/CUDA extension — build & ops specifics

This is the concrete GPU/CUDA realization of the hardware-agnostic principles in
`../architecture/out-of-process.md`. Read that first; this file is only the
GPU-specific mechanics (nvcc, conda, CUDA context, rpath/ldconfig, cloud GPU VM, cost). Do
not generalize from the specifics here — generalize from the parent reference.

---

## Contents

- [Why a separate daemon (the GPU realization of Shape C)](#why-a-separate-daemon-the-gpu-realization-of-shape-c)
- [Build system (mixed C / C++ / CUDA under PGXS)](#build-system-mixed-c--c--cuda-under-pgxs)
- [The ldconfig disaster (do NOT do this)](#the-ldconfig-disaster-do-not-do-this)
- [Remote GPU VM workflow](#remote-gpu-vm-workflow-edit-local-buildtest-remote--adr-004)
- [Cost & CI](#cost--ci)

---

## Why a separate daemon (the GPU realization of Shape C)

A **CUDA context is per-process and expensive to create**, and the device's VRAM-resident
state (the index) must outlive any single short-lived PG backend. So one `<extension>_server`
daemon owns the single CUDA context + all VRAM-resident indexes; N PostgreSQL backends are
thin clients over a Unix socket. **Invariant: backends never create a CUDA context.** The
daemon returns candidate TIDs + distances only; the backend does the MVCC/ACL recheck (the
GPU never owns heap tuples).

---

## Build system (mixed C / C++ / CUDA under PGXS)

| Need | Mechanism |
|---|---|
| compile `.cu` | custom rule `src/device_wrapper.o: src/device_wrapper.cu` invokes `$(NVCC)`; object added to `OBJS` so the `.so` links it |
| `float4` redefinition between PG and CUDA headers | **never include PG headers in a `.cu`** (ADR-001). Split `.c` and `.cu`; share only the `extern "C"` interface in a small device-wrapper header |
| PGXS JIT bitcode step chokes on `.cu` | emit a clang stub `.bc`: `void device_wrapper_jit_stub(void){}` |
| libstdc++ ABI/version skew at load | `SHLIB_LINK = ... -Wl,-Bstatic -lstdc++ -Wl,-Bdynamic -lrt` |
| postmaster can't find the device library | `-Wl,-rpath,$(DEVICE_LIB_DIR)` (ADR-007) — NOT `LD_LIBRARY_PATH`, NOT ldconfig |
| daemon must not pull PG headers | build `<extension>_server` outside PGXS with its own `SERVER_CFLAGS`/`SERVER_LDFLAGS`; shared IPC/util files compiled twice (`*.o` for the `.so`, `*_server.o` for the daemon) |
| portability | `DEVICE_PREFIX ?= $(CONDA_PREFIX)`, `CUDA_ARCH ?= sm_80`, `NVCC ?= nvcc`; sanitizer via `EXTRA_SERVER_CFLAGS` |
| header changes silently stale objects | `$(OBJS): $(wildcard src/*.h)` forces full rebuild on any header change (wire ABI) |

### CPU shim (so laptops and free CI build with no CUDA)

`make CPU_SHIM=1` swaps `WRAPPER_OBJ` to `src/device_wrapper_shim_cpu.c`, which
reimplements every symbol in the device-wrapper header in pure C (opaque handles → host structs;
`typedef void *cudaStream_t;`), computing **exact** brute-force kNN so it doubles as ground
truth. Zero CUDA headers on the boundary path.

---

## The ldconfig disaster (do NOT do this)

```bash
# NEVER: registers the WHOLE conda env lib dir into the system linker
echo "$CONDA_PREFIX/lib" | sudo tee /etc/ld.so.conf.d/device-lib.conf && sudo ldconfig
```

A conda env's `lib/` contains alternate `libssl.so.3`, `libdbus-1.so.3`, etc. After
`ldconfig`, the system's own sshd/dbus load conda's (different-version) libraries, ABI-clash,
and **die on next boot — the VM becomes unreachable.**

**Correct:** use `-Wl,-rpath,$(CUVS_LIB)` only; give postgres traverse rights to the conda
path with `chmod o+x /home/<user>`. If system registration is truly required, symlink the one
specific `.so`: `sudo ln -s $CONDA_PREFIX/lib/libdevice.so /usr/local/lib/ && sudo ldconfig`.

**Recovery if already bricked:** VM stop → detach boot disk → attach to a rescue VM →
mount + `rm /mnt/broken/etc/ld.so.conf.d/device-lib.conf /mnt/broken/etc/ld.so.cache` →
bind-mount `/dev` etc. → `chroot /mnt/broken ldconfig` → reattach as boot → start.

---

## Remote GPU VM workflow (edit local, build/test remote — ADR-004)

Local Mac edits only; build/test on a GCP L4 VM (`sm_89`, 24 GB VRAM). conda env
`device_dev`, PostgreSQL 16.

| `make` target | does |
|---|---|
| `vm-start` / `vm-stop` | start / **stop** the VM (cost) |
| `sync` | rsync local→VM, `--exclude 'src/*.o' --exclude '*.so' --exclude 'src/*.bc'` (never push laptop objects over nvcc-built ones) |
| `gpu-build` | on VM: `source ~/miniforge3/bin/activate device_dev && make` |
| `gpu-install` / `gpu-test` | `sudo make install` / `make installcheck` |
| `gpu-cycle` | sync → build → install → test |
| `gpu-test-all` | unit → regress → isolation → daemon-fault → e2e ladder |

Common traps: nvcc can't find device headers → conda env not activated; `pg_config not found` →
PG16 not on PATH; `could not load library libdevice.so` → missing `-rpath`; installcheck
"could not connect" → `systemctl start postgresql`; `dpkg locked` → startup script still
running (wait for the startup log's "setup complete").

### .env.gpu (gitignored)

```
GCP_VM=ubuntu@<ip>   GCP_INSTANCE=<gpu-dev-vm>   GCP_ZONE=...   GCP_PROJECT=...
CONDA_ENV=device_dev   CUDA_ARCH=sm_89    # L4=sm_89, A100=sm_80, H100=sm_90
```

---

## Cost & CI

- **Always `make vm-stop` after work.** g2-standard-4 + L4 ≈ $0.85/hr running vs ~$0.003/hr
  stopped (disk only). `preemptible = true` ≈ 70% off (24h cap) — use for benchmark sessions,
  not long dev.
- **CI:** Tier 1 (`ubuntu-latest`, every PR, `CPU_SHIM=1`); Tier 2 (self-hosted A100,
  `workflow_dispatch` only) via a `start-vm → gpu-test → stop-vm(if:always)` workflow gated by
  an `environment: gpu` with required reviewers, authenticated by Workload Identity Federation
  scoped to the one repo. See the generic tiering rules in
  `../architecture/out-of-process.md` §5.

GPU resident state can't be left running; the daemon's `_test` build (`-DDEVICE_TEST_HOOKS`,
`device_fault("...")`) drives failure paths in integration tests without a real device fault.
