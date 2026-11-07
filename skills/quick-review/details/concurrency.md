# Concurrency and repeated runs

Read this file now, before Pass 1, when two paths can write the same rows, or the diff takes a lock, retries, or runs a job that can run twice or overlap with itself. Angle 2.18, the race against every other writer, stays in the body and applies to every diff that writes.

## Contents

- 2.4 Divergent-input races
- 2.5 Shared-state race severity escalation
- 2.6 Resource-create-then-attribute atomicity (security tag as access control)
- 2.7 Self-race / lease TOCTOU (two copies of one path against a DB row)
- 2.21 Unbounded attempt
- 8.4 Shared destinations

Each angle below belongs to the pass its number names. Walk it in that pass, give it a disposition, and print its line in the Checklist under that pass.

## Checklist lines

```
Pass 2:
  2.4   Divergent-input races            race handler :ok; payloads diverge
  2.5   Shared-state race severity       auth/billing/single-use, or a gate other
                                          code trusts (verified, approved, posted)
                                          → Fix-class
  2.6a-c Tag used as access control    cloud resource tagged after create,
                                          on overwrite, or after delete: see 2.6
  2.7   Self-race / lease TOCTOU         2 runs at once: every write, not just 1 step
                                          proof: run two copies at once against real
                                          Postgres, or quote the lock both take first
        2.7/2.18 proofs assert the promised invariant ("≤ 30 rows"), not "no errors",
                                          at replicas × pool size copies at once
  2.21  Unbounded attempt                each retry loop, outside call, or lock wait
                                          names what limits one attempt
                                          proof: the quoted limit and a test that
                                          fails without it; a retry count is not one
Pass 8:
  8.4   Shared destinations               each name the diff writes where other
                                          runs' output also lands: two runs with
                                          overlapping input never make one name
                                          proof: run two with a shared input and
                                          list the names each wrote
```

### 2.4 Divergent-input races

For each unique constraint or race-handling code path, consider concurrent writes with DIFFERENT payloads — not just identical-retry. When a race handler returns `:ok` on conflict, trace: does the persisted row match what the success path then uses downstream? The stored state and the caller's next action must agree on the same payload, or one concurrent user's input gets attributed to another user's stored state.

**Classic trap:** `create_or_find` returns `:ok` on "already exists", but the caller then operates on the caller's intended payload instead of the stored payload — issuing permissions for scopes the DB never persisted.

### 2.5 Shared-state race severity escalation

When a race window touches AUTHENTICATION, AUTHORIZATION, BILLING, single-use tokens (refresh tokens, password-reset codes, magic links, PKCE codes, CSRF nonces, idempotency keys), or any state where DUPLICATION implies a security or financial loss (double-spend, double-issuance of token pair, double-grant of trial, double-charge avoidance), the finding is **Fix-class, not Note-class**.

Justifications that under-weight the severity — "matches the library's posture", "known limitation upstream", "the library does this too", "single-instance deploys are unaffected" — are NOT acceptable downgrades. The library may itself be flawed; deploys can scale; the recommendation bar is the Yes-to-any gate.

The same severity holds for a race on a gate that other code trusts: a flag such as verified, approved, or posted, which downstream reads take as proof that a check passed. If a race lets the flag go true while the check it records no longer holds, the finding is Fix-class. "No auth, billing, or single-use stakes" does not downgrade it.

Worked example: a document verify ran its line-item reconciliation check and its `verified_at` update as two separate queries. A line-item edit landing between them left a verified document whose items no longer reconciled, and the customer totals read that flag. A review filed the shape as a Note under the "no auth, billing, or single-use stakes" wording, and an outside reviewer then raised it on the PR. The fix ran the check and the update inside one transaction that locks the document row (`select … for update`), and every line-item edit takes the same lock.

If a tighter primitive exists (`UPDATE ... WHERE used_at IS NULL RETURNING *` pattern, advisory lock, atomic CAS, single-flight cache), surface it as the Fix. The race itself is the finding; document the proposed fix even if the team chooses to defer.

### 2.6 Resource-create-then-attribute atomicity (security tag as access control)

