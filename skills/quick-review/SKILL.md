---
name: quick-review
description: Fast single-agent code review in nine structured angle passes, each having to say where it landed. Fights LLM magic-number satisficing by forcing explicit per-angle analysis. Also holds the Yes-to-any gate that every fix has to clear — security, performance, maintainability, spec compliance — and the loop that re-runs both reviews until the working tree comes back clean. Use when reviewing code changes, diffs or PRs, when asked for a quick review or a code review, and when deciding what to do with the findings afterwards.
activation:
  - "quick-review"
  - "quick review"
  - "review changes"
  - "review the code"
  - "review this"
  - "code review"
---

# Quick Review

Structured 9-pass code review. Each pass has a named-angle CHECKLIST. The checklist is the forcing function — every named angle MUST receive an explicit disposition: `DEMONSTRATED` (artifact shown), `N/A` (one line why), or `hypothesis:` (suspected, couldn't prove). See **Demonstration discipline** below — a bare "looks fine" is not a disposition. Stopping at the first N findings is one failure this skill prevents; "NONE FOUND because <plausible sentence>" is the other, and the demonstration discipline is what closes it.

## Orchestrator guidance

Your prompt should contain only: (a) the diff scope or path, (b) one sentence describing the mission/intent, (c) any non-obvious context the skill cannot infer from the diff. Do NOT enumerate which angles to check — the checklists below are the source of truth. If a concern recurs across sessions, fix the skill instead. The skill is the durable artifact.

## Workflow

1. **Pass 0 — Determine diff scope.** Cumulative `<merge-base>..HEAD` against `origin/<default_branch>` (`git fetch` first), plus uncommitted working tree. Full read; no truncation, no `| head -N`. If the orchestrator passed a delta scope (e.g., `HEAD~1..HEAD` on an amended commit), STOP and request cumulative.
2. **Load skills.** Language skill if applicable; project guideline skills matching the diff; every `CLAUDE.md` from repo root to the diff's directory. See "Skills to load."
3. **State Mission** in one sentence. If diff touches an auth surface (`oauth`, `auth`, `token`, `session`, `saml`, `oidc`, `lti`, `signin`, `signout`, `/.well-known/`, routes under `/oauth`, `/auth`, `/sso`, `/lti`, `/saml`), Read `details/rfc-oauth.md` BEFORE passes start and list the RFC sections governing each touched endpoint in the mission line.
4. **Walk Class Checklist** — mark each CWE as IN SCOPE / N/A. Every IN-SCOPE class is a mandatory angle in its pass.
5. **Run 9 passes × 12+ named angles each** = 108+ attempts minimum. For each pass: walk every named angle below. For each, resolve to one of the three dispositions in **Demonstration discipline** below — `DEMONSTRATED` (artifact shown), `N/A` (one line why), or `hypothesis:` (suspected, couldn't prove, flagged anyway). There is no "read it and it's fine" disposition. Read the matching `details/0N-*.md` for discovery methods and worked examples when needed. Repeating an angle name across passes does NOT count toward the minimum — pull fresh angles from siblings, the language skill, or the loaded project skill.
6. **Classify** each candidate through the gates (Screen → Yes-to-any → Destructive-recommendation → Author-acknowledged deviation).
7. **Output** per template.

## Diff scope

- No arg or `all`: `git fetch origin <default_branch>` then `git diff $(git merge-base HEAD origin/<default_branch>)..HEAD` + working tree
- `staged`: `git diff --staged`
- `branch`: same as no-arg (cumulative)
- `last`: `git show HEAD`
- Specific SHA: `git show <ref>`

Always use `origin/<default_branch>`, never the local branch ref. Local refs lag and silently expand scope with already-merged work.

Empty diff → stop.

## Skills to load

Load each that matches. Each becomes additional named angles in the relevant pass.

- **Any `.ex` / `.exs`** → `elixir-development` (Pass 5 conventions, Pass 7 tests)
- **Any backend change** → `code-quality-checklist` (lint, console-log removal, duplicate detection, testing requirements; `capture_log` rule)
- **Raw SQL / `Repo.query` / ClickHouse / untrusted input** → `security-review`
- **Frontend null/race/XSS/GraphQL errors** → `security-review-fe`
- **TypeScript** → `quality-checks`, `eslint`
- **Migrations** → `safe-migration`, `elixir-migrations`

**CLAUDE.md cascade.** Load every `CLAUDE.md` from repo root to diff directory:

```
git rev-parse --show-toplevel
find <root> -name CLAUDE.md -not -path '*/node_modules/*' -not -path '*/_build/*' -not -path '*/deps/*'
```

Each CLAUDE.md rule is an additional named angle in its relevant pass. Recurring rules to watch for:

- **Default-branch detection** — `master` vs `main`; wrong branch ref produces a silently-empty diff
- **Elixir/Phoenix project rules** — SSM string-coercion, SSM-backed secrets vs `System.get_env`, `Phoenix.Token` vs DB-backed tokens, two-tier logging, direnv-required `mix`: `details/language-elixir.md`

## Class Checklist

Before passes start, mark each as IN SCOPE / N/A. IN-SCOPE classes become mandatory angles in their pass. Deep dives + discovery methods: `details/class-checklist-cwes.md`.

**Reference taxonomies** (consult when shape isn't clear): CWE Top 25 (https://cwe.mitre.org/top25/), OWASP Top 10 (web), OWASP API Security Top 10, SANS Top 25.

```
Pass 1/2 — Access control:
  CWE-284/285  Improper Authorization
  CWE-287      Improper Authentication
  CWE-306      Missing Authentication
  CWE-639      Authorization Bypass via User-Controlled Key (IDOR)
  CWE-862      Missing Authorization
  CWE-863      Incorrect Authorization

Pass 2 — Injection / SSRF / protocol:
  CWE-89       SQL Injection
  CWE-79       XSS
  CWE-78       OS Command Injection (compound-string in single outer quote)
  CWE-94       Code Injection (eval, dynamic require, Code.eval_string)
  CWE-918      SSRF
  CWE-601      Open Redirect
  CWE-300/319  MITM / Cleartext Transmission (scheme downgrade)
  CWE-295      Improper Certificate Validation
  CWE-352      CSRF
  CWE-22       Path Traversal
  CWE-502      Insecure Deserialization
  CWE-611      XXE

Pass 2/3 — Concurrency / state:
  CWE-362      TOCTOU race (Fix-class for auth/billing/single-use tokens)
  CWE-400      Uncontrolled Resource Consumption
  CWE-770      Allocation Without Limits

Pass 3 — Error handling / info exposure:
  CWE-209      Error message contains sensitive info
  CWE-532      Log exposes sensitive info
  CWE-497      Exposure of System Data
  CWE-754      Improper Check for Unusual Conditions

Pass 4 — Data correctness:
  CWE-190      Integer Overflow / Wraparound
  CWE-193      Off-by-one
  CWE-697      Incorrect Comparison (==/===, loose equality)
  CWE-707      Improper Neutralization (boundary input)
  CWE-20       Improper Input Validation
```

Language-specific shape catalogs: `details/language-typescript.md`, `details/language-elixir.md`.

## Distinct-angle rule (anti-satisficing)

**12 named angles per pass minimum = 108 attempts minimum.** Each attempt targets a DIFFERENT named angle. Rephrasing does not count. If you run out before 12, pull from sibling code patterns, the language skill, the loaded project skill, or a CLAUDE.md rule that fits.

**The 108 is a FLOOR, not a ceiling.** Security-sensitive diffs do more.

**Enumerate attempts before classify.** Before the Classify step, internally list every angle name you attempted. If two passes share an angle name, you are repeating — replace one with a fresh angle. This list stays internal; the Classify step reads it.

**Scope rule.** Pre-existing code on the call path is in scope. "Not my diff" is not a dismissal. Question: does this diff INTERACT with a problem?

**Context.** Read surrounding code for each touched file, not just the diff. Identify callers, callees, sibling functions, related tests.

---

## Demonstration discipline (anti-satisficing v2)

A disposition is an **observation, not a verdict**. Why that is the rule, and what a
narrated absence costs, is in [details/why-the-gates.md](details/why-the-gates.md).

Every in-scope angle resolves to exactly one of three states. There is no fourth.

- **DEMONSTRATED** — backed by something that RAN in this session and produced output in the chat: a mutation the test caught, an adversarial input that got rejected, a grep that returned the neutralizing line. Cite the artifact.
- **N/A** — the angle is not live in this diff. One line of why (`no SQL here`, `no auth surface touched`).
- **`hypothesis:`** — you suspect a problem but could not produce the artifact. Flag it anyway, labeled. Honest, not hidden.

"I read it and it looks fine" is not a disposition. It is the satisficing slot. Delete it.

### The demonstrate-line — what owes an artifact even on a CLEAN bill

Demonstrating all 108 angles bankrupts the review, so the burden is tiered by blast radius:

- **Every Fix and every Flag always demonstrates.** Assert a bug → prove it runs or breaks. Findings are few; this is cheap.
- **A clean bill demonstrates only for these five classes** when in scope. For them, `DEMONSTRATED` REQUIRES the artifact below; bare prose is an invalid disposition:
  1. Assertion strength / test coverage
  2. Injection / untrusted input (SQL, command, path)
  3. Authorization scope
  4. Atomicity / TOCTOU
  5. Error-return shape (raise vs `{:error, _}`)
- **All other angles** may use a prose disposition — but it must be an *observation that cites the line*, never a story. (This boundary is the tunable knob. Widen it for security-sensitive diffs; the five above are the floor.)

### Proof-shape catalog — the artifact that licenses each clean bill

```
Assertion strength /   MUTATION. Edit the production code to a wrong-but-plausible
test coverage          value; re-run the test; paste the result.
                       Stays GREEN → FINDING (the assertion doesn't pin behavior).
                       Goes RED → DEMONSTRATED clean. Never judge an assertion
                       "specific enough" by reading it.

Injection / untrusted  Feed the adversarial input through the REAL entry point and
input                  show it rejected/escaped, OR quote the exact line that
                       parameterizes/neutralizes and show the value cannot reach a
                       raw sink. "No literal DROP found" is NOT proof.

Authorization scope    Construct the row the new gate should exclude; run the
                       query/resolver AS the unprivileged subject; show it is absent
                       from the result. "The gate looks correct" is NOT proof.

Atomicity / TOCTOU     Show the single-transaction boundary in the code (one call /
                       advisory lock / CAS). Two separate calls with a read between
                       them is a FINDING, not a clean bill.

Error-return shape     Trigger the error path (probe or test); show the return is the
                       {:error, _} callers destructure, not a raise that aborts the
                       surrounding transaction.
```

The deliverable of the review IS these artifacts. The Fix/Flag/Note verdict is a summary *derived* from them, never a substitute for them.

---

## Pass 1 — Call-graph and seam analysis

Worked examples: `details/01-call-graph.md`.

```
Seam checks:
  1.1   Schema-query alignment           index every new where/orderBy column
  1.2   Query consistency                grep sibling queries; compare WHERE clauses
  1.3   Return-value assumptions         3-level caller trace; recovered-error
                                          checkpoints are NOT terminal
  1.4   Handoff completeness             unchanged consumer reads new shape
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

Mint → consume seam (cross-endpoint credential contract):
  1.15a Authentication asymmetry         issuer mints X; consumer requires Y
  1.15b Scope asymmetry                  token scope vs resolver enforcement
  1.15c Lifecycle asymmetry              issuer TTL vs consumer expiry check
  1.15d Revocation asymmetry             durable mint; no consumer revocation
  1.15e Verifier missing                 signed/encrypted; consumer skips verify

Identity-keyed bucket integrity:
  1.16  Network-identifier source        real client IP vs LB IP (rate-limit / audit)

Migration-coverage discipline:
  1.17  Mass-migration coverage          per-site Pass 2 + Pass 4 attempts
  1.18  Role-discriminator twin          every role branch gets equivalent guard
```

## Pass 2 — Adversarial

Construct an input/state that crashes the code. Concurrent execution, partial failures, stale data, unexpected NULL. Worked examples: `details/02-adversarial.md`.

```
Side-effect call hygiene:
  2.1   Discarded results                fallible call result ignored
  2.2   Semantic completeness            name promises X, body delivers partial-X
  2.3   Defense-in-depth in isolation    boundary guards independent of caller

Concurrency / race shapes:
  2.4   Divergent-input races            race handler :ok; payloads diverge
  2.5   Shared-state race severity       auth/billing/single-use → Fix-class
  2.6a  Tag-after-create non-atomic      create then AddTags (separate call)
  2.6b  Overwrite without re-applying tag PutParameter --overwrite drops tags
  2.6c  Stale-delete-then-put            transient-window readers see un-tagged
  2.7   Completion-gate / lease TOCTOU   read-then-update; use CAS / advisory lock

Auth boundary:
  2.8   Pre-auth information oracles     lookup-then-auth distinguishable errors
  2.9   Identifier parse/comparison      .startsWith vs .origin; case folding
  2.10  Trigger-vs-precondition order    cheap filter before side-effecting mint

Error swallowing:
  2.11  Discarded error tuple            TS/JS and Elixir shapes: see 2.11-2.12
  2.13  Lookup-then-filter cardinality   wide lookup + post-auth-filter leaks
                                          existence across tenants
```

## Pass 3 — Error handling / information exposure

Failure modes, pattern-match style, sibling consistency, observability of failure paths. Worked examples: `details/03-error-info.md`.

```
  3.1   Error propagation trace          duplicate logging across chain levels
  3.2   Logging discipline               two-tier policy per language: see 3.2a-3.2b
  3.3   Shell-trace credential exposure  `set -x` over secret-handling commands
  3.4   Cloud-init / journald log sinks  xtrace lands in durable log; secret TTL
  3.5   capture_log assertion shape      `assert log == ""` vs `refute log =~`
  3.6   Silent catch-alls at boundaries  webhook 200 regardless of B's return
  3.7   with-chain escape hatches        else `_ ->` conflates step failures
  3.8   with-chain over-gating           optional step gates critical step
  3.9   Error-class differentiation      AbortError vs TypeError vs domain
  3.10  CWE-209 sensitive info in error  stack traces; secrets in error strings
  3.11  CWE-532 sensitive info in log    tokens, PII, passwords, session IDs
  3.12  CWE-497 system-data exposure     hostnames, pod IDs, DB errors leaked
  3.13  CWE-754 unusual-condition checks dead guards; collapsed error classes
```

## Pass 4 — Data correctness

Boundaries, nil semantics, type coercion across system boundaries, interpolation safety. Worked examples: `details/04-data-correctness.md` + language-specific in `details/language-typescript.md`.

```
Semantic boundaries:
  4.1   Empty-value semantics            "nothing" vs "everything" vs "reject"
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
  4.24  CWE-20 input validation          trust shape/type/range without check
```

## Pass 5 — Conventions

Module patterns, naming, def/defp visibility, sibling function symmetry. Worked examples: `details/05-conventions.md`. ARIA contracts: `details/accessibility-aria.md`. RFC compliance: `details/rfc-oauth.md`.

```
Sibling consistency:
  5.1   Sibling-endpoint conventions     param source / auth scheme / response /
                                          error vocabulary; same helpers
  5.2   RFC parameter completeness       enumerate spec params; honor or reject
  5.3   Spec-permitted value rejected    accept-set vs reject-set per RFC
  5.4   RFC 6749 §5.2 status codes       invalid_client 401 only on header creds
  5.5   Private-helper duplication       deletion test for near-identical defp
  5.6   Helper functions called          same validate_*/authorize_*/audit_*
  5.7   Same-module sibling consistency  asymmetric guards/clauses/fallbacks
  5.8   Within-function return-shape     all branches same shape (no :ok mix)
  5.9   Behaviour declaration consistency `@behaviour`/`@impl` symmetry across siblings

Cross-cutting infra:
  5.10  CORS preflight                   OPTIONS on browser-callable endpoints
  5.11  Pipeline shared-assign precedence multiple plug writers → last-wins risk
  5.12  Config-block consistency         sibling block key sets diff

Frontend / UI:
  5.13  ARIA role/contract correctness   declared role → keyboard contract;
                                          modal-shape → declared role
  5.14  Button hygiene                   `type="button"` + icon-only a11y name
```

## Pass 6 — Doc/code coherence

For every comment, docstring, `@moduledoc`, `@doc`, or prose claim added or touched in the diff: verify the code delivers on it. Worked examples: `details/06-doc-coherence.md`.

```
  6.1   Comment-vs-body check            statements following comment actually fire
  6.2   Docstring contract               every listed error case reachable
  6.3   Name-vs-body check               validate_*/verify_*/ensure_* perform action
  6.4   PR/commit-message-vs-diff check  claimed enforcement is present
  6.5   Distant-doc symbol drift         deleted symbol still named in distant docs/
```

Comment/code drift is how `hypothesis:` creeps into production code. Treat every comment in the diff as a testable assertion about the body below it.

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

Test-infrastructure hazards:
  7.12  Test-infra leaks (BEAM)          global mock + async, Mox :global, Ecto
                                          Sandbox ownership, :dbg tracer: see 7.12-7.14, 7.17
  7.15  Shared ETS / named processes     teardown missing
  7.16  Timer/clock reliance             Process.sleep / DateTime in assertions
  7.18  Literal call-count assertions    brittle to unrelated PR changes
  7.19  describe.skip without tracker    skip string needs `[<ticket>]` reference
  7.20  `as any` / `as unknown as X`     test mocks bypass type contract
  7.21  Weak URL/response-shape regex    pin to exact expected value
```

## Pass 8 — Second-order

Downstream systems, caches, cron jobs, deploy coordination. **Higher classification bar:** must be triggered by THIS deploy, not hypothetical future change. "If you later move modules" — drop. "This deploy changes a cached value cron job X reads at midnight" — keep. Worked examples: `details/08-second-order.md`.

```
  8.1   This-deploy triggers              concrete cron/cache/dependent reads
  8.2   Data precedes code (SCOPE GUARD) Read scope guard FIRST. Filter PRs
                                          are NOT in scope — destructive recs on
                                          filter-excluded rows are CATEGORY ERRORS.
                                          Only NEW write-time invariants trigger.
```

## Pass 9 — Test-suite reach

The diff is not the only place that talks about the diff's symbols. Mechanical grep of `test/` for every public symbol the diff touches. Worked examples: `details/09-test-suite-reach.md`.

```
  9.1   Bare-name grep                   function/module/struct name in tests
  9.2   BEAM mock/tracer targeting       :dbg, :meck, Mock, Mox: see 9.2-9.4
  9.5   Literal call-count assertions    stale on diff's call-count change
  9.6   assert_called / assert_received  message-pattern references
  9.7   Telemetry handlers               attach/detach for touched events
  9.8   Comment-thread stitches          describe / test / @moduletag strings
```

For each hit, classify as:
- **Maintenance gap** — test encodes behavior the diff INTENTIONALLY changes; must update in same PR
- **Hidden contract** — test encodes behavior the diff didn't realize it was changing; Fix-class regression
- **Stale reference** — comments/strings naming the old behavior; same-PR cleanup

If no hits: this angle is `DEMONSTRATED` clean — the greps ran and returned nothing, so the grep IS the artifact. Record "ran greps for <symbols>, 0 hits", not a bare assertion. (This is the cheapest demonstrate-line class to satisfy: the search is the proof.)

---

## Classify (internal — before any output)

Enumerate every candidate finding internally. For each, walk these gates IN ORDER.

### Screen (silent drops)

1. Is this actually a problem, or did I realize mid-write it's fine? → **Drop silently.**
2. Is this the intended effect described in Mission? → **Drop silently.**
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

Any finding that proposes DELETE / UPDATE / DROP / TRUNCATE / schema rewrite / data migration to "cleanse"/"reject"/"purge" rows / any other IRREVERSIBLE operation on USER-AUTHORED data must clear an additional precondition:

The finding MUST name the SPECIFIC invariant the existing rows violate AND cite the evidence those rows actually violate it. Acceptable invariants: NOT NULL violation, unique-key violation, FK dangling reference, content-validation rule (regex/length/format), schema-type mismatch, referential-integrity break.

NOT acceptable as "invariant": a new filter, a new authorization predicate, a new visibility scope, an ABAC subject narrowing, an ownership column added to a query. Rows excluded by a filter are legitimate data outside the caller's view — not "leaked," not "invalid," not "stale," not "orphaned."

If the finding cannot name a violated invariant AND cite specific affected rows: **DROP the destructive recommendation entirely**, OR downgrade to Flag with explicit caveats: "the diff filters X; rows excluded by the filter are NOT recommended for deletion, only for visibility scoping."

The default for any irreversible operation on user data is **preserve-and-flag**, never **recommend-deletion-from-pattern-match**.

### Author-acknowledged deviation is not exempt

An acknowledgment in a moduledoc, comment, commit message or PR body is the TRIGGER to run the Yes-to-any gate against the deviation, never a reason to skip it. The acknowledgment phrases to grep for, and why the gate has no "author already knew" exemption: [details/author-acknowledged.md](details/author-acknowledged.md).

### Classifications

Surviving candidates get one of three:
- **Fix** — bug. Include the fix.
- **Flag** — needs human judgment.
- **Note** — must be aware to ship safely, but not a bug or judgment call. If you can't articulate what the developer should DO with the information, drop.

## Output

```
# Quick Review

**Mission:** <one sentence>
**Scope:** <N files, M lines, against <merge-base>>

## Fixes
## Flags
## Notes (action-required only)

## Demonstrations (the artifacts behind the clean bills)
  One line per demonstrate-line class that was in scope: <class>: <what ran> → <result>
  e.g. assertion-strength: flipped redirect target to evil.com in
       auth_controller.ex:512 → auth_controller_test.exs:535 stayed GREEN → FINDING
  e.g. authz-scope: ran district_search as teacher subject with foreign state_id
       → 0 rows returned → DEMONSTRATED clean
  An in-scope class with no artifact here is an incomplete review, not a clean one.

## Coverage
  N candidates after 108+ attempts across 9 passes × 12+ distinct angles,
  M survived classification; K demonstrate-line classes in scope, all with artifacts above
```

## Re-review and the fix loop

The caller runs this loop; the passes above are one iteration of it.

**First, name what runs it.** For each finding, say what executes the code it is about and when that last happened — the caller, the recipe, the test, the request path. If nothing will reach it again — a one-shot tool whose job is finished, a branch no caller takes, a guarantee the surrounding system already makes — record it where the next reader will look (the handoff, the PR thread, the report to the user), say in one line why it is not being fixed, and move on. A correct finding about code that will not run again is the most expensive kind, because its correctness is what gets it fixed.

**Then filter what is left through the Yes-to-any gate above.** If the fix improves any one axis, apply it without pausing for user confirmation, then re-run BOTH `quick-review` and `security-review` against the updated tree. Repeat until a pass against the current working tree surfaces no findings that clear the gate. Only then does the commit decision arise. Do not pause to ask the user between iterations unless there is a genuine design question that cannot be resolved from existing context.

The four rules that decide when the loop is actually finished: [details/review-fix-loop.md](details/review-fix-loop.md).

If the review leads to code changes, those changes get a targeted pass before done.

**Anti-anchoring:** When re-reviewing after amends, the prior round's "triaged and dropped" list is informational context, not binding precedent. For any surface TOUCHED by the current amend, re-run the full 9-pass × 12-angle discipline on THAT surface. Previous dismissals applied to previous code; amended code is new evidence. An orchestrator passing "don't re-surface these" into the subagent prompt is a shortcut that saves tokens but erodes coverage — re-enumerate the angles and let the classify gate drop duplicates.

Targeted re-checks for the fix:
- Test coverage for the fix
- Call-graph integration
- Adversarial: does the fix create a new failure mode?
