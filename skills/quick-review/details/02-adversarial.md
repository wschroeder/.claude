# Pass 2 — Adversarial

Construct an input/state that crashes the code. Concurrent execution, partial failures, stale data, unexpected NULL. For each new path: what DB/API state makes this crash instead of error? Angle numbering matches SKILL.md.

## 2.1 Discarded results

Is the return value bound and checked? A fallible call whose result is ignored (e.g., `Stripe.Subscription.delete(id)` on its own line) is a bug — the failure case is invisible.

A result can also be bound and still ignored: `const deleted = await remove(...)` followed by a side effect that runs whatever `deleted` holds, such as an audit event, a notification, or a success response. Check that every side effect after the call depends on the result. Give each changed function its own line here, not one line for the diff.

A promise that is not awaited (`void`, fire-and-forget) and does durable work dies with the process. Name the stored record that reruns that work after a restart, or the angle is a Fix. Worked example: a reviewer's save moved a document and started its verification check without awaiting it, and the worker step cleared the request before the check ran. Our review wrote "deliberately not awaited (void) and catches its own errors" and filed the lost retry as a Note. An outside reviewer caught it; the fix stored the request and cleared it only after the check finished.

## 2.2 Semantic completeness

Does the call achieve its stated intent, or is it a partial step? Compare the function/variable name to what the API call actually does. Example: `maybe_attach_payment_method` that calls `attach` but never sets the attached method as the default — the name promises more than the implementation delivers.

If you check a partial body against today's call sites, you learn whether anything is open now, never whether the body is complete. Judge the body against every input its name promises to handle. Worked example: a patch to the Kita XSS scanner checked props passed by name and skipped props passed through a spread. Two handoffs carried the gap, and our review answered it with "All 13 JSX spreads print `markup=[]`", which measured today's spreads. An outside reviewer built a spread that carried user text into a markup prop, and the scanner passed it.

## 2.3 Defense-in-depth in isolation

Read each new/changed function assuming an UNTRUSTED caller — not the nice caller you're reviewing. If the function relies on "my caller validated X before calling me," grep every live caller to verify. More importantly, guard at the function boundary too. Any future refactor can break the caller's validation without touching this function; the boundary guard is insurance.

A function that returns `:ok` for a sentinel (e.g., "no challenge stored → pass") is fail-safe only if a sibling function in the call chain still enforces authentication; if that sibling is ever loosened, the sentinel becomes a fail-open.

"The page always sends it" is not a reason to drop a finding, and neither is a guard further down that still refuses the worst case. Anyone can post the request without the field. Post it that way, through the route, and quote what the server answers. The proof is that answer, not a reading of the form.

Measured (2026-10-22): `downloadBundle` skipped its changed-since-preview check when `previewedKey` was absent. Our review dropped it twice: once because the bar's Download button only posts to the preview, and once because the server still refused blocked files. A request with no key downloaded whatever the selection held at that moment, without the preview the spec requires. The outside reviewer found it, and the fix made the key required and answered 409 with the current preview.

## 2.20 Checker evasion

When the diff adds or changes a checker — a linter, a scanner, a validator, an allowlist — the checker is the code under review, and its inputs are the source it reads. List each way someone could write the forbidden thing so that it reaches the consumer but not the checker, write one fixture per way, and run the checker on each. The usual ways:

