# Worked examples for the angles in the body

Why each always-live angle in SKILL.md reads the way it does: the misses that shaped it. Every rule a review must follow is in SKILL.md; nothing here adds a step.

## Contents

- 1.2 Query consistency
- 1.4 Handoff completeness
- 1.10 Behavioral regression
- 2.2 Semantic completeness
- 2.20 Checker evasion
- 2.18 Cross-writer race
- 4.1 Empty-value semantics
- 4.26 Outside-format variants
- 5.5 Private-helper duplication
- 5.7 Same-module sibling consistency (static)
- 5.16 Leftover code
- 5.18 Readability
- 5.19 Project linter and formatter
- 5.20 Project CLAUDE.md duties
- 6.1 Comment-vs-body check
- 6.2 Docstring contract
- 6.3 Name-vs-body check
- 6.4 PR/commit-message-vs-diff check
- 6.5 Distant-doc symbol drift
- 6.7 Old rule still stated
- 6.8 Spec sentence vs code
- 6.9 Spec lists additions
- 7.2 Side-effect coverage
- 7.8 Test intent vs test effect
- 7.11 Tests added by the current review loop are not authoritative
- 7.23 Excess tests
- 9.9 Whole-repo copies of a changed value
- Classifying hits

### 1.2 Query consistency

When new code queries a table/schema, grep for all other queries on that same table for the same logical entity (e.g., same ID field). Compare WHERE clauses. If another function uses a broader or different lookup (e.g., `field_a OR field_b`), the new query must account for the same cases or explain why not.

When the diff changes what makes two rows the same, such as a saved parent name giving way to a parent id, list every query that decides sameness side by side: dedup deletes, unique indexes, merges, and lookups. Each one must compare the same expression. One left comparing the old key lets two rows the others treat as one survive, or lets a merge delete a row the index would have kept.

Worked example: a pull request tied each remembered external number to a parent id, but a vendor name can move from parent A to parent B while older remembered numbers keep A's id. The move-to-record dedup delete and the parent-merge combine still treated two rows with the same saved name as one, so they deleted A's row when the receiving record held the same number under B. The unique index compared the saved name too and refused to hold both rows. An outside reviewer caught it. Our review had written "6.3 test title: "keeps one remembered number when the imported record already remembers it" matches its assertions", which checked a title against one test and never put the sameness queries next to each other.

Compare which rows each query leaves out, not only its key. Worked example: the same pull request let a nightly sync from an outside system retire (supersede) a record. The main lookup skipped superseded records and the remembered-number lookup did not, so a later upload could file itself onto the retired record. Our review wrote "1.2 sameness queries: DEMONSTRATED. parentIdentity and rememberedParentIdentity both compare through one coalesce(parent_id, name key) expression", which compared the keys and never the filters.

When a match picks one of several candidates, by a tie-break such as `first` or `latest`, build two candidates that share the key and say what happens to the subject whose candidate lost. It is compared with the winner's record, so a finding can blame someone for a mismatch that is not theirs. Worked example: A client feature matched each new user to a scanned form by online-banking ID with `tieBreak: 'first'`. Two users under one ID both got the first form, and the second was reported as set up wrong. Neither review arm caught it on its own; the operator did.

### 1.4 Handoff completeness

When new code produces output later consumed by unchanged code, read the unchanged consumer. Does the new code's output cover all cases the consumer expects? Pay special attention to `Repo.one()` downstream — if it can match on multiple criteria, the upstream filter must exclude on all those criteria.

Reading the new shape is half the angle. For every write in the diff that clears a marker, releases a claim, or changes where a value came from, name the row's state afterwards, then read what the consumer shows from that state — the value and any label attached to it, such as a source badge — and check both against the product spec. A consumer that reads the state without error can still show something false: a value the badge credits to the wrong source, or one the product spec says should have been replaced. Prove it with a test or a query against the post-write row and the line that renders it, not by reading the write alone.

Measured on a client pull request: the review recorded that clearing an import's provenance marker left the imported value in place, and never asked what the page showed next. The page labeled any value without the marker as coming from the other source, so it showed the imported value under the wrong source's badge. Copilot found it by asking that question.

**Every reader, not only the writer.** When the diff adds a table or a new state, including a new value it writes into an existing column or a new kind of audit event under an existing action, grep for every unchanged function that reads it or should read it — existence checks, delete guards, and re-resolvers that run when a page opens — and drive each one through its real path. Testing the code that writes the new state proves nothing about a reader that ignores it.

Worked examples, both from one pull request that added remembered external numbers:

