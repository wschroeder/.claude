---
name: pr-create-task
description: Opens a pull request end to end — readiness gate, full-diff scan, a body authored to content discipline (what IS, the why, and the operational facts the diff can't show; cuts test/CI status, roadmaps, and diffstat narration), then a stop for explicit approval before the push. Use when creating or opening a pull request, writing a PR body or description, or running `gh pr create` — "make the PR", "open a PR", "create the PR".
activation:
  - "open a pull request"
  - "create a pull request"
  - "make the PR"
  - "open a PR"
  - "create the PR"
  - "PR body"
  - "PR description"
  - "gh pr create"
---

# pr-create-task — author and open a pull request

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
- Reviews:        <quick-review + security-review ran against the CURRENT
                   tree, per CLAUDE.md Change → Review — done / not done>
- Tests:          <green — a PRECONDITION recorded here, NOT a PR-body
                   section>
- Base branch:    <origin/master (or origin/main) — never the local ref>
```

**GO/NO-GO:**
- **GO** if the working tree holds only intended changes, both mandatory
  reviews ran against the current tree, and tests are green.
- **NO-GO** if reviews haven't run on the current tree, junk is staged, or
  the stack isn't the shape you mean to ship — fix that first, here.

## Diff Scan

Read the FULL cumulative diff, no truncation, before authoring. The body
must be grounded in what actually changed, not in memory of the session.

```bash
git diff origin/<base>..HEAD
```

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

Conventional-commit form (`type(scope): subject`), lowercase, describing
what IS. No roadmap tag ("step 1 of…") unless a reviewer genuinely cannot
make sense of the change without it — prefer to convey staging in one body
sentence ("reads still use the old path") instead.

## Push gate (STOP)

Present, then wait for explicit approval:

```bash
git status
git log origin/<base>..HEAD --oneline
git push --dry-run -u origin HEAD:<branch>   # explicit refspec; never push the default branch
```

Show the final title and body. **Await an explicit "push" / "make the
PR."** Prior approval for the commit or amend does NOT carry to the push.

After approval:

```bash
git push -u origin HEAD:<branch>
gh pr create --base <base> --title "<title>" --body-file <tempfile>
```

Report the PR URL.

## Notes on what this template does NOT do

- Does not push or open the PR before the Push gate is explicitly
  approved. Each destructive git action is its own authorization.
- Does not decide merge strategy. Whether the stack is squash-collapsed or
  preserved as sections is a separate, merge-time decision.
- Does not treat CI-green as PR-body content.
- Does not include AI attributions in the body or commits.
- Does not chain to merge, deploy, or any other template.
