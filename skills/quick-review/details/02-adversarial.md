# Pass 2 — Adversarial

Construct an input/state that crashes the code. Concurrent execution, partial failures, stale data, unexpected NULL. For each new path: what DB/API state makes this crash instead of error? Angle numbering matches SKILL.md.

## 2.1 Discarded results

Is the return value bound and checked? A fallible call whose result is ignored (e.g., `Stripe.Subscription.delete(id)` on its own line) is a bug — the failure case is invisible.

## 2.2 Semantic completeness

Does the call achieve its stated intent, or is it a partial step? Compare the function/variable name to what the API call actually does. Example: `maybe_attach_payment_method` that calls `attach` but never sets the attached method as the default — the name promises more than the implementation delivers.

## 2.3 Defense-in-depth in isolation

Read each new/changed function assuming an UNTRUSTED caller — not the nice caller you're reviewing. If the function relies on "my caller validated X before calling me," grep every live caller to verify. More importantly, guard at the function boundary too. Any future refactor can break the caller's validation without touching this function; the boundary guard is insurance.

A function that returns `:ok` for a sentinel (e.g., "no challenge stored → pass") is fail-safe only if a sibling function in the call chain still enforces authentication; if that sibling is ever loosened, the sentinel becomes a fail-open.

## 2.4 Divergent-input races

For each unique constraint or race-handling code path, consider concurrent writes with DIFFERENT payloads — not just identical-retry. When a race handler returns `:ok` on conflict, trace: does the persisted row match what the success path then uses downstream? The stored state and the caller's next action must agree on the same payload, or one concurrent user's input gets attributed to another user's stored state.

**Classic trap:** `create_or_find` returns `:ok` on "already exists", but the caller then operates on the caller's intended payload instead of the stored payload — issuing permissions for scopes the DB never persisted.

## 2.5 Shared-state race severity escalation

When a race window touches AUTHENTICATION, AUTHORIZATION, BILLING, single-use tokens (refresh tokens, password-reset codes, magic links, PKCE codes, CSRF nonces, idempotency keys), or any state where DUPLICATION implies a security or financial loss (double-spend, double-issuance of token pair, double-grant of trial, double-charge avoidance), the finding is **Fix-class, not Note-class**.

Justifications that under-weight the severity — "matches the library's posture", "known limitation upstream", "the library does this too", "single-instance deploys are unaffected" — are NOT acceptable downgrades. The library may itself be flawed; deploys can scale; the recommendation bar is "yes to any" of security/perf/maintainability.

If a tighter primitive exists (`UPDATE ... WHERE used_at IS NULL RETURNING *` pattern, advisory lock, atomic CAS, single-flight cache), surface it as the Fix. The race itself is the finding; document the proposed fix even if the team chooses to defer.

## 2.6 Resource-create-then-attribute atomicity (security tag as access control)

When the diff creates an external-system resource (AWS SSM Parameter, S3 object, KMS grant, IAM role-policy, Azure secret, GCP secret-manager version, K8s Secret/ConfigMap, Vault kv-v2 entry, a row in a permissions table) and then writes an ATTRIBUTE on that resource that GATES access — typically a tag, label, ACL entry, annotation, ownership column, or principal binding — those two operations together form a security-critical pair.

### 2.6a Tag-after-create with a separate API call

AWS `PutParameter --tags` is atomic if the tag is included in the create call; `PutParameter` followed by `AddTagsToResource` is NOT. Between the two calls, the resource exists without its security tag. If the access-control policy keys on that tag (`Condition: { StringEquals: { ssm:resourceTag/X: ... } }`), the policy MAY block reads (default-deny is the safe direction) but any IAM principal whose policy doesn't depend on the tag (a wildcard role, a `*` allow on the resource path, a managed policy union) can read it during the window.

The same shape appears in IAM `CreateRole` + `AttachRolePolicy`, K8s `create secret` + `kubectl label`, GCP `create secret` + `add-iam-policy-binding`.

### 2.6b Overwrite-existing without re-applying the tag

AWS `PutParameter --overwrite` deliberately does NOT carry tags forward — `Tags` is only honored on the create path. If the code does `PutParameter --overwrite Tags: [...]`, the tags silently no-op; the parameter retains whatever tags (or none) were on the previous value. The fix is to issue `AddTagsToResource` separately whenever the tag is required, AND to verify the prior resource had the tag (no, the API does not error on missing tags).

The same trap exists in GCP `secrets versions add` and Vault `kv put`.

### 2.6c Stale-delete then put (race against concurrent reader)

A `DeleteParameter` followed by `PutParameter` is the worst of both worlds for the tag invariant: the resource briefly does not exist (any consumer mid-read sees a transient error), and the new resource starts un-tagged for the put window. If the consumer retries on transient errors, it can hit the un-tagged window. Fix: `PutParameter --overwrite --type SecureString ...` (or the equivalent CAS primitive) followed immediately by `AddTagsToResource`. The delete is rarely necessary.

