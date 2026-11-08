---
name: pr-create-task
description: Opens a draft pull request end to end — readiness gate that folds the stack to one commit per feature, rebases the folded stack on the latest default branch, and runs quick-review and security-review over the whole branch, where any finding stops PR prep and goes to `retro-task` and then `spec-task`; a body drawn from the commit messages and authored to content discipline (what IS, the why, and the operational facts read from the non-test diff; cuts test/CI status, roadmaps, and diffstat narration), then a stop for explicit approval before the push. Use when preparing a branch for a pull request, creating or opening one, writing a PR body or description, or running `gh pr create` — "PR prep", "get this ready for a PR", "make the PR", "open a PR", "create the PR".
---

# pr-create-task — author and open a draft pull request

1. For the PR-create task in $ARGUMENTS, or the current branch's unpushed work if none is named, respond with the following sections in order.
2. Do NOT push or open the PR until the Push gate is explicitly approved, because the push is a separate authorization.
3. Put actual tool output in each section, not paraphrased summaries; a missing, hollow, or out-of-order section is an invalid output.

## Readiness Check

1. Confirm the current unpushed stack is shippable before writing a word of the body.
2. Detect the default branch first (`master` vs `main`), because a wrong base ref mis-scopes everything below.

```bash
git status --short                           # working tree
git log origin/<base>..HEAD --oneline        # the commits the PR will carry
git diff origin/<base>..HEAD --stat          # surface area
```

3. Report:

```
- Working tree:   <only intended files? junk is never staged>
- Commits:        <list — each is a section of the PR; is the stack the
                   shape you mean to ship, or does it need a reorder/split
                   first?>
- Tests:          <"not run: the rebase brought in no commits", or the
                   runners the project's CI skips on a pull request,
                   green at the rebased head; a spec that cannot run here
                   is named and marked UNTESTED, and so is each line a
                   rebase resolution added that no test failed without —
                   a PRECONDITION recorded here, NOT a PR-body section>
- Reviews:        <the last round of quick-review and security-review
                   found nothing — a PRECONDITION, NOT a PR-body section>
- Base branch:    <origin/master (or origin/main) — never the local ref>
```

4. **Fold the stack to one commit per claim first.** Group the commits by the claim each makes, under `git-commit`, "How many commits".
5. Fold on the branch's current base, `git merge-base HEAD origin/<base>`, so the fold replays only the branch's own commits.
6. Order the history feature by feature, not in the order the work happened: reorder freely, and let the migrations fix the order only where they must.
7. Fold every fix commit into the commit it fixes, and fold each group into one commit with a message authored through `git-commit`.
8. Resolve a reordered commit's conflict in the commit that replays it, so no commit in the stack carries another one's repair.
9. Never split a claim's group, or move a commit into another claim's group, to get past a conflict.
10. If a migration only patches another migration on this branch and no shared database has run either one, fold it into the migration it patches and renumber the versions after it.
11. If the fold ends with more commits than the plan had groups, name each extra commit at the push gate and say which claim it splits.
12. Expect a branch built one card at a time to arrive as one commit per card.
13. While `git branch -r --contains HEAD` prints nothing, fold without asking anyone.
14. **Then rebase the folded stack on the latest base.** Run `git fetch origin <base>`, record `git rev-list --count HEAD..origin/<base>`, the number of commits the rebase will bring in, then run `git rebase origin/<base>`.
15. Resolve each conflict in the folded commit that replays it, as in the fold above.
16. If a resolution writes code that neither side held, such as a new member of a list the base added or a base call moved into the branch's code, then treat it as a code change.
17. For such a resolution, search the project's specs and design documents for each sentence that names the list's other members, the check `quick-review` angle 6.8 makes, and fix any sentence that leaves the new member out in the same commit.
18. Then remove the added line, run its tests, and put it back; if no test fails, say so in that commit's message.
19. If the rebase brought in commits, list the files the branch adds with `git diff --name-only --diff-filter=A origin/<base> HEAD`, and for each directory that holds numbered files, such as migrations, list the base's copy with `git ls-tree --name-only origin/<base> <dir>/`.
20. If a branch file and a base file start with the same number, renumber the branch's file after the base's highest, in the commit that adds it, and run the migration tool the deploy uses over the directory, because git shows no conflict there but the tool refuses the directory.
21. If the rebase brought in no commits, run no tests: TDD already ran them against this base.
22. If it brought some in, read the project's CI workflow for the runners it runs on a pull request and leave those to CI's check on the draft PR.
23. Run every other runner against the rebased head, usually the browser tests, or at least every browser spec the branch adds or edits.
24. If the project has no CI on pull requests, run every runner.
25. **Then review the whole branch.** Run `quick-review` and then `security-review` over `origin/<base>..HEAD`, and record the tip they read (`git rev-parse HEAD`).
26. Fix nothing here: a finding of any size ends PR prep, so invoke `retro-task` in the same turn with every finding and the reviewed tip.
27. Let the fixes come back through `retro-task`, `spec-task`, build, and demo like any other work, and run PR prep again only when the operator asks for it.
28. On a later run, re-walk every pass on the code that changed since the tip the last run reviewed, `git diff <that tip> HEAD`, and reuse the earlier run's named artifacts only for code that has not changed.

