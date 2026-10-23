# Skills to load

Load each that matches. Each becomes additional named angles in the relevant pass.

- **Any `.ex` / `.exs`** → `elixir-development` (Pass 5 conventions, Pass 7 tests)
- **Raw SQL / `Repo.query` / ClickHouse / untrusted input** → `security-review`

These live in one project only. Load each when it appears in the available skills; otherwise the angles in Pass 5 and Pass 7 cover the same ground by hand:

- **Any backend change** → `code-quality-checklist` (lint, console-log removal, duplicate detection, testing requirements; `capture_log` rule)
- **Frontend null/race/XSS/GraphQL errors** → `security-review-fe`
- **TypeScript** → `quality-checks`, `eslint`
- **Migrations** → `safe-migration`, `elixir-migrations`

## The CLAUDE.md cascade

Load every `CLAUDE.md` from repo root to diff directory:

```
git rev-parse --show-toplevel
find <root> -name CLAUDE.md -not -path '*/node_modules/*' -not -path '*/_build/*' -not -path '*/deps/*'
```

Each CLAUDE.md rule is an additional named angle in its relevant pass. Recurring rules to watch for:

- **Default-branch detection** — `master` vs `main`; wrong branch ref produces a silently-empty diff
- **Elixir/Phoenix project rules** — SSM string-coercion, SSM-backed secrets vs `System.get_env`, `Phoenix.Token` vs DB-backed tokens, two-tier logging, direnv-required `mix`: `details/language-elixir.md`
