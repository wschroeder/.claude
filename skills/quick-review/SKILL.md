---
name: quick-review
description: Fast single-agent code review in nine structured angle passes, each having to say where it landed, with conditional angle files the diff's own content calls in (queries, concurrency, callers, endpoints, error handling, outside formats, deploys, markup, tests, TypeScript, Elixir). Fights LLM magic-number satisficing by forcing explicit per-angle analysis. Also holds the Yes-to-any gate that every fix has to clear — security, performance, maintainability, spec compliance — and the loop that re-runs the reviews until the working tree comes back clean. Use when reviewing code changes, diffs or PRs, when asked for a quick review or a code review, and when deciding what to do with the findings afterwards.
---

# Quick Review

Structured 9-pass code review. Each pass has a named-angle CHECKLIST. The checklist is the forcing function — every named angle MUST receive an explicit disposition: `DEMONSTRATED` (artifact shown), `N/A` (one line why), or `hypothesis:` (suspected, couldn't prove). See **Demonstration discipline** below — a bare "looks fine" is not a disposition. Stopping at the first N findings is one failure this skill prevents; "NONE FOUND because <plausible sentence>" is the other, and the demonstration discipline is what closes it.

## Orchestrator guidance

Run the review in the session that wrote the change, not in a subagent. That session holds the mission, the card, and the decisions behind the diff, and it needs them to tell a real finding from a false alarm. Do NOT pre-select which angles to check — the checklists below, and the files the trigger table in **Conditional angles** calls for, are the source of truth. If a concern recurs across sessions, fix the skill instead.

## Workflow

1. **Pass 0 — Determine diff scope.** Cumulative `<merge-base>..HEAD` against `origin/<default_branch>` (`git fetch` first), plus uncommitted working tree. Full read; no truncation, no `| head -N`. If the orchestrator passed a delta scope (e.g., `HEAD~1..HEAD` on an amended commit), STOP and request cumulative.
   **Then size it.** Measure the diff and the room this session has left. If the diff takes more than a third of that room, plan the review as stages before reading any of it: [details/stages.md](details/stages.md).
2. **Load skills.** The language skill, any project guideline skill that matches the diff, and every `CLAUDE.md` from repo root to the diff's directory. Each adds named angles to its pass. The list and the command that finds the CLAUDE.md files: [details/skills-to-load.md](details/skills-to-load.md).
3. **State Mission** in one sentence. Security is `security-review`'s, except input validation (4.24, in [details/outside-formats.md](details/outside-formats.md)): `writing-code` says which diffs owe one.
4. **Check the requirement.** Find the issue, card, or spec the diff serves and check the diff against each of its acceptance criteria. Method: [details/00-requirement.md](details/00-requirement.md).
5. **Run the 9 passes.** For each pass: walk every named angle below that is live in this diff. For each, resolve to one of the three dispositions in **Demonstration discipline** below — `DEMONSTRATED` (artifact shown), `N/A` (one line why), or `hypothesis:` (suspected, couldn't prove, flagged anyway). There is no "read it and it's fine" disposition. Before Pass 1, read every file the table in **Conditional angles** calls for. Write each pass to the notes file as it finishes; see "Record each pass as it finishes".
6. **Classify** each candidate through the gates (Screen → Yes-to-any → Destructive-recommendation → Author-acknowledged deviation).
7. **Output** per template, printed in the session after any Evidence block CLAUDE.md asks for, never folded into it.

### Record each pass as it finishes

At Pass 0, name a notes file after the tree you are about to review, read it if a session before you left one, and append each pass to it before you start the next. The commands and the rules: [details/notes-file.md](details/notes-file.md). When you hand off mid-review, name the file in the handoff.

## Diff scope

- No arg or `all`: `git fetch origin <default_branch>` then `git diff $(git merge-base HEAD origin/<default_branch>)..HEAD` + working tree
- `staged`: `git diff --staged`
- `branch`: same as no-arg (cumulative)
- `last`: `git show HEAD`
- Specific SHA: `git show <ref>`

Always use `origin/<default_branch>`, never the local branch ref: local refs lag and silently expand scope with already-merged work. Empty diff → stop.

## Scope and context

**No angle count.** Walk the named angles that are live in this diff and mark the rest `N/A`. There is no minimum number of attempts: the demonstration discipline below, not a count, is what stops a review at its first finding.

**Scope rule.** Pre-existing code on the call path is in scope. "Not my diff" is not a dismissal. Question: does this diff INTERACT with a problem?

- **When the diff changes or introduces a rule, every path that must obey it is in scope.** A rule is anything the code is held to: a spec line, a validation, a database check, a product decision. Grep code, docs, and user-facing pages for the old rule's shape — its comparison, its wording — and list every hit, edited by the diff or not. A hit that still enforces or states the old rule is a **Fix**, never a Note: it predates the branch, but the branch is what made it wrong. `pr-feedback-task` check 2 draws the same line for review comments.
- **Otherwise, a problem that predates the branch and that the diff does not make worse is not the branch's to fix:** report it in one line and leave it.
- **Code the branch adds is never out of scope.** A commit subject that names one kind does not narrow the review to that kind. Before the round ends, run a test against each hypothesis about the branch's own code, or raise it as a Flag. A hypothesis about the branch's own code never carries into a handoff. See [references/measurements.md](references/measurements.md).

Why: [details/why-the-gates.md](details/why-the-gates.md), "Why a changed rule pulls in code the diff never touched".

**Context.** Read surrounding code for each touched file, not just the diff. Identify callers, callees, sibling functions, related tests. A file that a handoff or a card calls out of scope is out of scope for changes, never for reading: the review still greps it.

---

## Demonstration discipline (anti-satisficing v2)

A disposition is an **observation, not a conclusion**. Why that is the rule, and what a
narrated absence costs, is in [details/why-the-gates.md](details/why-the-gates.md).

Every in-scope angle resolves to exactly one of three states. There is no fourth: "carried" from an earlier session is not a disposition, so a whole-branch review checks each angle again against HEAD and cites an earlier session's artifact only when it names that artifact and shows the code it covered has not changed since. The artifact covers only the functions it names: a file unchanged since an earlier round is not covered where that round's mutations never touched a function in it.

- **DEMONSTRATED** — backed by something that RAN in this session and produced output in the chat: a mutation this review ran and a test caught, an adversarial input that got rejected, a grep that returned the neutralizing line. Cite the artifact. A mutation proves only the clause or constraint it broke, so the review runs one per criterion clause and one per constraint of each new or changed function, as [details/proof-shapes.md](details/proof-shapes.md) "Assertion strength" lists them.
- **N/A** — the angle is not live in this diff. One line of why (`no SQL here`, `no auth surface touched`).
- **`hypothesis:`** — you suspect a problem but could not produce the artifact. Flag it anyway, labeled. Honest, not hidden.

"I read it and it looks fine" is not a disposition. It is the satisficing slot. Delete it.

### The demonstrate-line — what owes an artifact even on a CLEAN bill

Demonstrating every angle bankrupts the review, so the burden is tiered by blast radius:

- **Every Fix and every Flag always demonstrates.** Assert a bug → prove it runs or breaks. Findings are few; this is cheap.
- **A clean bill demonstrates only for these three classes** when in scope. For them, `DEMONSTRATED` REQUIRES the artifact below; bare prose is an invalid disposition:
  1. Assertion strength / test coverage
  2. Atomicity / TOCTOU
  3. Error-return shape (raise vs `{:error, _}`)
- **All other angles** may use a prose disposition — but it must be an *observation that cites the line*, never a story. (This boundary is the tunable knob. The three above are the floor; injection and authorization proofs are `security-review`'s.)

### Proof-shape catalog

Each of the three classes above has one artifact that licenses its clean bill, listed in [details/proof-shapes.md](details/proof-shapes.md). Read it before you mark any of the three `DEMONSTRATED`.

The deliverable of the review IS these artifacts. The Fix/Flag/Note label is a summary *derived* from them, never a substitute for them.

---

## Conditional angles

The passes below hold the angles that apply to every diff. The rest live in files, one per kind of change. Before Pass 1, read the diff against each row and read every file whose condition it meets, now. Each angle in a file keeps its pass number: walk it in that pass and print its line there.

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

In the Checklist, give each file you did not read one line naming the condition and why the diff does not meet it.

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

Construct an input or a state that crashes the code: concurrent execution, partial failure, stale data, an unexpected NULL. For each new path, name the database or outside-API state that makes it crash instead of returning an error.

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

Every Pass 3 angle is conditional: `error-handling.md`, and the language files for logging discipline. With neither read, print one line saying why.

## Pass 4 — Data correctness

For each field the new code reads, grep the file for every other read of the same field, and flag any read that guards against a missing value differently.

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

For every comment, docstring, `@moduledoc`, `@doc`, or prose claim added or touched in the diff: verify the code delivers on it.

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

**Angle 6.8 owes one line per item.** List every condition the diff's code applies in a path a spec sentence governs: each filter, guard, early return, and exit, the fix this review just made included. Each one gets its own line quoting the code line and the spec words that state it, or "no words → finding". Then list every step, job, or function whose order or behavior the diff changes, grep the project's spec pages for its name and for what it does, and print each grep with its hit count. Every sentence the grep finds gets its own line quoting it and saying whether it still holds on every run that reaches the step, or "contradicted → finding"; a sentence stating the old order is the usual miss. One example standing in for the whole diff is not a disposition.

For 6.6, run `python3 ~/.claude/skills/writing-code/scripts/comment_share.py` over Pass 0's scope; with no `--base` it already measures from the merge base, uncommitted and untracked work included. Paste its per-file lines. Give every block it lists "keep" with the non-obvious why it explains, or "delete", and read a file over 10% twice. The bill is not clean while any block lacks a disposition. `writing-code` "Measure before declaring done" owns the rule.

## Pass 7 — Test coverage

Tests over eyeballing. The review's primary job is to identify behaviors lacking test coverage. **You MUST have read the FULL test diff before claiming a coverage gap.** Tests must assert outcomes, not implementation. A change to how a screen is put together is not a coverage gap: it gets a demo. An operator's request for few tests never turns a missing test of what a write path stores into a Note: file a Flag that quotes the operator's own words. If the test diff came back truncated, read the rest before this pass. For every finding in passes 1-5, ask whether a test would catch it: if none would, the missing test is the finding. An assertion on a mock's call history proves a path ran, not that it worked.

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

Every Pass 8 angle is conditional: `deploy.md` holds 8.1-8.3 and `concurrency.md` holds 8.4. With neither read, print one line saying why.

## Pass 9 — Test-suite reach

For every public function or module the diff adds, renames, deletes, or changes the behavior of, `grep -rn` its bare name across the test tree. A hit in a test file the diff did not modify is the likeliest finding.

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

Classify each hit as one of three. A **maintenance gap** is a test encoding behavior the diff changes on purpose: Flag it with its file, line, and assertion. A **hidden contract** is behavior the diff changed without meaning to: a Fix. A **stale reference** is text still naming the old name or behavior: a Fix when it still states a rule the diff changed, as the scope rule at the top of this skill says, such as a runbook step that still sets up credentials for a deployment the diff removed. If the greps return no hits, print the greps and "0 hits": the grep is the artifact. The Elixir mock and tracer greps (9.2-9.7) are in `language-elixir.md`.

Why each body angle reads as it does, with the misses behind it: [references/worked-examples.md](references/worked-examples.md). Nobody needs to read it to run the review.

---

## Classify (internal — before any output)

Enumerate every candidate finding internally. For each, walk these gates IN ORDER.

### Screen (silent drops)

1. Is this actually a problem, or did I realize mid-write it's fine? → **Drop silently.** A measured violation of a stated contract (34 rows where the spec keeps 30) is a **Fix** even while its cause is unproven; never drop it or relabel it a hypothesis.
2. Is this an effect the requirement check confirmed the requirement asks for? → **Drop silently.** An effect that only the PR text or the Mission describes is not dropped on intent grounds; it continues through the Screen like any other candidate.
3. Is this hypothetical ("if someone later adds X...")? → **Drop silently.** Review what exists, not what might.
4. Positive observation ("good pattern", "properly handles X")? → **Drop silently.** The job is finding problems, not complimenting code.
5. Does the developer need to act on or be aware of this for THIS change? → **Keep.**
6. DESTRUCTIVE recommendation on user-authored data? → Apply Destructive gate (below) before keeping. Default action is DROP.

### Yes-to-any gate (recommendation bar for Fix/Flag)

For each surviving candidate that would be Fix or Flag, ask whether applying the fix would improve ANY of:

- **Security** — attack surface, authn/authz, data integrity, info leak, audit trail
- **Performance** — hot-path latency, memory, allocation pressure, query plans
- **Maintainability** — symmetry with siblings, reduced special-casing, clearer invariants, less hidden coupling
- **Spec compliance** — RFC/standard alignment, cross-system contract adherence, accessibility standards (WAI-ARIA roles and the keyboard and focus contracts they imply)

A missing test of any kind for a constant is never a finding, symmetry with siblings included, because a constant gets no test: `spec-task`, "If a requirement concerns a constant of any kind".

If YES to at least one, recommend the fix. The bar is "positive signal on any axis," not "positive on all axes." This is the anti-waffling rule — it prevents the "technically correct but maybe not worth it" drift. A 5-line fix that measurably improves one axis beats a 0-line "ship as-is" that improves none. This section is the only place the axes are defined; `writing-code`, `pr-respond-task` and `pr-feedback-task` point here rather than restating them.

### Destructive-recommendation gate (irreversibility ratchet)

A finding that proposes an irreversible operation on user-authored data (DELETE, UPDATE, DROP, TRUNCATE, a schema rewrite, a cleansing migration) must name the specific invariant the existing rows violate and cite rows that violate it. A new filter or authorization predicate is never such an invariant. If the finding cannot do both, drop the recommendation or downgrade it to a Flag. Read [details/destructive-gate.md](details/destructive-gate.md) whenever a finding proposes one.

### Author-acknowledged deviation is not exempt

An acknowledgment in a moduledoc, comment, commit message, PR body, this review's own Notes, or the session's handoff is the TRIGGER to run the Yes-to-any gate against the deviation, never a reason to skip it. A handoff's "Decision" line counts too, even one marked as not to relitigate: that tells the next session not to reopen the product choice, not this review to pass the code. When the decision is to copy a shared helper rather than call it, ask whether the helper could take a parameter that covers the difference, and name the helper either way. A finding that a later card will fix is still a Fix or a Flag in this commit, never a Note. The acknowledgment phrases to grep for, and why the gate has no "author already knew" exemption: [details/author-acknowledged.md](details/author-acknowledged.md).

### Classifications

Surviving candidates get one of three:
- **Fix** — bug. Include the fix.
- **Flag** — needs human judgment. A suspected deadlock is never a "traced, not run" Flag: run the pair (2.18) first, then classify what it showed. When the operator accepts a Flag as it stands, write their answer, quoted and dated, into the project's design document beside the requirement it narrows, in the same turn: [details/00-requirement.md](details/00-requirement.md).
- **Note** — must be aware to ship safely, but not a bug or judgment call. If you can't articulate what the developer should DO with the information, drop. A Note that says work or data can be lost is a Fix or a Flag.

## Output

**Print this block in the session, after any Evidence block CLAUDE.md asks for.** The Checklist and Files sections are the receipt that the review ran: a count, or a line saying the review found nothing, is not. Why: [details/why-the-gates.md](details/why-the-gates.md), "Why the receipt is a checklist".

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

Print this output in the session, and carry the Requirement line and the Checklist into the handoff. A card note or a handoff points to the printed block, by the time it printed; it never replaces it. They never go into a commit message, because `git-commit` keeps session measurements out of the body.

## Re-review and the fix loop

The caller runs this loop; the passes above are one iteration of it.

**First, name what runs it.** For each finding, say what executes the code it is about and when that last happened — the caller, the recipe, the test, the request path. If nothing will reach it again — a one-shot tool whose job is finished, a branch no caller takes, a guarantee the surrounding system already makes — record it where the next reader will look (the handoff, the PR thread, the report to the user), say in one line why it is not being fixed, and move on. A correct finding about code that will not run again is the most expensive kind, because its correctness is what gets it fixed.

**Then filter what is left through the Yes-to-any gate above.** If the fix improves any one axis, apply it without pausing for user confirmation, then re-run `quick-review` against the updated tree, and `security-review` too when `writing-code`'s list says the diff needs one. Repeat until a pass against the current working tree surfaces no findings that clear the gate. Only then does the commit decision arise. Do not pause to ask the user between iterations unless there is a genuine design question that cannot be resolved from existing context.

Any fix made during review starts another full round of review: all nine passes over the whole diff, with targeted re-checks added for the fix. In a staged review, the round re-runs each stage whose files changed and the cross-group stage, as [details/stages.md](details/stages.md) "After a fix" says. A prior round's dismissals do not bind amended code.

**A re-round line names the command that re-read the diff.** Where you report a later round, write the command you ran after the fix and the time it ran: "Re-round after the fix to the date parser: `git diff 9f8e7d6 -- .` at 14:09Z, nothing new." If no command re-read the diff after the fix, the re-round did not happen: run it, or report one round and name the fix as unreviewed.

The rules that decide when the loop is finished, the targeted re-checks, and anti-anchoring: [details/review-fix-loop.md](details/review-fix-loop.md).
