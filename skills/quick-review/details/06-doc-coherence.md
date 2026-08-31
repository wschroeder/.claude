# Pass 6 — Doc/code coherence

For every comment, docstring, `@moduledoc`, `@doc`, or prose claim added or touched in the diff: verify the code delivers on it. Comments that contradict the code are not cosmetic — they are the most common signal of a promise that was planned but not implemented, or implementation that drifted from intent.

## 6.1 Comment-vs-body check

For each comment in a new/changed function, read the following statements and confirm each claim is executed. If a comment says "still validated if presented", grep the body for the validation; if the body pattern-matches `_` and returns `:ok`, the comment is lying.

## 6.2 Docstring contract

For each `@doc` / `@moduledoc` with behavior claims (validates X, returns Y on Z, raises on W), check the function body produces that behavior on those inputs. If the docstring lists error cases, every listed case must be reachable from the body.

## 6.3 Name-vs-body check

Function and variable names that promise action (`validate_*`, `authenticate_*`, `verify_*`, `ensure_*`, `require_*`) must perform that action. A function named `validate_signature` whose body unconditionally returns `:ok` when a specific field is present is a misnomer — flag it.

## 6.4 PR/commit-message-vs-diff check

If the PR body or commit message claims the change does X ("reject wildcards", "require secret unless PKCE"), grep the diff for the enforcement. Missing enforcement with present claim is a legit finding — the bug-class the author thought they fixed is still open.

## 6.5 Distant-doc symbol drift

Angles 6.1-6.4 are scoped to claims TOUCHED in the diff. When the diff DELETES or RENAMES a model, function, route, env var, role enum value, or named concept, the distant docs (`docs/`, `README*`, `CHANGELOG*`, `ARCHITECTURE*`, design specs, RFCs, the project's `*.md` files) need to be re-checked even though they're outside the diff.

A doc that names a deleted symbol is itself a `hypothesis:` line — it asserts a reality the code no longer supports. Distant-doc claims about deleted concepts are Fix-class drift; the cost of strikethrough or paragraph rewrite is trivial, the cost of letting the spec lie to a future reader compounds across every onboarding pass.

**Discovery method:** for every `model X` decl removed, `function f` deleted, `route P` retired, `enum E` value dropped, or env var renamed in the diff, run `git grep -l "<old-name>" -- '*.md' 'docs/' 'README*'` and inspect each hit.

Sibling files that explicitly track the migration (a TODO.md, a CHANGELOG entry, a migration plan) are exempt — they're allowed to describe the historical state. Authoritative specs that still name the deleted concept are NOT exempt — they govern future work and will misdirect it.

Comment/code drift is how `hypothesis:` creeps into production code. Treat every comment added in the diff as a testable assertion about the body below it.
