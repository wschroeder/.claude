---
name: pr-feedback-task
description: Manual-invoke template — produces a structured PR-feedback artifact (readiness gate, feedback inventory, legitimacy evaluation, recommended actions); when nothing is left for the operator to decide it auto-launches pr-respond-task, else it stops for approval. Do not auto-activate; invoke explicitly only.
---

# pr-feedback-task — check readiness, evaluate legitimacy

For the PR feedback task in $ARGUMENTS (or the current branch's PR if
none specified), respond with the following sections in order. Produce
the evaluation through Recommended Actions, then reach the hand-off gate:
if nothing is left for the operator to decide, auto-launch pr-respond-task
on the Accepted findings; otherwise stop at the recommendation step and
wait for explicit approval. The hand-off gate (final section) defines
"nothing to decide."

The output discipline is structural: each section must contain actual
tool output, not paraphrased summaries. A missing section, a hollow
section, or out-of-order sections are all invalid outputs.

## Readiness Check

Surface the state of every feedback source. Use:

```bash
# (a) PR overview — review states, decision, status checks, merge readiness.
#     `reviewThreads` is NOT a valid --json field for `gh pr view`; use (c).
gh pr view <pr> --json reviews,latestReviews,reviewDecision,reviewRequests,statusCheckRollup,mergeStateStatus

# (b) Check runs with buckets categorizing state into
#     pass / fail / pending / skipping / cancel.
gh pr checks <pr> --json bucket,name,state,workflow

# (c) Review threads — exposed only via GraphQL.
#     `-f` carries the static query string; `-F` carries typed variables
#     (`pr` becomes Int via the magic-type conversion documented in
#     `gh api graphql --help`).
gh api graphql \
  -f query='query($owner: String!, $repo: String!, $pr: Int!) {
    repository(owner: $owner, name: $repo) {
      pullRequest(number: $pr) {
        reviewThreads(first: 100) {
          nodes {
            isResolved
            isOutdated
            path
            line
            comments(first: 50) {
              nodes { author { login } body path line id }
            }
          }
        }
      }
    }
  }' \
  -F owner=<owner> -F repo=<repo> -F pr=<pr>
```

Report:

```
- CodeRabbit check_run:    <status — "Review skipped" counts as DONE,
                            not a bounce; "in_progress" / "queued"
                            mean NOT READY>
- Cursor Bugbot check_run: <status — "neutral", "skipping", "pending"
                            mean NOT READY per the front-end project's
                            CLAUDE.md; only "passed" or "Review
                            skipped" count>
- Human reviewers:         <submitted / requested / changes_requested>
- Review threads:          <count: open / resolved / outdated>
- Test/CI checks:          <CI checks, lint, etc. — informational only;
                            per Linear feedback-first ordering, threads
                            come first; test status does not gate
                            evaluation>
- Vercel checks:           ignored on both axes per Linear workflow
- Browser validation
   (front-end PRs only):   <screenshots attached to PR? per the
                            front-end project's CLAUDE.md>
```

**GO/NO-GO** (explicit, before continuing to the next section):

- **GO** if every feedback-bot check_run is in a done state (passed OR
  "Review skipped") AND at least one unresolved thread or unevaluated
  finding exists worth reviewing.
- **NO-GO** if any feedback-bot check_run is still pending or
  in_progress — stop here, report exactly what we are waiting on, do
  not proceed to evaluation.

## Feedback Inventory

Paste raw output (not paraphrased) from all three sources:

```
gh api repos/{owner}/{repo}/pulls/<pr>/comments    # inline review comments
gh api repos/{owner}/{repo}/pulls/<pr>/reviews     # top-level review bodies
gh api repos/{owner}/{repo}/issues/<pr>/comments   # general PR conversation
```

For each thread, surface: file:line, author (CodeRabbit / Cursor Bugbot /
human reviewer / other), body, `in_reply_to_id`, `isResolved`,
`isOutdated`. Skip resolved and outdated threads from evaluation, but
list them in the inventory so the count reconciles.

## Legitimacy Evaluation

**Bot findings are HYPOTHESES, not facts.** For each unresolved
non-outdated thread, apply the five-check discipline before assigning a
disposition (from `william-linear-workflow/symphony/WORKFLOW.md:163-166`):

**The bot's severity label carries zero weight — never record it, never
anchor to it.** A "Critical", a "Major", a "Medium", a "nitpick" tag —
none of them is an input to prioritization. A bot rates from a local
pattern match, usually blind to the call chain: it will brand an
unreachable pattern "critical", and tag a scope-critical bug a "nitpick".
After you have traced legitimacy and scope yourself, YOU assign the real
priority from the actual consequence and who it reaches — overriding the
bot freely in either direction (down when it misunderstood the call
chain, up when it underweighted the scope). Do not write "stated Major"
or quote the bot's rating in your output as if it carried evidentiary
weight; state your own severity with the reasoning that earned it. You
know this codebase; the bot does not.