- A delete guard checked documents, adjustments, notes, and tags before retiring a record, but not remembered numbers. The nightly sync then deleted a record that held only remembered numbers and cascaded them away. Our review wrote "misreading of two records keeps its numbers: met (test "misreads two records")": that test checked the numbers were left in place and never checked whether the record survived.
- `resolveDocumentMatch` re-resolved a document whenever the file page opened, using the main lookup alone, and saved `no_match` over the `ambiguous` result that processing had reached from remembered numbers. Our review wrote "1.4 handoff completeness: DEMONSTRATED. The F4 test drives real processing and reads back the stored record and status.", which drove the writer and never opened the page.
- A remembered-number check wrote an `auto_verify` decision into the existing document-verification audit action. `documentCardStatus` labelled a file card from the latest such decision, so a card read Verified after a reviewer had unverified the document. Our reader grep searched for the new table and column names only, and the card's reader names neither.

**A new value in an old column reaches every query of that table.** A reader that sums or counts the table's rows never names the new value, so a grep for the value cannot find it. Grep for the table, and for each total or count it feeds, show with a test whether a row in the new state is in or out, as the spec says. Measured: the sync began keeping a superseded record when a note or an entered amount referenced it. Our review wrote "1.4 Handoff to the next run: DEMONSTRATED. The superseded record stays superseded and is not flagged not found the next night", which drove the sync alone. `customerTotals` took every record with the customer's id, so one 10,000 item counted as 20,000 in the customer's total. An outside reviewer found it.

**A list, a picker, or a write target reads the table too.** "Per-record, not a total" is no reason to mark a reader N/A. Measured on a second review pass (2026-10-22): the review grepped for the superseded state and wrote "listValueChanges, currentItemsSql, listCustomersByRecord, tag.ts matchingEntitySql: per-record or filter, not totals. N/A." It never named `listMergeCandidates` or `getCustomerDetailPage`. So the merge dialog offered a superseded record as a target, and the customer page listed superseded rows with their values beneath a total that left them out. An outside reviewer found both.

**When a row leaves the totals, ask where the user's data on it counts now.** That data includes an amount someone entered, an uploaded document, and a saved choice. On one branch a reviewer found that "nothing moves the amount elsewhere" when the sync superseded a record. The spec then settled it by copying the rule for a saved rate: "the entered amount stays on the superseded record". But a rate on a record that counts nowhere changes nothing, while the amount stopped counting, and so the customer fell back to a different value. That spec sentence went out without the operator seeing the question, and the outside reviewer asked it.

### 1.10 Behavioral regression

Silent contract changes are the most expensive kind of review miss: a function that used to merge two inputs and now returns only one has regressed, but its tests pass because someone wrote them against the new shape. If the new behavior is a fix the author meant, the pull request body says so.

### 2.2 Semantic completeness

Example: `maybe_attach_payment_method` calls `attach` but never sets the attached method as the default, so the name promises more than the body delivers.

Worked example: a patch to the Kita XSS scanner checked props passed by name and skipped props passed through a spread. Two handoffs carried the gap, and our review answered it with "All 13 JSX spreads print `markup=[]`", which measured today's spreads. An outside reviewer built a spread that carried user text into a markup prop, and the scanner passed it.

### 2.20 Checker evasion

When the diff adds or changes a checker — a linter, a scanner, a validator, an allowlist — the checker is the code under review, and its inputs are the source it reads. List each way someone could write the forbidden thing so that it reaches the consumer but not the checker, write one fixture per way, and run the checker on each. The usual ways:

