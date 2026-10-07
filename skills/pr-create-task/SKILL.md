---
name: pr-create-task
description: Opens a draft pull request end to end — readiness gate that folds the stack to one commit per claim, a body drawn from the commit messages and authored to content discipline (what IS, the why, and the operational facts read from the non-test diff; cuts test/CI status, roadmaps, and diffstat narration), then a stop for explicit approval before the push. Use when creating or opening a pull request, writing a PR body or description, or running `gh pr create` — "make the PR", "open a PR", "create the PR".
---

# pr-create-task — author and open a draft pull request

For the PR-create task in $ARGUMENTS (or the current branch's unpushed
work if none specified), respond with the following sections in order.
Do NOT push or open the PR until the Push gate is explicitly approved —
the push is a separate authorization per `~/.claude/CLAUDE.md` Change →
Review Workflow.

The output discipline is structural: each section contains actual tool
output, not paraphrased summaries. A missing, hollow, or out-of-order
section is an invalid output.

## Readiness Check

The PR ships the current unpushed stack. Confirm it is shippable before
writing a word of the body. Detect the default branch first (`master` vs
`main`); a wrong base ref silently mis-scopes everything below.

```bash
git status --short                           # working tree
git log origin/<base>..HEAD --oneline        # the commits the PR will carry
git diff origin/<base>..HEAD --stat          # surface area
```

Report:

```
- Working tree:   <only intended files? junk is never staged>
- Commits:        <list — each is a section of the PR; is the stack the
                   shape you mean to ship, or does it need a reorder/split
                   first?>
- Tests:          <green — a PRECONDITION recorded here, NOT a PR-body
                   section>
- Base branch:    <origin/master (or origin/main) — never the local ref>
```

**Fold the stack to one commit per claim before the push gate.** Group the
commits by the claim each makes, under `git-commit`, "How many commits".
Fold every fix commit into the commit it fixes, and fold each group into one
commit with a message authored through `git-commit`. A branch built one card
at a time arrives as one commit per card. While `git branch -r --contains
HEAD` prints nothing, the fold needs nobody's words. Measured: a push gate
listed 20 commits and raised nothing, and the operator had to ask; the fold
then made two.

**GO/NO-GO:**
- **GO** if the working tree holds only intended changes, tests are green,
  and the stack is one commit per claim.
- **NO-GO** if junk is staged or the stack isn't the shape you mean to
  ship — fix that first, here.

Reviewing the code is the operator's call, not this template's. Do not
run quick-review or security-review here, and do not ask whether they ran.

## Commit and Operational Scan

The commit messages already say what changed and why, so the body's what
and why come from them, not from the diff:

```bash
git log --format='%h %s%n%n%b' origin/<base>..HEAD
```

The diff is read for one thing only: an operational fact a deployer has to
act on, such as a migration, an environment variable, infra, CI, or a
dependency. Find those paths with the stat, leaving test files out, and read
the diff of those paths alone:

```bash
git diff --stat origin/<base>...HEAD -- . <':!<test path>' for each test path>
git diff origin/<base>...HEAD -- <each operational path>
```

Work out which paths are tests from the project's test runner config first,
such as vitest or jest `include`, playwright `testDir`, or pytest `testpaths`,
and then from naming (`*.test.*`, `*.spec.*`, `test_*.py`, `tests/`,
`__tests__/`). Never diff a test file for the body. Measured: two sessions
read a 3,257-line diff in full for one PR, and each climbed past the 170,000
handoff ceiling; tests made up 60% of its changed lines.

## Body — content discipline

A PR body answers two questions and nothing else:

1. **What is this change, and why?** Lead with the what in one tight
   paragraph, then the why: the problem it solves, the alternative
   rejected, the constraint that makes something mandatory. WHY over HOW —
   the diff already shows the how.
2. **What must someone acting on this know that the diff can't tell
   them?** A manual step that must follow, a cross-system contract change,
   a data dependency, a feature flag. This is the only "operational"
   content that belongs.

