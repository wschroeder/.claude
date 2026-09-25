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

**The subject follows the repository, not a house style.** Read enough of the
log to see its established style, not only its latest run:

```bash
git log --no-merges --format='%s' -60
```

Match what those subjects do: a `<type>(<scope>):` prefix if they carry one, a
plain sentence if they do not, and their capitalization, tense and length either
way. Where the log is empty or shows no pattern, write a plain sentence saying
what the change does, and say in one line that there was nothing to match.

**Where the recent subjects break from the older ones, match the older ones.** A
run of recent commits can be one session's habit rather than the repository's
style. A commit message the operator wrote or reworded themselves outranks the
log: it sets the pattern for every commit after it, subject and body alike.

Only the subject follows the repository. Everything under Body Content holds
everywhere.

**NEVER include AI attributions** - no "Co-Authored-By: Claude", no "Generated with Claude Code", no "via Happy", nothing. Clean commits only.

## Body Content

**The body records what the diff cannot show.** Most commits need only the
subject. Write a body only when the change carries something neither the
subject nor the diff can show.

**On a small commit, the diff shows what changed, so the body is the why:** the
reason for the change, a decision behind it, or a constraint that looks optional
and is not. Where there is no reason beyond the subject, write no body.

**On a large feature, the diff is too big to read the change from, so open with
one or two sentences saying what it is and does.** Then give the major decisions
and the reasons behind them.

**When there is a body, make it as short as it can reasonably be.** Aim for
about 100 words on a feature. Treat that as a target to check against, not a
limit to fill: a body that runs past it is usually carrying something from the
list below.

**A why has to be a real reason.** "Nothing measured X" or "X had no rules
written down" restates the feature as a gap and gives no reason for it. A fix
names what was broken, because for a fix that is the reason.

BAD: `Nothing measured how the importer handles real uploads, so nobody knew how many needed a person.`
GOOD: `The harness runs real uploads through the importer and reports how many went through without a person, compared against the hand-kept ledger.`

BAD: `Wires per-IP rate limiting on the three POST endpoints and revokes the descendant chain on refresh-token reuse`
GOOD: `Per-IP rate limiting and refresh-token chain revocation are preconditions for partner-facing rollout, not optional polish.`

**Record the major decisions, and leave out the small ones.** A major decision
is significant to the feature, and a later reader would want it called out:
flipping a feature flag from false to true, or measuring against a hand-kept
spreadsheet while a system of record exists that will replace it. A helper's
name, the order of two steps, or where a file lives is not one.

**What belongs in the body:**
- The why behind the change, where a real one exists
- On a large feature, what the change is, stated as an assertion
- The major decisions, including an alternative you rejected where a later reader would reach for it
- Constraints that look optional but aren't, with the reason
- High-level surface area: affected route names, public modules, external contracts, RFC references

**What does NOT belong in the body:**
- Action narration ("wires", "adds", "implements") — readable from `git show`
- Internal mechanism names that may rot: config block names, private helper names, file paths
- The reasons behind internal wiring, such as why a factory takes an injected dependency
- Restated diffstat content
- Measurements from the session: run times, token counts, test counts
- A pointer to a document the same commit adds
- An opener saying nothing did this before
- Current-session framing — the mission, investigation, or task you happen to be in the middle of. A trailing "this is part of fixing X" or "doesn't touch the Y we're chasing" sentence is the tell; delete it. Every sentence must stand on its own years later, with no knowledge of today's work.

## How many commits

**A commit is one claim, not one file you finished editing.** Write the subject line before you stage anything. Where two files would take the same subject, they belong in one commit, however many sittings you spent on them and however far apart they sit in the tree.

One change of mind usually reaches several files. A rule that changes what four skills do is one commit naming the rule, not four commits each naming a skill: the reader wants to know what changed about the work, and the file list is already in the diff.

**While the branch is unpushed, growing a commit is an amend.** `git branch -r --contains HEAD` prints nothing, so put the next file of the same sweep into the commit already sitting there rather than beside it, under the section below. That amend needs nobody's words.

Measured: a sweep that took the plan document out of four task skills, corrected two measurements in the reference behind them, and added one citation rule to two more, landed as eight commits. Two subjects covered all eight.

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
