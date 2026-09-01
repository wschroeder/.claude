---
name: elixir-development
description: Elixir, Ecto, and Phoenix conventions that hold in any project — pipe-style queries, schemas and changesets over Ecto.Changeset.change/2, query timeouts, migration safety, module organization, dependency lookup, ExUnit test hygiene including capture_log, and date/timezone handling. Loaded by writing-code when the work is Elixir. Use when writing or reviewing .ex, .exs or .heex code, adding dependencies, running mix, or chasing a compiler warning.
paths:
  - "**/*.ex"
  - "**/*.exs"
  - "**/*.heex"
  - "**/*.eex"
  - "**/mix.lock"
---

## Purpose

Elixir, Ecto, and Phoenix conventions that hold regardless of project. Comment
discipline and naming are not here — `writing-code` owns those for every language,
and this skill assumes it is already loaded.

A project that carries its own `elixir-development` overrides this one inside that
project. Whatever is specific to a repo — its directory layout, its shell setup, its
repo module names, its Elixir and OTP versions — belongs in that copy, not here.

## Ecto

### Query syntax

Always use pipe syntax:

```elixir
# Good
User
|> where([u], u.active == true)
|> order_by([u], desc: u.inserted_at)
|> limit(10)
|> Repo.all()

# Bad
Repo.all(from u in User, where: u.active == true, order_by: [desc: u.inserted_at], limit: 10)
```

### Changesets

Go through the schema module's `changeset/2` (or another schema-defined changeset
such as `create_changeset/2`), never `Ecto.Changeset.change/2` directly. The
schema's changeset enforces casts, required-field validation, and domain
validators; `change/2` bypasses all of them and lets bad data reach the database,
where only raw unique indexes and NOT NULL constraints catch it — often as an
exception that aborts the surrounding transaction. This applies to one-off scripts
and production fixes as much as to application code. If a schema has no changeset
for the fields you need, add one.

`Repo.insert_all`, `update_all`, `delete_all`, and raw SQL bypass the changeset
entirely. For any field written through one of those, confirm it is validated
somewhere on the path — route the rows through `changeset/2` first, or replicate
the check. Bulk-insert convenience is not a reason to ship unvalidated writes.

Adding a validation to a *shared* changeset binds every caller: a `Repo.insert!`
caller turns the new error into a raised exception. Scope new strictness to a
dedicated changeset variant when some callers must stay lenient.

### Query timeouts

Ecto query functions use a 15-second default timeout. Batch queries and complex
joins on large tables exceed it. Pass a timeout explicitly on any query touching
large tables:

```elixir
Repo.all(query, timeout: @timeout)
```

See [references/ecto-timeouts.md](references/ecto-timeouts.md) for what happens to
the connection pool when one of these times out.

### Migration safety

**Never run `mix ecto.reset`** unless explicitly asked and confirmed. It drops and
recreates the database.

On a missing-field error: check for unrun migrations first, read the migration
files, explain what needs to run, and wait for explicit confirmation before running
anything.

Specify the repo explicitly when generating migrations:

```bash
mix ecto.gen.migration -r MyApp.Repo migration_name
```

## Elixir

### Pattern matching

Prefer pattern matching in function heads over branching in the body:

```elixir
def handle_event(%{type: "create"} = event), do: create_handler(event)
def handle_event(%{type: "update"} = event), do: update_handler(event)
def handle_event(%{type: "delete"} = event), do: delete_handler(event)
```

### Pipes

Use pipes for data transformations:

```elixir
params
|> validate_params()
|> transform_data()
|> save_to_database()
|> handle_result()
```

### With

Use `with` for sequential operations that can fail:

```elixir
with {:ok, user} <- fetch_user(id),
     {:ok, account} <- fetch_account(user),
     {:ok, balance} <- calculate_balance(account) do
  {:ok, balance}
end
```

### Module organization

Private functions (`defp`) go at the end of the module, after all public functions
and test blocks. Changeset helpers may sit next to the changeset they support.

### Aliases

Add an `alias` only when the module is used more than once. Otherwise write the
full path.

### `@doc` on private functions

Never put `@doc` on a `defp` — the compiler warns, because the docstring has
nowhere to go.

## Dependencies

Never use trained knowledge for versions; training data is stale by definition. Look
the version up:

- `mix hex.info <package>` for available versions
- [hex.pm](https://hex.pm) for the latest release
- Web search for compatibility

Check compatibility against the project's Elixir and OTP versions before adding, and
take the latest compatible version.

## Build verification

Verify the build compiles cleanly before committing:

```bash
mix compile --warnings-as-errors
```

Fix every warning. Do not commit code that warns.

## Testing

`tdd-cycle` drives the loop. What follows is what the tests themselves look like.

### Structure

```elixir
describe "function_name/arity" do
  test "returns expected result for valid input" do
    input = build_input()
    result = Module.function_name(input)
    assert result == expected_value
  end
end
```

### `Mock` requires `async: false`

`Mock` is incompatible with async tests. Any test using it sets `async: false`.

### No unused variables

If a value is returned, either assert on it or do not capture it:

```elixir
# Bad — underscoring fixtures
_other_user = insert(:user)
{:ok, _user, _token, roles} = authenticate(...)

# Good — assert on what came back
{:ok, user, token, roles} = authenticate(...)
assert user.id == expected_id
assert is_binary(token)

# Also good — do not capture what you do not need
insert(:user)
{:ok, _, _, roles} = authenticate(...)
```

Underscores are for function parameters and descriptive wildcard matches, not for
"I created this but do not need it."

### No leaked logs

Wrap any test that triggers logging in `capture_log`, and assert on the message when
it is part of the expected behavior:

```elixir
import ExUnit.CaptureLog

test "handles failure" do
  log = capture_log(fn ->
    assert {:error, _} = SomeModule.operation()
  end)
  assert log =~ "expected error message"
end
```

New code must not introduce new compiler warnings or new log output.

### Fire-and-forget tasks

An async task that makes database calls must skip in test, or it outlives the
sandbox connection:

```elixir
defp async_update(id) do
  if Application.fetch_env!(:my_app, :env) == :test do
    :noop
  else
    now = DateTime.utc_now()
    Task.start(fn -> Repo.update(...) end)
  end
end
```

Capture any timestamp at call time, not inside the task.

### Association consistency

When building a struct with an association, set both the association and its id, or
Ecto warns:

```elixir
# Bad
%Post{author: user}

# Good
%Post{author: user, author_id: user.id}
```

### Run what you changed

You are not done until every test you added or modified runs successfully.

## Phoenix

### Controllers

Keep them thin; delegate to contexts.

```elixir
def create(conn, params) do
  case Accounts.create_user(params) do
    {:ok, user} ->
      conn
      |> put_flash(:info, "User created")
      |> redirect(to: ~p"/users/#{user}")

    {:error, changeset} ->
      render(conn, :new, changeset: changeset)
  end
end
```

### Contexts

Group related functionality behind one module rather than scattering it across
controllers.

## Dates and timezones

See [references/date-handling.md](references/date-handling.md).

## Reviewing rather than writing

When you are reviewing and find a violation, do not fix it on the spot. Report it
and wait for confirmation.

## Key principle

Match the patterns already in the codebase. When in doubt, find a similar
implementation and follow it.