Test every sentence: *would this mean anything to a reviewer two years
from now with no knowledge of today's work?* If not, cut it.

**CUT — these are noise, every time:**

- **Test / CI status** ("33 tests pass", "all green"). Green is a
  precondition for the PR existing; restating it says nothing. The only
  test content that earns a line is a genuinely non-obvious coverage
  decision — *what* is covered that a reader wouldn't expect — never a
  pass count.
- **"Not in this PR" / roadmap / future steps.** A PR describes what IS.
  The set of what-it-isn't is infinite; naming a slice of it is filler.
- **Restated diffstat / file lists / action narration** ("adds X, wires
  Y, implements Z"). The diff shows this.
- **Current-session / mission framing** ("this is part of fixing X", "as
  discussed"). Every sentence must stand on its own later.
- **HOW-mechanics the code already shows** — exact formulas, private
  function names, config-block names that will rot.

**KEEP — the diff can't show these:**

- The one-paragraph what, and the why behind it.
- A load-bearing operational fact a deployer or reviewer genuinely cannot
  infer from the diff (the manual follow-up).
- A rider commit doing something distinct from the headline, in one line.

These rules are the `git-commit` skill's body discipline ("What does NOT
belong: restated diffstat content; current-session framing") carried over
to PR bodies, where it was previously unwritten.

**Mechanics:**

- Write the body to a markdown tempfile and pass it to `gh` with
  `--body-file`. Keep it concise — no terminal-command dumps, no
  whitespace noise.
- **No AI attributions** — no "Generated with", no "Co-Authored-By",
  nothing, per `~/.claude/CLAUDE.md`.

## Title

**The title follows the repository, not a house style.** Read what its PRs
already look like:

```bash
gh pr list --state all --limit 20 --json title -q '.[].title'
```

Match what those titles do: a `type(scope):` prefix if they carry one, a
plain sentence if they do not, and their capitalization and length either
way. Where the repository has no PRs to read, fall back to its commit
subjects (`git log --format='%s' -20`), and say in one line which of the
two you matched.

If the work is for a particular Jira issue, put its key in the title, in
parentheses at the end — `feat(evals): measure accuracy per carrier
(MBG-106)` — unless the repository's titles already place keys another
way, in which case match them. A link to the issue in the body is not
enough on its own, because the Jira integration looks for the key in the
title, the branch, or the commits. Take the key from the branch name, the commits, or the
conversation. If none of them names one, leave the key out rather than
guess.

Whatever the form, the title describes what IS. No roadmap tag ("step 1
of…") unless a reviewer genuinely cannot make sense of the change without
it — prefer to convey staging in one body sentence ("reads still use the
old path") instead.

## Push gate (STOP)

Present, then wait for explicit approval:

```bash
git status
git log origin/<base>..HEAD --oneline
git push --dry-run -u origin HEAD:<branch>   # explicit refspec; never push the default branch
```

Show the final title and body, and say the PR will open as a draft.
**Await an explicit "push" / "make the PR."** Prior approval for the
commit or amend does NOT carry to the push.

After approval:

```bash
git push -u origin HEAD:<branch>
gh pr create --draft --base <base> --title "<title>" --body-file <tempfile>
```

If `gh` refuses to open a draft, stop and report its error. Do not retry
without `--draft`.

Report the PR URL.

## Notes on what this template does NOT do

- Does not push or open the PR before the Push gate is explicitly
  approved. Each destructive git action is its own authorization.
- Does not mark the PR ready for review. It opens as a draft, and
  `gh pr ready` is the operator's own step.
- Does not decide merge strategy. Whether the stack is squash-collapsed or
  preserved as sections is a separate, merge-time decision.
- Does not treat CI-green as PR-body content.
- Does not include AI attributions in the body or commits.
- Does not chain to merge, deploy, or any other template.
