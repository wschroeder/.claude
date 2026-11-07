---
name: quick-review
description: Fast single-agent code review in nine structured angle passes, each having to say where it landed, with conditional angle files the diff's own content calls in (queries, concurrency, callers, endpoints, error handling, outside formats, deploys, markup, tests, TypeScript, Elixir). Fights LLM magic-number satisficing by forcing explicit per-angle analysis. Also holds the Yes-to-any gate that every fix has to clear — security, performance, maintainability, spec compliance — and the loop that re-runs the reviews until the working tree comes back clean. Use when reviewing code changes, diffs or PRs, when asked for a quick review or a code review, and when deciding what to do with the findings afterwards.
---

# Quick Review

1. Run nine passes, each with a named-angle checklist, and give every live angle one disposition from **Demonstration discipline**: `DEMONSTRATED`, `N/A`, or `hypothesis:`. Never write "looks fine", never stop at the first few findings, and never write "NONE FOUND because <plausible sentence>".

## Orchestrator guidance

1. Run the review in the session that wrote the change, never in a subagent, because that session holds the mission, the card, and the decisions behind the diff.
2. Do not pre-select angles; the checklists below and the files the **Conditional angles** table calls for decide them. If a concern recurs across sessions, fix this skill.

## Workflow

1. **Pass 0 — Determine diff scope.** Take the cumulative `<merge-base>..HEAD` against `origin/<default_branch>` (`git fetch` first), plus the uncommitted working tree, and read it in full with no truncation and no `| head -N`. If the orchestrator passed a delta scope, such as `HEAD~1..HEAD` on an amended commit, then stop and request the cumulative one.
   **Then size it.** Measure the diff and the room this session has left; if the diff takes more than a third of that room, then read [details/stages.md](details/stages.md) now and plan the review as stages before reading any of the diff.
2. **Load skills.** Load the language skill, any project guideline skill matching the diff, and every `CLAUDE.md` from the repo root to the diff's directory, each adding named angles to its pass; read [details/skills-to-load.md](details/skills-to-load.md) now for the list and the command that finds the CLAUDE.md files.
3. **State Mission** in one sentence. Leave security to `security-review`, except input validation (4.24, in [details/outside-formats.md](details/outside-formats.md)); `writing-code` says which diffs owe one.
4. **Check the requirement.** Find the issue, card, or spec the diff serves and check the diff against each acceptance criterion, reading [details/00-requirement.md](details/00-requirement.md) now for the method.
5. **Run the 9 passes.** Before Pass 1, read every file the **Conditional angles** table calls for. In each pass, walk every live named angle and resolve it to one of the three dispositions. Write each pass to the notes file as it finishes, per "Record each pass as it finishes".
6. **Classify** each candidate through the gates in order: Screen, Yes-to-any, Destructive-recommendation, and Author-acknowledged deviation.
7. **Output** per the template, printed in the session after any Evidence block CLAUDE.md asks for, never folded into it.

### Record each pass as it finishes

1. At Pass 0, name a notes file after the tree you are about to review, and read it if an earlier session left one, then append each pass to it before starting the next, following [details/notes-file.md](details/notes-file.md), which you read now.
2. If you hand off mid-review, then name the file in the handoff.

## Diff scope

- No arg or `all`: `git fetch origin <default_branch>` then `git diff $(git merge-base HEAD origin/<default_branch>)..HEAD` + working tree
- `staged`: `git diff --staged`
- `branch`: same as no-arg (cumulative)
- `last`: `git show HEAD`
- Specific SHA: `git show <ref>`

1. Always use `origin/<default_branch>`, never the local branch ref, because local refs lag and pull in already-merged work. If the diff is empty, then stop.

## Scope and context