**Discovery method:** for every IaC or runtime resource-creation call in the diff, locate the policy/condition/binding that gates ACCESS to the resource. If that policy keys on an attribute (tag, label, annotation, ownership column), check whether the create + attribute writes are atomic OR ordered such that the attribute is always present before any consumer reads. A Fix-class downgrade is justified only if the gating policy fails CLOSED on the missing attribute AND no other policy union grants access during the window. Document the closed-window reasoning explicitly; default is Fix.

## 2.7 Completion-gate / lease TOCTOU (read-then-update against a DB row)

A common stampede-prevention pattern: a cron handler reads a row `cron_job_state.last_completed_at` (or `leases.expires_at`, `job_locks.acquired_at`), checks whether the configured idle window has elapsed, and proceeds. If two invocations arrive concurrently, BOTH read the same value, BOTH pass the gate, BOTH execute the job. This is canonical CWE-362 — the check (read) and the act (update) are separated by an event boundary.

Mitigations the orchestrator typically claims (single Vercel cron, single Quartz schedule, single Oban worker) are environmental, not invariants; manual triggers, retries, and migrations to a different scheduler invalidate them silently.

The fix is an atomic CAS: `UPDATE state SET last_started_at = now() WHERE path = ? AND last_completed_at = <snapshot>` and inspect the matched-row count — zero rows updated means another invocation won the gate, so skip. The same pattern applies to:
- **Supabase / PostgREST:** `.update({...}).match({ path, last_completed_at: snapshot })` and check `count`
- **Postgres advisory locks:** `pg_try_advisory_xact_lock(hashtext('cron:path'))` returns false on contention
- **Redis:** `SET key value NX EX <ttl>` returns nil on contention
- **DynamoDB:** `UpdateItem` with `ConditionExpression: "last_completed_at = :snapshot"`

The non-atomic read-then-update shape is Fix-class regardless of how single-source the trigger is today. The doc that claims "completion-gated" but the code that implements read-then-update is itself a comment/code drift finding (Pass 6).

## 2.8 Pre-auth information oracles

For any endpoint that performs both a resource lookup (by caller-supplied identifier) AND authentication, check the ORDER of those operations. If the resource lookup runs first and its failure modes produce distinguishable error messages or status codes ("already used" vs "expired" vs "not found" vs "invalid signature"), an unauthenticated caller who can enumerate or guess identifiers gets an oracle into internal state — token/code lifecycle, user existence, session status.

Fix is either to authenticate before any resource-state disclosure, or to collapse all pre-auth failure modes into a single opaque error. Applies to OAuth token endpoints, password-reset flows, session-validation endpoints, and any lookup-then-auth pattern.

## 2.9 Identifier parse/comparison asymmetry

When code compares a parsed URL/path/header/token component against an allowlist, name the components the parser strips. Does the stripped piece matter for security?

For URL authz:
- **`.host`** strips scheme (http-downgrade bypass)
- **`.hostname`** strips port (port-hopping)
- **`.pathname`** strips query (acl bypass)
- The correct primitive for scoping bearer/cookie delivery is **`.origin`** (scheme+host+port)

Apply the same reasoning to:
- Path allowlists (normalization: trailing slash, `../`, `%2e%2e`)
- Header comparisons (case folding, whitespace)
- Secret/token comparisons (constant-time vs `===`)

The `.startsWith(issuer)` URL-comparison is the canonical anti-pattern — `https://app.example.com.evil.tld` passes a prefix check against `https://app.example.com`. Use `URL.origin` compare with try/catch on parse failure.

## 2.10 Trigger-vs-precondition ordering

For any check in a `with` chain (or imperative sequence) whose failure has a SIDE EFFECT — writes a row, sends a notification, kills sessions, revokes other state, increments a breach counter, broadcasts an event, **mints or rotates a single-use credential** — verify natural-flow filters that should reject benign cases run FIRST. The side-effecting check must never see input it didn't need to act on.

**Concrete shapes:**

- **Elixir/Phoenix:** if `ensure_not_revoked/1` triggers chain revocation when descendants exist, and `ensure_refresh_window_open/1` rejects expired tokens, then `ensure_refresh_window_open` MUST come before `ensure_not_revoked` — otherwise a replayed expired token from a legitimate user reaches the revocation trigger and DoS's the user via a benign-cause path.

- **Credential mint before authorization / quota / allowance:** an entrypoint that performs `getValidUserToken(userId)` (which rotates a single-use refresh token at the IdP), `presignS3Url(...)` (which produces a durable URL), `createStripeCustomer(...)` (which provisions a billable artifact), or any other side-effecting mint BEFORE the request's authorization, quota, allowance, or anti-abuse checks pass. A denied request that has already minted credentials has burned a rotation, polluted an audit log, or produced a usable artifact for a caller who should not have been allowed past the gate. Fix: reorder cheap filters first (request-shape, auth/identity), authorization next, quota/allowance next, side-effecting mints last.

