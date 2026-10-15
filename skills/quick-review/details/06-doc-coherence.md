# Pass 6 — Doc/code coherence

For every comment, docstring, `@moduledoc`, `@doc`, or prose claim added or touched in the diff: verify the code delivers on it. Comments that contradict the code are not cosmetic — they are the most common signal of a promise that was planned but not implemented, or implementation that drifted from intent.

## 6.1 Comment-vs-body check

For each comment in a new/changed function, read the following statements and confirm each claim is executed. If a comment says "still validated if presented", grep the body for the validation; if the body pattern-matches `_` and returns `:ok`, the comment is lying.

When a comment claims that a value stays safe somewhere else — escaped for a parser, valid for a consumer — the statements next to the comment cannot prove it. Run the value through every path that the consumer has, and show what comes out. Worked example: `dsValue` escaped `$`, `@`, and `;` for Datastar, and its comment said so. Our review wrote "comments match the code (& $ @ ; escaped ...)". Datastar's keyless `data-signals` path decoded the escapes and compiled the text again, so `$activePath` inside a string became a signal read.

When a comment claims a transform produces a shape a consumer reads, run the transform on every input shape its type admits (array, enum, object, union), not only the shapes in use today, and show what comes out. Worked example: `modelReplySchema` rewrote Zod's nullable `anyOf` into `type: [X, 'null']`, as its comment said strict structured outputs expect. Every nullable field in use was a string or a number, so the pinned schemas matched. A nullable array, enum, or object lost its `items`, values, or properties, and an outside reviewer found it.

## 6.2 Docstring contract

For each `@doc` / `@moduledoc` with behavior claims (validates X, returns Y on Z, raises on W), check the function body produces that behavior on those inputs. If the docstring lists error cases, every listed case must be reachable from the body.

## 6.3 Name-vs-body check

Function and variable names that promise action (`validate_*`, `authenticate_*`, `verify_*`, `ensure_*`, `require_*`) must perform that action. A function named `validate_signature` whose body unconditionally returns `:ok` when a specific field is present is a misnomer — flag it.

A test's title is a name that promises behavior too. For every test the diff adds or changes, read the title against its assertions. Where they disagree, one of them is wrong, and the review has to say which one, by checking the spec, before it moves on. A test whose assertions pin the opposite of its title passes every mutation check while it guards the bug.

Measured on a client pull request: a test titled as handing a value back to its original source asserted that the replacement value stayed.

## 6.4 PR/commit-message-vs-diff check

If the PR body or commit message claims the change does X ("reject wildcards", "require secret unless PKCE"), grep the diff for the enforcement. Missing enforcement with present claim is a legit finding — the bug-class the author thought they fixed is still open.

## 6.5 Distant-doc symbol drift

Angles 6.1-6.4 are scoped to claims TOUCHED in the diff. When the diff DELETES or RENAMES a model, function, route, env var, role enum value, or named concept, the distant docs (`docs/`, `README*`, `CHANGELOG*`, `ARCHITECTURE*`, design specs, RFCs, the project's `*.md` files) need to be re-checked even though they're outside the diff.

A doc that names a deleted symbol is itself a `hypothesis:` line — it asserts a reality the code no longer supports. Distant-doc claims about deleted concepts are Fix-class drift; the cost of strikethrough or paragraph rewrite is trivial, the cost of letting the spec lie to a future reader compounds across every onboarding pass.

**Discovery method:** for every `model X` decl removed, `function f` deleted, `route P` retired, `enum E` value dropped, or env var renamed in the diff, run `git grep -l "<old-name>" -- '*.md' 'docs/' 'README*'` and inspect each hit.

Sibling files that explicitly track the migration (a TODO.md, a CHANGELOG entry, a migration plan) are exempt — they're allowed to describe the historical state. Authoritative specs that still name the deleted concept are NOT exempt — they govern future work and will misdirect it.

Comment/code drift is how `hypothesis:` creeps into production code. Treat every comment added in the diff as a testable assertion about the body below it.