1. Walk the named angles live in this diff and mark the rest `N/A`, with no minimum count of attempts.
2. Treat pre-existing code on the call path as in scope, and ask whether the diff interacts with a problem; "Not my diff" is not a dismissal.
3. When the diff changes or introduces a rule, such as a spec line, a validation, a database check, or a product decision, grep code, docs, and user-facing pages for the old rule's comparison and wording, and list every hit, edited by the diff or not. Make a hit that still enforces or states the old rule a **Fix**, never a Note; `pr-feedback-task` check 2 draws the same line for review comments.
4. If a problem predates the branch and the diff does not make it worse, then report it in one line and leave it.
5. Never put code the branch adds out of scope, whatever kind a commit subject names. Before the round ends, run a test against each hypothesis about the branch's own code, or raise it as a Flag, and never carry such a hypothesis into a handoff.
6. Read surrounding code for each touched file: callers, callees, sibling functions, and related tests. Read and grep a file that a handoff or card calls out of scope, because it is out of scope only for changes.

## Demonstration discipline (anti-satisficing v2)

1. Write each disposition as an observation, not a conclusion.
2. Resolve every in-scope angle to exactly one of three states:
   - **DEMONSTRATED:** backed by something that ran in this session and printed output in the chat, such as a mutation a test caught, an adversarial input that was rejected, or a grep returning the neutralizing line; cite the artifact.
   - **N/A:** the angle is not live in this diff, with one line of why.
   - **`hypothesis:`:** a suspected problem you could not produce the artifact for, flagged and labeled.
3. Never use "carried" from an earlier session as a disposition: a whole-branch review checks each angle again against HEAD. Cite an earlier session's artifact only when you name it and show the code it covered has not changed since, and only for the functions it names.
4. Run one mutation per criterion clause and one per constraint of each new or changed function, as [details/proof-shapes.md](details/proof-shapes.md) "Assertion strength" lists them, because a mutation proves only what it broke.

### The demonstrate-line — what owes an artifact even on a CLEAN bill

1. Demonstrate every Fix and every Flag.
2. On a clean bill, demonstrate with the required artifact these three classes when in scope, and treat bare prose as invalid for them:
   1. Assertion strength / test coverage
   2. Atomicity / TOCTOU
   3. Error-return shape (raise vs `{:error, _}`)
3. Give every other angle a prose disposition that cites the line, never a story. Leave injection and authorization proofs to `security-review`.

### Proof-shape catalog

1. Read [details/proof-shapes.md](details/proof-shapes.md) now, before you mark any of the three classes `DEMONSTRATED`; it lists the artifact that licenses each one's clean bill.
2. Derive the Fix, Flag, or Note label from those artifacts, and never let it stand in for them.

## Conditional angles

1. Before Pass 1, read the diff against each row below and read every file whose condition it meets, now.
2. Walk each angle from a file in the pass its number names, and print its line there.

