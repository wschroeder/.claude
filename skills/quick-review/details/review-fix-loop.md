# When the fix loop is finished

Four rules decide when the loop in `quick-review`, "Re-review and the fix loop", is finished.

**The loop iterates on the diff, not on finding severity.** Applying any Fix, Flag, or Note that clears the gate changes the diff. A changed diff requires a fresh pass of `quick-review`, and of `security-review` when `writing-code`'s list in "After the edit: the review sequence is owed" says the diff needs one, before the loop can be declared complete. This is true regardless of how minor the applied finding was; "it was just a Note" is not an exception.

**A green test suite does not stand in for a review pass.** Tests verify behavior; reviews verify cross-cutting properties (sibling consistency, doc/code drift, evidence-of-intent) that test runs cannot detect. Passing tests and a clean linter leave the review sequence still owed.

**Say a review pass is complete only when it ran against the current tree.** Both reviews must have run against the current working tree with no edits since. Otherwise, say which edits landed after the last pass.

**Prose-only diffs are exempt.** A diff that introduces no executable change — pure prose files (`*.md`, `*.txt`, `*.rst`) and/or comment-only hunks in code files — does not trigger the review sequence, and applying a prose-only fix during the loop does not re-trigger reviews. The test is "any executable change anywhere in the diff": if yes, the whole diff is in scope; if no, skip.

## Each new round

**Anti-anchoring:** When re-reviewing after amends, the prior round's "triaged and dropped" list is informational context, not binding precedent. For any surface TOUCHED by the current amend, re-run all nine passes on THAT surface. Previous dismissals applied to previous code; amended code is new evidence. An orchestrator passing "don't re-surface these" into the subagent prompt is a shortcut that saves tokens but erodes coverage — re-enumerate the angles and let the classify gate drop duplicates.

In a staged review, a full round means the stages that [stages.md](stages.md) "After a fix" re-runs; a stage it keeps counts as run against the current tree.

Each fix adds these targeted re-checks to the full round:
- Test coverage for the fix
- Call-graph integration
- Adversarial: does the fix create a new failure mode?
