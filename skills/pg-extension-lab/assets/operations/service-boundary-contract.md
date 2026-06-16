# Service-boundary contract template

Use this when a PostgreSQL extension delegates work to a service, worker, daemon, or
externally deployed component. The goal is not to document every API. The goal is to preserve
the invariants that make split ownership safe.

## Boundary

- Extension object:
- External component:
- Component that owns durable data:
- Component that owns expensive transient state:
- Synchronous calls:
- Asynchronous calls:

## Shared Contract

| Field / invariant | Owner | Checked where | Failure mode | Recovery |
|---|---|---|---|---|
| schema version | | startup + each request | fail closed | |
| payload shape | | SQL constraint + service validation | reject | |
| result identity mapping | | SQL test + E2E test | reject / retry | |
| idempotency key | | queue claim + service handler | retry safe | |
| timeout / retry budget | | worker config | mark retryable | |

## Mock vs Real Split

- Mock proves:
- Real environment proves:
- The mock is allowed to fake:
- The mock must never fake:
- CI gate:
- Manual or nightly gate:

## Triple Confirmation

| Track | Evidence artifact | Command / probe | Owner |
|---|---|---|---|
| API contract | request/response sample, schema, error case | | |
| Fixture semantics | fixture generator, expected rows/oracle, cleanup proof | | |
| Environment | effective endpoint, registry row, env dump with secrets redacted, image/version | | |

Classify failures before fixing: API mismatch, fixture mismatch, or environment mismatch.

## Evidence

- Contract tests:
- SQL assertions:
- Source/code path checked:
- Runtime execution checked:
- Raw artifacts:
- Reproduce command:

## Change Rule

Any change to a shared invariant needs a migration plan. It is not a config-only change.
State whether old and new rows can coexist, whether reprocessing is required, and what runtime
check prevents silent mixed-state behavior.
