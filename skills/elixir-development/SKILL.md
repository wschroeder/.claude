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

1. Apply these Elixir, Ecto, and Phoenix conventions in any project, with `writing-code` already loaded for comment discipline and naming.
2. Let a project's own `elixir-development` override this one inside that project, and put whatever is specific to a repo there: its directory layout, shell setup, repo module names, and Elixir and OTP versions.

## Ecto

### Query syntax

1. Always use pipe syntax:

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

1. Go through the schema module's `changeset/2`, or another schema-defined changeset such as `create_changeset/2`, never `Ecto.Changeset.change/2` directly, because `change/2` bypasses casts, required-field validation, and domain validators.
2. Apply this to one-off scripts and production fixes as much as to application code.
3. If a schema has no changeset for the fields you need, add one.
4. For any field written through `Repo.insert_all`, `update_all`, `delete_all`, or raw SQL, confirm it is validated somewhere on the path: route the rows through `changeset/2` first, or replicate the check.
5. If some callers of a *shared* changeset must stay lenient, scope new strictness to a dedicated changeset variant, because a `Repo.insert!` caller turns the new error into a raised exception.

### Query timeouts

1. Pass a timeout explicitly on any query touching large tables, because Ecto's 15-second default is too short for batch queries and complex joins there:

```elixir
Repo.all(query, timeout: @timeout)
```

2. See [references/ecto-timeouts.md](references/ecto-timeouts.md) for what happens to the connection pool when one of these times out.

### Migration safety

1. **Never run `mix ecto.reset`** unless explicitly asked and confirmed, because it drops and recreates the database.
2. On a missing-field error, check for unrun migrations first, read the migration files, explain what needs to run, and wait for explicit confirmation before running anything.
3. Specify the repo explicitly when generating migrations:

```bash
mix ecto.gen.migration -r MyApp.Repo migration_name
```

## Elixir

### Pattern matching

1. Prefer pattern matching in function heads over branching in the body:

```elixir
def handle_event(%{type: "create"} = event), do: create_handler(event)
def handle_event(%{type: "update"} = event), do: update_handler(event)
def handle_event(%{type: "delete"} = event), do: delete_handler(event)
```

### Pipes

1. Use pipes for data transformations:

```elixir
params
|> validate_params()
|> transform_data()
|> save_to_database()
|> handle_result()
```

### With

1. Use `with` for sequential operations that can fail:

```elixir
with {:ok, user} <- fetch_user(id),
     {:ok, account} <- fetch_account(user),
     {:ok, balance} <- calculate_balance(account) do
  {:ok, balance}
end
```

### Module organization

1. Put private functions (`defp`) at the end of the module, after all public functions and test blocks.
2. Let changeset helpers sit next to the changeset they support.

### Aliases

1. Add an `alias` only when the module is used more than once, and otherwise write the full path.

### `@doc` on private functions

1. Never put `@doc` on a `defp`, because the compiler warns.

## Dependencies

1. Never use trained knowledge for versions; look the version up:
   - `mix hex.info <package>` for available versions
   - [hex.pm](https://hex.pm) for the latest release
   - Web search for compatibility
2. Check compatibility against the project's Elixir and OTP versions before adding, and take the latest compatible version.

## Build verification

1. Verify the build compiles cleanly before committing:

```bash
mix compile --warnings-as-errors
```

2. Fix every warning, and do not commit code that warns.

## Testing

1. Let `tdd-cycle` drive the loop; these rules govern what the tests themselves look like.

### Structure

1. Structure tests as `describe` blocks per function:

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

1. Set `async: false` on any test using `Mock`, because `Mock` is incompatible with async tests.

### No unused variables

1. If a value is returned, either assert on it or do not capture it:

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

2. Use underscores only for function parameters and descriptive wildcard matches.

### No leaked logs

1. Wrap any test that triggers logging in `capture_log`, and assert on the message when it is part of the expected behavior:

```elixir
import ExUnit.CaptureLog

test "handles failure" do
  log = capture_log(fn ->
    assert {:error, _} = SomeModule.operation()
  end)
  assert log =~ "expected error message"
end
```

2. Introduce no new compiler warnings and no new log output.

### Fire-and-forget tasks

1. Make an async task that makes database calls skip in test, because otherwise it outlives the sandbox connection:

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

2. Capture any timestamp at call time, not inside the task.

### Association consistency

1. When building a struct with an association, set both the association and its id, or Ecto warns:

```elixir
# Bad
%Post{author: user}

# Good
%Post{author: user, author_id: user.id}
```

### Run what you changed

1. Run every test you added or modified, and finish only when each passes.

## Phoenix

### Controllers

1. Keep controllers thin, and delegate to contexts:

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

1. Group related functionality behind one module rather than scattering it across controllers.

## Dates and timezones

1. Read [references/date-handling.md](references/date-handling.md) before handling dates or timezones.

## Reviewing rather than writing

1. When you are reviewing and find a violation, report it and wait for confirmation rather than fixing it on the spot.

## Key principle

1. Match the patterns already in the codebase, and when in doubt, find a similar implementation and follow it.
