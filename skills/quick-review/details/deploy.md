# Migrations, deploys, and scheduled readers

1. Read this file now, before Pass 1, when the diff adds a migration, changes deploy or job configuration, or changes a value that a cache or a scheduled job reads.
2. Walk each angle below in the pass its number names, give it a disposition, and print its line in the Checklist under that pass.
3. Keep a Pass 8 finding only when this deploy triggers it, such as a cached value a cron job reads at midnight, and drop a hypothetical future change.

## Checklist lines

```
Pass 5:
  5.12  Config-block consistency         sibling block key sets diff
Pass 8:
  8.1   This-deploy triggers              concrete cron/cache/dependent reads
  8.2   Data precedes code (SCOPE GUARD) Read scope guard FIRST. Filter PRs
                                          are NOT in scope — destructive recs on
                                          filter-excluded rows are CATEGORY ERRORS.
                                          Only NEW write-time invariants trigger.
                                          So does a new column new code reads:
                                          run the reader on an old row's value
  8.3   Rollback after user edits         run each down migration after the edits
                                          the feature allows, then up again, then the
                                          previous release's writers on what is left
```

### 5.12 Config-block consistency

1. When the diff adds a keyword-list config block, such as `config :app, Module, ...`, beside an existing block of the same shape, diff the key sets and report the difference explicitly.
2. For each key the sibling has and the new block lacks, flag it for addition or require an inline `# omitted because ...` comment.
3. For each key the new block has and the sibling lacks, ask whether the sibling needs it too.
4. Treat a missing key as possibly live, because libraries such as `ExOauth2Provider`, Guardian, Oban, and Phoenix endpoints change behavior silently when one is omitted; take the sibling block as the ground truth.

### 8.1 This-deploy triggers

1. List the downstream surfaces this deploy actually touches:

- **Caches** the deploy invalidates or refills (Redis keys, in-process ETS, CDN paths)
- **Cron jobs / scheduled tasks** that read the changed value
- **Cached config** loaded at boot time vs at-call time
- **Webhooks** the deploy registers or de-registers
- **Database migrations** that change column types or constraints

2. For each, state when its next consumer meets the change and how long the mixed or stale state lasts.

### 8.2 Data precedes code (SCOPE GUARD — read FIRST)

1. Apply this angle only when the diff adds a write-time invariant, such as a validator, schema constraint, NOT NULL, unique index, or registration check, or a new column that new code reads.
2. Mark it N/A and stop when the diff adds a read-time visibility filter, such as a `where` scoping results to a user, tenant, role, or ABAC scope, or an authorization predicate on a query.
3. Never recommend deleting, cleansing, or rewriting rows because a filter was added.
4. For a write-time invariant, grep for every stored field the new validation guards and check whether its readers re-validate or trust it.
5. Where readers trust it, require a read-time guard that re-validates each row, or a data migration that cleanses or rejects old rows.
6. Put any data-cleanup recommendation from this angle through the Destructive-recommendation gate in Classify.
7. For each line the diff adds that reads a new column, run it against a row as the migration leaves an old one, and say what the user gets; "the new columns are nullable" is not a disposition.

### 8.3 Rollback after user edits

1. Walk this angle whenever the diff adds a down migration, especially one that reverses a seed or a data change.
2. On a scratch database, run the up migration, then each supported edit of the key the down migration finds rows by, such as a rename, delete, merge, or change of primary value, through the app's own functions or routes.
3. Run the down migration and then the up again, and show what the down left behind and whether the up succeeded; reading the down file is not a disposition.
4. On a scratch database holding what the feature left behind, run the previous release's writers, at least every import or sync that writes the tables the feature changed, and show what they write.
5. Report a finding here as a Flag or a Note, not a Fix, and say what the rollback leaves behind so the PR body or runbook can record it.
