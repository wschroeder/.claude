---
name: pr-feedback-task
description: Gathers every source of feedback on a pull request and works out which of it is right — readiness gate, feedback inventory, legitimacy evaluation, recommended actions — then treats the review as a demo given to outside reviewers: any legitimate finding ends the PR work and goes to `retro-task`, which hands it on to `spec-task`. Fixes nothing itself. Use when triaging or working through PR review comments, checking what reviewers asked for, or deciding which feedback to act on — "what's blocking the PR", "go through the PR comments", "address the review".
---

# pr-feedback-task — check readiness, evaluate legitimacy

1. For the PR feedback task in $ARGUMENTS, or the current branch's PR if none is named, respond with the following sections in order.
2. Produce the evaluation through Recommended Actions, then reach the hand-off gate, which sends any legitimate finding back through the cycle.
3. Put actual tool output in each section, not paraphrased summaries; a missing, hollow, or out-of-order section is an invalid output.

## Readiness Check

1. Surface the state of every feedback source. Use:

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

2. Report:

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

1. Paste raw output, not paraphrased, from all three sources:

```
gh api repos/{owner}/{repo}/pulls/<pr>/comments    # inline review comments
gh api repos/{owner}/{repo}/pulls/<pr>/reviews     # top-level review bodies
gh api repos/{owner}/{repo}/issues/<pr>/comments   # general PR conversation
```

2. For each thread, surface: file:line, author (CodeRabbit / Cursor Bugbot / human reviewer / other), body, `in_reply_to_id`, `isResolved`, and `isOutdated`.
3. Skip resolved and outdated threads from evaluation, but list them in the inventory so the count reconciles.

## Legitimacy Evaluation

1. **Bot findings are HYPOTHESES, not facts.** For each unresolved non-outdated thread, apply the five checks below before assigning a disposition.
2. **The bot's severity label carries zero weight — never record it, never anchor to it.** Do not write "stated Major" or quote the bot's rating in your output.
3. After you have traced legitimacy and scope yourself, assign the real priority from the actual consequence and who it reaches, overriding the bot freely in either direction, and state your own severity with the reasoning that earned it.

The five checks:

1. **Read the current code at HEAD yourself.** Do not trust the bot's
   quoted snippet; if the code at HEAD no longer has the issue, record the
   finding as Outdated with the evidence.
