# Reference: integrating an external (often paid) service / provider

When the extension calls out to an external API — an LLM/embedding provider, a model server,
any third-party HTTP service — these patterns keep it provider-agnostic, configurable,
testable without paying, and safe. (Security specifics — secrets, SSRF — are in
`security.md`; this file is about the integration shape.)

---

## Contents

- [Config lives in the DB as a registry, not in code](#config-lives-in-the-db-as-a-registry-not-in-code)
- [Provider abstraction: swap via env, native adapter only for the odd one out](#provider-abstraction-swap-via-env-native-adapter-only-for-the-odd-one-out)
- [The data-contract invariant (ADR-007)](#the-data-contract-invariant-the-most-important-lesson-adr-007)
- [Testing against a paid external dependency: mock vs real](#testing-against-a-paid-external-dependency-mock-vs-real)
- [Benchmarking a RAG / embedding / LLM pipeline](#benchmarking-a-rag--embedding--llm-pipeline)
- [Observability with zero external infra](#observability-with-zero-external-infra)

---

## Config lives in the DB as a registry, not in code

Put endpoints/models/pipelines in catalog tables the extension owns:

```
ai.endpoints  (name, base_url, api_key_env, ...)   -- where + how to auth
ai.models     (name, endpoint, dim, metric, ...)   -- a usable model on an endpoint
ai.pipelines  (name, embed_model, ...)             -- a named config bundle callers reference
```

Callers reference a *pipeline name*; everything resolvable changes in one place. This beats
per-call URL/model arguments (un-auditable, an SSRF hole) and per-service env (causes drift —
see the invariant below).

## Provider abstraction: swap via env, native adapter only for the odd one out

Wrap each provider behind one thin abstraction (`embed(texts)`, `generate(messages)`). The
big win: **any OpenAI-compatible endpoint works by changing env only — no code change.** One
abstraction covers OpenAI, Gemini (compat mode), OpenRouter, Ollama, vLLM, local servers;
write a *native* adapter only for a provider with an incompatible API (e.g. Anthropic
messages). The provider matrix becomes a documentation table, not a code fork:

```
LLM_PROVIDER=openai  OPENAI_BASE_URL=<compat endpoint>  LLM_MODEL=...  EMBED_MODEL=...
```

Empty-string env trap: a base-url env set to `""` is *not* the same as unset — many SDKs use
the empty string as the base URL and fail with a connection error. Strip empty values at
service startup (`del os.environ["X"]` if blank).

---

## The data-contract invariant (the most important lesson; ADR-007)

Independently-deployable services can be **independently callable yet not independently
consistent** — they are coupled by a *data contract*, not by code. For an ingest path + query
path over the same store, the embedding **model + dimension + metric + collection** is a
shared invariant. Violate it (write side embeds with model A, read side queries with model B)
and you get **silent corruption — wrong results, not an error.**

Consequences for any split-compute design:

- Split compute freely, but **never fork the registry** — bind the model choice to the
  *pipeline registry row*, not to per-service env (per-service env is exactly how write/read
  drift happens).
- An invariant-changing operation (change embed model/dim) must be a **guarded** operation
  that forces re-ingest, never a silent config edit. Enforce it at runtime (fail loud on a
  dimension mismatch — see `async-outbox.md`), not just by convention.

---

## Testing against a paid external dependency: mock vs real

- **Mock for correctness/CI ($0, offline, deterministic).** Ship a mock server that mimics
  the provider's API; the full E2E (`make run-rag-mock`) runs in CI on every PR with no API
  key and no cost. The mock returns fixed embeddings/completions so assertions are stable.
- **Real for a sanity check / latency, gated and cost-minimized.** `make run-rag-real` hits
  the live API; use the cheapest model (e.g. a `-mini`, ~$0.001/run) and require the key only
  here. Correctness rests on the mock; the real run is a small confidence check.
- The E2E asserts the *pipeline contract* end to end: ingest → wait-for-async-complete →
  chunks stored → search returns rows → ask returns an answer → cleanup. Isolate test data by
  a unique `collection` so cleanup is automatic and reruns don't collide.

---

## Benchmarking a RAG / embedding / LLM pipeline

The external call dominates, so the methodology differs from a pure-DB benchmark:

- **Say the network is in the path, and give the without-network estimate.** "All timings
  include the provider round-trip; pure-DB latency is much lower (a local embed model would
  drop p50 to ~10–30 ms)." Never present provider-network latency as engine latency.
- **Mock for correctness, real for latency (latency is the point).** The inverse of the
  testing split: the *bench* runs real, flagged network-dominated; *correctness* uses the
  mock.
- **Avoid the throughput anti-metric.** "docs/min" is meaningless without controlling
  document size — report `chars/min` or an explicit `est_tokens = chars/4` ("rough, relative
  comparison only").
- **Attribute every latency delta to a named cause.** Split search into dense / hybrid / MMR
  with p50/p95/p99 and annotate the source of each delta (hybrid = "network + BM25 scan";
  MMR = "numpy cosine loop over fetch_k"), computed live as the difference.
- **The harness owns the full lifecycle** — cleanup → setup → measure → cleanup — and is
  idempotent across runs (clean any previous run first).
- **Filter-correctness can't be asserted by "0 results."** Vector search has no similarity
  threshold, so you can't prove a filter excluded everything; instead assert **every returned
  row matches the filter.**

---

## Observability with zero external infra

Defer Prometheus until actually needed. Emit **structured JSON logs** (one object per line to
stdout, custom fields via `extra=`), and persist usage/cost into the result row's JSON
(`ai.results.data`), exposed as a SQL view (`usage_v1`). Observability becomes
`docker logs | jq` plus SQL `GROUP BY` — no new infrastructure.
