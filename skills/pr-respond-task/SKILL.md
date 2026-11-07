---
name: pr-respond-task
description: Ships the branch back to an open pull request once the operator chooses to — drafts and posts a threaded reply to each review comment, refreshes the PR body against the commits, folds the cycle's commits into the commits they fix, and pushes with --force-with-lease. Runs only on the operator's own words to update the PR, after every legitimate finding has gone through retro, spec, build, demo, and retro again; it fixes nothing itself. Use when the operator says to answer the review comments, update the PR, or push the fixes back onto a PR branch.
---

# pr-respond-task — answer the review and update the PR

1. For the PR in $ARGUMENTS (or the current branch's PR if none specified), respond with the following sections in order, ending at the autonomy gate.
2. Fix nothing here: a legitimate review finding goes to `retro-task` and then `spec-task` (see `pr-feedback-task`, "Hand-off gate"), and the branch picks up its fix through the ordinary cycle.
3. Run only when the operator's own words say to update the PR.
4. Put actual tool output in each section, not paraphrased summaries.

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

1. If the working tree is not clean, STOP and report.
2. If an Accepted finding has no commit or no accepted demo behind it, STOP and report it; do not fix it here.

## Reply drafts

1. Write one reply per thread, fact-grounded, citing the mechanism, with no filler, from these templates:

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

2. Never reject pre-existing code that sits in the path the PR is already touching, such as a helper the diff calls, a function the diff edits, or a query the new behavior relies on; it is an Accepted finding under the in-path vs unrelated split in `pr-feedback-task` check 2.

```
Rejected — mechanism not present: traced <call graph / state machine>;
<what you found that contradicts the bot's pattern-match>.
```

```
Re-evaluated: not reproducible at HEAD. <what you observed running
the bot's stated reproduction>.
```

## Reply posting plan

1. For each draft reply, surface the exact `gh api` invocation that posts it:

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

2. Always pass `in_reply_to` for an inline reply, because without it the reply becomes a new top-level comment.

## PR body refresh

1. Read the body as it stands (`gh pr view <pr> --json body`) against the commits the branch now carries.
2. Rewrite any sentence the cycle made untrue, under `pr-create-task`, "Body — content discipline", and quote the code or test line behind each sentence that says what the change does.
3. Show the old and new body side by side, and apply it with `gh pr edit <pr> --body-file <tempfile>`.

## Fold plan

1. Before the push, fold each of the cycle's fix commits into the commit that owns the changed code, under `git-commit`, "Fixing work you already committed".
2. Never ask the operator "fix commit or amend?": always fold.

```
For each cycle commit, name the commit it folds into and the files it carries:
  <cycle commit sha + subject> -> <owning commit sha + subject>
    - <file 1>
```

3. Record `pre=$(git rev-parse HEAD)` before folding; afterwards `git diff "$pre" HEAD` must print nothing, and if it prints anything, stop and report the diff.
4. Push with `git push --force-with-lease`, never a bare `--force`.

## Final step — autonomy gate

1. Take the operator's words to update the PR as authority for this one update only: post the replies, apply the refreshed body, fold, and `git push --force-with-lease` without pausing, then report what was done.
2. Use that authority only when ALL of these hold:

- Every Accepted finding has a commit and a demo the operator accepted.
- Every reply answers its thread as drafted above; none declines a finding
  the operator accepted.
- The fold left the tree unchanged: `git diff "$pre" HEAD` printed nothing.
- Every sentence in the refreshed body has its code or test line.

3. If ANY is false, STOP and present the three actions for explicit authorization instead, each a separate decision, and do NOT chain them:

1. Posting each reply (or batch authorization for all drafted replies)
2. Applying the refreshed body
3. The fold and `git push --force-with-lease`

4. On BOTH paths, stage explicitly (never `git add -A`), fold into the owning commit (never a separate "fix review" commit), push with `--force-with-lease` (never bare `--force`), and go no further than reply, body, and push; merge and deploy are always separate operator decisions (the merge procedure below).

## Merge procedure (separate operator decision — never autonomous)

1. Never merge under the autonomy gate, because a merge lands on the default branch and can trigger the prod deploy.
2. Merge only when the operator asks, such as "merge with rebase and branch deletion; update local" or any equivalent go-ahead, and then run exactly:

   1. `gh pr merge <pr> --rebase --delete-branch` — rebase-merge, delete the
      remote and local branch.
   2. `git checkout <base> && git pull --ff-only` — update the local default
      branch to the merged commit.
   3. Verify: PR state `MERGED`, local `<base>` HEAD is the rebased commit,
      and the feature branch is gone locally.

3. Treat a merge approval as per-PR; it never carries to the next one.

## Notes on what this template does NOT do

- Does not fix a finding, run a review, or walk a demo. Those belong to the
  cycle: `retro-task`, `spec-task`, `tdd-cycle`, and `demo-task`.
- Does not run unless the operator said to update the PR, and does not
  offer to.
- Does not edit existing replies. New comments only, threaded via
  `in_reply_to`.
- Does not assume CI green / reviewers signed off / merge ready — merge
  gating is a separate decision.
