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

## 6.7 Old rule still stated

Angles 6.1-6.4 read the lines the diff touched, and 6.5 reads distant docs about a deleted symbol. Neither reads an untouched line that states a rule the diff changed. Name each rule the diff changes in one sentence, such as "an account with no verified statement adds nothing to the totals". Grep every file the diff edits, and the spec pages, for the old rule's key words, and quote each hit. Fix each one, or give it a line saying why it stays.

Measured (2026-10-20): the outside reviewer found stale text in all four ranges it read, and our own review found none of it first. One hit was a comment in an aggregates module that still said records with no document contribute nothing, two lines below a comment the diff had updated. Others were a form hint, an analytics header, and a line in `features.md`. The same kind of finding had come from the outside reviewer on the two slices before.

## 6.8 Spec sentence vs code

6.1 lists comment blocks, and 6.7 greps for the old rule's words. Neither splits a new spec sentence into the cases it names. For each sentence the diff adds to or edits in `docs/spec/`, list every case the sentence names, and quote the code line that makes each one true. A sentence joined by "or" or "and" names two cases and needs two lines. A case with no line is a finding: either the code is missing or the sentence promises too much, and the review checks which.

Measured (2026-10-22): `workers.md` said the 15-minute pickup checks again a document "whose save keeps failing, or whose model call keeps failing". Only the first case had a line: when `savedWithRetries` gives up and throws, `runRequestedCheck` skips `finishCheckRequest`, so the request stays. A model failure returns a needs_review decision with `verification_model_failed`, the save succeeds, and `runRequestedCheck` clears the request, so nothing checks it again. Our review's 6.1 covered only the six code comment blocks that `comment_share.py` listed, and its 6.7 grepped only for the old rule's words. The outside reviewer found it on the second pass.

A sentence that names a whole class names one case for each member of that class, even with no "and" or "or" in it. Before quoting code, write down which members the code covers. If the code covers fewer, either the sentence names those members or it is a finding. Measured (2026-10-22): `design-system.md` said "Password managers offer to fill only the sign-in form", while the form components told only four named password managers to stay away. The sentence had no "and" or "or" to split on, and our review printed nothing for it under 6.1. The outside reviewer asked which manager the client's staff use, and the line was changed to name that one.

**A new member of a class reaches sentences the diff never touched.** Suppose the diff adds a kind, a source, or a state beside existing ones. Grep `docs/spec/` for each unchanged sentence that names one of its siblings, and say whether the new member follows that sentence. A sentence that leaves the answer unsaid is a finding. Measured (2026-10-22): the branch brought a second kind of record into the records the sync matches, pairs, and creates. An exclusion rule in the spec still said "every record of the first kind it matches, pairs, or creates", and the branch never edited it, so 6.8 never reached it. The spec said nothing on whether the new kind records exclusions, and the code wrote an empty list. The question came up only during the pull request's second review.

## 6.9 Spec lists additions

6.5 checks distant docs for what the diff deletes. Nothing checks them for what it adds. A spec often keeps one page that lists every thing of a kind: the schema page lists columns and constraints, the routes page lists routes, the configuration page lists settings, and the audit page lists actions. For each column, constraint, route, setting, or audit action the diff adds, find that page and quote the line that names the addition. A missing line is a finding, whether or not the diff touched that page.

Discovery method: list the migration's `add column` and `add constraint` lines, each new route path, each new key in the config schema, and each new audit action string. Then grep `docs/spec/` for each name.

Measured (2026-10-22): three migrations added two columns, a check pairing them, and a new table, and `database-schema.md` named none of them. No line of our reviews under 5.20, 6.5, or 6.8 named a migration, a column, or the schema page. The outside reviewer found it.

Comment/code drift is how `hypothesis:` creeps into production code. Treat every comment added in the diff as a testable assertion about the body below it.
