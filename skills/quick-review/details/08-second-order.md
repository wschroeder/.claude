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

**A new column that new code reads is in scope too.** A nullable column with no backfill holds null on every row written before the migration. For each line the diff adds that reads the column, run it against a row the way the migration leaves an old one, and say what the user gets. "The new columns are nullable" is not a disposition: it says the migration succeeds, not what the reader does with the null.

Measured (2026-10-22): a migration added `pdf_page_count` with no backfill, and the export bundle refused any file whose PDF ran past its page limit and had no count recorded. Our review wrote "8.2 Data before code: clear. The new columns are nullable." The outside reviewer found that every long file processed before the migration could no longer download. The fix backfilled the count from existing audit events, else from the pages read, and a migration test seeds rows at the version before and checks each one after.

## 8.3 Rollback after user edits

In scope whenever the diff adds a down migration, and especially a down migration that reverses a seed or a data change. A down migration finds its rows by some key. If users can change that key through the feature (rename, delete, merge, change which value is primary), then the rollback can miss the rows it was written to remove, and a later up can then collide with what it left behind.

Method: on a scratch database, run the up migration and then each supported edit through the app's own functions or routes. Then run the down migration, and then the up migration again. Show what the down left behind and whether the up succeeded. Reading the down file is not a disposition for this angle: the miss happens only after the edits.

A finding here is usually a Flag or a Note, not a Fix. Whether a rollback has to survive user edits is a decision for the person who owns the deploy, and the cure (an immutable seed marker, say) changes the schema. Say what the rollback leaves behind so the PR body or the runbook can record it.

## 8.4 Shared destinations

In scope whenever the diff writes a named thing into a place where other runs' output also lands: a folder another system reads, a bucket, a queue, a table keyed by name, or a file a downstream import picks up. For each name, ask what two runs with overlapping input would write. If the name comes only from the input, such as a record id, then two runs that share a record write the same name, and the second overwrites or collides with the first.

Method: run the code twice with one input in common, and list the names each run wrote. Every name must be different, or the review must quote the rule at the destination that keeps them apart. A test that pins one run's names proves nothing about the second run.

Measured (2026-10-22): each export bundle named its PDFs by document id alone. Two bundles that shared a document would drop two files of one name into the downstream system's import folder. Our review recorded that the PDF name had moved from file id to document id, and judged it as a change in behavior. It answered the concurrency angles with "no concurrency and no I/O", because one run has none. The outside reviewer found it, and the fix named each PDF `<bundle id>-<document id>.pdf`.
