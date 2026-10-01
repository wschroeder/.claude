# PostgreSQL schema and migrations

Conventions for designing or changing a PostgreSQL schema: a migration file, any
DDL, and the comments stored in the catalog. Writing queries is out of scope. Every
SQL example here ran against PostgreSQL 16.

## Contents

- Before you design
- One fact in one place
- Every reference is a foreign key
- Indexes
- Column types
- Document every table and column
- Migrations
- Audit queries
- Sources

## Before you design

Read the live schema and the project's schema spec before you change either one.
Dump the live schema with `pg_dump --schema-only --schema=<schema> --no-owner
--no-privileges`, because migrations, spec pages, and the live database can drift
apart, and only the dump shows what is actually there.

## One fact in one place

Every non-key column gives "a fact about the key, the whole key, and nothing but
the key" (Kent). A fact stored twice drifts apart: one write path updates one copy,
and a reader that prefers the other copy shows stale data.

- **Derive a flag from the column that implies it.** If `is_verified` is true
  exactly when `verified_at` is set, make the flag a generated column so nothing
  can write it out of step:

  ```sql
  is_verified boolean generated always as (verified_at is not null) stored
  ```

  A write to a generated column fails with `column "is_verified" can only be
  updated to DEFAULT`, so remove the column from every insert and update. In
  PostgreSQL 16 an existing plain column cannot become generated: drop it and add
  it again, and recreate any index that used it.
- **Columns set and cleared together get a check that holds them together.** A
  "who" and "when" pair, such as `kept_by` and `kept_at`:

  ```sql
  constraint kept_pair check ((kept_by is null) = (kept_at is null))
  ```

- **Give a one-to-many result one owner.** When one parent row can produce
  several child rows, such as one file yielding several statements, a per-child
  result belongs on the child. A copy on the parent can hold only one value.
- **Keep a fact the app filters, matches, or joins on in a real column, not
  inside a JSON document.** JSON suits data whose shape varies by subtype and
  that the app only reads back whole.
- **Denormalize only for a measured reason.** "There is no obligation to fully
  normalize all records when actual performance requirements are taken into
  account" (Kent). Write the measurement in the migration's comment.

## Every reference is a foreign key

- **Do not point at rows through an `entity_type` and `entity_id` pair.** No
  foreign key can check that pair, so deleting the target leaves orphans, and
  every later migration that retires an entity type has to delete those rows by
  hand. Karwin's *SQL Antipatterns* names this "Polymorphic Associations".
  Instead, give the referencing table one nullable foreign key column per target
  table, with a check that exactly one is set:

  ```sql
  client_id uuid references app.clients(id) on delete cascade,
  loan_id   uuid references app.loans(id) on delete cascade,
  constraint one_target check (num_nonnulls(client_id, loan_id) = 1)
  ```

  An append-only audit log may keep the pair, because an audit record has to
  outlive the row it describes.
- **Reference a natural key with a composite foreign key.** When the parent
  already has a unique constraint on `(statement_id, section_key)`, a child's
  `foreign key (statement_id, section_key) references parent (statement_id,
  section_key)` rejects a key that the parent lacks. A null in any referencing
  column skips the check, so a nullable child column stays optional.
- **Choose `on delete` deliberately.** Use `cascade` for rows that mean nothing
  without their parent, `restrict` for a parent that must not vanish while
  referenced, and `set null` only when the child row stays meaningful.
- **A check constraint sees only its own row.** PostgreSQL "does not support
  CHECK constraints that reference table data other than the new or updated row
  being checked". A rule that spans rows needs a foreign key, a unique or
  exclusion constraint, or a trigger.

## Indexes

- **Index the referencing columns of every foreign key.** PostgreSQL does not do
  it for you, and a delete or key update on the parent scans the child table for
  matches.
- **Do not repeat an index.** A primary key or unique constraint already builds an
  index. A plain index whose columns lead another index on the same table adds
  write cost and serves no query that the longer index cannot.
- **Index what the app looks up.** That covers a business key inside JSON, an
  expression, or a partial predicate the queries use. Use a unique index when the
  business key must be unique.
- Run the audit queries below after every migration that adds a table or a
  foreign key.

## Column types

- **Use `timestamptz`, never `timestamp`.** It stores an instant and does
  arithmetic correctly across time zones (PostgreSQL wiki, "Don't Do This").
- **Use `text`, not `varchar(n)` or `char(n)`.** They take the same storage and
  bring no performance benefit, only an arbitrary length limit. Put a real limit
  in a check constraint.
- **Use `numeric` for money and rates**, never `money` or a float.
- **Use identity columns, not `serial` or `bigserial`:** `bigint generated always
  as identity`. To convert an existing serial column:

  ```sql
  alter table t alter column id drop default;
  drop sequence t_id_seq;
  alter table t alter column id add generated always as identity;
  select setval(pg_get_serial_sequence('t', 'id'), (select max(id) from t));
  ```

- **Prefer a check constraint over an enum type for a list of allowed values.**
  You cannot remove a value from an enum type or reorder it without dropping and
  recreating the type. A check constraint can be dropped and re-added in one
  migration.
- **Use an array only for values nothing searches inside.** "Arrays are not sets;
  searching for specific array elements can be a sign of database misdesign.
  Consider using a separate table" (PostgreSQL docs).
- **Use `uuid` keys, or `bigint` identity keys, consistently.** A column that
  refers to a uuid key is `uuid`, never `text`.

