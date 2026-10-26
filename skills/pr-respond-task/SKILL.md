---
name: pr-respond-task
description: Ships the branch back to an open pull request once the operator chooses to — drafts and posts a threaded reply to each review comment, refreshes the PR body against the commits, folds the cycle's commits into the commits they fix, and pushes with --force-with-lease. Runs only on the operator's own words to update the PR, after every legitimate finding has gone through retro, spec, build, demo, and retro again; it fixes nothing itself. Use when the operator says to answer the review comments, update the PR, or push the fixes back onto a PR branch.
---

# pr-respond-task — answer the review and update the PR

For the PR in $ARGUMENTS (or the current branch's PR if none specified),
respond with the following sections in order, ending at the autonomy gate.

This skill fixes nothing. A legitimate review finding goes to `retro-task`
and then `spec-task` (see `pr-feedback-task`, "Hand-off gate"), and the
branch picks up its fix through the ordinary cycle. This skill runs
afterwards, and only when the operator says to update the PR: their words
for this update are what start it, and nothing else does.

The output discipline is structural: each section contains actual tool
output, not paraphrased summaries.

## Preconditions

```
PR identifier:  <gh pr view --json number,headRefName,baseRefName,url>
Repo:           <gh repo view --json nameWithOwner>
Base ref:       <baseRefName>
Working tree:   <git status --porcelain — must be clean before starting>
Operator's words to update the PR: <quoted, with timestamp>
Findings and their dispositions (from pr-feedback-task output):
  1. <thread URL, file:line, one-line claim, comment_id, disposition>
  2. ...
For each Accepted finding, the cycle that answered it:
  1. <the commit that fixes it, and the demo where the operator accepted it>
```

If the working tree is not clean, STOP and report. If an Accepted finding
has no commit or no accepted demo behind it, STOP and report it: the cycle
has not finished with it, and this skill does not fix it here.

## Reply drafts

One reply per thread, fact-grounded, citing the mechanism, no filler.
Templates:

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
relies on — is NOT rejected here. It is an Accepted finding; see the
in-path vs unrelated split in `pr-feedback-task` check 2.)

```
Rejected — mechanism not present: traced <call graph / state machine>;
<what you found that contradicts the bot's pattern-match>.
```

```
Re-evaluated: not reproducible at HEAD. <what you observed running
the bot's stated reproduction>.
```

## Reply posting plan

For each draft reply, surface the exact `gh api` invocation that posts it:

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

## PR body refresh

Read the body as it stands (`gh pr view <pr> --json body`) against the
commits the branch now carries. Rewrite any sentence the cycle made untrue,
under `pr-create-task`, "Body — content discipline", and quote the code or
test line behind each sentence that says what the change does. Show the old
and new body side by side. Apply it with
`gh pr edit <pr> --body-file <tempfile>`.

## Fold plan

The cycle committed its fixes as new commits. Before the push, fold each one
into the commit that owns the changed code, under `git-commit`, "Fixing work
you already committed", so the history reads as the feature done correctly
rather than as a chronology. Do not ask the operator "fix commit or amend?":
the answer is always fold.

```
For each cycle commit, name the commit it folds into and the files it carries:
  <cycle commit sha + subject> -> <owning commit sha + subject>
    - <file 1>
```

Record `pre=$(git rev-parse HEAD)` before folding. A fold never changes the
final tree, so `git diff "$pre" HEAD` prints nothing afterwards; if it prints
anything, stop and report the diff. The branch is already on a remote, so the
push is `git push --force-with-lease` (never a bare `--force`).

## Final step — autonomy gate

The operator's words to update the PR authorize this one update: post the
replies, apply the refreshed body, fold, and `git push --force-with-lease`
without pausing, then report what was done. They do not carry to the next
update.

They cover the tail only when ALL of these hold — if any is false, the gate
fails:

- Every Accepted finding has a commit and a demo the operator accepted.
- Every reply answers its thread as drafted above; none declines a finding
  the operator accepted.
- The fold left the tree unchanged: `git diff "$pre" HEAD` printed nothing.
- Every sentence in the refreshed body has its code or test line.

If ANY is false, STOP and present the three actions for explicit
authorization instead — each a separate decision, do NOT chain them:

1. Posting each reply (or batch authorization for all drafted replies)
2. Applying the refreshed body
3. The fold and `git push --force-with-lease`

The safety invariants hold on BOTH paths: explicit staging (never
`git add -A`), fold into the owning commit (never a separate "fix
review" commit), `--force-with-lease` (never bare `--force`), and the
autonomy never extends past reply, body, and push — merge and deploy are
always separate operator decisions (the merge procedure below).

## Merge procedure (separate operator decision — never autonomous)

Merge is never part of the autonomy gate: it lands on the default branch
and, in this codebase, triggers the prod deploy. Merge only when the
operator asks; their standing phrasing for this procedure is "merge with
rebase and branch deletion; update local" (or any equivalent go-ahead).

On approval, run exactly:

1. `gh pr merge <pr> --rebase --delete-branch` — rebase-merge, delete the
   remote and local branch.
2. `git checkout <base> && git pull --ff-only` — update the local default
   branch to the merged commit.
3. Verify: PR state `MERGED`, local `<base>` HEAD is the rebased commit,
   and the feature branch is gone locally.

A merge approval is per-PR — it never carries to the next one.

## Notes on what this template does NOT do

- Does not fix a finding, run a review, or walk a demo. Those belong to the
  cycle: `retro-task`, `spec-task`, `tdd-cycle`, and `demo-task`.
- Does not run unless the operator said to update the PR, and does not
  offer to.
- Does not edit existing replies. New comments only, threaded via
  `in_reply_to`.
- Does not assume CI green / reviewers signed off / merge ready — merge
  gating is a separate decision.
