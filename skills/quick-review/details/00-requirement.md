# Requirement check — does the diff do what was asked?

1. Run this after you state the Mission and before the passes, to check the change against what someone asked for rather than what the author believes it does.

## Find the requirement

1. Look in this order, and stop at the first source that carries acceptance criteria:

1. The orchestrator's prompt, if it names an issue, a card, or a spec.
2. The PR body: `gh pr view --json body,closingIssuesReferences`.
3. Commit messages on the branch: `git log <merge-base>..HEAD --format=%B`, for an
   issue number, a card id, or a `Refs:` or `Closes:` trailer.
4. The branch name, for an issue number or a card id.
5. A bd card, if the repository uses beads: `bd show <id>` for any id found above.
6. A design document or spec the commits or the card name.

2. Read an issue number with `gh issue view <n>`, and for a card read its acceptance criteria and any proof command it carries.
3. If none of these turns up a requirement, write `Requirement: none found` in the output, say where you looked, and let the Screen drop nothing on intent grounds.

## Check each criterion

1. Split the requirement into separate criteria, taking a `spec-task` card's EARS lines as they are and writing each promised behavior of a prose issue as one line before you check anything.
2. Give each criterion one of three dispositions:

- **met**: cite the line of code that delivers it and the test that asserts it. If
  the card carries a proof command, run it and quote the result.
- **partly met**: say what is missing. This is a Flag.
- **not met**: nothing in the diff delivers it. This is a Fix, unless the PR text
  says the criterion is deferred, in which case it is a Note naming where the
  deferral is recorded.

3. Never mark **met** because the handler looks like it does it.
4. Where a design document records the operator's answer that narrows a criterion, check the diff against the narrowed line and write **met as narrowed**, citing its file and line; a handoff's Decision line does not count.
5. Check each criterion on every failure path the diff adds, such as a catch, a fallback, or a retry that gives up, and require for **met** a test that reaches the criterion's outcome through it, or a line saying why the criterion does not apply there; angle 3.6 in [error-handling.md](error-handling.md) covers this.

## When the operator accepts a Flag

1. When the operator answers a Flag with "accept as is" or its equivalent, write their answer, quoted and dated, into the design document beside the requirement it narrows, in the same turn, and say in plain words what the requirement now means.

## Effects the requirement does not ask for

1. Never let the Screen drop an effect on intent grounds because no criterion covers it; send it through the Screen and the gates like any other candidate.