1. **Read the current code at HEAD yourself.** Do not trust the bot's
   quoted snippet. Bots reference stale state, hallucinate code paths,
   and pattern-match on names rather than mechanisms. CodeRabbit's own
   prompt-for-AI-agents: "Verify each finding against current code. Fix
   only still-valid issues, skip the rest with a brief reason, keep
   changes minimal."
2. **Confirm the finding is in this PR's mission scope.** Run
   `git diff <base>..HEAD -- <file>` and verify whether the diff
   touches the cited code path. There are three outcomes here, not two
   — and the middle one is the trap, where reviews punt work they
   should keep:

   - **The PR introduced the cited code.** In scope. Evaluate it with
     the mechanism and reachability checks below.
   - **The PR did not introduce the cited code, but the code sits in
     the path the PR is already touching** — the same function the diff
     edits, a helper the changed code calls, a query whose result the
     PR's new behavior now relies on. Fix it here. This is the
     operator's standing rule: don't defer related work. A pre-existing
     bug directly under the change you are making is yours to fix in
     this PR, because the next reader will take your diff as a statement
     that the path you touched is sound. This is NOT a Rejected
     disposition — record it under **Accepted** and fix it in the same
     PR.
   - **The PR did not introduce the cited code AND the code is
     unrelated to anything the PR touches** — a different module, an
     untouched call path, code the change neither calls nor depends on.
     This is the only genuinely out-of-scope case, and the only
     legitimate **Rejected — unrelated pre-existing code** disposition.
     The reply must cite the diff check AND state the lack of
     dependency ("git diff confirms this PR's diff does not touch the
     cited path, and the change neither calls nor relies on it; the
     issue, if real, predates this PR and is unrelated to its
     mission").
3. **Verify the mechanism in this instance.** A bot saying "this could
   leak X" is an observation that a pattern is present, not proof the
   mechanism applies. Two distinct checks are required:

   **(a) Syntactic mechanism — does the code do what the bot says?**
   Trace the call graph or state machine; reproduce the failure where
   possible. If the code doesn't do what the bot describes, the finding
   is **Rejected — mechanism not present**.

   **(b) Reachability — does the triggering input actually arrive?**
   Confirming that the function crashes / leaks / mis-orders on certain
   input (3a) is different from confirming that input arrives in
   production. Bots pattern-match on names and shapes; they don't trace
   what constrains the input upstream. Ask where the triggering input
   comes from and what limits its shape — an LLM-output parser is
   constrained by the prompt; a user-input handler may be constrained
   by an upstream validator; an internal call site is constrained by
   the caller's contract; a struct field is constrained by its
   typespec. When upstream constraints make the input unreachable, the
   mechanism is present but cannot fire — per `~/.claude/CLAUDE.md`:
   *"Don't add error handling, fallbacks, or validation for scenarios
   that can't happen. Trust internal code and framework guarantees.
   Only validate at system boundaries."* This is a legitimate
   **Rejected — input unreachable** disposition. The reply must name
   the upstream constraint, not just say "mechanism not present" — the
   mechanism IS present, the triggering input isn't.

   Conflating (a) with (b) is the most common review error and the
   reason this step was promoted to two sub-checks. A probe that
   confirms (a) does NOT establish (b). The probe shows the failure
   mode is real if the triggering input arrives; it does not show the
   input arrives.

4. **Distinguish bot pushback from operator pushback.** A bot's reply
   to your earlier fix that re-asserts its original concern without
   new evidence is itself a hypothesis. Re-evaluate with the three
   checks above; do not capitulate to repeated assertions.
5. **Probe the mechanism whenever the finding spans a module boundary,
   questions an algorithm or logic, or claims runtime behavior.**
   Staring at code in your head is not a probe. Reading the file at
   HEAD is not a probe either — it confirms what the code SAYS, not
   what the running system DOES. An acceptable probe is something that
   ran on this machine in the last few minutes and produced output now
   in the chat: a `mix run -e "..."` snippet, an IEx session, a one-
   off test that exercises the actual path, a curl + saved JSON. Paste
   the probe command AND its real output. That output becomes a [REF]
   in the disposition.

   For algorithmic or logic findings, the probe IS the proof of
   legitimacy. Don't trust your memory of an API's behavior, the
   library docs, or pattern-matching on a familiar shape — verify
   with a light test. The discipline this skill enforces is the same
   one an experienced developer applies to their own work: rarely
   trust APIs or your own expertise; manually test with curl,
   snippets, or one-off scripts while investigating.

   When no boundary is crossed (pure-syntactic findings: formatting,
   import order, unused var, comment typo, name choice): write
   `EXEMPT — <reason>` in the disposition. Staring is sufficient for
   these, but use the literal token so the omission of a probe is
   visible to the reader.

   When a probe is impractical (live prod infra, complex seed, multi-
   service orchestration): write `UNPROBED — <impracticality reason>`
   in the disposition, making the limitation explicit instead of
   pretending the trace is conclusive. The user gets to decide
   whether to invest in seeding before accepting/rejecting.

   Why this exists: the most expensive misses in this workflow have
   been cross-file mechanism claims where reading-the-code missed a
   detail that a 5-line probe would have surfaced in seconds. The
   bug-confirmation probe in `~/.claude/CLAUDE.md` "Probe Before
   Build" is the same discipline applied to *building*; this rule
   applies it to *evaluating bot findings*.

For each finding, output the disposition with its evidence:

### Accepted — real issue, will fix
For each: thread URL, file:line, the finding, evidence the issue is real
at HEAD, in-scope, with the mechanism traced. "In-scope" includes
pre-existing code in the path the PR is already touching (check 2), not
only code the PR introduced — fixing a related pre-existing bug belongs
here, not in a deferred ticket. For cross-file or runtime claims,
include the probe command and its actual output (or `UNPROBED` with the
impracticality reason).

### Rejected — unrelated pre-existing code (out of scope)
ONLY for pre-existing code the PR neither touches, calls, nor relies on.
For each: thread URL, file:line, the finding, the `git diff` check
showing the PR did not touch the cited path, AND a one-line note that
the change does not call or depend on the cited code — that absence of
dependency is what makes it unrelated rather than in-path. Pre-existing
code that sits in the path the PR is already touching (a helper the diff
calls, a function the diff edits, a query the new behavior relies on)
does NOT belong here: fix it under this PR and record it under
**Accepted** (check 2 above). Defer to a separate ticket only when the
code is genuinely unrelated to the PR's mission.

### Rejected — mechanism not present
For each: thread URL, file:line, the finding, what you traced (call
graph, state machine, or actual code path), what you found that
contradicts the bot's pattern-match. For runtime-behavior claims,
include the probe command and its actual output showing the absence
(or `UNPROBED` with the impracticality reason).

### Rejected — input unreachable
For each: thread URL, file:line, the finding, and the upstream
constraint that prevents the triggering input from arriving. Examples
of acceptable constraints to cite: a prompt that pins the shape, an
upstream validator that filters the field, a typespec or pattern-
matched function head that limits caller input, a schema-level
NOT NULL / type constraint. The mechanism IS present (3a passed);
the input that triggers it cannot arrive (3b failed). Per
`~/.claude/CLAUDE.md`, validation against unreachable scenarios is
over-engineering. Cite the constraint in the reply so a future
reader can verify.

### Nitpick — worth taking
For each: thread URL, file:line, why the change improves quality,
performance, or maintainability. Take nitpicks seriously
— "would this improve code quality, performance, or maintainability?"

### Outdated — code already changed
For each: thread URL, evidence the cited code path no longer matches.

### Informational
For each: thread URL, what it is, the planned acknowledgment.

## Recommended Actions

Ranked list — what to address, in order of priority:

```
1. <file:line>  <disposition>  <proposed change OR "reply only">
                <one-line rationale grounded in the evaluation above>
2. ...
```

This template makes no code changes itself — the evaluation is read-only.
What happens next is decided by the hand-off gate.

## Hand-off gate — auto-launch or ask

If the evaluation leaves a genuine question for the operator, STOP here and
put that question to them. If the only thing left would be a rhetorical
"how's this look?" — every disposition is high-confidence and nothing needs
the operator's judgment — automatically invoke `pr-respond-task` on the
Accepted findings instead of waiting. Its own autonomy gate then governs
whether the reply/amend/push tail runs without a further stop.

"No question for the operator" requires ALL of these — if any fails, STOP
and ask the specific question:

- Every disposition is high-confidence: each Accepted has a clear in-scope
  fix; each Rejected is a confident bot-rebuttal backed by a traced
  mechanism or probe — not a guess, not UNPROBED, not "I'm unsure."
- No finding needs a preference or design call — no borderline Nitpick
  offered as optional, no fix with more than one viable approach.
- No finding is deferred to a separate ticket — a deferral is a judgment
  for the operator to confirm.
- No new or unrelated issue surfaced that the operator would want raised
  separately.

A confident Rejected disposition is pushback to a *bot*, not to you, so it
does not by itself block the auto-launch — pr-respond-task posts the
rebuttal. Anything that is genuinely a question for *you* — an uncertain
call, a preference, a deferral — does block it.

## Notes on what this template does NOT do

- Does not push, commit, or amend itself — those happen only in the
  `pr-respond-task` it may hand off to, governed by that skill's gate.
- Does not post replies itself — reply posting happens in
  `pr-respond-task` after fixes land.
- Does not assume CI green = ready. Per Linear workflow, threads are
  the actionable signal; test status does not gate the evaluation.
- Chains to `pr-respond-task` only when the hand-off gate finds no
  operator question; otherwise each subsequent step needs its own
  invocation.
