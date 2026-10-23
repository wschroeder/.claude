---
name: quick-review
description: Fast single-agent code review in nine structured angle passes, each having to say where it landed. Fights LLM magic-number satisficing by forcing explicit per-angle analysis. Also holds the Yes-to-any gate that every fix has to clear — security, performance, maintainability, spec compliance — and the loop that re-runs the reviews until the working tree comes back clean. Use when reviewing code changes, diffs or PRs, when asked for a quick review or a code review, and when deciding what to do with the findings afterwards.
---

# Quick Review

Structured 9-pass code review. Each pass has a named-angle CHECKLIST. The checklist is the forcing function — every named angle MUST receive an explicit disposition: `DEMONSTRATED` (artifact shown), `N/A` (one line why), or `hypothesis:` (suspected, couldn't prove). See **Demonstration discipline** below — a bare "looks fine" is not a disposition. Stopping at the first N findings is one failure this skill prevents; "NONE FOUND because <plausible sentence>" is the other, and the demonstration discipline is what closes it.

## Orchestrator guidance

Run the review in the session that wrote the change, not in a subagent. That session holds the mission, the card, and the decisions behind the diff, and it needs them to tell a real finding from a false alarm. Do NOT pre-select which angles to check — the checklists below are the source of truth. If a concern recurs across sessions, fix the skill instead.

## Workflow

1. **Pass 0 — Determine diff scope.** Cumulative `<merge-base>..HEAD` against `origin/<default_branch>` (`git fetch` first), plus uncommitted working tree. Full read; no truncation, no `| head -N`. If the orchestrator passed a delta scope (e.g., `HEAD~1..HEAD` on an amended commit), STOP and request cumulative.
   **Then size it.** Measure the diff and the room this session has left. If the diff takes more than a third of that room, plan the review as stages before reading any of it: [details/stages.md](details/stages.md).
2. **Load skills.** The language skill, any project guideline skill that matches the diff, and every `CLAUDE.md` from repo root to the diff's directory. Each adds named angles to its pass. The list and the command that finds the CLAUDE.md files: [details/skills-to-load.md](details/skills-to-load.md).
3. **State Mission** in one sentence. If diff touches an auth surface (`oauth`, `auth`, `token`, `session`, `saml`, `oidc`, `lti`, `signin`, `signout`, `/.well-known/`, routes under `/oauth`, `/auth`, `/sso`, `/lti`, `/saml`), Read `details/rfc-oauth.md` BEFORE passes start and list the RFC sections governing each touched endpoint in the mission line.
4. **Check the requirement.** Find the issue, card, or spec the diff serves and check the diff against each of its acceptance criteria. Method: [details/00-requirement.md](details/00-requirement.md).
5. **Walk the Class Checklist** in [details/class-checklist-cwes.md](details/class-checklist-cwes.md): mark each CWE class IN SCOPE or N/A. Every IN-SCOPE class is a mandatory angle in its pass.
6. **Run the 9 passes.** For each pass: walk every named angle below that is live in this diff. For each, resolve to one of the three dispositions in **Demonstration discipline** below — `DEMONSTRATED` (artifact shown), `N/A` (one line why), or `hypothesis:` (suspected, couldn't prove, flagged anyway). There is no "read it and it's fine" disposition. Read the matching `details/0N-*.md` for discovery methods and worked examples when needed. Write each pass to the notes file as it finishes; see "Record each pass as it finishes".
7. **Classify** each candidate through the gates (Screen → Yes-to-any → Destructive-recommendation → Author-acknowledged deviation).
8. **Output** per template, printed in the session after any Evidence block CLAUDE.md asks for, never folded into it.

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
- **Code the branch adds is never out of scope.** A commit subject that names one kind does not narrow the review to that kind. Before the round ends, run a test against each hypothesis about the branch's own code, or raise it as a Flag. A hypothesis about the branch's own code never carries into a handoff. Measured: a review wrote "hypothesis (likely out of scope): `keepNumberlessRecords` runs only on the new kind", four sessions carried the line forward unprobed, and an outside reviewer then found records of a third kind splitting in two.

Why: [details/why-the-gates.md](details/why-the-gates.md), "Why a changed rule pulls in code the diff never touched".

**Context.** Read surrounding code for each touched file, not just the diff. Identify callers, callees, sibling functions, related tests. A file that a handoff or a card calls out of scope is out of scope for changes, never for reading: the review still greps it.

---

## Demonstration discipline (anti-satisficing v2)

A disposition is an **observation, not a conclusion**. Why that is the rule, and what a
narrated absence costs, is in [details/why-the-gates.md](details/why-the-gates.md).

Every in-scope angle resolves to exactly one of three states. There is no fourth: "carried" from an earlier session is not a disposition, so a whole-branch review checks each angle again against HEAD and cites an earlier session's artifact only when it names that artifact and shows the code it covered has not changed since.

- **DEMONSTRATED** — backed by something that RAN in this session and produced output in the chat: the mutation receipt `tdd-cycle` 4a left, an adversarial input that got rejected, a grep that returned the neutralizing line. Cite the artifact.
- **N/A** — the angle is not live in this diff. One line of why (`no SQL here`, `no auth surface touched`).
- **`hypothesis:`** — you suspect a problem but could not produce the artifact. Flag it anyway, labeled. Honest, not hidden.

"I read it and it looks fine" is not a disposition. It is the satisficing slot. Delete it.

**Angles 1.3 and 2.1 owe one line per changed function.** List every function in the diff that is new or whose arguments or return value changed. Each one gets its own 1.3 line naming every caller, including callers outside the diff, with the grep and its hit count printed beside the list, and its own 2.1 line saying what that caller does with the result. One example standing in for the whole diff is not a disposition.

### The demonstrate-line — what owes an artifact even on a CLEAN bill

Demonstrating every angle bankrupts the review, so the burden is tiered by blast radius:

- **Every Fix and every Flag always demonstrates.** Assert a bug → prove it runs or breaks. Findings are few; this is cheap.
- **A clean bill demonstrates only for these five classes** when in scope. For them, `DEMONSTRATED` REQUIRES the artifact below; bare prose is an invalid disposition:
  1. Assertion strength / test coverage
  2. Injection / untrusted input (SQL, command, path)
  3. Authorization scope
  4. Atomicity / TOCTOU
  5. Error-return shape (raise vs `{:error, _}`)
- **All other angles** may use a prose disposition — but it must be an *observation that cites the line*, never a story. (This boundary is the tunable knob. Widen it for security-sensitive diffs; the five above are the floor.)

### Proof-shape catalog

Each of the five classes above has one artifact that licenses its clean bill, listed in [details/proof-shapes.md](details/proof-shapes.md). Read it before you mark any of the five `DEMONSTRATED`.

The deliverable of the review IS these artifacts. The Fix/Flag/Note label is a summary *derived* from them, never a substitute for them.

---

## Pass 1 — Call-graph and seam analysis

Worked examples: `details/01-call-graph.md`.

```
Seam checks:
  1.1   Schema-query alignment           index every new where/orderBy column
  1.2   Query consistency                every sameness query (dedup, unique index,
                                          lookup) side by side; each compares one expression
                                          and leaves out the same rows (superseded,
                                          hidden, deleted); a match that picks one
                                          of several candidates: build two, say
                                          what the loser's subject gets
  1.3   Return-value assumptions         3-level caller trace; recovered-error
                                          checkpoints are NOT terminal; each early return
                                          names every state reaching it, another row too
  1.4   Handoff completeness             grep every unchanged reader of the new table
                                          or state, a new value in an old column
                                          or audit action too, and drive each one; what
                                          it shows from each new state is true
                                          a new value in an old column: grep the
                                          table, not the value; each sum, count,
                                          list, picker, and write target shows or
                                          offers that state's row in or out, as
                                          the spec says; "not a total" is no N/A
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
  1.5   Spec contract changes            @spec change → every caller updated

Forward data propagation:
  1.6   Extracted-but-not-forwarded      trace each extracted value end-to-end
  1.7   New-field-not-threaded           new map key → downstream pattern-match
  1.8   Filter-dimension gaps            upstream filter covers downstream dims
  1.9   Control-flow coupling            independent side-effects in one branch
  1.10  Behavioral regression            git show <base>:<path>; diff old vs new
  1.11  Documented-placeholder UX        silent-zero-row UX is itself the finding
  1.12  Closure capture vs accumulator   outer-scope intent → accumulator threading
  1.13  Magic-constant aligned to param  derive literal from configurable
  1.14  Time-window ceiling              round up, never truncate

Conditional seams (1.15a-1.18), listed in details/01-call-graph.md:
  walk 1.15a-e when the diff mints or consumes a credential, 1.16 when
  it keys a bucket or audit row by client identity, and 1.17-1.18 when
  it migrates many call sites or branches on a role; N/A otherwise.

Producer coverage:
  1.19  New-field producers              every path that creates or edits the row
                                          can set the field a new check needs
```

## Pass 2 — Adversarial

Construct an input/state that crashes the code. Concurrent execution, partial failures, stale data, unexpected NULL. Worked examples: `details/02-adversarial.md`.

```
Side-effect call hygiene:
  2.1   Discarded results                fallible call result ignored; a void or
                                          detached promise doing durable work names the
                                          stored record that reruns it after a restart,
                                          or it is a Fix
  2.2   Semantic completeness            name promises X, body delivers partial-X;
                                          today's call sites passing proves only
                                          that nothing is open now
  2.3   Defense-in-depth in isolation    boundary guards independent of caller;
                                          "the page always sends it" drops nothing
                                          proof: post the request without the
                                          field and quote what the server answers
  2.20  Checker evasion                  a linter, scanner, or allowlist the diff
                                          adds or changes: one input per way round
                                          it (case, computed key, spread, look-alike
                                          type), each run through the checker

Concurrency / race shapes:
  2.4   Divergent-input races            race handler :ok; payloads diverge
  2.5   Shared-state race severity       auth/billing/single-use, or a gate other
                                          code trusts (verified, approved, posted)
                                          → Fix-class
  2.6a-c Tag used as access control    cloud resource tagged after create,
                                          on overwrite, or after delete: see 2.6
  2.7   Self-race / lease TOCTOU         2 runs at once: every write, not just 1 step
                                          proof: run two copies at once against real
                                          Postgres, or quote the lock both take first
  2.18  Cross-writer race                each write path against every OTHER writer
                                          of its rows and their FK parents, listed by
                                          name, deferred steps too, one test each; a sibling
                                          that locks where this path does not → finding
                                          proof: hold the other writer open (pg_sleep),
                                          run this one, show the outcome
                                          reading the SQL, "one statement", or a
                                          transaction boundary is not proof
                                          two paths taking the same two locks: quote
                                          each path's order side by side, with the row
                                          locks UPDATE/DELETE take and FK key-shares;
                                          after a path deletes, combines, or leaves
                                          duplicates of rows, run every other writer
                                          once more afterwards and show it holds
        2.7/2.18 proofs assert the promised invariant ("≤ 30 rows"), not "no errors",
                                          at replicas × pool size copies at once
  2.19  Read skew                        2+ queries, read-only too; writer between
                                          them → re-check selecting condition;
                                          a decision judges the same read its
                                          re-check compares; two nulls never match

Auth boundary:
  2.8   Pre-auth information oracles     lookup-then-auth distinguishable errors
  2.9   Identifier parse/comparison      .startsWith vs .origin; case folding
  2.10  Trigger-vs-precondition order    cheap filter before side-effecting mint

Error swallowing:
  2.11  Discarded error tuple            TS/JS and Elixir shapes: see 2.11-2.12
  2.13  Lookup-then-filter cardinality   wide lookup + post-auth-filter leaks
                                          existence across tenants

Cost and resource shapes (CWE-400 / CWE-770):
  2.14  N+1 calls                        query or remote call inside a loop;
                                          first: does the DB already store what
                                          it fetches? then read that, not batch;
                                          a view or CTE read inside a per-row
                                          subquery or lateral join counts, even
                                          when the page makes one call
                                          proof: explain analyze on data at least
                                          the size of a real book, quoting the loop
                                          count of each scan of that view or CTE; a
                                          plan read on a dev database is not proof
  2.15  Quadratic scans                  nested pass over one collection;
                                          membership test on a list in a loop;
                                          a SubPlan under a correlated not exists,
                                          even when its loop count is 1
  2.16  Resource not released            handle / socket / listener / timer /
                                          process opened with no close path
  2.17  Unbounded growth                 cache / map / table / state only added to;
                                          a whole file, response, or archive held
                                          in memory names what limits its size,
                                          in helpers the diff calls too
                                          proof: the quoted limit, or peak memory
                                          with one input as large as expected
                                          measured at the largest size the
                                          deployment allows
  2.21  Unbounded attempt                each retry loop, outside call, or lock wait
                                          names what limits one attempt
                                          proof: the quoted limit and a test that
                                          fails without it; a retry count is not one
  2.22  Partial compatibility check      a check that two things fit: every field
                                          the consumer reads from each is compared
```

## Pass 3 — Error handling / information exposure

Failure modes, pattern-match style, sibling consistency, observability of failure paths. Worked examples: `details/03-error-info.md`.

```
  3.1   Error propagation trace          duplicate logging across chain levels
  3.2   Logging discipline               two-tier policy per language: see 3.2a-3.2b
  3.3   Shell-trace credential exposure  `set -x` over secret-handling commands
  3.4   Cloud-init / journald log sinks  xtrace lands in durable log; secret TTL
  3.5   capture_log assertion shape      `assert log == ""` vs `refute log =~`
  3.6   Silent catch-alls at boundaries  webhook 200 regardless of B's return;
                                          each catch the diff adds: what a person
                                          sees afterward, against each criterion
  3.7   with-chain escape hatches        else `_ ->` conflates step failures
  3.8   with-chain over-gating           optional step gates critical step
  3.9   Error-class differentiation      AbortError vs TypeError vs domain
  3.10  CWE-209 sensitive info in error  stack traces; secrets in error strings
  3.11  CWE-532 sensitive info in log    tokens, PII, passwords, session IDs
  3.12  CWE-497 system-data exposure     hostnames, pod IDs, DB errors leaked
  3.13  CWE-754 unusual-condition checks dead guards; collapsed error classes
  3.14  A failure log names its operation each warn/error inside a download, run,
                                          or request carries that operation's id
```

## Pass 4 — Data correctness

Boundaries, nil semantics, type coercion across system boundaries, interpolation safety. Worked examples: `details/04-data-correctness.md` + language-specific in `details/language-typescript.md`.

```
Semantic boundaries:
  4.1   Empty-value semantics            "nothing" vs "everything" vs "reject";
                                          blank is null, '', only spaces, and what
                                          each transform leaves; a promised rule
                                          holds even where no input reaches it today;
                                          a filter that can drop every row an
                                          aggregate reads: sum is null, not 0
  4.2   Schema default ≠ DB default      Ecto struct default vs migration NULL
  4.3   Redaction/truncation completeness all sinks (throw, log, cause) use redacted

TS/JS-specific shapes (4.4-4.19):  16 angles, listed with worked examples in
                                   details/04-data-correctness.md. Walk them for any
                                   .ts/.tsx/.js/.jsx diff; skip as N/A otherwise.

CWE class checks:
  4.20  CWE-190 int overflow             arithmetic on untrusted bounds
  4.21  CWE-193 off-by-one               slice/loop/buffer bounds
  4.22  CWE-697 incorrect comparison     `==` vs `===`; loose equality
  4.23  CWE-707 boundary input           neutralize at system boundary
  4.24  CWE-20 input validation          trust shape/type/range without check;
                                          a raw outside value past the edge, or
                                          coerced where it lands → parse at the edge

Linked input:
  4.25  Linked-input normalization       outside data that links its own records:
                                          loops of any length, not only self-links
  4.26  Outside-format variants          each construct a parser reads: every
                                          variant the format allows is read or
                                          refused, never skipped
                                          proof: drive each variant through every
                                          path that reads the same field (create,
                                          match, pair); a path that reads it
                                          another way is the finding
```

## Pass 5 — Conventions

Module patterns, naming, def/defp visibility, sibling function symmetry, reuse, and hygiene. Worked examples: `details/05-conventions.md`. ARIA contracts: `details/accessibility-aria.md`. RFC compliance: `details/rfc-oauth.md`.

```
Sibling consistency:
  5.1   Sibling-endpoint conventions     param source / auth scheme / response /
                                          error vocabulary; same helpers
  5.2-5.4 RFC compliance               auth endpoints: every spec param, value,
                                          and status code; see 5.2-5.4
  5.5   Private-helper duplication       deletion test for near-identical defp;
                                          the same edit made in several copies, or
                                          one shape in two notations (JSON schema
                                          and Zod) → derive one, or a drift test;
                                          a shared helper serving a new kind runs
                                          that kind's own reader, parser, and
                                          default: name each, or it is a finding;
                                          one value under two names (a test's
                                          literal copying a constant the diff
                                          defines) → import it, and name the one
                                          place that spells it out on purpose
  5.6   Helper functions called          same validate_*/authorize_*/audit_*
  5.7   Same-module sibling consistency  asymmetric guards/clauses/fallbacks;
                                          a match proves the convention, never
                                          the behavior; two helpers giving one
                                          verdict both honor a reviewer's choice;
                                          a rule applied to one kind of a family:
                                          name each sibling kind, shown in or out
                                          by a test or a spec line
  5.8   Within-function return-shape     all branches same shape (no :ok mix)
  5.9   Behaviour declaration consistency `@behaviour`/`@impl` symmetry across siblings

Cross-cutting infra:
  5.10  CORS preflight                   OPTIONS on browser-callable endpoints
  5.11  Pipeline shared-assign precedence multiple plug writers → last-wins risk
  5.12  Config-block consistency         sibling block key sets diff

Frontend / UI:
  5.13-5.14 ARIA contract, button hygiene see 5.13-5.14 for any markup diff

Reuse and hygiene:
  5.15  Codebase-wide reuse              grep repo for an existing function that
                                          already does, or could do, the new job
  5.16  Leftover code                    debug prints, commented-out code, focused
                                          tests, TODO without a ticket; a field every
                                          producer sets to a constant and no
                                          consumer reads (grep for readers)
  5.17  Deprecated API calls             compiler / linter deprecation warnings
                                          on touched files
  5.18  Readability                      name that needs a comment; wrapper that
                                          adds nothing; mixed abstraction levels
  5.19  Project linter and formatter     run the repo's own check on touched files
  5.20  Project CLAUDE.md duties         each rule there whose trigger the diff
                                          meets: quote where the diff obeys it
```

## Pass 6 — Doc/code coherence

For every comment, docstring, `@moduledoc`, `@doc`, or prose claim added or touched in the diff: verify the code delivers on it. Worked examples: `details/06-doc-coherence.md`.

```
  6.1   Comment-vs-body check            statements following comment actually fire;
                                          a claim that a value stays safe elsewhere
                                          → run it through every path that place has
  6.2   Docstring contract               every listed error case reachable
  6.3   Name-vs-body check               validate_*/verify_*/ensure_* perform action;
                                          each test's title matches its assertions
                                          proof: quote each added or renamed test's
                                          title beside the assertion line proving
                                          each thing it names; no line → finding
  6.4   PR/commit-message-vs-diff check  claimed enforcement is present
  6.5   Distant-doc symbol drift         deleted symbol still named in distant docs/
  6.6   Deletion test, every block       each listed comment block: keep plus its why, or delete
  6.7   Old rule still stated            each rule the diff changes: grep the files it
                                          edits and docs/spec for the old rule's
                                          words; each hit fixed or given a reason
                                          proof: state each changed rule in one
                                          sentence, then quote each hit and what
                                          became of it; no rule named → finding
  6.8   Spec sentence vs code            each spec sentence the diff adds or edits:
                                          split it into the cases it names; a class
                                          names one case per member
                                          proof: quote one code line per case that
                                          makes that case true; a case with no
                                          line → finding
                                          a new member of a class (a kind, a
                                          source, a state): grep docs/spec for
                                          each unchanged sentence naming a
                                          sibling; say whether the new member
                                          follows it; left unsaid → finding
  6.9   Spec lists additions             each column, route, setting, or audit
                                          action the diff adds: quote its line on
                                          the spec page that lists things of that
                                          kind; no line → finding
```

For 6.6, run `python3 ~/.claude/skills/writing-code/scripts/comment_share.py` over Pass 0's scope; with no `--base` it already measures from the merge base, uncommitted and untracked work included. Paste its per-file lines. Give every block it lists "keep" with the non-obvious why it explains, or "delete", and read a file over 10% twice. The bill is not clean while any block lacks a disposition. `writing-code` "Measure before declaring done" owns the rule.

## Pass 7 — Test coverage

Tests over eyeballing. The review's primary job is to identify behaviors lacking test coverage. **You MUST have read the FULL test diff before claiming a coverage gap.** Tests must assert outcomes, not implementation. Worked examples: `details/07-test-coverage.md`.

```
  7.1   Failure path coverage            test exists for external-call failure
  7.2   Side-effect coverage             each side effect independently asserted
  7.3   Refactored-code coverage         pre-refactor tests exist; if not, flag
  7.4   End-to-end path coverage         integration test for cross-module flow
  7.5   New external API without mocks   test files include fixture/mock
  7.6   Partial-chain tests masking gaps middle-layer mocked despite change
  7.7   Symmetry cross-check (Pass 5×6)  symmetric production changes → symmetric tests
  7.8   Test intent vs test effect       earlier guards short-circuit target branch
  7.9   Test-to-test assertion symmetry  siblings assert same invariants
  7.10  Range-assertions correctness gap pin to exact value when known
  7.11  Tests added by current loop      verify behavior; don't lock status quo
  7.22  A fixed bug's test               the assertion goes into the feature test
                                          that had the hole, and asserts the
                                          symptom a person saw
                                          proof: quote that feature test's title
                                          and the line asserting the symptom; a
                                          test named for the bug, or no symptom
                                          line → finding

Test-infrastructure hazards (7.12-7.21), listed in details/07-test-coverage.md:
  walk them for any diff that adds or edits a test: global mocks, sandbox
  ownership, tracers, shared ETS, clocks, call counts, skips, casts, regexes
```

## Pass 8 — Second-order

Downstream systems, caches, cron jobs, deploy coordination. **Higher classification bar:** must be triggered by THIS deploy, not hypothetical future change. "If you later move modules" — drop. "This deploy changes a cached value cron job X reads at midnight" — keep. Worked examples: `details/08-second-order.md`.

```
  8.1   This-deploy triggers              concrete cron/cache/dependent reads
  8.2   Data precedes code (SCOPE GUARD) Read scope guard FIRST. Filter PRs
                                          are NOT in scope — destructive recs on
                                          filter-excluded rows are CATEGORY ERRORS.
                                          Only NEW write-time invariants trigger.
                                          So does a new column new code reads:
                                          run the reader on an old row's value
  8.3   Rollback after user edits         run each down migration after the edits
                                          the feature allows, then up again
  8.4   Shared destinations               each name the diff writes where other
                                          runs' output also lands: two runs with
                                          overlapping input never make one name
                                          proof: run two with a shared input and
                                          list the names each wrote
```

## Pass 9 — Test-suite reach

The diff is not the only place that talks about the diff's symbols. Mechanical grep of `test/` for every public symbol the diff touches, and of the whole repository for every value it changes (9.9). Worked examples: `details/09-test-suite-reach.md`.

```
  9.1   Bare-name grep                   function/module/struct name in tests
  9.2   BEAM mock/tracer targeting       :dbg, :meck, Mock, Mox: see 9.2-9.4
  9.5   Literal call-count assertions    stale on diff's call-count change
  9.6   assert_called / assert_received  message-pattern references
  9.7   Telemetry handlers               attach/detach for touched events
  9.8   Comment-thread stitches          describe / test / @moduletag strings
  9.9   Whole-repo copies                every changed constant, list, enum, or
                                          text a user reads: grep its name and one
                                          member from the repository root, all
                                          files, every language
```

Classify each hit as a maintenance gap, a hidden contract, or a stale reference, as `details/09-test-suite-reach.md` "Classifying hits" defines them. If the greps return no hits, print the greps and "0 hits": the grep is the artifact.

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

If YES to at least one, recommend the fix. The bar is "positive signal on any axis," not "positive on all axes." This is the anti-waffling rule — it prevents the "technically correct but maybe not worth it" drift. A 5-line fix that measurably improves one axis beats a 0-line "ship as-is" that improves none. This section is the only place the axes are defined; `writing-code`, `pr-respond-task` and `pr-feedback-task` point here rather than restating them.

### Destructive-recommendation gate (irreversibility ratchet)

A finding that proposes an irreversible operation on user-authored data (DELETE, UPDATE, DROP, TRUNCATE, a schema rewrite, a cleansing migration) must name the specific invariant the existing rows violate and cite rows that violate it. A new filter or authorization predicate is never such an invariant. If the finding cannot do both, drop the recommendation or downgrade it to a Flag. Read [details/destructive-gate.md](details/destructive-gate.md) whenever a finding proposes one.

### Author-acknowledged deviation is not exempt

An acknowledgment in a moduledoc, comment, commit message, PR body, this review's own Notes, or the session's handoff is the TRIGGER to run the Yes-to-any gate against the deviation, never a reason to skip it. A finding that a later card will fix is still a Fix or a Flag in this commit, never a Note. The acknowledgment phrases to grep for, and why the gate has no "author already knew" exemption: [details/author-acknowledged.md](details/author-acknowledged.md).

### Classifications

Surviving candidates get one of three:
- **Fix** — bug. Include the fix.
- **Flag** — needs human judgment.
- **Note** — must be aware to ship safely, but not a bug or judgment call. If you can't articulate what the developer should DO with the information, drop. A Note that says work or data can be lost is a Fix or a Flag.

## Output

**Print this block in the session, after any Evidence block CLAUDE.md asks for.** The Checklist and Files sections are the receipt that the review ran: a count, or a line saying the review found nothing, is not. Why: [details/why-the-gates.md](details/why-the-gates.md), "Why the receipt is a checklist".

```
# Quick Review

**Mission:** <one sentence>
**Requirement:** <source, or "none found"> — <each criterion: met / partly met / not met>
**Scope:** <N files, M lines, against <merge-base>>

## Fixes
## Flags
## Notes (action-required only)

## Demonstrations (the artifacts behind the clean bills)
  One line per demonstrate-line class that was in scope: <class>: <what ran> → <result>
  e.g. assertion-strength: the card note carries no 4a receipt for
       auth_controller_test.exs:535 → FINDING
  e.g. authz-scope: ran district_search as teacher subject with foreign state_id
       → 0 rows returned → DEMONSTRATED clean
  An in-scope class with no artifact here is an incomplete review, not a clean one.

## Checklist
  Every pass, in order. Each angle in a pass the diff touches gets one line: <number> <name>: <disposition>, <what you saw>, with N/A and its reason where the angle is not live.
  A pass with no live angle gets one line saying why.
  e.g. Pass 2 — Adversarial
       2.3 self-race: DEMONSTRATED, two concurrent saves left one row
       2.5 replay: N/A, the route takes no client-supplied id
  e.g. Pass 3 — Error handling: N/A, no error path in the diff

## Files
  Every file in scope, marked read or skipped; a skip names its reason in a few words.
```

Print this output in the session, and carry the Requirement line and the Checklist into the handoff. They never go into a commit message, because `git-commit` keeps session measurements out of the body.

## Re-review and the fix loop

The caller runs this loop; the passes above are one iteration of it.

**First, name what runs it.** For each finding, say what executes the code it is about and when that last happened — the caller, the recipe, the test, the request path. If nothing will reach it again — a one-shot tool whose job is finished, a branch no caller takes, a guarantee the surrounding system already makes — record it where the next reader will look (the handoff, the PR thread, the report to the user), say in one line why it is not being fixed, and move on. A correct finding about code that will not run again is the most expensive kind, because its correctness is what gets it fixed.

**Then filter what is left through the Yes-to-any gate above.** If the fix improves any one axis, apply it without pausing for user confirmation, then re-run `quick-review` against the updated tree, and `security-review` too when `writing-code`'s list says the diff needs one. Repeat until a pass against the current working tree surfaces no findings that clear the gate. Only then does the commit decision arise. Do not pause to ask the user between iterations unless there is a genuine design question that cannot be resolved from existing context.

Any fix made during review starts another full round of review: all nine passes over the whole diff, with targeted re-checks added for the fix. In a staged review, the round re-runs each stage whose files changed and the cross-group stage, as [details/stages.md](details/stages.md) "After a fix" says. A prior round's dismissals do not bind amended code.

The rules that decide when the loop is finished, the targeted re-checks, and anti-anchoring: [details/review-fix-loop.md](details/review-fix-loop.md).
