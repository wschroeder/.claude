# When the fix loop is finished

1. Apply these rules to decide when the loop in `quick-review`, "Re-review and the fix loop", is finished.
2. After applying any Fix, Flag, or Note, however minor, run `quick-review` again, and `security-review` when `writing-code`'s list in "After the edit: the review sequence is owed" says the diff needs one, before you call the loop complete.
3. Never count a green test suite or a clean linter as a review pass.
4. Say a review pass is complete only when both reviews ran against the current working tree with no edits since; otherwise say which edits landed after the last pass.
5. Skip the review sequence for a diff with no executable change anywhere, only prose files (`*.md`, `*.txt`, `*.rst`) or comment-only hunks, and let a prose-only fix during the loop trigger no new review.

## Each new round

1. Treat the prior round's "triaged and dropped" list as context, never as precedent, and re-run all nine passes on every surface the current amend touched.
2. Never pass a "don't re-surface these" list into a reviewer's prompt; re-enumerate the angles and let the classify gate drop duplicates.
3. In a staged review, count as a full round the stages that [stages.md](stages.md) "After a fix" re-runs, and count a stage it keeps as run against the current tree.
4. Add these targeted re-checks for each fix to the full round:
- Test coverage for the fix
- Call-graph integration
- Adversarial: does the fix create a new failure mode?
