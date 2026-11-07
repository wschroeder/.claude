---
name: git-commit
description: Enforces git commit conventions and authors commit messages — staging rules, subjects matched to the repository's own log, message-body authoring, no AI attributions, when to amend instead of adding a follow-up commit, and safety checks. Use whenever committing, amending, pushing, branching, OR drafting/proposing a commit message — even speculatively, before authorization.
---

## When to invoke

1. Invoke this skill the moment you start composing a commit subject or body, even a draft and even before the user has approved the commit, instead of writing the message in chat or a temp file.
2. For a pull request description, use the `pr-create-task` skill, which carries these body principles to PR bodies and stops for approval before the push.

## Git Staging Rules

1. **Never use `git add -A`**, because it stages untracked files you may not want.
2. Use `git add -u` to stage only tracked files that were modified or deleted, or `git add <specific files>` to name them.
3. If a tool writes tracked files as a side effect of your work, such as an audit trail or an export, stage by path.

## Commit Messages

1. Match the subject to the repository's established style, read from enough of the log:

```bash
git log --no-merges --format='%s' -60
```

2. Match a `<type>(<scope>):` prefix if the subjects carry one, a plain sentence if they do not, and their capitalization, tense, and length either way.
3. If the log is empty or shows no pattern, write a plain sentence saying what the change does, and say in one line that there was nothing to match.
4. If the recent subjects break from the older ones, match the older ones.
5. Treat a commit message the operator wrote or reworded themselves as the pattern for every commit after it, subject and body alike.
6. Apply everything under Body Content in every repository; only the subject follows the repository.
7. **NEVER include AI attributions**, such as "Co-Authored-By: Claude", "Generated with Claude Code", or "via Happy".
8. **NEVER reference a bd (beads) card in a commit message**, not its id, in the subject, the body, or a trailer; the card's note names the commit instead.
9. If an external issue, such as a Jira key or a GitHub issue, tracks the work, name it the way the repository's log already does: a subject prefix such as `ABC-6:` or a closing `Jira: ABC-6` line.
10. In `~/.claude` itself, name no issue at all, under `systematize`, "Keep every client and project out of `~/.claude`".

## Body Content

1. Write a body only when the change carries something neither the subject nor the diff can show; most commits need only the subject.
2. On a small commit, make the body the why: the reason for the change, a decision behind it, or a constraint that looks optional and is not. If there is no reason beyond the subject, write no body.
3. On a large feature, open with one or two sentences saying what it is and does, then give the major decisions and the reasons behind them.
4. Make the body as short as it can reasonably be, checking against about 100 words on a feature.
5. Give a real reason as the why; for a fix, name what was broken.
6. Record the major decisions a later reader would want called out, such as flipping a feature flag, and leave out small ones, such as a helper's name, the order of two steps, or where a file lives.

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
- Current-session framing — the mission, investigation, or task you happen to be in the middle of. Every sentence must stand on its own years later, with no knowledge of today's work.

## How many commits

1. Make each commit one claim: one feature is one commit, with its code, its tests, and its documents.
2. Write the subject line before you stage anything, and put files that would take the same subject in one commit.
3. Make one change of mind that reaches several files one commit naming the rule, not one commit per file.
4. While the branch is unpushed (`git branch -r --contains HEAD` prints nothing), put the next file of the same sweep into the commit already there by amending, under the section below; that amend needs nobody's words.

See [references/measurements.md](references/measurements.md).

## Fixing work you already committed

1. Fold a fix into the commit on this branch that already covers it, rather than adding a separate `fix: address review feedback` commit.
2. **Before any commit, list the commits no remote has yet** with `git log --oneline HEAD --not --remotes`, which needs no upstream.
3. If one of those commits introduced the feature this change touches, fold the change into it, even when it is not `HEAD`, unless the operator asked for a separate commit.
4. For `HEAD`, use `git commit --amend`. For an older one, commit with `git commit --fixup=<sha>`, then run `git rebase --autosquash <base>`, where `<base>` is the commit the branch started from; that rebase needs no editor and no `-i`.
5. **Fold each fixup as soon as you commit it, and check the tree after.** Record `pre=$(git rev-parse HEAD)` before the rebase; after it, `git diff "$pre" HEAD` must print nothing, and if it prints anything, stop and report the diff.
6. If the rebase stops on a conflict you cannot resolve within the one fixup you just made, run `git rebase --abort`, confirm `git rev-parse HEAD` equals `$pre`, and report which commit and which files conflicted. A fold that reorders the whole stack resolves its conflicts under `pr-create-task`. See [references/measurements.md](references/measurements.md).
7. **At a rebase stop caused by a conflict, do not amend**, because `git commit --amend` there rewrites the commit before the one being replayed. Resolve the files, stage them by path, and run `GIT_EDITOR=true git rebase --continue`; amend only at an `edit` stop that reported no conflict.
8. **Check whether the commit has reached a remote before you decide**, with `git branch -r --contains HEAD`, which prints nothing and exits 0 when no remote has it. Never use `git log @{u}..HEAD`, which aborts on a branch that was never pushed. Run `git fetch` first if the branch may have been pushed from somewhere else.

- **No remote has it** — amend. This is the default; do not ask the user to choose between a follow-up commit and an amend when the commit is unpushed.
- **A remote already has it** — amending rewrites published history, so the push becomes `git push --force-with-lease` (never a bare `--force`). On your own PR branch that is still the right call, and the `pr-respond-task` skill drives it. On a branch someone else may have pulled, add a new commit instead.

9. **After a fold, rewrite every commit id the handoff records.** Run `git log --oneline HEAD --not --remotes` again and put each new id in place of its old one, matched by position in that list, not by subject, and record ids rather than subjects. See [references/measurements.md](references/measurements.md).
10. Stage explicitly, never with `git add -A`.
11. Keep the existing message unless the fix changes what that commit claims; if it does, re-author the message through this skill, and otherwise use `git commit --amend --no-edit`.
12. After an amend, run `git show --stat HEAD` and check that it lists the file you meant to fold in, because an amend with nothing staged changes only the message.
13. **Amending an unpushed commit needs no approval. Amending a pushed one does.** If a remote carries the commit, stop, say what the amend would rewrite, and wait, because the next push becomes `git push --force-with-lease`.

## Safety

- **Committing and amending carry standing permission. Pushing and deploying never do.** Commit when a piece of work is finished, and amend an unpushed commit, without asking first. Push, force-push, `--force-with-lease` push, and deploy each need the user's words for that specific action, every time. Never chain commit → push → deploy.
- **A repository's own CLAUDE.md can grant standing permission for a deploy to a target it names.** Read the project instructions before you stop to ask: if they name the service and say a deploy to it carries standing permission, deploy there without asking. That grant reaches only the target it names. See [references/measurements.md](references/measurements.md).
- **Approval from earlier in the session does not transfer to a push.** Ask again for each push.
- **"Apply the fixes" is not "push".** Write the fixes to the working tree and commit them; ask separately before putting them on a remote.
- **Judge a push by whether the process was followed, not by whether the code is right.** A push that skipped the review sequence in `writing-code` is a process violation.
- Never run destructive commands (`push --force`, `reset --hard`) without explicit confirmation
- Never skip hooks (`--no-verify`) unless explicitly requested
- Verify with `git status` and `git diff` before committing

If you find yourself writing "amended and pushed" in a summary without the user having explicitly said "push" AFTER the change was made AFTER the reviews completed, stop, then revert or surface what happened before any further work.
