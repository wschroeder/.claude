---
name: git-commit
description: Enforces git commit conventions and authors commit messages — staging rules, subjects matched to the repository's own log, message-body authoring, no AI attributions, when to amend instead of adding a follow-up commit, and safety checks. Use whenever committing, amending, pushing, branching, OR drafting/proposing a commit message — even speculatively, before authorization.
---

## When to invoke

**This skill owns commit-message authoring.** The moment you start composing a commit subject or body — even a draft, even before the user has approved the commit — invoke this skill instead of writing the message in chat or a temp file.

**For pull request descriptions, use the `pr-create-task` skill.** It carries these same body principles (WHY over HOW, no restated diffstat, no current-session framing) to PR bodies — where they were previously unwritten — and walks PR creation end to end with a stop for approval before the push. The moment you start composing a PR body or reach for `gh pr create`, route there.

## Git Staging Rules

**Never use `git add -A`** - it stages everything including untracked files you may not want.

Instead use:
- `git add -u` - stage only tracked files that have been modified/deleted
- `git add <specific files>` - explicitly name the files to stage

**Where a tool writes tracked files as a side effect of your work, stage by
path.** `git add -u` takes every tracked modification, including an audit
trail or export the tool rewrote while you were working, and those land in
a commit that does not describe them. Measured: `bd close` writes
`.beads/interactions.jsonl`, and because the close follows the commit, nine
consecutive card commits in one run each carried the previous card's close
record.

## Commit Messages

**The subject follows the repository, not a house style.** Read the log before
writing one:

```bash
git log --format='%s' -20
```

Match what those subjects do: a `<type>(<scope>):` prefix if they carry one, a
plain sentence if they do not, and their capitalization, tense and length either
way. Where the log is empty or shows no pattern, write a plain sentence saying
what the change does, and say in one line that there was nothing to match.

Only the subject follows the repository. Everything under Body Content holds
everywhere.

**Guidelines:**
- Focus on WHY, not HOW - the code shows the how
- **NEVER include AI attributions** - no "Co-Authored-By: Claude", no "Generated with Claude Code", no "via Happy", nothing. Clean commits only.

## Body Content

The subject line goes in the header. The body is for the WHY — design decisions, rejected alternatives, and mandatory constraints. The diff already shows what changed; the body records what the diff cannot.

**Structure:** each body paragraph answers one of:
- What was wrong with the prior state ("the legacy bearer had no refresh path…")
- What the new approach gets that the old couldn't ("library-backed flow gets us token rotation, RFC 7009 revocation…")
- Why a tempting alternative was rejected ("replacing those would have been UX and security regressions…")
- Why something that looks optional is actually mandatory ("…preconditions for partner-facing rollout, not optional polish")

**Lead with replacement framing, not action narration.**

BAD: `Wires per-IP rate limiting on the three POST endpoints and revokes the descendant chain on refresh-token reuse`
GOOD: `Per-IP rate limiting and RFC 6749 §10.4 chain revocation land here because client-secret brute-force defense and refresh-reuse detection are preconditions for partner-facing rollout, not optional polish.`

BAD: `Adds /oauth/refresh and /oauth/revoke endpoints and configures ex_oauth2_provider in the :lol_user_oauth otp_app config`
GOOD: `Replace the hand-rolled Phoenix.Token bearer envelope at /oauth/token with library-backed OAuth2 (ex_oauth2_provider). The legacy bearer had no refresh path, no real revocation, and pinned token lifetime to the cookie session.`

**What belongs in the body:**
- High-level surface area: affected route names, public modules, external contracts, RFC references
- Constraints that look optional but aren't, with the reason

**What does NOT belong in the body:**
- Action narration ("wires", "adds", "implements") — readable from `git show`
- Internal mechanism names that may rot: config block names, private helper names, file paths
- Restated diffstat content
- Current-session framing — the mission, investigation, or task you happen to be in the middle of. A trailing "this is part of fixing X" or "doesn't touch the Y we're chasing" sentence is the tell; delete it. Every sentence must stand on its own years later, with no knowledge of today's work.

