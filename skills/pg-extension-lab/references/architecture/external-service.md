# Reference: external service boundaries and data contracts

Use this when a PostgreSQL extension delegates work to a separately deployed service, worker,
or daemon. The lesson is not "add an API client." The lesson is that split components stay
correct only when their shared contract is explicit, versioned, and executable.

Security specifics such as secrets, outbound allowlists, and `SECURITY DEFINER` are in
`security.md`; this file covers the integration shape.

---

## Contents

- [Do not start from the API surface](#do-not-start-from-the-api-surface)
- [Triple-confirm API, fixture, and environment](#triple-confirm-api-fixture-and-environment)
- [Registry-owned configuration](#registry-owned-configuration)
- [One authority per durable object](#one-authority-per-durable-object)
- [The data-contract invariant](#the-data-contract-invariant)
- [Mock vs real verification](#mock-vs-real-verification)
- [Benchmarking across a service boundary](#benchmarking-across-a-service-boundary)
- [Observability without adding a platform](#observability-without-adding-a-platform)

---

## Do not start from the API surface

An external component usually exposes more methods, flags, and endpoints than the extension
should care about. Start by reading docs to understand the intended contract, then inspect
source, schemas, migrations, tests, and a minimal execution path to find the real contract.

The design target is a narrow boundary:

- the extension exposes SQL-visible behavior;
- the service owns one explicit capability;
- shared state is represented as rows, payloads, status transitions, and versioned
  invariants;
- calls across the boundary are idempotent, timeout-bounded, and observable.

If the boundary is not narrow, the extension turns into a remote-control panel for another
system. That makes testing slow, failures ambiguous, and security review nearly impossible.

## Triple-confirm API, fixture, and environment

When a database extension is attached to a model-like or externally hosted service, failures
often hide in three different layers that look similar from SQL: the API can be called
correctly, the fixture can ask the wrong question, or the runtime environment can silently
change the behavior.

Treat these as three independent evidence tracks:

| Track | What to verify | Typical hidden failure |
|---|---|---|
| **API contract** | request/response schema, auth, timeout, retry, idempotency, error shape, version | SDK accepts the call but maps options differently; mock omits a required field; errors are not stable |
| **Fixture semantics** | input rows, expected rows, deterministic IDs, payload version, oracle, cleanup | fixture is too friendly, uses stale rows, tests only "returns something", or encodes the old contract |
| **Environment** | endpoint, env vars, catalog registry row, container image, network path, dependency versions, runtime flags | local and CI call different endpoints; blank env overrides default; old volume/schema persists; service version drift |

Do not collapse these into one E2E test. A good boundary suite has:

- a contract test that can fail before PostgreSQL is involved;
- a SQL-visible fixture test that proves the extension interprets service results correctly;
- an environment probe that prints the effective endpoint, contract version, dependency
  version, and registry row used for the run;
- a real-service smoke that is gated and labeled as compatibility/latency evidence, not the
  primary correctness oracle.

If an end-to-end run fails, classify the failure as API, fixture, or environment before
changing code. Otherwise the next "fix" may only retune the fixture around the same broken
contract.

## Registry-owned configuration

Put integration configuration in catalog tables the extension owns when the setting affects
stored data, replay, authorization, or result interpretation:

```text
ext.service_endpoints  (name, base_url, auth_ref, timeout_ms, ...)
ext.contract_versions  (name, version, payload_schema, result_schema, ...)
ext.pipelines          (name, endpoint, contract_version, runtime_options, ...)
```

Callers reference a named pipeline or contract row. They should not pass arbitrary URLs,
payload formats, or interpretation knobs per call. Per-call freedom is hard to audit and often
turns into SSRF, mixed-state behavior, or unreproducible results.

Environment variables are still useful for deployment-local secrets and hostnames, but they
must not be the only source of a data-changing invariant. If two services can drift by setting
different env values, the registry is missing a contract.

## One authority per durable object

In a split extension + service design, exactly one component creates and migrates each durable
object. The other component consumes it through a typed contract.

Examples:

- If the extension owns the table, the service writes only through the approved SQL/API path.
- If the service owns the table, the extension treats it as a remote system and validates the
  returned contract instead of assuming catalog control.
- If an async worker owns status transitions, SQL functions enqueue and read state; they do
  not also invent alternate state machines.

Two DDL authorities for the same object is not flexibility. It is silent drift with better
packaging.

## The data-contract invariant

Independently deployable components can be independently callable yet not independently
consistent. They are coupled by a data contract, not by code.

A shared invariant is any value that changes how persisted data is interpreted: payload
schema, result schema, identity mapping, version, metric, normalization rule, authorization
scope, retry semantics, timeout budget, or external resource placement. If two components
disagree on one of these, the system may return plausible but wrong results.

Rules:

- Bind shared invariants to a registry row or migration, not scattered env variables.
- Validate the invariant at startup and at the request boundary.
- Treat invariant changes as migrations. State whether old and new rows can coexist.
- Fail loud on mixed-state input. A wrong result is worse than a rejected request.
- Record the invariant version in result artifacts so reports can be reproduced.

Use `assets/operations/service-boundary-contract.md` as the lightweight artifact template.

## Mock vs real verification

Mocks and real services answer different questions.

- **Mock/stub path:** proves contract shape, SQL behavior, retries, idempotency, status
  transitions, cleanup, and failure handling. It should run in CI without credentials or
  network dependency.
- **Real path:** proves compatibility with the deployed dependency, latency envelope, rate
  limits, authentication, and operational failure modes. It should be gated, small, and
  explicitly labeled.

The mock is not allowed to fake the contract itself. If the real service requires a field,
ordering rule, status code, or idempotency behavior, the mock should enforce it too. The mock
may fake expensive computation; it must not fake boundary semantics.

## Benchmarking across a service boundary

Do not mix local engine latency with service-boundary latency without labeling it.

Report separately:

- SQL-visible end-to-end latency;
- local database work;
- external call time;
- queue wait time if async;
- retry count and timeout count;
- throughput denominator, including payload size or work units.

For fair comparison, equalize the decision condition, not the implementation knobs. If one
design is synchronous and another is async, compare under the same user-visible contract:
freshness target, timeout budget, retry policy, and failure semantics.

If one design is absolutely better, state a mechanism hypothesis. For example: "the async
path wins because it batches fixed per-call overhead." Then look for the hidden dimension
where the claim should stop holding: small payloads, low concurrency, strict freshness, or
retry storms.

## Observability without adding a platform

Start with durable, queryable evidence before adding infrastructure:

- structured logs with request id, contract version, status transition, retry count, and
  external latency;
- result rows that include compact usage/cost/error metadata;
- SQL views for operational summaries;
- reports that link raw result JSON/CSV, logs, and reproduce commands.

The point is not more dashboards. The point is that a failed or slow boundary crossing can be
attributed to the right layer without guessing.
