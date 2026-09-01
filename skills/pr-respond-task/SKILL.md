---
name: pr-respond-task
description: Fixes approved PR-feedback findings one at a time, each through its own probe → red → green → refactor cycle, then runs quick-review and security-review over the combined diff and surfaces a plan for the replies and commits; posts, amends and pushes with --force-with-lease when nothing is left for the operator to decide, else stops for approval. Use when acting on PR review comments, fixing what a reviewer asked for, or pushing fixes back onto a PR branch.
---

# pr-respond-task — fix approved PR-feedback findings via probe-first TDD

For the PR in $ARGUMENTS (or the current branch's PR if none specified)
and the approved Accepted findings provided by the user (or carried
from a prior `pr-feedback-task` run), respond with the following
sections in order, ending at the autonomy gate: when nothing is left
for the operator to decide, you are authorized to post the replies,
amend each fix, and `git push --force-with-lease` without pausing;
otherwise stop at the plans and wait for explicit per-action approval.
The final section defines what "nothing to decide" requires.

The output discipline is structural: each section contains actual tool
output, not paraphrased summaries. Per-finding micro-cycles must be
complete (probe, red, green, refactor, reply draft all present) before
the combined-diff reviews run.

## Preconditions

```
PR identifier:  <gh pr view --json number,headRefName,baseRefName,url>
Repo:           <gh repo view --json nameWithOwner>
Base ref:       <baseRefName>
Working tree:   <git status --porcelain — must be clean before starting>
Approved findings (from operator or pr-feedback-task output):
  1. <thread URL, file:line, one-line claim, comment_id>
  2. ...
```

If the working tree is not clean, STOP and report — do not begin fixes
on top of uncommitted changes.

## Per-finding micro-cycles

For each Accepted finding, in order, run the full `tdd-cycle` discipline
(probe → gray → red → green → refactor). Each finding gets its own
sub-section with the same structural headers — *no skipping, even on
"obvious" one-line fixes*. The headers exist precisely because
"obvious" is where shortcuts hide.

### Finding `<N>` of `<TOTAL>` — `<thread URL or file:line>`

Bot's claim (verbatim from the inventory): `<one line>`.

#### Static reads (scope + code at HEAD)

These are static-artifact reads that confirm what the code SAYS. They
do not measure what the running system DOES. Paste the actual output,
not a paraphrase.

- `git diff <base>..HEAD -- <file>` — confirm the fix touches code this
  PR actually owns
- The current state of the cited code path at HEAD (`Read` or
  `sed -n '<line-5>,<line+10>p' <file>`)

#### Probe

A Probe is a runtime observation — of a boundary you don't own, an
algorithm or logic whose behavior you haven't measured, or any
runtime behavior the finding claims. The body of this section MUST
contain BOTH (a) the literal command, query, or snippet that ran AND
(b) the actual captured output from running it. File reads, diff
reads, grep output, and prose paraphrases of what you observed are
NOT probes — they belong above under "Static reads." If the body of
this section does not contain both a command and its captured output,
the section label is wrong: either run the probe or replace the
section body with one of the explicit disposition states below.

For algorithmic or logic findings, the probe IS the proof of
legitimacy. Don't trust your memory of an API's behavior, the
library docs, or pattern-matching on a familiar shape — verify with
a light test. The discipline is the same one an experienced
developer applies to their own work: rarely trust APIs or your own
expertise; manually test with curl, snippets, or one-off scripts
while investigating.

Acceptable probes: a `curl` + the returned JSON, a SQL query and its
returned rows, an IEx session, a `mix run -e "..."` snippet, a one-
off test that exercises the actual path. The probe is throwaway; its
output becomes the [REF] that anchors the Red and Green steps below.

When a probe is impractical (live prod infra, complex seed, multi-
service orchestration): write `UNPROBED — <impracticality reason>`.
The user gets to decide whether to invest in seeding before accepting
the finding.

When the finding is pure syntactic (formatting, name choice, unused
var, comment typo) and crosses no boundary, algorithm, or logic
claim: write `EXEMPT — <reason>`.

Both `UNPROBED` and `EXEMPT` are honest disposition states. Staging
static reads under the Probe label — or writing prose under it that
describes code you read rather than output you measured — is the
failure mode this section's structure exists to prevent.

Without this section's output (or an explicit `UNPROBED` / `EXEMPT`
line), the next two sections are invalid by construction — the test
in Red would be encoding an assumption rather than an observation.
See `writing-code`, "Probe before you build".

#### Red — write the test (Gray) and run it (Red)

The test asserts the *desired* post-fix behavior at the boundary you
just probed. It must fail against the current code for the *specific*
reason the bot identified — not for a coincidental reason like "module
not loaded."

```
<test diff>
<runner output showing red, including the assertion that failed>
```

