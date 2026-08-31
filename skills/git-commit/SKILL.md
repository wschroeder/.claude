---
name: git-commit
description: Enforces git commit conventions and authors commit messages — staging rules, subjects matched to the repository's own log, message-body authoring, no AI attributions, when to amend instead of adding a follow-up commit, and safety checks. Use whenever committing, amending, pushing, branching, OR drafting/proposing a commit message — even speculatively, before authorization.
activation:
  - "git"
  - "commit"
  - "commit message"
  - "amend"
  - "push"
  - "branch"
---

## When to invoke

**This skill owns commit-message authoring.** The moment you start composing a commit subject or body — even a draft, even before the user has approved the commit — invoke this skill instead of writing the message in chat or a temp file.

**For pull request descriptions, use the `pr-create-task` skill.** It carries these same body principles (WHY over HOW, no restated diffstat, no current-session framing) to PR bodies — where they were previously unwritten — and walks PR creation end to end with a stop for approval before the push. The moment you start composing a PR body or reach for `gh pr create`, route there.

## Git Staging Rules

**Never use `git add -A`** - it stages everything including untracked files you may not want.

Instead use:
- `git add -u` - stage only tracked files that have been modified/deleted
- `git add <specific files>` - explicitly name the files to stage

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

**An amend needs its own approval.** `git commit --amend` rewrites history and counts as a separate destructive action. Approval to commit is not approval to amend, and approval to amend is not approval to push the rewritten branch.

## Safety

- **Never commit, push, or deploy without explicit approval for each action.** Previous approval does not carry forward. "Commit this" approves a commit — not a push. "Push this" approves a push — not a deploy. Each step requires its own approval. Do not chain commit → push → deploy on momentum.
- Never run destructive commands (`push --force`, `reset --hard`) without explicit confirmation
- Never skip hooks (`--no-verify`) unless explicitly requested
- Verify with `git status` and `git diff` before committing