| If the diff ... | Read now, before Pass 1 |
|-----------------|-------------------------|
| adds or changes a query, a table, a view, or a column, or carries a value from one function to another through a new field | [details/queries.md](details/queries.md) |
| has two paths that can write the same rows, takes a lock, retries, or runs a job that can run twice or overlap itself | [details/concurrency.md](details/concurrency.md) |
| adds a function, or changes one's arguments, return value, or error shape | [details/callers.md](details/callers.md) |
| adds or changes a route, an endpoint, or a request handler, or mints or consumes a credential | [details/endpoints.md](details/endpoints.md) |
| adds or changes a catch, a rescue, an error return, a fallback, or a warn or error log | [details/error-handling.md](details/error-handling.md) |
| parses a format from outside (a file, a model's reply, a third-party payload) or takes input from outside the process | [details/outside-formats.md](details/outside-formats.md) |
| adds a migration, changes deploy or job configuration, or changes a value a cache or a scheduled job reads | [details/deploy.md](details/deploy.md) |
| changes markup, a browser event handler, or text a person reads on a screen | [details/markup.md](details/markup.md) |
| adds, changes, or deletes a test | [details/tests.md](details/tests.md) |
| touches a `.ts`, `.tsx`, `.js`, or `.jsx` file | [details/language-typescript.md](details/language-typescript.md) |
| touches a `.ex` or `.exs` file | [details/language-elixir.md](details/language-elixir.md) |

3. In the Checklist, give each file you did not read one line naming the condition and why the diff does not meet it.

## Pass 1 — Call-graph and seam analysis

```
  1.2   Query consistency                grep every other query of the same table
                                          for the same entity; compare where clauses,
                                          and account for a broader lookup
                                          every sameness query (dedup, unique index,
                                          merge, lookup) side by side; each compares one
                                          expression and leaves out the same rows
                                          (superseded, hidden, deleted); a match that
                                          picks one of several candidates: build two,
                                          say what the loser's subject gets
  1.4   Handoff completeness             grep every unchanged reader of the new table
                                          or state, a new value in an old column
                                          or audit action too, and drive each one; what
                                          it shows from each new state is true;
                                          readers include existence checks, delete
                                          guards, and re-resolvers run when a page opens
                                          a write that clears a marker, releases a
                                          claim, or changes where a value came from:
                                          name the row's state afterwards and check the
                                          value and its label (a source badge) against
                                          the spec
                                          a new value in an old column: grep the
                                          table, not the value; each sum, count,
                                          list, picker, merge target, and write target
                                          shows or offers that state's row in or out,
                                          as the spec says; "not a total" is no N/A
                                          a state that leaves the totals: name
                                          each thing a user put on the row and
                                          where it counts now; "stays on the row"
                                          is a finding unless the operator chose it
                                          proof: drive each new state through the
                                          real path, quote the rows, audit events,
                                          and rendered text it left; a code reading
                                          is not proof; in each state, submit every
                                          choice each control offers and quote the
                                          server's answer; a refusal is a finding
  1.10  Behavioral regression            every touched function with callers:
                                          `git show <base>:<path>`, compare the old
                                          return and side effects with the new; a
                                          difference the author did not state is a
                                          regression, even where the new tests pass
```

## Pass 2 — Adversarial

1. For each new path, construct an input or state that crashes it, such as concurrent execution, partial failure, stale data, or an unexpected NULL, and name the database or outside-API state that makes it crash instead of returning an error.

```
  2.2   Semantic completeness            name promises X, body delivers part of X;
                                          judge the body against every input its
                                          name promises, not today's call sites,
                                          which prove only that nothing is open now
  2.18  Cross-writer race                each write path: list the tables it writes
                                          and the FK parents; grep every OTHER writer,
                                          deleter, or merger of those rows, inside the
                                          diff and out, deferred ones too (a job that
                                          resumes from what it captured, a model call
                                          in flight while a person edits); name the
                                          lock, constraint, or transaction ordering
                                          each pair; nothing between them → finding;
                                          a sibling that locks where this path does
                                          not → finding; one test per pair
                                          proof: hold the other writer open (pg_sleep),
                                          run this one, show the outcome
                                          reading the SQL, "one statement", or a
                                          transaction boundary is not proof
                                          two paths taking the same two locks: quote
                                          each path's order side by side, with the row
                                          locks UPDATE/DELETE take, FK key-shares, and
                                          the table lock each needs (FOR UPDATE takes
                                          ROW SHARE, the first write ROW EXCLUSIVE);
                                          if either path holds a table lock, run the pair;
                                          a shared lock helper is not a shared order:
                                          quote the ids each caller passes it, in the
                                          order it passes them; rows locked in list or
                                          name order, or from two pages two users can
                                          have open → run the pair
                                          a suspected deadlock is run, never dropped
                                          as unmeasured
                                          a decision ruling out one race (no two runs
                                          at once) covers only the writers it names;
                                          every other pair of lock-takers still gets
                                          the order check, never "N/A per decision"
                                          after a path deletes, combines, or leaves
                                          duplicates of rows, run every other writer
                                          once more afterwards and show it holds
                                          a child insert against a parent another
                                          writer deletes or merges: lock the parent
                                          first, or the insert fails on the FK (23503)
                                          proofs assert the promised invariant ("≤ 30
                                          rows"), not "no errors", at replicas × pool
                                          size copies at once
  2.20  Checker evasion                  a linter, scanner, or allowlist the diff
                                          adds or changes: one input per way round
                                          it (case, computed key, spread, look-alike,
                                          a type with no declaration site, a value
                                          stored first), each run through the checker
                                          ways that share one thing the checker trusts
                                          (a type, a flag, a declaration site): name it,
                                          run the checker with that trust removed on
                                          the fixtures and the real codebase; a reason
                                          to keep the trust stays a hypothesis until
                                          that run shows the false alarm
```

## Pass 3 — Error handling

1. Take every Pass 3 angle from `error-handling.md` and the language files; if you read neither, then print one line saying why.

## Pass 4 — Data correctness

1. For each field the new code reads, grep the file for every other read of it, and flag any read that guards against a missing value differently.

```
  4.1   Empty-value semantics            empty means "nothing requested",
                                          "everything", or "reject": say which the
                                          code does and which the product means;
                                          blank is null, '', only spaces, and what
                                          each transform leaves; run each through every
                                          transform, then the guard; a promised rule
                                          holds even where no input reaches it today;
                                          a filter that can drop every row an
                                          aggregate reads: sum is null, not 0; drive
                                          that case and quote what each reader of the
                                          aggregate does with the null
  4.26  Outside-format variants          each construct a parser reads: open the
                                          format's spec at that element, list its
                                          siblings and alternatives; every variant is
                                          read or refused, never skipped
                                          proof: drive each variant through every
                                          path that reads the same field (create,
                                          match, pair); a path that reads it
                                          another way is the finding
```

## Pass 5 — Conventions

```
  5.5   Private-helper duplication       deletion test for near-identical helpers:
                                          bodies that differ only in name collapse
                                          unless they differ meaningfully today;
                                          the same edit made in several copies, or
                                          one shape in two notations (JSON schema
                                          and Zod) → derive one, or a drift test
                                          with one mutation per branch; count
                                          copies in every file the branch adds,
                                          earlier migrations included;
                                          a shared helper serving a new kind runs
                                          that kind's own reader, parser, and
                                          default: name each, or it is a finding;
                                          one value under two names (a test's
                                          literal copying a constant the diff
                                          defines) → import it, and name the one
                                          place that spells it out on purpose
  5.7   Same-module sibling consistency  asymmetric guards/clauses/fallbacks;
                                          a match settles only this angle, never a
                                          Pass 1, 2, or 4 angle, and a flaw both
                                          share is a finding against both;
                                          two helpers giving one verdict both honor
                                          a reviewer's saved choice;
                                          a rule applied to one kind of a family:
                                          name each sibling kind, shown in or out
                                          by a test or a spec line; two siblings
                                          that use different bounds or clauses
                                          stay a candidate until you quote the
                                          spec line or test saying which is
                                          right, and "behaves correctly" cites it
  5.16  Leftover code                    grep added lines for debug output, code
                                          in comments, focused tests (.only, fit,
                                          @tag :focus), and TODO/FIXME/XXX/HACK
                                          without a ticket; each is a Fix, a TODO
                                          a Flag asking for a ticket; a field every
                                          producer sets to a constant and no
                                          consumer reads (grep for readers)
  5.18  Readability                      name that needs a comment; wrapper that
                                          adds nothing; mixed abstraction levels;
                                          cite the line
  5.19  Project linter and formatter     run the repo's own check on touched files
  5.20  Project CLAUDE.md duties         each rule there whose trigger the diff
                                          meets: quote where the diff obeys it;
                                          no line → Fix
```

## Pass 6 — Doc/code coherence

1. For every comment, docstring, `@moduledoc`, `@doc`, or prose claim added or touched in the diff, verify the code delivers on it.

```
  6.1   Comment-vs-body check            statements following comment actually fire;
                                          a claim that a value stays safe elsewhere
                                          → run it through every path that place has;
                                          a claim that a transform yields a shape →
                                          run every input shape its type admits
                                          proof: split each added or changed comment
                                          or description into the claims it makes,
                                          and quote beside each claim the line that
                                          makes it true, including when a card
                                          dictated the wording; a claim with no
                                          line → finding
  6.2   Docstring contract               every listed error case reachable
  6.3   Name-vs-body check               validate_*/verify_*/ensure_* perform action;
                                          each test's title matches its assertions
                                          proof: quote each added, renamed, or
                                          changed test's title beside the assertion
                                          line proving each thing it names, and each
                                          of its assertions beside the title words
                                          it proves; a thing named with no line, or
                                          a line with no title words → finding
  6.4   PR/commit-message-vs-diff check  claimed enforcement is present
  6.5   Distant-doc symbol drift         deleted symbol still named in distant docs/
  6.6   Deletion test, every block       each listed comment block: keep plus its why, or delete
  6.7   Old rule still stated            each rule the diff changes: grep from the
                                          repository root, all files, for the old
                                          rule's words and for each code, field, or
                                          identifier the code names its terms by;
                                          grep each identifier on its own, with
                                          no pattern around it, and read every hit;
                                          each hit fixed or given a reason
                                          proof: state each changed rule in one
                                          sentence, then quote each hit and what
                                          became of it; no rule named → finding
  6.8   Spec sentence vs code            each spec sentence the diff adds or edits,
                                          and each existing spec sentence, on any
                                          spec page, governing a path the diff
                                          changes; a word diff that shows only a
                                          rename does not exempt a sentence whose
                                          code path changed (a retry or resume
                                          that reuses a stored result: quote the step
                                          on what a retry reads again):
                                          split it into the cases it names; a class
                                          names one case per member
                                          proof: quote one code line per case that
                                          makes that case true; a case with no
                                          line → finding
                                          then the other way: each condition the code
                                          applies to that case (a filter, a guard, an
                                          early return): quote the spec words that
                                          state it; no words → finding
                                          a member added to, removed from, or exempted
                                          from a class (a kind, a source, a state):
                                          grep docs/spec for each unchanged sentence
                                          naming the class or a sibling; say whether
                                          it still holds; left unsaid → finding
  6.9   Spec lists additions             each table, view, column, constraint, route,
                                          setting, or audit action the diff adds
                                          (list the migration's create and add lines,
                                          new routes, config keys, audit strings, and
                                          grep docs/spec for each): quote its line on
                                          the spec page that lists things of that
                                          kind; a new table or view needs its own
                                          section of columns, and a name in a
                                          paragraph does not count; no line → finding
```

2. For angle 6.8, list every condition the diff's code applies in a path a spec sentence governs, including a fix this review just made, and give each its own line quoting the code line and the spec words that state it, or "no words → finding".
3. For 6.8, also list every step, job, or function whose order or behavior the diff changes, grep the spec pages for its name and what it does, print each grep with its hit count, and give every sentence found its own line saying whether it still holds on every run that reaches the step, or "contradicted → finding"; one example never stands in for the whole diff.
4. For 6.6, run `python3 ~/.claude/skills/writing-code/scripts/comment_share.py` over Pass 0's scope (with no `--base` it measures from the merge base, uncommitted and untracked work included), paste its per-file lines, and read a file over 10% twice.
5. Give every block it lists "keep" with the non-obvious why it explains, or "delete", and do not call the bill clean until each has one; `writing-code` "Measure before declaring done" owns the rule.

## Pass 7 — Test coverage

1. Identify behaviors lacking test coverage, and read the full test diff before claiming a gap, finishing any truncated read first.
2. Require tests to assert outcomes, not implementation; an assertion on a mock's call history proves only that a path ran. Give a change to how a screen is put together a demo, not a coverage finding.
3. If the operator asked for few tests and a test of what a write path stores is missing, then file a Flag quoting the operator's words, never a Note.
4. For every finding in passes 1-5, ask whether a test would catch it; if none would, then the missing test is the finding.

```
  7.2   Side-effect coverage             each side effect independently asserted
  7.8   Test intent vs test effect       every added or changed test: earlier guards
                                          short-circuit the target branch; trace setup
                                          to assertion, and fix the inputs so the
                                          branch the title names is reached
  7.11  Tests added by current loop      each test written in this review: its
                                          assertion checked against the mission, not
                                          the code; don't lock status quo
  7.23  Excess tests                     a copy of another test's cases, an
                                          assertion outside the title, a CSS class
                                          in any kind of test, whatever the
                                          project's selector rule names, a pinned
                                          derived literal, a second variant, setup
                                          copied a third time (→ a helper)
                                          proof: per deletion, quote where each
                                          assertion now lives and a mutation it fails;
                                          per added or changed test, quote one
                                          assertion that no other test in its file
                                          makes; none → finding
```

## Pass 8 — Second-order

1. Take 8.1-8.3 from `deploy.md` and 8.4 from `concurrency.md`; if you read neither, then print one line saying why.

## Pass 9 — Test-suite reach

1. For every public function or module the diff adds, renames, deletes, or changes the behavior of, `grep -rn` its bare name across the test tree, and look hardest at hits in test files the diff did not modify.

```
  9.9   Whole-repo copies                every changed constant, list, enum, text
                                          a user reads, or count a document
                                          states: `git grep -n` from the repository
                                          root, never a package directory, all
                                          files, every language, for its name and
                                          one unchanged member; a count with its
                                          noun ("12 records"); a hit outside the
                                          diff that holds the old value → Fix
```

2. Classify each hit:
   - **Maintenance gap:** a test encoding behavior the diff changes on purpose; Flag it with its file, line, and assertion.
   - **Hidden contract:** behavior the diff changed without meaning to; a Fix.
   - **Stale reference:** text still naming the old name or behavior; a Fix when it still states a rule the diff changed, per the scope rule.
3. If the greps return no hits, then print the greps and "0 hits".
4. Take the Elixir mock and tracer greps (9.2-9.7) from `language-elixir.md`.

## Classify (internal — before any output)

1. Enumerate every candidate finding internally, and walk each through these gates in order.

### Screen (silent drops)

1. Is this actually a problem, or did I realize mid-write it's fine? → **Drop silently.** Keep a measured violation of a stated contract as a **Fix** even while its cause is unproven; never drop it or relabel it a hypothesis.
2. Is this an effect the requirement check confirmed the requirement asks for? → **Drop silently.** Keep an effect that only the PR text or the Mission describes in the Screen like any other candidate.
3. Is this hypothetical ("if someone later adds X...")? → **Drop silently.**
4. Positive observation ("good pattern", "properly handles X")? → **Drop silently.**
5. Does the developer need to act on or be aware of this for THIS change? → **Keep.**
6. DESTRUCTIVE recommendation on user-authored data? → Apply Destructive gate (below) before keeping. Default action is DROP.

### Yes-to-any gate (recommendation bar for Fix/Flag)

1. For each surviving candidate that would be Fix or Flag, ask whether applying the fix would improve ANY of:

- **Security** — attack surface, authn/authz, data integrity, info leak, audit trail
- **Performance** — hot-path latency, memory, allocation pressure, query plans
- **Maintainability** — symmetry with siblings, reduced special-casing, clearer invariants, less hidden coupling
- **Spec compliance** — RFC/standard alignment, cross-system contract adherence, accessibility standards (WAI-ARIA roles and the keyboard and focus contracts they imply)

2. Never make a missing test for a constant a finding, symmetry with siblings included: `spec-task`, "If a requirement concerns a constant of any kind".
3. If the answer is yes on at least one axis, then recommend the fix. Define the axes here only; `writing-code`, `pr-respond-task`, and `pr-feedback-task` point here.

### Destructive-recommendation gate (irreversibility ratchet)

1. If a finding proposes an irreversible operation on user-authored data (DELETE, UPDATE, DROP, TRUNCATE, a schema rewrite, a cleansing migration), then read [details/destructive-gate.md](details/destructive-gate.md) now.
2. Make such a finding name the specific invariant the existing rows violate and cite rows that violate it, or else drop the recommendation or downgrade it to a Flag; a new filter or authorization predicate is never such an invariant.

### Author-acknowledged deviation is not exempt

1. Treat an acknowledgment in a moduledoc, comment, commit message, PR body, this review's Notes, or the session's handoff as the trigger to run the Yes-to-any gate on the deviation, never a reason to skip it, including a handoff's "Decision" line marked not to relitigate, which closes the product choice but not the review of the code.
2. If the decision copies a shared helper rather than calling it, then ask whether the helper could take a parameter covering the difference, and name the helper either way.
3. Keep a finding that a later card will fix as a Fix or a Flag in this commit, never a Note.
4. Read [details/author-acknowledged.md](details/author-acknowledged.md) now for the acknowledgment phrases to grep for.

### Classifications

1. Give each surviving candidate one of three:
   - **Fix:** a bug; include the fix.
   - **Flag:** needs human judgment. Run a suspected deadlock's pair (2.18) before classifying it, never leaving it "traced, not run".
   - **Note:** something to know to ship safely that is neither a bug nor a judgment call; drop it if you cannot say what the developer should do, and make a Note about lost work or data a Fix or a Flag.
2. If the operator accepts a Flag as it stands, then write their answer, quoted and dated, into the project's design document beside the requirement it narrows, in the same turn, per [details/00-requirement.md](details/00-requirement.md).

## Output

1. Print this block in the session, after any Evidence block CLAUDE.md asks for.
2. Fill the Checklist and Files sections in full; a count, or a line saying the review found nothing, does not replace them.

```
# Quick Review

**Mission:** <one sentence>
**Requirement:** <source, or "none found"> — <each criterion: met / partly met / not met; partly met and not met are each a Flag>
**Scope:** <N files, M lines, against <merge-base>>

## Fixes
## Flags
## Notes (action-required only)

## Demonstrations (the artifacts behind the clean bills)
  One line per demonstrate-line class that was in scope: <class>: <what ran> → <result>
  e.g. assertion-strength: mutated session.ex:88 `>=` -> `>`, the
       expiry clause; auth_controller_test.exs still passed → FINDING
  An in-scope class with no artifact here is an incomplete review, not a clean one.

## Checklist
  Every pass, in order. Each angle in a pass the diff touches gets one line: <number> <name>: <disposition>, <what you saw>, with N/A and its reason where the angle is not live.
  A pass with no live angle gets one line saying why.
  e.g. Pass 2 — Adversarial
       2.3 self-race: DEMONSTRATED, two concurrent saves left one row
       2.5 replay: N/A, the route takes no client-supplied id
  e.g. Pass 3 — Error handling: N/A, no error path in the diff
  e.g. Pass 6 — Doc coherence
       6.8 import.sh:28 "No files to read in $dir" (both folders): spec says
           "cannot read the files in the source folder": target folder
           has no words → finding
       6.8 import.sh:64 "$undo is missing": no words → finding

## Files
  Every file in scope, marked read or skipped; a skip names its reason in a few words.
```

3. Carry the Requirement line and the Checklist into the handoff, and point a card note or a handoff at the printed block by the time it printed, never replacing it.
4. Keep the block out of commit messages, per `git-commit`.

## Re-review and the fix loop

1. Run this loop as the caller; the passes above are one iteration.
2. For each finding, name what executes the code it is about and when that last happened, such as the caller, the recipe, the test, or the request path. If nothing will reach that code again, then record the finding where the next reader will look, say in one line why it is not being fixed, and move on.
3. Filter what is left through the Yes-to-any gate, and apply each fix that improves any axis without asking.
4. Re-run `quick-review` against the updated tree, and `security-review` when `writing-code`'s list says the diff needs one, until a pass against the current tree surfaces no finding that clears the gate; only then decide the commit. Do not ask the user between iterations unless a design question cannot be settled from existing context.
5. After any fix, run another full round: all nine passes over the whole diff, plus targeted re-checks for the fix; a prior round's dismissals do not bind amended code.
6. In a staged review, re-run each stage whose files changed and the cross-group stage, as [details/stages.md](details/stages.md) "After a fix" says.
7. Write each re-round line with the command that re-read the diff after the fix and the time it ran: "Re-round after the fix to the date parser: `git diff 9f8e7d6 -- .` at 14:09Z, nothing new." If no command re-read the diff after the fix, then run it, or report one round and name the fix as unreviewed.
8. Read [details/review-fix-loop.md](details/review-fix-loop.md) now, before deciding the loop is finished, for its stopping rules, targeted re-checks, and anti-anchoring.