If the test passes immediately, the bug claim was wrong or already
fixed — STOP, mark the finding **Re-evaluated: not reproducible**,
draft a reply explaining what you observed at HEAD, and move to the
next finding without changing code.

#### Green — minimum implementation

```
<implementation diff>
<runner output showing green>
```

#### Refactor — structure only

Per `tdd-cycle` step 3:

- **Dead code the fix orphaned.** Remove now-unreachable branches,
  helpers the fix left with no caller, commented-out blocks it
  stranded. Collapsing duplication and polishing names is not this
  pass — the `quick-review` that follows owns those.
- **Hindsight Open-Closed (in retrospect).** Count *modifications to
  existing files* this fix required. If adding this case forced
  lockstep edits across many existing files (dispatcher + call sites
  + tests + docs), AND you can name the next concrete case that will
  land against the same shape, lift to a registry / behaviour /
  dispatch table where new cases register themselves. Do not lift
  speculatively — only when (a) the lockstep pattern is observable
  and (b) the next case has a name.
- **Re-run tests.** Refactor must keep green.

State explicitly:
```
Dead code:       <none | <what was removed>>
Hindsight OCP:   <none | <which lift; named follow-on: <name>>>
Re-ran tests:    <pass | fail>
```

#### Self-review (tdd-cycle step 4)

Close both gates against this micro-cycle's diff:

- 4a assertion strength — mutate the production value, re-run, confirm the test goes red
- 4b scope — no drive-by refactors; every file in the diff required by this finding

Doc and code agreeing, sibling symmetry, failure-path coverage and behavioral
regression are not re-walked here — the combined-diff `quick-review` below owns them.

Either gate failing → return to Red or Refactor before continuing.

#### Reply draft (NOT posted)

Fact-grounded, cites the mechanism, no filler. Templates:

```
Fixed: <one-line mechanism statement, e.g. "added null guard at
        Foo.bar/2 before the bang call; failing case now returns
        {:error, :missing_x} which the caller already handles">.
```

```
Rejected — unrelated pre-existing code: git diff <base>..HEAD -- <path>
confirms this PR's diff does not touch the cited path, and the change
neither calls nor relies on it; the issue, if real, predates this PR
and is unrelated to its mission.
```

(Pre-existing code that sits in the path the PR is already touching — a
helper the diff calls, a function the diff edits, a query the new behavior
relies on — is NOT rejected here. Fix it under this PR; see the in-path vs
unrelated split in `pr-feedback-task` check 2.)

```
Rejected — mechanism not present: traced <call graph / state machine>;
<what you found that contradicts the bot's pattern-match>.
```

```
Re-evaluated: not reproducible at HEAD. <what you observed running
the bot's stated reproduction>.
```

(Repeat the full sub-section for each Accepted finding.)

## Reviews on the combined diff