- a different case, where the consumer folds case and the checker does not (an HTML parser lowercases attribute names)
- a computed key or a value whose type is `string`, where the checker reads only literals
- a spread, where the checker reads only named attributes or arguments
- a look-alike, where the checker matches a name another type can also carry (a property called `__brand`)
- a type with no declaration site (`Record`, `Pick`, a mapped type), where the checker trusts a property by where it was declared
- a value stored first (a const, a let, a destructure, a function's return), where the checker reads only the expression at the point of use

The proof is each fixture with the checker's output beside it. Matching the checker's list against today's registered names, or grepping today's code for the look-alike, measures the present and proves nothing about the next input. Worked example: lint-datastar matched `data-on-click` but not `data-on-Click`, read only literal keys, and accepted any `__brand` property as its own. Our review wrote "DATASTAR_PLUGINS matches all 22 registered names" and "`__brand` appears only in datastar-expression.ts". An outside reviewer wrote three fixtures and got past the linter with each. After those fixes our review wrote "2.20 checker evasion: DEMONSTRATED, 7 probes", every probe one of the first four ways. The same reviewer then got past it again with a `Record<'data-text', string>` spread, whose property has no declarations, and with `const text = label as 'x'` stored before the attribute read it.

When two or more ways round share one thing the checker trusts, such as a type, a flag, or where something was declared, name it. Then run the checker with that trust removed, on the fixtures and on the real codebase. If a fix closes the ways one at a time, it leaves the trust open. A reason to keep the trust, such as "it would fire on legitimate code", stays a hypothesis until that codebase run shows the false alarm. Worked example: lint-datastar trusted any value whose type was a string literal. Our reviews found a literal cast, then a stored cast, a branch, an assignment, a literal-typed parameter, and a tuple element, and each fix followed one more form. We kept the trust on a guess that dropping it would fire on `query.sort as …` in the activity routes. An outside reviewer dropped it, and the app linted clean.

### 2.18 Cross-writer race

2.4 to 2.7 ask whether one path is safe against a second copy of itself. This angle asks whether it is safe against every other path that writes the same rows. Concurrency findings in a review usually hide here, because each function looks atomic when read alone.

Method:

1. For each write path in the diff, list the tables it writes and the parent rows its foreign keys reference.
2. Grep for every other function that writes, deletes, or merges those rows or those parents, inside the diff and outside it.
3. Build a table of the pairs. For each one, name the lock, constraint, or transaction that puts the two in order. A pair with nothing between them is the finding.

Watch for these two signs:

- **Sibling lock asymmetry.** Most writers of an entity open with `select ... for update` on it, and one does not. If the review writes "A, B, and C lock the row; D is one statement", then it has already described the finding. One statement is atomic against itself and orders nothing against a writer holding a row lock.
- **Two paths taking the same two locks in opposite orders.** Quote each path's lock order side by side. Count the locks a statement takes without asking as well as the explicit ones: an UPDATE or DELETE locks every row it touches, and an insert or a foreign-key change takes a key-share lock on the parent row. Worked example: the document save took the new-parent lock and then the remembered-number lock, while the record page took them in the reverse order, and the two deadlocked (Postgres `40P01`). Second worked example: the record-page edit locked its remembered row and then key-share locked the parent, while the parent merge locked both parents `for update` and then ran `update app.remembered_numbers set parent_id = ...`, which locks those rows. Our review listed "mergeParent = documents of records holding numbers under parent -> parents FOR UPDATE", left out the UPDATE's row locks, and wrote "No pair reversed."; the two deadlocked. Count the table lock each statement needs too. In Postgres, `select … for update` takes only ROW SHARE on the table, which a SHARE ROW EXCLUSIVE lock held by another path does not block. The first UPDATE, INSERT, or DELETE needs ROW EXCLUSIVE, which it does block. So a path that row-locks a row and then writes it deadlocks against a path that holds a table lock and then writes the same row. If either path takes a table lock, then quoting the lock order is not proof: hold the pair open and run them. Third worked example: a person's merge locked the record it kept `for update` and then updated it, while the nightly sync held a share row exclusive lock on the table and then upserted that same record. Our review wrote "A user merge's UPDATE takes row exclusive, which waits behind share row exclusive.", and a second review checked only the record merged away, which the sync never writes. Neither review ran the two transactions, and the outside reviewer found the deadlock.
- **A writer that runs after a delete, a combine, or a duplicate left behind.** Once a path deletes or combines rows, or leaves duplicates that another path assumed could not exist, run every other writer of that table once more afterwards, not only at the same time, and show the result holds. Worked example: a parent merge deleted a record as a duplicate, and the next spreadsheet import's upsert inserted it again under a new id. Our review wrote "2.5, 2.7, and 2.18 races: DEMONSTRATED by [T3]" and ran no writer after the merge. Second worked example: a parent merge kept one remembered number on two records, and the next reviewer's link of an ambiguous document deleted the other record's copy and moved its unverified documents onto the linked record. Our review wrote "2.18 cross-writer: DEMONSTRATED, held-transaction tests for merge, sync, page add, and save", all run at the same time as the merge and none after it.
- **A child insert against a parent another writer is deleting.** Writer A inserts a child row that references a parent. Writer B has locked the parent and is deleting it or merging it into another. A's insert blocks on the foreign key's key-share lock. After B commits, the insert fails with a foreign-key violation (Postgres `23503`), and the route returns 500 where it should return 404. To fix it, have A lock the parent first in the same transaction, so that A either runs before B or finds no parent.

Artifact: hold writer B's transaction open in one session (for example with `pg_sleep`), run writer A in a second, and show the outcome. A test that races A against another A does not demonstrate this angle. "The outcome" means the invariant both writers promise, checked on the rows afterwards, at the concurrency production can reach (replicas times pool size). "Ran clean" is not an outcome.

List the writers by name, and include the deferred ones: a worker job that resumes later from what it captured earlier, and a model call that is in flight while a person edits the same rows. Pair each writer with its own test. "The concurrency tests" as a group is not proof for any one pair.

Worked examples, both from one pull request that added remembered external numbers:

- The moved-document check captured a remembered row's id, then resumed after the nightly sync had moved that row to another record without changing its id. The id still matched, so the check moved a waiting document onto the retired record. Our review wrote "2.18 cross-writer: DEMONSTRATED for the sync against the link and against the add", which paired the sync with two writers and never with the deferred check.
- Initial processing applied the model's answer after a reviewer had deleted the remembered number it relied on, and verified the document against the old record's evidence. Our review wrote "2.5, 2.7, and 2.18 races: DEMONSTRATED by the F1 test and the concurrency tests.", naming no pair at all.

### 4.1 Empty-value semantics

For every field in the diff that could be empty (empty list `[]`, empty string `""`, zero, absent key, empty MapSet), trace what the application does when it IS empty. Empty has three common meanings and they often get conflated:

- **"nothing requested"** — usually fine: fall back to defaults, skip the operation, no-op
- **"everything"** — wildcard, dangerous if it grants broader access than intended
- **"invalid — reject"** — spec violation: reject with a specific error

When the code's behavior for empty doesn't match the product's intent, it's a bug. Classic trap: `covers?(_, _, [])` returning `false` makes an empty-request "never satisfied" — resulting in an infinite consent re-prompt. Ask: "does the UX make sense if this field is empty?"

A string field is blank in more than one form: `null`, `''`, a string of only spaces, and whatever a transform leaves behind. A guard that refuses one form lets the rest through, and a `trim` turns `'   '` into `''`, which a `null` check passes. Run each form through every transform and then through the guard. Where a comment or doc promises the rule ("a blank login matches no login"), an input that cannot reach it today does not dismiss the gap: the promise is the contract.

Worked example: in a client repository, `transform` returned `null` only for an exactly empty cell, so two logins of only spaces both trimmed to `''`, and `keyMatch`, which refused only `null`, matched them. A review walked 4.1, wrote "keyMatch refuses null; LOGIN_ID is `\S+`, never blank", and moved on. The operator caught it.

An aggregate is empty too when a filter drops every row it reads: SQL's `sum`, `avg`, `min`, and `max` return `null` over no rows, not `0`, and so does `sum(...) filter (where ...)` when the filter matches nothing. For every filter or join in the diff that narrows an aggregate's input, drive the case where it drops every row, then find each reader of the aggregate and quote what it does with the `null`. A reader that takes `null` to mean "not reported" treats "reported, and worth nothing" as missing.

Worked example: in a client repository, `sum(...) filter (where excluded.item_key is null)` returned `null` when every line item on a document was excluded. `hasReportedTotal` read that record as unreported, so its customer never got the overdue flag. The whole-branch review had written "4.1 Empty values: DEMONSTRATED. A blank name matches nothing", which covered the item names and never the aggregate. A reviewer caught it on the pull request.

### 4.26 Outside-format variants

A parser of an outside format, such as a Word document, a PDF, a spreadsheet, or an API payload, usually handles the common form of each construct it reads. For each construct, name the variants the format allows and show that each one is read or refused with an error. A variant that is skipped without error loses data, and nothing reports the loss.

Worked example: a document generator's `findImages` matched pictures by `r:embed` only. It skipped an `r:link` picture without error and lost a paragraph's tail after a `<w:txbxContent>` text box. The subagent arm of the 2026-10-22 review trial found both by probing; the single session did not.

**Discovery method:** open the format's specification or schema at each element the parser matches, list the siblings and alternatives, and feed one of each through the parser.

**Drive each variant through every path that reads the same field.** A variant one path handles can still be read wrongly by another. Measured (2026-10-22): the sync used `itemNumber` to read the new kind's number when it created a record, but `pairNearNumbers` still called the old kind's reader `extractRecordNumber`. So an item line holding a number one digit off never paired with its imported record, and the sync created a second record for the same item. Our review checked only the create path ("The fix reuses the sync's own `itemNumber` instead of a new reader"). No review on the branch walked 4.26.

### 5.5 Private-helper duplication

Sibling-endpoint consistency (5.1) focuses on PUBLIC actions; the same scrutiny applies to PRIVATE helpers within the same module (or its imports). Look for `defp` functions with substantially-identical bodies — same `case`/`cond` structure, same response shape, same control flow, same conditional branching on the same predicate (`basic_auth_attempted?/1`, `authenticated_via_header?/1`, etc.).

Differences in name (`send_token_error/3` vs `send_refresh_revoke_error/3`), in which siblings call them, or in their place in the file do NOT justify duplication. Two helpers that diverge only in name are one helper waiting to be collapsed.

**Deletion test:** line up the two bodies; if every line of one matches the corresponding line of the other (modulo cosmetic ordering), collapse to a single shared helper. The exception — and it must be argued explicitly — is when the helpers diverge MEANINGFULLY today (different realm strings, different default error codes, different tracing/telemetry tags). Speculation about future divergence ("we might want different behavior later") does not justify keeping duplicates; the future change can introduce the split.

**A diff that makes the same edit in several copies triggers the deletion test.** Name the copies, then collapse them or argue how each one differs. Checking that every copy changed the same way treats them as siblings to keep in step, which is the cost the deletion test exists to remove. Worked example: an escaping fix changed four copies of a `Field` component the same way. Our review wrote "every Field copy ... converted the same way" and moved on. An outside reviewer pointed out that the next escaping fix would have to find all four again.

**One shape written in two notations is duplication too:** a JSON schema and the Zod schema that parses the same reply, SQL DDL and the TS row type, an OpenAPI document and its handler. Agreement today is not the proof. The proof is that one copy derives from the other, or that a test fails when the two drift. Worked example: the reply schemas sent to the model and the strict Zod schemas that parsed the replies were both written by hand. Our review wrote "`PageTriageReplySchema` matches `PAGE_TRIAGE_RESPONSE_SCHEMA`." A required field added to one and not the other would have failed every file, while the test doubles, built from the Zod types, stayed green.

**A test holds two copies together only on the branches it was shown to catch.** Where the copy branches, prove it with one mutation per branch, as [proof-shapes.md](proof-shapes.md) "Assertion strength" lists them: two caught mutations prove those two branches and no others. Measured (2026-11-05): a database view recomputed in SQL a figure the app computes in TypeScript, through a ladder of more than a dozen fallbacks. Our review wrote "the view copies [the app's functions], and the test holds the copies together", citing two mutations. The whole-branch review ran 37 mutations, and 11 of them left the test green.

**Count copies across every file the branch adds, an earlier migration on the same branch included.** Where a later migration on the branch replaces what an earlier one on the same branch created, so the earlier file still carries a full copy, flag it: folding the two is the operator's call, once they confirm no shared database has run either. Measured (2026-11-05): our review wrote "[the SQL] lives once, in [the new view]", while an earlier migration on the branch still held a full inline copy and the later migration's down file restored about 200 lines of it.

**Sharing a helper is not proof that it fits a new kind.** When a helper written for one kind starts serving another, name the reader, parser, and default it runs for the new kind. Measured (2026-10-22): our review wrote "5.5 DEMONSTRATED: one pairing helper is shared, not copied". The new kind's pairing went through that helper, which still ran the old kind's number reader inside it.

### 5.7 Same-module sibling consistency (static)

Grep sibling functions with similar signatures in the same file. If `find/3` has an `when is_binary(x)` guard and a fallback clause but `find_and_do/4` doesn't, the inconsistency is a latent bug even if nobody triggers it today. Don't wait for an upstream change to justify the finding — static inconsistency between siblings is itself the finding. Flag any same-module pair with asymmetric guards, asymmetric error shapes, or asymmetric fallback clauses.

A pair that matches settles only this angle. "Mirrors `<sibling>`" is never a disposition for a correctness angle in Pass 1, 2, or 4: the new function's behavior still owes those passes, and so does the sibling's whenever the new function copies it. A flaw the two share is a finding against both, and the sibling's half falls under the scope rule because the diff copied it.

Measured on a client pull request: a release function left a stale value in place, and the review cleared it because its sibling release function did the same. Both had the bug.

**Two helpers that compute the same verdict must honor the same saved choice.** When a module holds two functions that each decide one thing, such as whether a document's line items block verification, read both for every choice a reviewer can save. One that honors the choice and one that overrides it is the finding, whichever one the diff touched. Worked example: `documentItemChecks` honored a reviewer's "keep items as read", while `itemChecks` forced `keptItemsAsRead` to false, so a moved document's check failed on a difference the reviewer had already settled. Copilot found it.

### 5.16 Leftover code

Grep the added lines for:

- debug output: `IO.inspect`, `dbg(`, `IEx.pry`, `console.log`, `console.debug`, `debugger`, `print(`, `pp `, `puts `, `fmt.Println`, `binding.pry`
- commented-out code: a comment whose body parses as code
- focused tests: `.only(`, `fit(`, `fdescribe(`, `@tag :focus`, `@moduletag :focus`
- `TODO`, `FIXME`, `XXX`, or `HACK` with no ticket reference
- a field the diff touches that every producer sets to a constant and that no consumer reads; grep for readers. Asking whether the constant is a regression is the wrong question. Worked example: a document file's `verifiedAt` was always `null` and nothing read it. Our review wrote "base was already null" and kept it, though the field looked like data a page could use.

A debug print is a Fix unless the surrounding file uses that call as its deliberate logging, which Pass 3 logging discipline then governs. Commented-out code is a Fix: delete it, since version control keeps it. A focused test is a Fix, because it silently skips the rest of the suite in CI. A `TODO` without a ticket is a Flag asking for one.

### 5.18 Readability

Three shapes, each checked by pointing at the line:

- **A name that needs its comment.** If a comment above a function or variable exists only to say what the name should have said, rename it and delete the comment.
- **A wrapper that adds nothing.** A function whose whole body calls one other function with the same arguments, used in one place, is indirection a reader has to follow for no gain. Inline it.
- **Mixed levels of abstraction.** A function that calls two high-level helpers and then does byte-level string slicing between them makes the reader switch levels mid-read. Extract the low-level part and name it.

These go through the maintainability axis of the Yes-to-any gate. A prose disposition is enough, but it must cite the line.

### 5.19 Project linter and formatter

Find the repository's own lint and format checks: the task runner (`justfile`, `Makefile`, `package.json` scripts, `mix.exs` aliases), then CI config. Run them over the touched files, for example `mix format --check-formatted`, `mix credo`, `npx eslint <files>`, or `ruff check <files>`.

A failure is a Fix. If the repository has no lint or format check, mark the angle `N/A` and say so. The artifact is the command and its output.

### 5.20 Project CLAUDE.md duties

A project's CLAUDE.md often attaches a duty to a kind of change: record why a confidence level moved, add a self-test case when the scanner changes, write down what crossed a seam. List each such rule whose trigger the diff meets, then quote the line in the diff that does what the rule asks. A triggered rule with no such line is a Fix.

Worked example: A client pull request moved report A's origin confidence from `our-hypothesis` to `observed` in `status.ts`. The project's CLAUDE.md asks for the reason in `docs/origins.md`, and the diff added none. The single-session review cited CLAUDE.md for the scanner and the seam, and never checked this rule.

### 6.1 Comment-vs-body check

For each comment in a new/changed function, read the following statements and confirm each claim is executed. If a comment says "still validated if presented", grep the body for the validation; if the body pattern-matches `_` and returns `:ok`, the comment is lying.

When a comment claims that a value stays safe somewhere else — escaped for a parser, valid for a consumer — the statements next to the comment cannot prove it. Run the value through every path that the consumer has, and show what comes out. Worked example: `dsValue` escaped `$`, `@`, and `;` for Datastar, and its comment said so. Our review wrote "comments match the code (& $ @ ; escaped ...)". Datastar's keyless `data-signals` path decoded the escapes and compiled the text again, so `$activePath` inside a string became a signal read.

When a comment claims a transform produces a shape a consumer reads, run the transform on every input shape its type admits (array, enum, object, union), not only the shapes in use today, and show what comes out. Worked example: `modelReplySchema` rewrote Zod's nullable `anyOf` into `type: [X, 'null']`, as its comment said strict structured outputs expect. Every nullable field in use was a string or a number, so the pinned schemas matched. A nullable array, enum, or object lost its `items`, values, or properties, and an outside reviewer found it.

### 6.2 Docstring contract

For each `@doc` / `@moduledoc` with behavior claims (validates X, returns Y on Z, raises on W), check the function body produces that behavior on those inputs. If the docstring lists error cases, every listed case must be reachable from the body.

### 6.3 Name-vs-body check

Function and variable names that promise action (`validate_*`, `authenticate_*`, `verify_*`, `ensure_*`, `require_*`) must perform that action. A function named `validate_signature` whose body unconditionally returns `:ok` when a specific field is present is a misnomer — flag it.

A test's title is a name that promises behavior too. For every test the diff adds or changes, read the title against its assertions. Where they disagree, one of them is wrong, and the review has to say which one, by checking the spec, before it moves on. A test whose assertions pin the opposite of its title passes every mutation check while it guards the bug.

Measured on a client pull request: a test titled as handing a value back to its original source asserted that the replacement value stayed.

### 6.4 PR/commit-message-vs-diff check

If the PR body or commit message claims the change does X ("reject wildcards", "require secret unless PKCE"), grep the diff for the enforcement. Missing enforcement with present claim is a legit finding — the bug-class the author thought they fixed is still open.

### 6.5 Distant-doc symbol drift

Angles 6.1-6.4 are scoped to claims TOUCHED in the diff. When the diff DELETES or RENAMES a model, function, route, env var, role enum value, or named concept, the distant docs (`docs/`, `README*`, `CHANGELOG*`, `ARCHITECTURE*`, design specs, RFCs, the project's `*.md` files) need to be re-checked even though they're outside the diff.

A doc that names a deleted symbol is itself a `hypothesis:` line — it asserts a reality the code no longer supports. Distant-doc claims about deleted concepts are Fix-class drift; the cost of strikethrough or paragraph rewrite is trivial, the cost of letting the spec lie to a future reader compounds across every onboarding pass.

**Discovery method:** for every `model X` decl removed, `function f` deleted, `route P` retired, `enum E` value dropped, or env var renamed in the diff, run `git grep -l "<old-name>" -- '*.md' 'docs/' 'README*'` and inspect each hit.

Sibling files that explicitly track the migration (a TODO.md, a CHANGELOG entry, a migration plan) are exempt — they're allowed to describe the historical state. Authoritative specs that still name the deleted concept are NOT exempt — they govern future work and will misdirect it.

### 6.7 Old rule still stated

Angles 6.1-6.4 read the lines the diff touched, and 6.5 reads distant docs about a deleted symbol. Neither reads an untouched line that states a rule the diff changed. Name each rule the diff changes in one sentence, such as "an account with no verified statement adds nothing to the totals". Grep every file the diff edits, and the spec pages, for the old rule's key words, and quote each hit. Grep too for each column code, field name, or identifier that stands for one of the rule's terms, because a comment often states the rule in those rather than in words. Fix each hit, or give it a line saying why it stays.

Measured (2026-10-29): a slice changed an imported item's date from "the received date, else the status date" to the later of the two. Its 6.7 grepped for "oldest" and "received", fixed three hits, and wrote DEMONSTRATED. A comment on the item's type said the same old rule in the outside system's two column codes, which contain neither word, and the whole-branch review found it. The slice's own 6.8 had quoted a spec sentence naming both codes.

Measured (2026-10-20): the outside reviewer found stale text in all four ranges it read, and our own review found none of it first. One hit was a comment in an aggregates module that still said records with no document contribute nothing, two lines below a comment the diff had updated. Others were a form hint, an analytics header, and a line in `features.md`. The same kind of finding had come from the outside reviewer on the two slices before.

### 6.8 Spec sentence vs code

6.1 lists comment blocks, and 6.7 greps for the old rule's words. Neither splits a new spec sentence into the cases it names. For each sentence the diff adds to or edits in `docs/spec/`, list every case the sentence names, and quote the code line that makes each one true. A sentence joined by "or" or "and" names two cases and needs two lines. A case with no line is a finding: either the code is missing or the sentence promises too much, and the review checks which.

Measured (2026-10-22): `workers.md` said the 15-minute pickup checks again a document "whose save keeps failing, or whose model call keeps failing". Only the first case had a line: when `savedWithRetries` gives up and throws, `runRequestedCheck` skips `finishCheckRequest`, so the request stays. A model failure returns a needs_review decision with `verification_model_failed`, the save succeeds, and `runRequestedCheck` clears the request, so nothing checks it again. Our review's 6.1 covered only the six code comment blocks that `comment_share.py` listed, and its 6.7 grepped only for the old rule's words. The outside reviewer found it on the second pass.

A sentence that names a whole class names one case for each member of that class, even with no "and" or "or" in it. Before quoting code, write down which members the code covers. If the code covers fewer, either the sentence names those members or it is a finding. Measured (2026-10-22): `design-system.md` said "Password managers offer to fill only the sign-in form", while the form components told only four named password managers to stay away. The sentence had no "and" or "or" to split on, and our review printed nothing for it under 6.1. The outside reviewer asked which manager the client's staff use, and the line was changed to name that one.

**A new member of a class reaches sentences the diff never touched.** Suppose the diff adds a kind, a source, or a state beside existing ones. Grep `docs/spec/` for each unchanged sentence that names one of its siblings, and say whether the new member follows that sentence. A sentence that leaves the answer unsaid is a finding. Measured (2026-10-22): the branch brought a second kind of record into the records the sync matches, pairs, and creates. An exclusion rule in the spec still said "every record of the first kind it matches, pairs, or creates", and the branch never edited it, so 6.8 never reached it. The spec said nothing on whether the new kind records exclusions, and the code wrote an empty list. The question came up only during the pull request's second review.

**Removing or exempting a member reaches the same sentences.** When the diff takes a member out of a class or exempts it from a rule, grep `docs/spec/` for the sentences that name the whole class or its siblings, not only for the member's own name, and say whether each sentence still holds. A sentence that names the class without the exception is a finding. Measured (2026-10-31): the operator removed the help text from one collapsed indicator. The review grepped `docs/spec/` for that indicator's own words and fixed the one sentence they found. A second document said every badge and pill on that screen region has help text, never used the indicator's name, and kept promising it. The whole-branch review caught it.

### 6.9 Spec lists additions

6.5 checks distant docs for what the diff deletes. Nothing checks them for what it adds. A spec often keeps one page that lists every thing of a kind: the schema page lists columns and constraints, the routes page lists routes, the configuration page lists settings, and the audit page lists actions. For each table, view, column, constraint, route, setting, or audit action the diff adds, find that page and quote the line that names the addition. A missing line is a finding, whether or not the diff touched that page. A new table or view needs a section of its own that lists its columns. A name in a paragraph, such as the list of migrations, does not count.

Discovery method: list the migration's `create table`, `create view`, `add column`, and `add constraint` lines, each new route path, each new key in the config schema, and each new audit action string. Then grep `docs/spec/` for each name.

Measured (2026-10-22): three migrations added two columns, a check pairing them, and a new table, and `database-schema.md` named none of them. No line of our reviews under 5.20, 6.5, or 6.8 named a migration, a column, or the schema page. The outside reviewer found it.

Measured (2026-11-05): a branch added three views, and the schema page gave only one of them a section with its columns. Our review wrote "6.9: [the schema page] and [the security page] both name the view", and another wrote "6.9 N/A: no column ... added ([the function] is listed in [the schema page]'s paragraph)". The whole-branch review found the two views missing their sections.

Comment/code drift is how `hypothesis:` creeps into production code. Treat every comment added in the diff as a testable assertion about the body below it.

### 7.2 Side-effect coverage

For operations with multiple side effects (e.g., attach payment method AND set as default), is each side effect independently asserted? A test that only checks the first side effect won't catch the second being dropped.

### 7.8 Test intent vs test effect

Read each new test's body end-to-end. Does execution actually reach the branch the test's name claims to exercise, or does an earlier guard / validation / nil check / regex / length check short-circuit before that branch runs? A test named "rejects malformed JSON" that hits a session-nil check *before* JSON parsing has never touched malformed-JSON code; a test named "rejects wrong PKCE verifier" that uses a 22-char string fails the 43-char length regex *before* reaching `secure_compare`. The test's name lies; the code path is untested.

For every test whose name describes a specific rejection or code path, trace execution setup → assertion and confirm the claimed code path fires. If earlier validations short-circuit, fix the test inputs to pass those validations so the target branch is reached.

**This angle applies to EVERY added or modified test in the diff — not just the test the reviewer's prompt points at.**

### 7.11 Tests added by the current review loop are not authoritative

When a test was WRITTEN during the current review (not pre-existing), ask: does the test VERIFY behavior the mission claims, or does it DOCUMENT the behavior the code happens to produce? A test that locks the status quo of code we just wrote can freeze a wrong design.

For every test authored in-loop, re-evaluate its assertion against the mission, not against the code. This is the dual of the anti-anchoring rule: anti-anchoring says prior dismissals don't bind; this says prior in-loop additions don't certify.

### 7.23 Excess tests

Pass 7 hunts for missing tests, and this angle hunts for the opposite. Every test the diff adds is a finding when it does any of these:

- It repeats another test. A browser test that proves what an integration test proves is a copy, and so is a unit test whose cases a sibling test already runs.
- It asserts something its title does not name, such as another step's output. One regression then fails several tests, and the title no longer says what broke.
- It matches markup instead of content: a CSS class, a utility-class regex, or a wrapper element. Assert the text a person reads. When a state shows only through styling, the fix is a stable attribute in the markup (`data-state`), not a class match.
- It pins a literal that the code derives from another source, such as a reply schema generated from a validator. Such a test only proves the generator ran.
- It folds a second input variant into a test about something else.
- It copies setup that two other tests copy too. Fold the setup into a helper.

The fix is to delete the test or the assertion, which `git-commit` folds into the commit that introduced it. Before you delete, find a home for every assertion the test held that no other test makes: move it into the neighbouring test that sets up the same state. Then mutate the production line that the moved assertion covers, and show that the test now fails.

Measured (2026-10-29): a branch added 1064 test lines for one feature. A pare-down cut 172 of them: an end-to-end spec, five tests whose assertions others already made, class-matching regexes, and assertions about one step in tests titled for another. One test had been the only one checking a streamed fragment. Its assertion moved into a neighbour that set up the same failed state, and when the route stopped passing that state, the neighbour failed. Matching step labels alone left the timeline tests unable to tell a done step from a pending one, which is the gap a `data-state` attribute closes.

### 9.9 Whole-repo copies of a changed value

This one angle leaves `test/`. For every constant, list, enum value, literal set, or piece of text a user reads (an error message, a refusal, a label) that the diff changes, run `git grep -n` from the repository root, every file type, for the value's name and for one of its unchanged members, or for a distinctive phrase of the old text. A count or figure that a document states about data the diff changes, such as a test fixture or a seed file, counts as text a user reads: grep the old figure with its noun (`12 records`), because a document often states the same count twice, once in a paragraph and once in a table. Run it from the root, not from a package directory: browser tests often sit beside the app, as `e2e/` does, and a grep inside `app/` never reaches them. A script, a config file, or a module in another language can keep its own copy, held in step by a comment or by nothing at all. No import links the two, so tracing callers never reaches it. A hit outside the diff that still holds the old value is a Fix: the diff is what made it wrong.

Measured on a client pull request: the change added a table to a TypeScript list of tables that must share one snapshot date. A Python script that seeds the same data kept an identical list under the same name, and no review grep had searched beyond `*.ts` and the spec. Copilot found the stale copy.

Measured on another: the diff changed the refusal shown when someone deletes a parent record that still holds remembered numbers. An end-to-end spec still expected the old text, and every review grep had run inside `app/`. Copilot found it.

---

### Classifying hits

For each hit, classify as:

- **Maintenance gap** — the test encodes behavior the diff INTENTIONALLY changes (e.g., a literal call-count assertion that the diff was designed to reduce). The test must be updated in the same PR or it will fail in CI. Flag with file path, line number, and the specific assertion that needs updating.
- **Hidden contract** — the test encodes a behavior the diff did not realize it was changing. This is a behavioral regression hiding behind a passing CI on the local file's tests but a red CI elsewhere. Treat as a Fix-class finding.
- **Stale reference** — comments, descriptions, or `@moduletag` strings that mention the old name/behavior. Doc/code drift; flag for the same-PR cleanup.

This pass is the structural fix for "the call-graph and test-coverage passes are scoped to whatever the orchestrator's prompt mentions." The orchestrator's prompt should NOT enumerate which test files to check — this pass discovers them mechanically from the diff's symbol set, every time, regardless of what the prompt says.

If you find no hits, this angle is `DEMONSTRATED` clean — the greps are the artifact. Record "ran greps for <symbols>, 0 hits", and only after running the actual greps. A bare "no references" without the greps having run is the satisficing this pass exists to prevent.