**Length:** as long as needed for the WHY, no longer. Trivial diffs warrant a one-line subject and no body. Multi-paragraph bodies are appropriate when there are real design decisions worth recording.

## Fixing work you already committed

When you fix something a commit on this branch already covers, fold the fix into that commit with `git commit --amend` rather than adding a separate `fix: address review feedback` commit. Each commit is a section of an essay written for the next reader. A standalone follow-up commit records the chronology of your mistakes — "I wrote a bug, then patched it" — and buries the structure the reader actually wants.

**Check whether the commit has reached a remote before you decide.** Run `git branch -r --contains HEAD`. It lists the remote branches carrying that commit, and prints nothing while still exiting 0 when no remote has it. Do NOT reach for `git log @{u}..HEAD` — it aborts with `fatal: no upstream configured for branch '<name>'` on a branch that was never pushed, which is exactly the case you are trying to detect. (The check reads remote-tracking refs, so `git fetch` first if the branch may have been pushed from somewhere else.)

- **No remote has it** — amend. Nobody else can hold the old commit, so rewriting it costs nothing and the eventual push is an ordinary push. This is the default; do not ask the user to choose between a follow-up commit and an amend when the commit is unpushed.
- **A remote already has it** — amending rewrites published history, so the push becomes `git push --force-with-lease` (never a bare `--force`). On your own PR branch that is still the right call, and the `pr-respond-task` skill drives it. On a branch someone else may have pulled, add a new commit instead.

Stage explicitly, the same as any other commit — never `git add -A`. Keep the existing message unless the fix changes what that commit claims; when it does, re-author the message through this skill, otherwise use `git commit --amend --no-edit`.

**Amending an unpushed commit needs no approval. Amending a pushed one does.** The `git branch -r --contains HEAD` check above is what tells them apart. While it prints nothing, the amend is covered by the standing permission in Safety below — make it and move on. Once a remote carries the commit, the next push becomes `git push --force-with-lease`, and no standing permission reaches a push: stop, say what the amend would rewrite, and wait.

## Safety

- **Committing and amending carry standing permission. Pushing and deploying never do.** Commit when a piece of work is finished, and amend an unpushed commit, without asking first. Push, force-push, `--force-with-lease` push, and deploy each need the user's words for that specific action, every time. Do not chain commit → push → deploy on momentum: the momentum stops at the push.
- **A repository's own CLAUDE.md can grant standing permission for a deploy to a target it names.** Read the project instructions in front of you before you stop to ask: where they name the service and say a deploy to it carries standing permission, that grant holds, and asking again is the error. It reaches the target it names and nothing else — a push to a git remote still needs the user's words, and so does a deploy anywhere else. Measured: a build loop halted on the rule above and sat idle for 23 minutes waiting for an answer the operator had already settled.
- **Approval from earlier in the session does not transfer to a push.** If the user said "Push" an hour ago, that authorized THAT push — not this one. Ask again.
- **"Apply the fixes" is not "push".** Applying fixes means writing them to the working tree, and committing them is already covered. Putting them on a remote is a separate decision with its own authorization; do not batch the two into one proposal.
- **"The commit is correct so the push is fine" is not a reason.** The question is never whether the code is right; it is whether the process was followed. A technically-correct push that skipped the review sequence in `writing-code` is a process violation, not a neutral outcome.
- Never run destructive commands (`push --force`, `reset --hard`) without explicit confirmation
- Never skip hooks (`--no-verify`) unless explicitly requested
- Verify with `git status` and `git diff` before committing

If you find yourself writing "amended and pushed" in a summary without the user having explicitly said "push" AFTER the change was made AFTER the reviews completed, stop — you shortcut the user. Revert or surface what happened before any further work.