After every per-finding cycle is complete, run both reviews against
the working tree (per `writing-code`, "After the edit: the review
sequence is owed"):

1. `quick-review` against the combined diff
2. `security-review` against the combined diff

Then work `quick-review`'s "Re-review and the fix loop" over the
findings. It owns naming what actually runs each finding, the Yes-to-any
gate a fix has to clear, and when the loop counts as finished. Record a
finding you are not fixing in the PR thread, with one line saying why.

State the loop outcome:
```
quick-review:    <PASS | N findings, P fixed in loop, R deferred>
security-review: <PASS | N findings, P fixed in loop, R deferred>
Loops:           <count>
```

## Reply posting plan (NOT executed)

For each draft reply, surface the exact `gh api` invocation that would
post it. **Do not execute.** Verified syntax from `respond-all` Phase 6
(`legends-agent-skills/skills/respond-all/SKILL.md:127-143`):

```bash
# In-thread reply to an inline review comment:
gh api repos/<owner>/<repo>/pulls/<pr>/comments \
  --method POST \
  --field body="<draft body>" \
  --field in_reply_to=<original_comment_id>

# Reply to general PR conversation (issue comments):
gh api repos/<owner>/<repo>/issues/<pr>/comments \
  --method POST \
  --field body="<draft body>"
```

`in_reply_to` is mandatory for inline replies — without it, the reply
becomes a new top-level comment instead of threading.

## Amend plan (NOT executed)

Fixes are **amended into the commit that owns the changed code**, never
appended as a separate "fix review feedback" commit. Git is a documentation
system: each commit in a branch is a section of an essay written for the
next reader. A standalone fix commit is a chronology artifact ("I wrote a
bug, then patched it") that buries the real structure and tells the future
reader nothing they want. Fold the fix in so the section reads as the
feature done correctly. **Do not ask the operator "fix commit or amend?" —
the answer is always amend.**

```
For each fix, name its owning commit and the files it stages:
  <fix> -> <commit sha + subject>
    - <file 1>
    - <file 2>
```

Staging is explicit (never `git add -A` / `git add .` — and never the
known junk files). Keep the commit's message unless the fix changes what
the section claims; when it does, re-author through `git-commit`, otherwise
`--amend --no-edit`.

**Mechanics** (the Bash tool blocks `rebase -i` / `add -p`, so use these):
- Owning commit is HEAD → stage its files, `git commit --amend`.
- Owning commit is buried → `git stash push -- <that fix's files>`,
  `git checkout <commit>` (detached), `git stash pop`, stage,
  `git commit --amend`, capture the new sha, then
  `git rebase --onto <new-sha> <old-sha> <branch>` to replay the rest.
- Verify before pushing: `git diff <backup-pre-amend> HEAD` must equal
  EXACTLY the fixes and nothing else. The branch is a pre-push check, not
  an artifact for the operator to inspect — the instant that diff confirms
  only the intended fixes, delete it (`git branch -D backup-pre-amend`).
  The pre-amend commit remains in the reflog if recovery is ever needed.
- Amending rewrites already-pushed history, so the push is
  `git push --force-with-lease` (never a bare `--force`).

## Final step — autonomy gate

After the plans above, decide whether anything is left for the operator
to weigh. If NOTHING is, you are authorized to execute the whole tail —
post the replies, amend each fix into its owning commit, and
`git push --force-with-lease` — without pausing, then report what was
done. This is the operator's explicit, durable grant: it overrides the
global `~/.claude/CLAUDE.md` "fresh per-action authorization" default for
THIS bounded, decision-free case only, and matches how the task is run in
practice.

"Nothing to decide" requires ALL of these to hold — if any is false, the
gate fails:

- Every operator-Accepted finding was fixed as accepted — none flipped to
  Rejected, not-reproducible, or only partially fixed (a decline overrides
  what you approved: that is pushback to you, and it fails the gate).
- The combined quick-review AND security-review are clean on the current
  tree, with no finding deferred rather than fixed.
- Replies post autonomously whether they confirm a fix (`Fixed:
  <mechanism>`) or rebut a review bot — pushback to a *bot* needs no
  sign-off. The gate concerns only pushback to *you*: if probing flips an
  Accepted finding into a decline (Rejected / not-reproducible / partial),
  that overrides what you approved, so the first condition fails and the
  agent surfaces it to you rather than posting.
- The fixes changed only what was accepted — none introduced an
  externally-observable behavior change the operator has not seen.
- The amend verification passed: `git diff <backup-pre-amend> HEAD`
  equals EXACTLY the fixes (then the backup branch is deleted).
- No new ticket-worthy issue surfaced during the cycles.

If ANY is false, STOP and present the three actions for explicit
authorization instead — each a separate decision, do NOT chain them:

1. Posting each reply (or batch authorization for all drafted replies)
2. Amending each fix into its owning commit (see Amend plan above)
3. `git push --force-with-lease` (amends rewrite already-pushed history)

The safety invariants hold on BOTH paths: explicit staging (never
`git add -A`), amend into the owning commit (never a separate "fix
review" commit), `--force-with-lease` (never bare `--force`), and the
autonomy never extends past reply/amend/push — merge and deploy are
always separate operator decisions (the merge procedure below).

## Merge procedure (separate operator decision — never autonomous)

Merge is never part of the autonomy gate: it lands on the default branch
and, in this codebase, triggers the prod deploy. So once the PR is green
and its feedback is resolved, OFFER the merge as a plain yes/no rather than
making the operator spell out the steps. The operator's standing phrasing
for this procedure is "merge with rebase and branch deletion; update local"
(or any equivalent go-ahead) — and a "yes" to the offer is the same
approval.

On approval, run exactly:

1. `gh pr merge <pr> --rebase --delete-branch` — rebase-merge, delete the
   remote and local branch.
2. `git checkout <base> && git pull --ff-only` — update the local default
   branch to the merged commit.
3. Verify: PR state `MERGED`, local `<base>` HEAD is the rebased commit,
   and the feature branch is gone locally.

A merge approval is per-PR — it never carries to the next one.

## Notes on what this template does NOT do

- Auto-executes the reply/amend/push tail only when the autonomy gate
  finds nothing for the operator to decide; otherwise each action is a
  separate authorization.
- Does not run on findings that haven't been Accepted by the operator
  (typically via `pr-feedback-task` output).
- Does not chain to any other template. If a fix surfaces a deeper
  issue or a separate ticket-worthy finding, surface it as a TODO and
  let the operator decide.
- Does not edit existing replies. New comments only, threaded via
  `in_reply_to`.
- Does not assume CI green / reviewers signed off / merge ready —
  threads being addressed is the actionable signal; merge gating is a
  separate decision.
