# Concurrency and repeated runs

1. Read this file now, before Pass 1, when two paths can write the same rows, or the diff takes a lock, retries, or runs a job that can run twice or overlap with itself. Angle 2.18, the race against every other writer, stays in the body and applies to every diff that writes.

## Contents

- 2.4 Divergent-input races
- 2.5 Shared-state race severity escalation
- 2.6 Resource-create-then-attribute atomicity (security tag as access control)
- 2.7 Self-race / lease TOCTOU (two copies of one path against a DB row)
- 2.21 Unbounded attempt
- 8.4 Shared destinations

1. Walk each angle below in the pass its number names, give it a disposition, and print its line in the Checklist under that pass.

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

1. For each unique constraint or race handler, consider concurrent writes with different payloads, not only identical retries.
2. When a race handler returns `:ok` on conflict, check that the caller then uses the stored payload, not its own intended one.

### 2.5 Shared-state race severity escalation

1. Class a race as Fix, never Note, when it touches authentication, authorization, billing, a single-use token such as a refresh token, reset code, magic link, PKCE code, CSRF nonce, or idempotency key, or any state whose duplication means a security or financial loss.
2. Class a race as Fix when it can set a gate other code trusts, such as a verified, approved, or posted flag, while the check the flag records no longer holds.
3. Reject downgrades such as "matches the library's posture", "known limitation upstream", "single-instance deploys are unaffected", or "no auth, billing, or single-use stakes".
4. Name the tighter primitive as the Fix where one exists, such as `UPDATE ... WHERE used_at IS NULL RETURNING *`, an advisory lock, an atomic CAS, a single-flight cache, or one transaction holding `select … for update`, and record it even if the team defers.

### 2.6 Resource-create-then-attribute atomicity (security tag as access control)

1. Treat as a security-critical pair any create of an outside resource, such as a cloud parameter, object, grant, role policy, secret, K8s Secret or ConfigMap, Vault entry, or permissions row, followed by a write of an attribute that gates access to it, such as a tag, label, ACL entry, annotation, ownership column, or principal binding.

#### 2.6a Tag-after-create with a separate API call

1. Flag a create followed by a separate tag call, such as `PutParameter` then `AddTagsToResource`, IAM `CreateRole` then `AttachRolePolicy`, K8s `create secret` then `kubectl label`, or GCP `create secret` then `add-iam-policy-binding`.
2. Give the fix as the tag inside the create call, such as `PutParameter --tags`.

#### 2.6b Overwrite-existing without re-applying the tag

1. Flag `PutParameter --overwrite` with `Tags`, GCP `secrets versions add`, and Vault `kv put` where a tag is required, because the overwrite path ignores tags without error.
2. Give the fix as a separate `AddTagsToResource` whenever the tag is required, plus a check that the prior resource had it.

#### 2.6c Stale-delete then put (race against concurrent reader)

1. Flag a `DeleteParameter` followed by `PutParameter`.
2. Give the fix as `PutParameter --overwrite --type SecureString ...`, or the equivalent CAS primitive, followed at once by `AddTagsToResource`.

For all of 2.6a-c:

1. For every resource-creation call in the diff, find the policy, condition, or binding that gates access to it.
2. If that policy keys on an attribute, check that the create and the attribute write are atomic, or ordered so the attribute exists before any consumer reads.
3. Downgrade from Fix only when the gating policy fails closed on the missing attribute and no other policy grants access during the window, and write that reasoning down.

### 2.7 Self-race / lease TOCTOU (two copies of one path against a DB row)

1. Flag as Fix-class a path that reads a gate row, such as a last-completed time or a lease expiry, checks it, and then acts, however single-source its trigger is today.
2. Never accept a single scheduler or single worker as the mitigation.
3. Give the fix as an atomic CAS, such as `UPDATE state SET last_started_at = now() WHERE path = ? AND last_completed_at = <snapshot>`, skipping when the matched-row count is zero, or an equivalent:
- **Supabase / PostgREST:** `.update({...}).match({ path, last_completed_at: snapshot })` and check `count`
- **Postgres advisory locks:** `pg_try_advisory_xact_lock(hashtext('cron:path'))` returns false on contention
- **Redis:** `SET key value NX EX <ttl>` returns nil on contention
- **DynamoDB:** `UpdateItem` with `ConditionExpression: "last_completed_at = :snapshot"`
4. Report a document that claims "completion-gated" over read-then-update code as a Pass 6 comment drift finding.

#### Two copies of a multi-write transaction

1. For any path a person or a job can start twice for one row, such as two re-uploads, two retry clicks, or two webhook deliveries, ask what each copy writes, not only whether the last step runs twice.
2. Count a transaction as no ordering under `read committed`; only a lock both copies take before their first write orders them, such as `select … for update` on the row, an advisory lock, or a CAS predicate whose matched-row count the code checks.
3. Count a downstream claim that picks only the newest job as no answer to what each copy writes.
4. Build the artifact by running two copies at once against real Postgres, with `Promise.all` or one copy held open by `pg_sleep`, and assert what each wrote: audit events, rows deleted, and the final value of every column the path sets.
5. Assert the invariant the code promises, such as a cap of 30 rows, not only that nothing failed.
6. Run at least as many copies at once as production can: the replica count times the connection pool size.

### 2.21 Unbounded attempt

1. For every retry loop, outside call, and lock wait the diff adds or wraps, name what ends one attempt, such as a request timeout, `statement_timeout`, `lock_timeout`, `AbortSignal.timeout`, or a pool's `connectionTimeoutMillis`.
2. Quote the line that sets it, and show a test that fails when the limit is removed or raised.
3. Count a limit set elsewhere only when you quote it and show it reaches this call, and a library default only when you quote its documented value.
4. Count the attempt count, the backoff, and the total wait across attempts as no limit on one attempt.
5. Check the wait for a resource, such as a pool connection or a lock, as well as the work done once it is held.
6. Report a missing limit as a Flag, and as a Fix when a request a person waits on sits behind it.

### 8.4 Shared destinations

1. Walk this angle whenever the diff writes a named thing where other runs' output also lands, such as a folder another system reads, a bucket, a queue, a table keyed by name, or a file a downstream import picks up.
2. Run the code twice with one input in common and list the names each run wrote.
3. Require every name to differ, or quote the rule at the destination that keeps them apart; a test of one run's names proves nothing.
