# Pass 8 — Second-order

Downstream systems, caches, cron jobs, deploy coordination. **Higher classification bar:** second-order findings must be triggered by THIS deploy, not a hypothetical future change. "If you later move modules to separate OTP apps" is hypothetical — drop it. "This deploy changes a cached value that cron job X reads at midnight" is concrete — keep it.

## 8.1 This-deploy triggers

Enumerate concrete downstream surfaces this deploy actually touches:

- **Caches** the deploy invalidates or refills (Redis keys, in-process ETS, CDN paths)
- **Cron jobs / scheduled tasks** that read the changed value
- **Cached config** loaded at boot time vs at-call time
- **Webhooks** the deploy registers or de-registers
- **Database migrations** that change column types or constraints

For each, ask: when does the next consumer encounter the change? If it's a midnight cron and the deploy ships at 3pm, the gap is 9 hours of mixed state. If it's an in-flight long poll, the gap is one poll cycle. If it's a CDN cache with 24h TTL, the gap is 24h of stale.

These are real deploy-coordination findings. Hypothetical second-order findings ("if you later add caching") are not.

## 8.2 Data precedes code (SCOPE GUARD — read FIRST)

**Scope guard:** this angle applies ONLY when the diff introduces a NEW write-time invariant — a validator, schema constraint, NOT NULL, unique index, registration check, or other rule that NEW rows must satisfy.

If the diff is a read-time visibility filter (a `where` clause scoping results to the current user/tenant/role/scope, an authorization predicate added to a query, a context-dependent SELECT narrowing, an ABAC subject-scope filter), this angle is N/A — STOP and skip it.

Filtered rows are not invariant violations; they are legitimate user-authored data outside the caller's visibility scope. A filter changes WHO SEES data, not WHETHER data is valid. There is no "legacy data to cleanse" in response to a filter diff — recommending deletion, cleansing, or rewriting of rows because a filter was added is a category error. The shapes share syntactic surface (a new `where`, a new check) but have OPPOSITE data semantics: a filter says "subset X is what this caller sees"; a constraint says "subset X is what is valid." Conflating them produces irreversible data-loss recommendations from filter PRs.

**When the angle IS in scope** (the diff introduces a write-time invariant): when the diff adds new validation at write-time (registration, insertion, schema constraint), ask: do pre-existing rows in the DB satisfy the new invariant? A hardening commit that tightens `register_client(valid_uri?)` does not retroactively validate rows inserted before the commit. Reads that TRUST the invariant (e.g., authorize-time exact-match against a stored URI) will accept legacy rows that the new write-path would reject.

Either (a) add a read-time guard that re-validates each row's invariant before trusting it, or (b) plan a data migration to cleanse or reject legacy rows. This is the inverse of downstream — it's upstream data that precedes the current code. Grep for every stored field the new validation would have guarded and check whether the consumers re-validate or trust.

The Destructive-recommendation gate in Classify applies to any data-cleanup recommendation produced by this angle.
