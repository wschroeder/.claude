# Queries, tables, and data flow

Read this file now, before Pass 1, when the diff adds or changes a query, a table, a view, or a column, or threads a value from one function to another through a new field.

## Contents

- 1.1 Schema-query alignment (index coverage)
- 1.6 Extracted-but-not-forwarded
- 1.7 New fields not threaded
- 1.8 Filter-dimension gaps
- 1.19 New-field producers
- 2.14 N+1 calls
- 2.15 Quadratic scans
- 2.19 Read skew
- 4.2 Schema default ≠ DB default

Each angle below belongs to the pass its number names. Walk it in that pass, give it a disposition, and print its line in the Checklist under that pass.

## Checklist lines

```
Pass 1:
  1.1   Schema-query alignment           index every new where/orderBy column
  1.6   Extracted-but-not-forwarded      trace each extracted value end-to-end
  1.7   New-field-not-threaded           new map key → downstream pattern-match
  1.8   Filter-dimension gaps            upstream filter covers downstream dims
  1.19  New-field producers              every path that creates or edits the row
                                          can set the field a new check needs
Pass 2:
  2.14  N+1 calls                        query or remote call inside a loop;
                                          first: does the DB already store what
                                          it fetches? then read that, not batch;
                                          a view or CTE read inside a per-row
                                          subquery or lateral join counts, even
                                          when the page makes one call
                                          proof: explain analyze on data at least
                                          the size of a real book, quoting the loop
                                          count of each scan of that view or CTE; a
                                          plan read on a dev database is not proof
  2.15  Quadratic scans                  nested pass over one collection;
                                          membership test on a list in a loop;
                                          a SubPlan under a correlated not exists,
                                          even when its loop count is 1
  2.19  Read skew                        2+ queries, read-only too; writer between
                                          them → re-check selecting condition;
                                          a decision judges the same read its
                                          re-check compares; two nulls never match
Pass 4:
  4.2   Schema default ≠ DB default      Ecto struct default vs migration NULL
```

### 1.1 Schema-query alignment (index coverage)

For every new `where`, `order_by`, `join … on`, raw SQL filter, or Ecto preload-with-where introduced by the diff, identify the column(s) being filtered or sorted. Search the migrations directory for a `create index`, `create unique_index`, or schema-level `@index` covering those column(s). If the column lacks an index AND the query is on a hot path (request-handling, breach response, billing, auth, refresh-token lookup, session validation), flag as both PERF and SEC — slow breach response IS a security concern (e.g., a refresh-token-reuse detection query that scans the table cannot meet its design SLA).

For composite filters (`WHERE a = ? AND b = ?`), a single-column index on the lower-cardinality column is usually inadequate; require a composite index or document why.

Always-required: a NEW lookup column on a NEW or pre-existing hot table needs an index in the SAME migration that introduces the column or query, not "a follow-up."

### 1.6 Extracted-but-not-forwarded

For each value extracted, parsed, or created in a function within the diff (params, decoded fields, API response values, IDs), trace it forward through every downstream function call in the diff. If function A extracts `promo_code` from params but function B (called later in the chain) does not receive it in its arguments, flag it. The trace must follow the full call chain, not just the immediate caller — a value lost at hop 2 of 4 is invisible without end-to-end tracing.

### 1.7 New fields not threaded

When a function adds a new key to a map/struct or a new parameter to its signature, check every call site within the diff that invokes downstream functions. If the downstream function's signature or pattern match does not include the new field, it is silently dropped. This includes pipeline stages where a map is built up and then passed to a function that only destructures known keys.

### 1.8 Filter-dimension gaps

When new code queries with specific filters (e.g., `WHERE status = 'active'`), and the result feeds into a function that queries the same entity with additional filter dimensions (e.g., also filtering by `org_id`), the upstream query must include all dimensions the downstream consumer assumes were already applied. Read the downstream function to identify its assumptions.

### 1.19 New-field producers

Angle 1.7 follows a new field forward to the code that reads it. This angle runs the other way. When the diff adds a field that a new check, sum, or gate depends on, list every path that creates or edits that row: each form, import, extraction step, seed, and admin route. Confirm that each path can set the field. A path that leaves it null produces rows the check treats as absent, and the person using that path has no way to correct them.

Worked example: line items gained a `section_key` so the app could check each printed section total against the items under it. Extraction set the key, but the reviewer's Add item form sent none. An item added by hand landed in no section, and the document stayed blocked unless the reviewer distorted another item. An outside reviewer caught it on the PR. The fix put a section selector on the add and edit forms and made the route refuse a key the document does not print.

List the producers from that grep, never from the routes. Worked example: a pull request added remembered external numbers with add, update, and delete routes. Our review wrote "1.19 producers: the add, update, and delete routes all go through services.rememberedNumbers", which missed the reviewer's document save, which also wrote remembered rows and did not check the document's kind against the record's. An outside reviewer caught it.

**Discovery method:** grep for every insert or upsert into the table and every form or DTO that feeds one, then make a two-column list (path, sets the field?). A row that says no is the finding.

### 2.14 N+1 calls

For every loop the diff adds or changes (`for`, `Enum.map`, `Enum.each`, `.map`, `.forEach`, `for await`, a list comprehension), check whether its body makes a database query, an HTTP request, or any other remote call. One call per element turns a page of 50 rows into 51 round trips, and the cost grows with the data rather than the code.

**Discovery method:** grep the loop bodies for `Repo.`, `from(`, `fetch(`, `axios`, `prisma.`, `.query(`, `Req.`, `HTTPoison`, and the project's own API client names. For Ecto, also look for association access inside a loop that has no `preload` upstream.

**First ask whether the call is needed.** Where it fetches or parses something to work out a value the database already stores, such as a file's page count, the fix is to read the stored value, and batching it only makes an unneeded call faster. Worked example: a preview fetched every selected PDF to count its pages, this check flagged the reads as slow and unmeasured, and a slice was planned to measure them, while the query behind the preview already selected each file's stored page count.

**Fix:** batch the call (`where: x.id in ^ids`, a bulk endpoint, `Repo.preload`, a dataloader) and join the results in memory. Construct the input that shows it: the row count at which the loop exceeds the request timeout.

### 2.15 Quadratic scans

Two shapes:

- A nested pass over the same collection, or over two collections that grow together: `for a in xs, for b in xs`, `Enum.find` inside `Enum.map`, `.filter` inside `.map`.
- A membership test on a list inside a loop: `x in list`, `Enum.member?/2`, `.includes()`, `.indexOf()`, `list.contains`. Each test is a linear scan.

**Fix:** build a `MapSet`, `Set`, or map keyed on the lookup field once, before the loop. Repeated `++` onto the end of a list inside a loop is the same shape in Elixir and Erlang; prepend and reverse once instead.

A collection bounded by a small constant (the five states of an enum) is `N/A` for this angle; say what bounds it.

### 2.19 Read skew

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

### 4.2 Schema default ≠ DB default

Ecto `field :foo, T, default: X` is a STRUCT default — it applies when a record is loaded with the field missing, not when a row is inserted with the column absent. For any field whose nil-vs-populated distinction matters, read the MIGRATION: is the column `null: false`? Is there a DB-level `default:` in the `add` call? Without BOTH, nil is reachable at runtime regardless of the schema struct default. A reader who stops at the schema file and concludes "nil is impossible" will miss rows inserted via raw SQL, admin scripts, or older migrations that predate the default. Grep the migration history for the column's creation and every subsequent alter — then check the `null:` and `default:` options on each.
