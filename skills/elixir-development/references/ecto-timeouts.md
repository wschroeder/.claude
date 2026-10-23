# Ecto query timeouts

## The default

`Repo.all/2`, `Repo.one/2`, and the other query functions use a 15-second default
timeout. This is the Ecto adapter's default, not a PostgreSQL setting — a database
with no `statement_timeout` configured anywhere will still produce these.

When the timeout fires, PostgreSQL returns error code `57014` (`query_canceled`),
because Ecto/DBConnection calls `pg_cancel_backend()`.

## The common miss: a module attribute that only covers some calls

A module that defines a `@timeout` attribute usually applies it to the main query
and forgets the batch helpers around it. Those bare `Repo.all(query)` calls inherit
the 15-second default, and they are often the ones joining the largest tables.

When adding a timeout to a module, grep the module for every `Repo.` call rather
than only the one that timed out.

## Connection pool corruption after a timeout

A timed-out query can leave its connection in a bad state. Subsequent queries on
that same connection fail with `ssl recv: closed`, and that cascades through the
pool — several consecutive failures follow a single slow query.

The signature in a retrying job is: attempt 1 `query_canceled`, attempts 2 through 5
`ssl recv: closed`. The later attempts are not new problems; they are the pool
recovering.

## The fix

```elixir
Repo.all(query, timeout: @timeout)
```

Pass it explicitly on any query touching a large table or using a complex join.