When the diff creates an external-system resource (AWS SSM Parameter, S3 object, KMS grant, IAM role-policy, Azure secret, GCP secret-manager version, K8s Secret/ConfigMap, Vault kv-v2 entry, a row in a permissions table) and then writes an ATTRIBUTE on that resource that GATES access — typically a tag, label, ACL entry, annotation, ownership column, or principal binding — those two operations together form a security-critical pair.

#### 2.6a Tag-after-create with a separate API call

AWS `PutParameter --tags` is atomic if the tag is included in the create call; `PutParameter` followed by `AddTagsToResource` is NOT. Between the two calls, the resource exists without its security tag. If the access-control policy keys on that tag (`Condition: { StringEquals: { ssm:resourceTag/X: ... } }`), the policy MAY block reads (default-deny is the safe direction) but any IAM principal whose policy doesn't depend on the tag (a wildcard role, a `*` allow on the resource path, a managed policy union) can read it during the window.

The same shape appears in IAM `CreateRole` + `AttachRolePolicy`, K8s `create secret` + `kubectl label`, GCP `create secret` + `add-iam-policy-binding`.

#### 2.6b Overwrite-existing without re-applying the tag

AWS `PutParameter --overwrite` deliberately does NOT carry tags forward — `Tags` is only honored on the create path. If the code does `PutParameter --overwrite Tags: [...]`, the tags silently no-op; the parameter retains whatever tags (or none) were on the previous value. The fix is to issue `AddTagsToResource` separately whenever the tag is required, AND to verify the prior resource had the tag (no, the API does not error on missing tags).

The same trap exists in GCP `secrets versions add` and Vault `kv put`.

#### 2.6c Stale-delete then put (race against concurrent reader)

A `DeleteParameter` followed by `PutParameter` is the worst of both worlds for the tag invariant: the resource briefly does not exist (any consumer mid-read sees a transient error), and the new resource starts un-tagged for the put window. If the consumer retries on transient errors, it can hit the un-tagged window. Fix: `PutParameter --overwrite --type SecureString ...` (or the equivalent CAS primitive) followed immediately by `AddTagsToResource`. The delete is rarely necessary.

**Discovery method:** for every IaC or runtime resource-creation call in the diff, locate the policy/condition/binding that gates ACCESS to the resource. If that policy keys on an attribute (tag, label, annotation, ownership column), check whether the create + attribute writes are atomic OR ordered such that the attribute is always present before any consumer reads. A Fix-class downgrade is justified only if the gating policy fails CLOSED on the missing attribute AND no other policy union grants access during the window. Document the closed-window reasoning explicitly; default is Fix.

### 2.7 Self-race / lease TOCTOU (two copies of one path against a DB row)

A common stampede-prevention pattern: a cron handler reads a row `cron_job_state.last_completed_at` (or `leases.expires_at`, `job_locks.acquired_at`), checks whether the configured idle window has elapsed, and proceeds. If two invocations arrive concurrently, BOTH read the same value, BOTH pass the gate, BOTH execute the job. This is canonical CWE-362 — the check (read) and the act (update) are separated by an event boundary.

Mitigations the orchestrator typically claims (single Vercel cron, single Quartz schedule, single Oban worker) are environmental, not invariants; manual triggers, retries, and migrations to a different scheduler invalidate them silently.

The fix is an atomic CAS: `UPDATE state SET last_started_at = now() WHERE path = ? AND last_completed_at = <snapshot>` and inspect the matched-row count — zero rows updated means another invocation won the gate, so skip. The same pattern applies to:
- **Supabase / PostgREST:** `.update({...}).match({ path, last_completed_at: snapshot })` and check `count`
- **Postgres advisory locks:** `pg_try_advisory_xact_lock(hashtext('cron:path'))` returns false on contention
- **Redis:** `SET key value NX EX <ttl>` returns nil on contention
- **DynamoDB:** `UpdateItem` with `ConditionExpression: "last_completed_at = :snapshot"`

The non-atomic read-then-update shape is Fix-class regardless of how single-source the trigger is today. The doc that claims "completion-gated" but the code that implements read-then-update is itself a comment/code drift finding (Pass 6).