**GO/NO-GO:**
- **GO** if the working tree holds only intended changes, the branch sits
  on the latest base, every runner the rebase calls for above is green at
  the rebased head, the stack is one commit per claim,
  and the last review round found nothing.
- **NO-GO** if junk is staged or the stack isn't the shape you mean to
  ship — fix that first, here. A review finding is not a NO-GO to fix here:
  it ends PR prep, as above.

## Commit and Operational Scan

1. Take the body's what and why from the commit messages, not from the diff:

```bash
git log --format='%h %s%n%n%b' origin/<base>..HEAD
```

2. Read the diff for one thing only: an operational fact a deployer has to act on, such as a migration, an environment variable, infra, CI, or a dependency.
3. Find those paths with the stat, leaving test files out, and read the diff of those paths alone:

```bash
git diff --stat origin/<base>...HEAD -- . <':!<test path>' for each test path>
git diff origin/<base>...HEAD -- <each operational path>
```

4. Work out which paths are tests from the project's test runner config first, such as vitest or jest `include`, playwright `testDir`, or pytest `testpaths`, and then from naming (`*.test.*`, `*.spec.*`, `test_*.py`, `tests/`, `__tests__/`).
5. Never diff a test file for the body.

## Body — content discipline

1. Answer two questions in the body and nothing else:
   - **What is this change, and why?** Lead with the what in one tight paragraph, then the why: the problem it solves, the alternative rejected, the constraint that makes something mandatory. Give the why over the how, which the diff already shows.
   - **What must someone acting on this know that the diff can't tell them?** A manual step that must follow, a cross-system contract change, a data dependency, or a feature flag. This is the only operational content that belongs.
2. Cut every sentence that would mean nothing to a reviewer two years from now with no knowledge of today's work.
3. **Check every sentence that says what the change does against the code,** not only the Deploying bullets: before the push gate, quote the code or test line that makes each one true, and fix or cut a sentence with no line.
4. **Cut**, every time:
   - Test or CI status, such as a pass count; keep a test line only for a non-obvious coverage decision, naming what is covered.
   - "Not in this PR", roadmap, or future steps.
   - Restated diffstat, file lists, or action narration ("adds X, wires Y, implements Z").
   - Current-session or mission framing ("this is part of fixing X", "as discussed").
   - How-mechanics the code already shows: exact formulas, private function names, config-block names that will rot.
5. **Keep**:
   - The one-paragraph what, and the why behind it.
   - A load-bearing operational fact a deployer or reviewer cannot infer from the diff, such as a manual follow-up.
   - A rider commit doing something distinct from the headline, in one line.
6. Write the body to a markdown tempfile and pass it to `gh` with `--body-file`, with no terminal-command dumps and no whitespace noise.
7. **No AI attributions**: no "Generated with", no "Co-Authored-By", nothing.

## Title

1. **The title follows the repository, not a house style.** Read what its PRs already look like:

```bash
gh pr list --state all --limit 20 --json title -q '.[].title'
```

2. Match what those titles do: a `type(scope):` prefix if they carry one, a plain sentence if they do not, and their capitalization and length either way.
3. If the repository has no PRs to read, fall back to its commit subjects (`git log --format='%s' -20`), and say in one line which of the two you matched.
4. If the work is for a particular Jira issue, put its key in the title, in parentheses at the end — `feat(evals): measure accuracy per carrier (ABC-106)` — unless the repository's titles already place keys another way, in which case match them; a link in the body is not enough, because the Jira integration looks for the key in the title, the branch, or the commits.
5. Take the key from the branch name, the commits, or the conversation, and if none of them names one, leave the key out rather than guess.
6. Describe what IS in the title, with no roadmap tag ("step 1 of…") unless a reviewer cannot make sense of the change without it; prefer one body sentence for staging ("reads still use the old path").

## Push gate (STOP)

1. Present, then wait for explicit approval:

```bash
git status
git log origin/<base>..HEAD --oneline
git push --dry-run -u origin HEAD:<branch>   # explicit refspec; never push the default branch
```

2. Show the final title and body, and say the PR will open as a draft.
3. **Await an explicit "push" / "make the PR."** Prior approval for the commit or amend does NOT carry to the push.
4. After approval:

```bash
git push -u origin HEAD:<branch>
gh pr create --draft --base <base> --title "<title>" --body-file <tempfile>
```

5. If `gh` refuses to open a draft, stop and report its error, and do not retry without `--draft`.
6. Report the PR URL.

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