- **Webhook handler that emits an outbound call before signature verification:** any code that fires an idempotency event, audits a request, or notifies a downstream system before the inbound signature is verified leaks abuse-burst potential. Verify the signature first; side-effect after.

Enumerate every step in the chain by side-effect-class; non-side-effecting filters always precede side-effecting triggers. If two side-effecting triggers must coexist, document the ordering invariant inline. Flag any reordering of an existing chain that moves a trigger ahead of a filter, AND any new entrypoint that introduces a side-effecting trigger above an existing filter wall.

## 2.11 Discarded error tuple pattern (TS/JS)

- **`const { data } = await supabase.from(...).select(...).single()`** — Supabase JS returns `{ data, error }`. Destructuring only `data` silently swallows DB errors; the call collapses transient outages (`PGRST-…`, connection drops, RLS denials) into "row not found" semantics. The result: the caller returns 404/400/empty-success when the right answer is 500/transient. Required shape: `const { data, error } = await ...; if (error) { logger.error(...); return { kind: 'transient' } /* or apiError(500) */; }` — then handle the `data === null` case separately.
- **`await fetch(...)` without `.ok` / `.status` check** — `fetch` only rejects on network failure; 4xx/5xx return a resolved Response. Code that consumes `await fetch(...).json()` without inspecting `.ok` happily parses an error body as the success shape.
- **`Promise.all([...])` swallowing individual rejections** — if any item rejects, the whole `Promise.all` rejects with the first one; the rest are lost. When that's not the intent (fire-and-forget audits, parallel pushes to N instances), use `Promise.allSettled` and inspect each result.
- **`.catch(() => null)` / `.catch(() => undefined)`** — the JS analogue of `case ... do {:error, _} -> :ok end`. The error reaches no log sink and no retry; the caller treats it as a happy null. Flag any catch that returns a sentinel without logging.
- **`try { ... } catch {}` (empty catch)** — verify there's a log, a retry, or a propagation. If none, the error is gone.

Each of these is the same severity class as the Elixir `_ = call` site. Fix-class.

## 2.12 Discarded error tuple pattern (Elixir)

Search the diff for `_ =` on the LHS of any function call. If the function returns an `{:ok, _} | {:error, _}` shape — `Repo.*`, `Ecto.Multi.*`, `AccessTokens.revoke/*`, `send_*`, `broadcast_*`, `:telemetry.execute` (when the handler is fallible), `ExAws.request`, HTTP clients — that's a discarded-error site. Verify the caller's response/state does not hinge on success. RFC 7009 §2.2.1, for example, allows 503 on retryable revoke errors; silently swallowing the `{:error, _}` and returning 200 is a spec violation, not defensive coding.

Side-effect-named verbs are the trap: `revoke`, `notify`, `flush`, `expire`, `invalidate` SOUND like fire-and-forget but the function still returns `{:ok | :error}`. Surface every `_ = fallible_call()` as a Fix unless the caller can prove the failure is genuinely uninteresting.

The `_ = fallible_call()` shape is one syntactic form. The same bug class also hides in `case fallible_call() do {:ok, _} -> ...; {:error, _} -> <fall-through> end` patterns where the `{:error, _}` arm does NOT log, retry, or propagate the error. Audit every `{:error, _}` (or `{:error, _reason}`) arm in `case` / `with` blocks: if the arm produces no `Logger.*` call AND no retry AND no propagation upward (the function returns `:ok` / a default counter / a sentinel as if the call succeeded), flag as Fix-class.

**Concrete failure shape:** `case AccessTokens.revoke(descendant) do {:ok, _} -> count + 1; {:error, _} -> count end` inside a chain-walk — the failure neither increments a counter nor logs, so a chain-walk that fails every revoke silently swallows the breach signal AND leaves descendants live. Both observability AND security degrade.

## 2.13 Lookup-then-filter cardinality leak

When a function performs a wide lookup (e.g., `Repo.get_by(Token, value: x)`, `Repo.one(from t in Token, where: t.value == ^x)`, `find_by_email/1` searching the entire users table) and THEN filters the result by an authorization predicate (`client_id`, `tenant_id`, `owner_id`, `org_id`, ABAC subject scope), the response distinguishes "doesn't exist anywhere" from "exists but you can't see it". That distinction is information disclosure — an authenticated caller learns about records belonging to OTHER tenants/clients/owners just by getting a different error code or status.

**Concrete shape:** `lookup_revocation_target/1` searches the entire `oauth_user_access_tokens` table → `check_revocation_ownership/2` returns `invalid_client` when `app_id` doesn't match → any client can probe whether a token belongs to a different client.

Fix is to scope the lookup query by the authorization predicate at the DATABASE level, not after the fetch — `get_by_token_for(token, application_id)` uses `WHERE value = ? AND application_id = ?`, so cross-tenant hits return `nil` and look identical to "doesn't exist". RFC 7009 §2.2 specifically requires this collapse for token revocation.

Once folded, the post-fetch authorization check often becomes dead code — remove it.