- a different case, where the consumer folds case and the checker does not (an HTML parser lowercases attribute names)
- a computed key or a value whose type is `string`, where the checker reads only literals
- a spread, where the checker reads only named attributes or arguments
- a look-alike, where the checker matches a name another type can also carry (a property called `__brand`)
- a type with no declaration site (`Record`, `Pick`, a mapped type), where the checker trusts a property by where it was declared
- a value stored first (a const, a let, a destructure, a function's return), where the checker reads only the expression at the point of use

The proof is each fixture with the checker's output beside it. Matching the checker's list against today's registered names, or grepping today's code for the look-alike, measures the present and proves nothing about the next input. Worked example: lint-datastar matched `data-on-click` but not `data-on-Click`, read only literal keys, and accepted any `__brand` property as its own. Our review wrote "DATASTAR_PLUGINS matches all 22 registered names" and "`__brand` appears only in datastar-expression.ts". An outside reviewer wrote three fixtures and got past the linter with each. After those fixes our review wrote "2.20 checker evasion: DEMONSTRATED, 7 probes", every probe one of the first four ways. The same reviewer then got past it again with a `Record<'data-text', string>` spread, whose property has no declarations, and with `const text = label as 'x'` stored before the attribute read it.

When two or more ways round share one thing the checker trusts, such as a type, a flag, or where something was declared, name it. Then run the checker with that trust removed, on the fixtures and on the real codebase. If a fix closes the ways one at a time, it leaves the trust open. A reason to keep the trust, such as "it would fire on legitimate code", stays a hypothesis until that codebase run shows the false alarm. Worked example: lint-datastar trusted any value whose type was a string literal. Our reviews found a literal cast, then a stored cast, a branch, an assignment, a literal-typed parameter, and a tuple element, and each fix followed one more form. We kept the trust on a guess that dropping it would fire on `query.sort as …` in the activity routes. An outside reviewer dropped it, and the app linted clean.

## 2.4 Divergent-input races

For each unique constraint or race-handling code path, consider concurrent writes with DIFFERENT payloads — not just identical-retry. When a race handler returns `:ok` on conflict, trace: does the persisted row match what the success path then uses downstream? The stored state and the caller's next action must agree on the same payload, or one concurrent user's input gets attributed to another user's stored state.

**Classic trap:** `create_or_find` returns `:ok` on "already exists", but the caller then operates on the caller's intended payload instead of the stored payload — issuing permissions for scopes the DB never persisted.

## 2.5 Shared-state race severity escalation

When a race window touches AUTHENTICATION, AUTHORIZATION, BILLING, single-use tokens (refresh tokens, password-reset codes, magic links, PKCE codes, CSRF nonces, idempotency keys), or any state where DUPLICATION implies a security or financial loss (double-spend, double-issuance of token pair, double-grant of trial, double-charge avoidance), the finding is **Fix-class, not Note-class**.

Justifications that under-weight the severity — "matches the library's posture", "known limitation upstream", "the library does this too", "single-instance deploys are unaffected" — are NOT acceptable downgrades. The library may itself be flawed; deploys can scale; the recommendation bar is the Yes-to-any gate.

The same severity holds for a race on a gate that other code trusts: a flag such as verified, approved, or posted, which downstream reads take as proof that a check passed. If a race lets the flag go true while the check it records no longer holds, the finding is Fix-class. "No auth, billing, or single-use stakes" does not downgrade it.

Worked example: a document verify ran its line-item reconciliation check and its `verified_at` update as two separate queries. A line-item edit landing between them left a verified document whose items no longer reconciled, and the customer totals read that flag. A review filed the shape as a Note under the "no auth, billing, or single-use stakes" wording, and an outside reviewer then raised it on the PR. The fix ran the check and the update inside one transaction that locks the document row (`select … for update`), and every line-item edit takes the same lock.

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

## 2.7 Self-race / lease TOCTOU (two copies of one path against a DB row)

A common stampede-prevention pattern: a cron handler reads a row `cron_job_state.last_completed_at` (or `leases.expires_at`, `job_locks.acquired_at`), checks whether the configured idle window has elapsed, and proceeds. If two invocations arrive concurrently, BOTH read the same value, BOTH pass the gate, BOTH execute the job. This is canonical CWE-362 — the check (read) and the act (update) are separated by an event boundary.

Mitigations the orchestrator typically claims (single Vercel cron, single Quartz schedule, single Oban worker) are environmental, not invariants; manual triggers, retries, and migrations to a different scheduler invalidate them silently.

The fix is an atomic CAS: `UPDATE state SET last_started_at = now() WHERE path = ? AND last_completed_at = <snapshot>` and inspect the matched-row count — zero rows updated means another invocation won the gate, so skip. The same pattern applies to:
- **Supabase / PostgREST:** `.update({...}).match({ path, last_completed_at: snapshot })` and check `count`
- **Postgres advisory locks:** `pg_try_advisory_xact_lock(hashtext('cron:path'))` returns false on contention
- **Redis:** `SET key value NX EX <ttl>` returns nil on contention
- **DynamoDB:** `UpdateItem` with `ConditionExpression: "last_completed_at = :snapshot"`

The non-atomic read-then-update shape is Fix-class regardless of how single-source the trigger is today. The doc that claims "completion-gated" but the code that implements read-then-update is itself a comment/code drift finding (Pass 6).

### Two copies of a multi-write transaction

The same race hides in any path a person or a job can start twice for the same row: two re-uploads of one file, two clicks on "retry", two webhook deliveries. Wrapping the path in a transaction does not order the two copies. Under Postgres's default `read committed`, both transactions read the same starting state, and each deletes, overwrites, and prunes before either commits. Only a lock that both copies take before their first write orders them: `select … for update` on the row they rewrite, an advisory lock, or a CAS predicate whose matched-row count the code checks.

Ask what each copy writes, not only whether the last step runs twice. A downstream claim that picks only the newest job (`for update skip locked`, "claims only the latest") answers the second question and says nothing about the first. Worked example: two re-uploads of one file each deleted the documents read from it, overwrote its page limit, and pruned its pages before the worker claimed anything. Two reviews read the worker's claim query, wrote "the stale row is never run", and left the race open. A test that ran both uploads at once showed both starting a read. The fix locked the file row at the top of the re-upload transaction.

Artifact: run two copies at once against real Postgres (`Promise.all` of two calls, or one copy held open with `pg_sleep` while the second runs), and assert on what each copy wrote: audit events, rows deleted, and the final value of every column the path sets. Reading the transaction boundary, or grepping the downstream claim, is not this artifact.

Assert the invariant the code promises, not only that nothing failed. If the path keeps at most 30 rows, count the rows after the run and compare with 30. A run that reports no errors over thousands of calls proves only that nothing threw. Run at least as many copies at once as production can, which is the replica count times the connection pool size. Worked example: a trim that kept the newest 30 job runs passed two concurrent copies with no errors on a 4-connection pool. Forty writers at once left 43 to 69 rows.

## 2.18 Cross-writer race

2.4 to 2.7 ask whether one path is safe against a second copy of itself. This angle asks whether it is safe against every other path that writes the same rows. Concurrency findings in a review usually hide here, because each function looks atomic when read alone.

Method:

1. For each write path in the diff, list the tables it writes and the parent rows its foreign keys reference.
2. Grep for every other function that writes, deletes, or merges those rows or those parents, inside the diff and outside it.
3. Build a table of the pairs. For each one, name the lock, constraint, or transaction that puts the two in order. A pair with nothing between them is the finding.

Watch for these two signs:

- **Sibling lock asymmetry.** Most writers of an entity open with `select ... for update` on it, and one does not. If the review writes "A, B, and C lock the row; D is one statement", then it has already described the finding. One statement is atomic against itself and orders nothing against a writer holding a row lock.
- **Two paths taking the same two locks in opposite orders.** Quote each path's lock order side by side. Count the locks a statement takes without asking as well as the explicit ones: an UPDATE or DELETE locks every row it touches, and an insert or a foreign-key change takes a key-share lock on the parent row. Worked example: the document save took the new-parent lock and then the remembered-number lock, while the record page took them in the reverse order, and the two deadlocked (Postgres `40P01`). Second worked example: the record-page edit locked its remembered row and then key-share locked the parent, while the parent merge locked both parents `for update` and then ran `update app.remembered_numbers set parent_id = ...`, which locks those rows. Our review listed "mergeParent = documents of records holding numbers under parent -> parents FOR UPDATE", left out the UPDATE's row locks, and wrote "No pair reversed."; the two deadlocked. Count the table lock each statement needs too. In Postgres, `select … for update` takes only ROW SHARE on the table, which a SHARE ROW EXCLUSIVE lock held by another path does not block. The first UPDATE, INSERT, or DELETE needs ROW EXCLUSIVE, which it does block. So a path that row-locks a row and then writes it deadlocks against a path that holds a table lock and then writes the same row. If either path takes a table lock, then quoting the lock order is not proof: hold the pair open and run them. Third worked example: a person's merge locked the record it kept `for update` and then updated it, while the nightly sync held a share row exclusive lock on the table and then upserted that same record. Our review wrote "A user merge's UPDATE takes row exclusive, which waits behind share row exclusive.", and a second review checked only the record merged away, which the sync never writes. Neither review ran the two transactions, and the outside reviewer found the deadlock.
- **A writer that runs after a delete, a combine, or a duplicate left behind.** Once a path deletes or combines rows, or leaves duplicates that another path assumed could not exist, run every other writer of that table once more afterwards, not only at the same time, and show the result holds. Worked example: a parent merge deleted a record as a duplicate, and the next spreadsheet import's upsert inserted it again under a new id. Our review wrote "2.5, 2.7, and 2.18 races: DEMONSTRATED by [T3]" and ran no writer after the merge. Second worked example: a parent merge kept one remembered number on two records, and the next reviewer's link of an ambiguous document deleted the other record's copy and moved its unverified documents onto the linked record. Our review wrote "2.18 cross-writer: DEMONSTRATED, held-transaction tests for merge, sync, page add, and save", all run at the same time as the merge and none after it.
- **A child insert against a parent another writer is deleting.** Writer A inserts a child row that references a parent. Writer B has locked the parent and is deleting it or merging it into another. A's insert blocks on the foreign key's key-share lock. After B commits, the insert fails with a foreign-key violation (Postgres `23503`), and the route returns 500 where it should return 404. To fix it, have A lock the parent first in the same transaction, so that A either runs before B or finds no parent.

Artifact: hold writer B's transaction open in one session (for example with `pg_sleep`), run writer A in a second, and show the outcome. A test that races A against another A does not demonstrate this angle. "The outcome" means the invariant both writers promise, checked on the rows afterwards, at the concurrency production can reach (replicas times pool size). "Ran clean" is not an outcome.

List the writers by name, and include the deferred ones: a worker job that resumes later from what it captured earlier, and a model call that is in flight while a person edits the same rows. Pair each writer with its own test. "The concurrency tests" as a group is not proof for any one pair.

Worked examples, both from one pull request that added remembered external numbers:

- The moved-document check captured a remembered row's id, then resumed after the nightly sync had moved that row to another record without changing its id. The id still matched, so the check moved a waiting document onto the retired record. Our review wrote "2.18 cross-writer: DEMONSTRATED for the sync against the link and against the add", which paired the sync with two writers and never with the deferred check.
- Initial processing applied the model's answer after a reviewer had deleted the remembered number it relied on, and verified the document against the old record's evidence. Our review wrote "2.5, 2.7, and 2.18 races: DEMONSTRATED by the F1 test and the concurrency tests.", naming no pair at all.

## 2.19 Read skew

2.7 and 2.18 cover paths that write. This angle covers a path that reads, including a read-only page, a report, or a health check. If the path makes two or more queries and another writer can change the rows between them, then the second query can contradict the first, and the path reports a state that never existed. "Read-only, no writes" does not make this angle N/A.

Method:

1. For each path in the diff that makes more than one query, write down the condition that selected each row in the first query.
2. Find every writer that can change that condition between the queries.
3. Check whether the later query, or the code that joins the results, re-checks the condition on the fresh data. A path that trusts the first query's selection is the finding.

The fix is either to re-check the selecting condition on the second read, or to make both reads one query or one `repeatable read` transaction.

**A decision and its re-check use one read.** When a path decides from data it read, then re-reads under a lock to confirm nothing changed before applying the decision, the data the decision judged and the data the re-check compares must be the same read. If the path reads twice before deciding, then a writer between those two reads goes unnoticed: the re-check compares the fresh copy, and the decision came from the older one. A re-check that finds both reads empty (null) has confirmed nothing, so refuse it rather than count it a match.

Worked example: a check on a moved document read document B's line items, handed them to the reconciliation and the verification model, then took a fresh read of B to use as its check token. A reviewer's edit to B between those reads left the token matching under the lock, and the check verified B from items the reviewer had already changed. Copilot found it. The fix reads B once and uses that read both as the model's input and as the token.

Worked example: a Health page listed failed files in two steps. The first query picked files whose latest sync had failed, and the second fetched those files' latest syncs. A retry between the two queries started a new running sync, and the page still listed the file as failed. Two reviews marked the path "N/A, read-only". The fix re-checked `sync?.status === 'failed'` on the sync the second query returned.

Artifact: run the real writer between the two reads, and assert what the path reports. Wrap the function that makes the second query so that it runs the writer first, then calls through. A test named like `does not list a file as failed when someone retries it while Health reads the files` does this. Reading the two queries and arguing that the window is small is not this artifact.

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

## 2.14 N+1 calls

For every loop the diff adds or changes (`for`, `Enum.map`, `Enum.each`, `.map`, `.forEach`, `for await`, a list comprehension), check whether its body makes a database query, an HTTP request, or any other remote call. One call per element turns a page of 50 rows into 51 round trips, and the cost grows with the data rather than the code.

**Discovery method:** grep the loop bodies for `Repo.`, `from(`, `fetch(`, `axios`, `prisma.`, `.query(`, `Req.`, `HTTPoison`, and the project's own API client names. For Ecto, also look for association access inside a loop that has no `preload` upstream.

**First ask whether the call is needed.** Where it fetches or parses something to work out a value the database already stores, such as a file's page count, the fix is to read the stored value, and batching it only makes an unneeded call faster. Worked example: a preview fetched every selected PDF to count its pages, this check flagged the reads as slow and unmeasured, and a slice was planned to measure them, while the query behind the preview already selected each file's stored page count.

**Fix:** batch the call (`where: x.id in ^ids`, a bulk endpoint, `Repo.preload`, a dataloader) and join the results in memory. Construct the input that shows it: the row count at which the loop exceeds the request timeout.

## 2.15 Quadratic scans

Two shapes:

- A nested pass over the same collection, or over two collections that grow together: `for a in xs, for b in xs`, `Enum.find` inside `Enum.map`, `.filter` inside `.map`.
- A membership test on a list inside a loop: `x in list`, `Enum.member?/2`, `.includes()`, `.indexOf()`, `list.contains`. Each test is a linear scan.

**Fix:** build a `MapSet`, `Set`, or map keyed on the lookup field once, before the loop. Repeated `++` onto the end of a list inside a loop is the same shape in Elixir and Erlang; prepend and reverse once instead.

A collection bounded by a small constant (the five states of an enum) is `N/A` for this angle; say what bounds it.

## 2.16 Resource not released

For every resource the diff opens, find the line that releases it on every exit path, including the error path:

- files, sockets, and database connections checked out by hand
- event listeners, subscriptions, observers, and PubSub subscriptions
- timers and intervals (`setInterval`, `setTimeout` held in a ref, `Process.send_after` loops, `:timer.send_interval`)
- processes and tasks started outside a supervisor (`spawn`, `Task.start`, a bare `GenServer.start`)
- React effects that attach anything without returning a cleanup function

A resource with no release line, or one released only on the success path, is the finding. The artifact is the line that opens it and the absence of a close on the error branch.

## 2.17 Unbounded growth

Any structure the diff adds to without a bound: a module-level cache or array, a map held in process state, an ETS table, a `Map.put` accumulator that lives across requests, a memoization table. Check for an eviction rule, a TTL, or a size cap.

If none exists, construct the input that fills it: the key the caller controls (a user id, a URL, a query string) and the rate at which a caller can mint new keys. A key the caller controls with no cap is also CWE-770 and a denial-of-service shape; route it through the security axis of the Yes-to-any gate.

One request can grow without bound too. A whole file, response body, or archive that the diff builds in memory must name what limits its size: a quoted cap, or a stream. If it names neither, measure peak memory at the largest size the deployment allows, and compare it with the container's memory limit. "No handles or caches" does not answer this angle, and a security review's exclusion of denial of service does not drop it either, because the person it hurts is the one ordinary user whose download is big.

Measured (2026-10-22): `zipStored` built the whole export bundle in memory, PDFs included. One review listed it as a hypothesis and never measured it, security-review dropped it under its exclusion for denial of service, and a third answered 2.16 and 2.17 with "N/A, no handles or caches". The outside reviewer saw memory climb to 1.5 GiB, and the deployed containers get 2 GiB. The fix streamed one document at a time, and a 500 MiB zip then peaked at 71 MiB of buffers.

Follow each read the diff calls into, including helpers in files the diff does not touch, such as a storage download or a file read. A helper that gathers a whole blob before writing it holds that blob in memory however carefully the caller streams. Run the memory proof with one input as large as the biggest one expected, not only with many small ones: many small files keep the peak low while each one is held whole.

Measured (2026-10-22): after that fix, the bundle still copied each stored PDF to disk through `materializeFile`, which gathered the whole blob into one buffer first. The next review answered 2.17 with "POST bodies" and "note on bodyLimit", and its memory proof measured the whole zip. A second outside review found the buffer. Against Azurite, a 100 MB blob grew buffers by 116 MB with the old helper and by 10 MB once it piped the download stream to the file.

## 2.21 Unbounded attempt

A call that hangs raises no error, so a retry around it never reaches its next attempt, and a caller waiting on it waits forever. For every retry loop, call to an outside system (a database, an HTTP API, a model, a queue), and lock wait the diff adds or wraps, name what ends one attempt: a request timeout, a `statement_timeout` or `lock_timeout`, an `AbortSignal.timeout`, a pool's `connectionTimeoutMillis`. Quote the line that sets it, and show a test that fails when the limit is removed or raised.

A limit set elsewhere counts when you quote it and show it reaches this call. A client library's default counts only when you quote its documented value; many default to no limit. The attempt count, the backoff, and the total wait across attempts are not a limit on one attempt. Check the wait for a resource too, such as a pool connection or a lock, not only the work done once the resource is held. If nothing ends an attempt, that is a Flag, and a Fix when a request a person is waiting on sits behind it.

Measured (2026-10-21): the branch retried the save of a document check five times with backoff and jitter. The review ran six mutations on the attempt count, the delay, and the jitter, and noted the total wait across attempts. It never asked what ends a save that hangs, and the operator caught it. The fix sets `select set_config('statement_timeout', $1, true)` inside the transaction, before the `select ... for update` that takes the row lock, so the lock wait counts. Its test reads `current_setting('statement_timeout')` from inside the save and fails when the limit is raised, made session-wide, or not passed. The wait for a pool connection stayed unlimited, which this angle reports as its own finding.

## 2.22 Partial compatibility check

A check that two things fit together, such as one config naming another's files, a schema checked against a reader, or a source borrowing another source's inputs, has to compare every field the consumer reads from each. List those fields from the consumer's code, then quote where the check compares each one. A field the consumer reads and the check skips lets a pair through that fails later, away from the check that should have named it.

Worked example: `fileCheck` in a client repository refused a source whose named role had a different primary file kind. If the named role had a CSV alternative or `multiFile`, the picker would offer it and `runLocal` would then throw, because the check never compared either. The subagent arm of the 2026-10-22 review trial found it by probing both; the single session did not.
