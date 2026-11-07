# Queries, tables, and data flow

1. Read this file now, before Pass 1, when the diff adds or changes a query, a table, a view, or a column, or threads a value from one function to another through a new field.

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

1. Walk each angle below in the pass its number names, give it a disposition, and print its line in the Checklist under that pass.

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

1. For every new `where`, `order_by`, `join … on`, raw SQL filter, or preload with a where, name the columns it filters or sorts on.
2. Search the migrations for a `create index`, `create unique_index`, or schema-level `@index` covering them.
3. Flag a missing index on a hot path, such as request handling, breach response, billing, auth, refresh-token lookup, or session validation, as both PERF and SEC.
4. Require a composite index for a composite filter, or a written reason why one column's index suffices.
5. Require the index in the same migration that adds a new lookup column on a hot table, never in a follow-up.

### 1.6 Extracted-but-not-forwarded

1. For each value the diff extracts, parses, or creates, such as a param, a decoded field, or an id, trace it through the whole call chain in the diff, not only the immediate caller.
2. Flag every function later in the chain that needs the value and does not receive it.

### 1.7 New fields not threaded

1. When a function adds a map or struct key or a new parameter, check every downstream call in the diff.
2. Flag every downstream signature or pattern match that drops the new field, including pipeline stages that destructure only known keys.

### 1.8 Filter-dimension gaps

1. When a filtered query feeds a function that queries the same entity, read that function and list the filter dimensions it assumes were applied.
2. Flag the upstream query if it lacks any of them.

### 1.19 New-field producers

1. When the diff adds a field that a new check, sum, or gate depends on, grep for every insert or upsert into the table and every form or DTO that feeds one; never list the producers from the routes alone.
2. Make a two-column list of each path, such as each form, import, extraction step, seed, and admin route, and whether it sets the field.
3. Report each path that cannot set the field as a finding.

### 2.14 N+1 calls

1. For every loop the diff adds or changes, check whether its body makes a database query, an HTTP request, or another remote call.
2. Grep the loop bodies for `Repo.`, `from(`, `fetch(`, `axios`, `prisma.`, `.query(`, `Req.`, `HTTPoison`, and the project's own API client names, and for Ecto association access with no `preload` upstream.
3. First ask whether the database already stores the value the call works out, such as a file's page count; if it does, the fix is to read the stored value, not to batch the call.
4. Otherwise give the fix as a batched call, such as `where: x.id in ^ids`, a bulk endpoint, `Repo.preload`, or a dataloader, joined in memory.
5. Construct the input that shows it: the row count at which the loop exceeds the request timeout.

### 2.15 Quadratic scans

1. Flag a nested pass over one collection, or over two that grow together, such as `Enum.find` inside `Enum.map` or `.filter` inside `.map`.
2. Flag a membership test on a list inside a loop, such as `x in list`, `Enum.member?/2`, `.includes()`, `.indexOf()`, or `list.contains`.
3. Flag repeated `++` onto the end of a list inside a loop in Elixir or Erlang, and give the fix as prepend and reverse once.
4. Give the fix as a `MapSet`, `Set`, or map keyed on the lookup field, built once before the loop.
5. Mark a collection bounded by a small constant `N/A`, and say what bounds it.

### 2.19 Read skew

1. Walk this angle on every path that makes two or more queries, including a read-only page, report, or health check; "read-only" never makes it N/A.
2. Give the fix as a re-check of the selecting condition on the second read, or as one query or one `repeatable read` transaction.
3. When a path decides from data it read and then re-reads under a lock to confirm, require the decision and the re-check to use the same read.
4. Refuse a re-check that finds both reads null; never count it a match.
5. Build the artifact by wrapping the function that makes the second query so it runs the real writer first, and assert what the path reports; an argument that the window is small is not the artifact.

Method:

1. For each path in the diff that makes more than one query, write down the condition that selected each row in the first query.
2. Find every writer that can change that condition between the queries.
3. Check whether the later query, or the code that joins the results, re-checks the condition on the fresh data. A path that trusts the first query's selection is the finding.

### 4.2 Schema default ≠ DB default

1. For any field whose nil-or-populated distinction matters, read the migrations, not only the schema, because an Ecto `default:` applies to the struct, not to an inserted row.
2. Grep the migration history for the column's creation and every later alter, and check each for `null: false` and a database `default:`.
3. Treat nil as reachable at runtime unless the migrations set both.