2. **Confirm the finding is in this PR's mission scope.** Run
   `git diff <base>..HEAD -- <file>` and verify whether the diff
   touches the cited code path. Expect three outcomes:

   - **The PR introduced the cited code.** In scope. Evaluate it with
     the mechanism and reachability checks below.
   - **The PR did not introduce the cited code, but the code sits in
     the path the PR is already touching**, such as the same function the
     diff edits, a helper the changed code calls, or a query whose result
     the PR's new behavior now relies on. Record it under **Accepted**,
     never Rejected, because the operator does not defer related work.
   - **The PR did not introduce the cited code AND the code is
     unrelated to anything the PR touches**, such as a different module,
     an untouched call path, or code the change neither calls nor depends
     on. Only this case takes **Rejected — unrelated pre-existing code**.
     Make the reply cite the diff check AND state the lack of
     dependency ("git diff confirms this PR's diff does not touch the
     cited path, and the change neither calls nor relies on it; the
     issue, if real, predates this PR and is unrelated to its
     mission").
3. **Verify the mechanism in this instance**, with two separate checks:

   **(a) Syntactic mechanism — does the code do what the bot says?**
   Trace the call graph or state machine, and reproduce the failure where
   possible. If the code doesn't do what the bot describes, the finding
   is **Rejected — mechanism not present**.

   **(b) Reachability — does the triggering input actually arrive?**
   Ask where the triggering input comes from and what limits its shape,
   such as a prompt that constrains an LLM-output parser, an upstream
   validator, a caller's contract, or a field's typespec. If upstream
   constraints make the input unreachable, the finding is **Rejected —
   input unreachable**, because validation belongs only at system
   boundaries. Make the reply name the upstream constraint, not "mechanism
   not present".

   Never treat a probe that confirms (a) as establishing (b).

4. **Distinguish bot pushback from operator pushback.** Treat a bot's
   reply that re-asserts its original concern without new evidence as a
   hypothesis, re-evaluate with the three checks above, and do not
   capitulate to repeated assertions.
5. **Probe the mechanism whenever the finding spans a module boundary,
   questions an algorithm or logic, or claims runtime behavior.**
   Count as a probe only something that ran on this machine in the last
   few minutes and produced output now in the chat, such as a
   `mix run -e "..."` snippet, an IEx session, a one-off test that
   exercises the actual path, or a curl with saved JSON; reading the file
   at HEAD is not a probe. Paste the probe command AND its real output,
   and cite that output as a [REF] in the disposition.

   For algorithmic or logic findings, make the probe the proof of
   legitimacy rather than your memory of an API, the library docs, or a
   familiar shape.

   If no boundary is crossed, as with formatting, import order, an unused
   var, a comment typo, or a name choice, write `EXEMPT — <reason>` in the
   disposition.

   If a probe is impractical, as with live prod infra, a complex seed, or
   multi-service orchestration, write `UNPROBED — <impracticality reason>`
   in the disposition, and let the user decide whether to invest in
   seeding before accepting or rejecting.

For each finding, output the disposition with its evidence:

### Accepted — real issue, in scope
1. Give the thread URL, file:line, the finding, evidence the issue is real at HEAD, its scope, and the mechanism traced.
2. Count as in scope pre-existing code in the path the PR is already touching (check 2), and send it on with the PR's other findings rather than to a deferred ticket.
3. For cross-file or runtime claims, include the probe command and its actual output, or `UNPROBED` with the impracticality reason.

### Rejected — unrelated pre-existing code (out of scope)
1. Use this ONLY for pre-existing code the PR neither touches, calls, nor relies on.
2. Give the thread URL, file:line, the finding, the `git diff` check showing the PR did not touch the cited path, AND a one-line note that the change does not call or depend on the cited code.
3. Record pre-existing code in the path the PR is already touching under **Accepted** instead (check 2 above), and defer to a separate ticket only when the code is unrelated to the PR's mission.

### Rejected — mechanism not present
1. Give the thread URL, file:line, the finding, what you traced (call graph, state machine, or actual code path), and what you found that contradicts the bot's pattern-match.
2. For runtime-behavior claims, include the probe command and its actual output showing the absence, or `UNPROBED` with the impracticality reason.

### Rejected — input unreachable
1. Give the thread URL, file:line, the finding, and the upstream constraint that prevents the triggering input from arriving, such as a prompt that pins the shape, an upstream validator that filters the field, a typespec or pattern-matched function head, or a schema-level NOT NULL or type constraint.
2. Use this only where 3a passed and 3b failed.
3. Cite the constraint in the reply so a future reader can verify it.

### Nitpick — worth taking
1. Give the thread URL, file:line, and which axis of `quick-review`'s Yes-to-any gate the change improves.
2. If `quick-review` has not been loaded this session, read the "Yes-to-any gate" section of `skills/quick-review/SKILL.md`.
3. Treat a nitpick that clears the gate as a finding, not a preference.

### Outdated — code already changed
1. Give the thread URL and evidence the cited code path no longer matches.

### Informational
1. Give the thread URL, what it is, and the planned acknowledgment.

## Recommended Actions

1. Rank what to address, in order of priority:

```
1. <file:line>  <disposition>  <proposed change OR "reply only">
                <one-line rationale grounded in the evaluation above>
2. ...
```

2. Make no code changes; the evaluation is read-only, and the hand-off gate decides what happens next.

## Hand-off gate — back through the cycle

1. Treat a PR review as a demo given to people outside the team and its comments as that demo's feedback.
2. End the PR work on any legitimate finding, whatever its size, whether a comment, a name, a lint fix, or a bug.
3. If the evaluation leaves a genuine question for the operator, such as an uncertain disposition, UNPROBED, a preference, a fix with more than one viable approach, or a deferral, STOP and ask that question first.
4. Then, if any finding is Accepted or a Nitpick worth taking, invoke `retro-task` on them in the same turn, passing the inventory and every disposition with its evidence.
5. Say nothing about updating the PR.
6. If no finding is legitimate, report that and stop, and leave the rebuttal replies to `pr-respond-task`, which runs only when the operator says to update the PR.

## Notes on what this template does NOT do

- Does not fix, commit, amend, push, or post a reply.
- Does not raise, propose, or schedule an update to the PR. The operator
  chooses when to ship.
- Does not assume CI green = ready. Per Linear workflow, threads are
  the actionable signal; test status does not gate the evaluation.