#### Two copies of a multi-write transaction

The same race hides in any path a person or a job can start twice for the same row: two re-uploads of one file, two clicks on "retry", two webhook deliveries. Wrapping the path in a transaction does not order the two copies. Under Postgres's default `read committed`, both transactions read the same starting state, and each deletes, overwrites, and prunes before either commits. Only a lock that both copies take before their first write orders them: `select … for update` on the row they rewrite, an advisory lock, or a CAS predicate whose matched-row count the code checks.

Ask what each copy writes, not only whether the last step runs twice. A downstream claim that picks only the newest job (`for update skip locked`, "claims only the latest") answers the second question and says nothing about the first. Worked example: two re-uploads of one file each deleted the documents read from it, overwrote its page limit, and pruned its pages before the worker claimed anything. Two reviews read the worker's claim query, wrote "the stale row is never run", and left the race open. A test that ran both uploads at once showed both starting a read. The fix locked the file row at the top of the re-upload transaction.

Artifact: run two copies at once against real Postgres (`Promise.all` of two calls, or one copy held open with `pg_sleep` while the second runs), and assert on what each copy wrote: audit events, rows deleted, and the final value of every column the path sets. Reading the transaction boundary, or grepping the downstream claim, is not this artifact.

Assert the invariant the code promises, not only that nothing failed. If the path keeps at most 30 rows, count the rows after the run and compare with 30. A run that reports no errors over thousands of calls proves only that nothing threw. Run at least as many copies at once as production can, which is the replica count times the connection pool size. Worked example: a trim that kept the newest 30 job runs passed two concurrent copies with no errors on a 4-connection pool. Forty writers at once left 43 to 69 rows.

### 2.21 Unbounded attempt

A call that hangs raises no error, so a retry around it never reaches its next attempt, and a caller waiting on it waits forever. For every retry loop, call to an outside system (a database, an HTTP API, a model, a queue), and lock wait the diff adds or wraps, name what ends one attempt: a request timeout, a `statement_timeout` or `lock_timeout`, an `AbortSignal.timeout`, a pool's `connectionTimeoutMillis`. Quote the line that sets it, and show a test that fails when the limit is removed or raised.

A limit set elsewhere counts when you quote it and show it reaches this call. A client library's default counts only when you quote its documented value; many default to no limit. The attempt count, the backoff, and the total wait across attempts are not a limit on one attempt. Check the wait for a resource too, such as a pool connection or a lock, not only the work done once the resource is held. If nothing ends an attempt, that is a Flag, and a Fix when a request a person is waiting on sits behind it.

Measured (2026-10-21): the branch retried the save of a document check five times with backoff and jitter. The review ran six mutations on the attempt count, the delay, and the jitter, and noted the total wait across attempts. It never asked what ends a save that hangs, and the operator caught it. The fix sets `select set_config('statement_timeout', $1, true)` inside the transaction, before the `select ... for update` that takes the row lock, so the lock wait counts. Its test reads `current_setting('statement_timeout')` from inside the save and fails when the limit is raised, made session-wide, or not passed. The wait for a pool connection stayed unlimited, which this angle reports as its own finding.

### 8.4 Shared destinations

In scope whenever the diff writes a named thing into a place where other runs' output also lands: a folder another system reads, a bucket, a queue, a table keyed by name, or a file a downstream import picks up. For each name, ask what two runs with overlapping input would write. If the name comes only from the input, such as a record id, then two runs that share a record write the same name, and the second overwrites or collides with the first.

Method: run the code twice with one input in common, and list the names each run wrote. Every name must be different, or the review must quote the rule at the destination that keeps them apart. A test that pins one run's names proves nothing about the second run.

Measured (2026-10-22): each export bundle named its PDFs by document id alone. Two bundles that shared a document would drop two files of one name into the downstream system's import folder. Our review recorded that the PDF name had moved from file id to document id, and judged it as a change in behavior. It answered the concurrency angles with "no concurrency and no I/O", because one run has none. The outside reviewer found it, and the fix named each PDF `<bundle id>-<document id>.pdf`.
