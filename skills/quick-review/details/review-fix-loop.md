# When the fix loop is finished

Four rules govern the loop in `quick-review`, "Re-review and the fix loop".

**The loop iterates on the diff, not on finding severity.** Applying any Fix, Flag, or Note that clears the gate changes the diff. A changed diff requires a fresh pass of *both* reviews — `quick-review` and `security-review` — before the loop can be declared complete. This is true regardless of how minor the applied finding was; "it was just a Note" is not an exception.

**A green test suite does not stand in for a review pass.** Tests verify behavior; reviews verify cross-cutting properties (sibling consistency, doc/code drift, evidence-of-intent) that test runs cannot detect. Passing tests and a clean linter leave the review sequence still owed.

**Say a review pass is complete only when it ran against the current tree.** Both reviews must have run against the current working tree with no edits since. Otherwise, say which edits landed after the last pass.

**Prose-only diffs are exempt.** A diff that introduces no executable change — pure prose files (`*.md`, `*.txt`, `*.rst`) and/or comment-only hunks in code files — does not trigger the review sequence, and applying a prose-only fix during the loop does not re-trigger reviews. The test is "any executable change anywhere in the diff": if yes, the whole diff is in scope; if no, skip.
