# Release and operations hardening

Read this before shipping an extension that owns background work, accelerator resources,
external-service state, or custom storage.

## Documentation source of truth

- Current-state docs describe what operators should believe today.
- ADRs explain why a decision was made. Do not make operators reconstruct current behavior
  from ADR history.
- Every benchmark report must include the exact command, dataset hash, extension version, and
  hardware/runtime facts needed to reproduce it.

## Pre-release checklist

- Fresh install, upgrade from previous version, and uninstall all pass.
- Extension SQL, shared library, control file, and upgrade scripts agree on version.
- `SECURITY DEFINER` functions pin `search_path`.
- Privileges are least-privilege by default; public execute is intentional or revoked.
- Background workers have stale-pending recovery and bounded retry behavior.
- Replica/bootstrap docs explain what happens to generated artifacts and sidecar state.

## Ops failure modes to test

- Device/VRAM unavailable, OOM, degraded fallback, and circuit breaker open/close behavior.
- Host memory and cgroup limits.
- Sidecar restart while backends are active.
- Provider timeout/rate limit with persisted retry state.
- Timeline/system_identifier mismatch for artifacts that cannot be reused across clusters.

## Runbook minimum

Each production-facing feature should have: health check, safe disable switch, capacity signal,
log message examples, remediation steps, and what data can be deleted or rebuilt.
