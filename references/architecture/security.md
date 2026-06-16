# Reference: security hardening for a PostgreSQL extension

A PostgreSQL extension runs inside the database's trust boundary and (if it calls out) can
make the server an HTTP client. These are the hardening patterns — most apply to any
extension, not just one that makes outbound calls.

---

## SECURITY DEFINER + search_path pinning (the non-negotiable one)

A `SECURITY DEFINER` function runs with the *definer's* privileges, so callers needn't own
the catalog tables. That power is also the classic injection vector: if `search_path` is
attacker-controlled, the definer function can be tricked into calling an attacker's function
or reading an attacker's table. **Pin `search_path` on every definer function:**

```sql
ALTER FUNCTION ai.search(...) SET search_path = pg_catalog, public, ai, pg_temp;
```

`pg_catalog` first (so built-ins can't be shadowed), the extension's own schema, and
`pg_temp` last (never early — a temp object must not shadow a real one). Do this for *every*
function, not just the obvious ones, and treat a missing `SET search_path` as a review-blocking
defect.

---

## Least privilege: ship a dormant REVOKE file, never auto-apply

Default to the permissive single-tenant case (PUBLIC EXECUTE) so `CREATE EXTENSION` just
works, and ship a **separate, opt-in** `restrict_acl.sql` that the extension never runs
itself:

- It only `REVOKE`s (EXECUTE on every `ai.*` function, ALL on tables) from `PUBLIC`, and
  grants *nothing* — forcing the operator to grant per-role, per-function (least privilege by
  construction).
- Include commented sample grants as documentation.

This separates "works out of the box" from "locked down for multi-tenant," and makes the
hardening an explicit, auditable operator action.

## Read/write is a privilege boundary, not just an API shape

Classify every callable as **read-side** (`search`, `ask`) vs **write-side**
(`create_pipeline`, `ingest`, `*_async`) and let deployments grant the two sets to different
roles. Organize the ACL file and the security doc along this axis so an operator can give an
app role read-only access trivially.

---

## Secrets by reference, resolved in the privileged process

Never store the secret value in a table. Store only the **environment-variable name**
(`ai.endpoints.api_key_env`), and have the definer function resolve it at call time
(`std::env::var(name)`):

- The key value never enters a table, never appears in `pg_dump`, and is invisible to
  non-owner roles (only the definer process can read its env).
- This is the general answer to "how does a DB make authenticated outbound calls without
  putting the secret in the DB."

**Redaction view as a column allowlist.** Expose the registry through a stable contract view
(`..._v1`) that *omits* the `api_key_env` column. The projection doubles as a column-level
allowlist — granting `SELECT` on the view cannot leak the secret-reference column even by
accident.

---

## SSRF: the reachable-host set is an owner-only catalog, not a call argument

When the DB makes outbound HTTP, the set of reachable hosts must come from an **owner-only
registry row** (`ai.endpoints.base_url`), never from a per-call argument. Then the SSRF
allowlist is enforced by table ACL — only someone who can write `ai.endpoints` can add a
destination. A per-call URL argument is an open SSRF hole; don't accept one.

---

## Document the threat model's out-of-scope set

A security doc that implies total coverage is dishonest. Enumerate explicitly what the
extension does **not** defend against and the per-gap mitigation, e.g.:

- Malicious *owner* / leaked env — out of scope (the owner can read secrets by definition).
- No rate-limiting → "mitigate at the provider project spend-limit level."
- Shared NOTIFY channel can be spoofed by anyone who can `NOTIFY` → document it; the result
  table (source of truth) is still authoritative.
- No RLS on the results table → note it if multi-tenant isolation is needed.

Listing the non-goals with mitigations is itself the security artifact — it tells an operator
exactly what they still own.