## Document every table and column

Every migration that adds a table or a column also adds a `COMMENT ON` for it, so
a person or a model reading the catalog learns what the thing is for without
having to open the code:

```sql
comment on table app.collateral_account_statement_section_totals is
  'A subtotal printed on a brokerage statement, kept as a check figure against the holdings read from that section. Never counts toward collateral value.';
comment on column app.collateral_account_statement_section_totals.kept_holdings_as_read_by is
  'Reviewer who chose to keep the holdings as read when they disagree with this printed total; null until someone chooses.';
```

- Say what the row or value means to the business, which rows it relates to, and
  when it is null. Leave out history, such as what the column used to hold or
  which ticket added it. That belongs in the migration file's own comment.
- Change the comment in the same migration that changes the column's meaning.
- `psql \d+ <table>` and `obj_description` and `col_description` read the
  comments back. The third audit query lists what has none.

## Migrations

- **A down file reverses its up file completely.** Prove it on a scratch
  database: apply every up file, then every down file in reverse with `psql -v
  ON_ERROR_STOP=1`, then every up file again. Dump the result and diff it against
  the live schema. A down file that deliberately keeps a table still has to leave
  the earlier down files able to run, so the first migration's down file drops
  that table too.
- **Name every delete or update in an up file, and the reason.** No down file can
  bring deleted rows back. Say so in the migration's comment.
- **Fail with a message, not a constraint error.** Before you tighten a
  constraint, count the rows that would violate it, and `raise exception` with
  that count.
- **Remember the triggers.** Without one, `updated_at` changes only where the app
  sets it.
- Never edit a migration that has run anywhere except to make its down file work.
  Change the schema in a new migration.

## Audit queries

Each query takes the schema name in place of `app`. All three ran against
PostgreSQL 16.

Foreign keys with no index that leads with their columns:

```sql
select c.conrelid::regclass as table_name, c.conname,
       (select string_agg(a.attname, ', ' order by k.n)
          from unnest(c.conkey) with ordinality k(attnum, n)
          join pg_attribute a on a.attrelid = c.conrelid and a.attnum = k.attnum) as columns
from pg_constraint c
where c.contype = 'f'
  and c.connamespace = 'app'::regnamespace
  and not exists (
    select 1 from pg_index i
    where i.indrelid = c.conrelid
      and (select array_agg(x order by x) from unnest((i.indkey::int2[])[0:cardinality(c.conkey) - 1]) x)
        = (select array_agg(x order by x) from unnest(c.conkey) x))
order by 1, 2;
```

Plain indexes whose columns lead another index on the same table. This query
ignores sort direction, expression indexes, and partial indexes:

```sql
select a.indrelid::regclass as table_name, a.indexrelid::regclass as redundant, b.indexrelid::regclass as covered_by
from pg_index a
join pg_index b on b.indrelid = a.indrelid and b.indexrelid <> a.indexrelid
where a.indrelid::regclass::text like 'app.%'
  and not a.indisunique
  and a.indexprs is null and b.indexprs is null
  and a.indpred is null and b.indpred is null
  and (string_to_array(b.indkey::text, ' '))[1:a.indnkeyatts] = string_to_array(a.indkey::text, ' ')
order by 1, 2;
```

`int2vector` casts to an array whose subscripts start at 0, and PostgreSQL counts
two arrays with different lower bounds as unequal. The text conversion starts both
sides at 1.

Tables and columns with no comment:

```sql
select c.relname as table_name, coalesce(a.attname, '(table)') as column_name
from pg_class c
left join pg_attribute a on a.attrelid = c.oid and a.attnum > 0 and not a.attisdropped
where c.relnamespace = 'app'::regnamespace and c.relkind = 'r'
  and ((a.attname is null and obj_description(c.oid, 'pg_class') is null)
    or (a.attname is not null and col_description(c.oid, a.attnum) is null))
order by 1, 2;
```

## Sources

- PostgreSQL docs, [Constraints](https://www.postgresql.org/docs/current/ddl-constraints.html):
  "the declaration of a foreign key constraint does not automatically create an
  index on the referencing columns", and "PostgreSQL does not support CHECK
  constraints that reference table data other than the new or updated row being
  checked."
- PostgreSQL docs, [Enumerated Types](https://www.postgresql.org/docs/current/datatype-enum.html):
  "Existing values cannot be removed from an enum type, nor can the sort ordering
  of such values be changed, short of dropping and re-creating the enum type."
- PostgreSQL docs, [Arrays](https://www.postgresql.org/docs/current/arrays.html):
  the tip quoted under Column types.
- PostgreSQL wiki, [Don't Do This](https://wiki.postgresql.org/wiki/Don't_Do_This):
  timestamp without time zone, char(n), varchar(n) by default, money, and serial.
- William Kent, [A Simple Guide to Five Normal Forms in Relational Database Theory](https://www.bkent.net/Doc/simple5.htm):
  normalization rules "are designed to prevent update anomalies and data
  inconsistencies".
- Bill Karwin, [*SQL Antipatterns, Volume 1*](https://pragprog.com/titles/bksap1/sql-antipatterns-volume-1/),
  chapter "Polymorphic Associations" ("Antipattern: Use Dual-Purpose Foreign
  Key"). Only the table of contents was readable on 2026-10-01. The one-target
  check above is this file's own recommendation, not a quotation from the book.
