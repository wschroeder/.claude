# PostgreSQL schema and migrations

Read this before designing or changing a PostgreSQL schema: a migration file, any DDL, or the comments stored in the catalog. Writing queries is out of scope. Every SQL block here ran against PostgreSQL 16.

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

1. Read the live schema and the project's schema spec before you change either one.
2. Dump the live schema with `pg_dump --schema-only --schema=<schema> --no-owner --no-privileges`, because migrations, spec pages, and the live database can drift apart.

## One fact in one place

1. Make every non-key column "a fact about the key, the whole key, and nothing but the key" (Kent).
2. Derive a flag from the column that implies it, as a generated column:

  ```sql
  is_verified boolean generated always as (verified_at is not null) stored
  ```

3. Remove a generated column from every insert and update, because a write to it fails with `column "is_verified" can only be updated to DEFAULT`.
4. To make an existing plain column generated in PostgreSQL 16, drop it and add it again, and recreate any index that used it.
5. Give columns set and cleared together, such as a "who" and "when" pair, a check that holds them together:

  ```sql
  constraint kept_pair check ((kept_by is null) = (kept_at is null))
  ```

6. Put a per-child result of a one-to-many relation on the child, never on the parent.
7. Keep a fact the app filters, matches, or joins on in a real column, not inside a JSON document; use JSON only for data whose shape varies by subtype and that the app reads back whole.
8. Search the code for every write to a column, and drop the column if nothing writes it.
9. Denormalize only for a measured reason, and write the measurement in the migration's comment.

## Every reference is a foreign key

1. Never point at rows through an `entity_type` and `entity_id` pair. Give the referencing table one nullable foreign key column per target table, with a check that exactly one is set:

  ```sql
  client_id uuid references app.clients(id) on delete cascade,
  order_id  uuid references app.orders(id) on delete cascade,
  constraint one_target check (num_nonnulls(client_id, order_id) = 1)
  ```

2. Let an append-only audit log keep the pair, because an audit record has to outlive the row it describes.
3. When you replace the pair, drop it; never keep `entity_type` and `entity_id` as generated columns beside the per-target foreign keys, and look rows up by the foreign key columns.
4. If a rule says "once per entity", such as a tag applied to a record at most once, then put a unique constraint over the target columns that treats nulls as equal, which also serves as the target of `on conflict (tag_id, client_id, order_id)`:

  ```sql
  constraint entity_tags_entity_unique
    unique nulls not distinct (tag_id, client_id, order_id)
  ```

5. Reference a natural key with a composite foreign key, such as `foreign key (statement_id, section_key) references parent (statement_id, section_key)`; a null in any referencing column skips the check, so a nullable child column stays optional.
6. Choose `on delete` deliberately: `cascade` for rows that mean nothing without their parent, `restrict` for a parent that must not vanish while referenced, and `set null` only when the child row stays meaningful.
7. Enforce a rule that spans rows with a foreign key, a unique or exclusion constraint, or a trigger, because a check constraint sees only its own row.

## Indexes

1. Index the referencing columns of every foreign key, because PostgreSQL does not.
2. Never repeat an index: a primary key or unique constraint already builds one, and a plain index whose columns lead another index on the same table serves no extra query.
3. Index what the app looks up, including a business key inside JSON, an expression, or a partial predicate the queries use, and use a unique index when the business key must be unique.
4. Run the audit queries below after every migration that adds a table or a foreign key.

## Column types

1. Store a missing value as null, never a sentinel such as `'empty'`, `''`, `0`, `-1`, or `'1900-01-01'`; where the app needs a default for an unknown value, derive the conservative one when reading.
2. Use `timestamptz`, never `timestamp`.
3. Use `text`, not `varchar(n)` or `char(n)`, and put a real length limit in a check constraint.
4. Use `numeric` for money and rates, never `money` or a float.
5. Use identity columns, not `serial` or `bigserial`: `bigint generated always as identity`. To convert an existing serial column:

  ```sql
  alter table t alter column id drop default;
  drop sequence t_id_seq;
  alter table t alter column id add generated always as identity;
  select setval(pg_get_serial_sequence('t', 'id'), (select max(id) from t));
  ```

6. Prefer a check constraint over an enum type for a list of allowed values, because an enum value cannot be removed or reordered without recreating the type.
7. Use an array only for values nothing searches inside, and use a separate table otherwise.
8. Use `uuid` keys, or `bigint` identity keys, consistently, and make a column that refers to a uuid key `uuid`, never `text`.

## Document every table and column

1. In every migration that adds a table or a column, add a `COMMENT ON` for it:

```sql
comment on table app.invoice_section_totals is
  'A subtotal printed on an uploaded invoice, kept as a check figure against the line items read from that section. Never counts toward the customer balance.';
comment on column app.invoice_section_totals.kept_items_as_read_by is
  'Reviewer who chose to keep the line items as read when they disagree with this printed total; null until someone chooses.';
```

2. Say what the row or value means to the business, which rows it relates to, and when it is null.
3. Leave history, such as what the column used to hold or which ticket added it, to the migration file's own comment.
4. Change the comment in the same migration that changes the column's meaning.
5. Read comments back with `psql \d+ <table>`, `obj_description`, or `col_description`; the third audit query lists what has none.

## Migrations

1. Carry live data forward: alter a table that holds data in place, or copy its rows into the new table in the same migration, and never drop and recreate it.
2. Prove that a down file fully undoes its up file on a scratch database: apply every up file, then every down file in reverse with `psql -v ON_ERROR_STOP=1`, then every up file again, and diff a dump of the result against the live schema.
3. If a down file deliberately keeps a table, then make the first migration's down file drop that table, so the earlier down files can still run.
4. Run the real migration and the real rollback through the command the project deploys with before you call either done.
5. Name every delete or update in an up file, and the reason, in the migration's comment, and say that no down file brings the rows back.
6. Before you tighten a constraint, count the rows that would violate it, and `raise exception` with that count.
7. Add a trigger for `updated_at`, or it changes only where the app sets it.
8. Never edit a migration that has run anywhere except to make its down file work; change the schema in a new migration.

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
