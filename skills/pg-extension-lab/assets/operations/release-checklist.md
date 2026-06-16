# Release checklist

## Build and install

- [ ] Clean build from an empty build directory.
- [ ] Install on every supported PostgreSQL major version.
- [ ] Upgrade from the previous released extension version.
- [ ] Drop extension succeeds or documented retained artifacts are intentional.

## Tests

- [ ] Unit tests pass.
- [ ] `make installcheck` or `cargo pgrx test` passes.
- [ ] Isolation tests pass for concurrent insert/scan/build/worker cases.
- [ ] Device/service-absent path fails closed or skips explicitly.

## Security

- [ ] `SECURITY DEFINER` functions pin `search_path`.
- [ ] Public execute privileges are reviewed.
- [ ] Secrets are stored by reference, not plaintext extension tables.
- [ ] Outbound endpoints are owner-controlled and allowlisted.

## Benchmark artifacts

- [ ] Result JSON/CSV committed or archived with report.
- [ ] Report includes command, dataset hash, extension version, PostgreSQL version, hardware.
- [ ] Recall/correctness claims are labeled `SOLID`; noisy latency is labeled `INDICATIVE`.
