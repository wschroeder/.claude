# Requirement check — does the diff do what was asked?

Run this after you state the Mission and before the Class Checklist. The Mission
comes from the diff and the PR text, so it says what the author believes the change
does. This step checks the change against what someone asked for.

## Find the requirement

Look in this order, and stop at the first source that carries acceptance criteria:

1. The orchestrator's prompt, if it names an issue, a card, or a spec.
2. The PR body: `gh pr view --json body,closingIssuesReferences`.
3. Commit messages on the branch: `git log <merge-base>..HEAD --format=%B`, for an
   issue number, a card id, or a `Refs:` or `Closes:` trailer.
4. The branch name, for an issue number or a card id.
5. A bd card, if the repository uses beads: `bd show <id>` for any id found above.
6. A design document or spec the commits or the card name.

For an issue number, read it with `gh issue view <n>`. For a card, read the
acceptance criteria and any proof command the card carries.

If none of these turns up a requirement, write `Requirement: none found` in the
output and say where you looked. The Screen then drops nothing on intent grounds.

## Check each criterion

Split the requirement into its separate criteria. A card written by `spec-task`
already has them as EARS lines. For an issue in prose, write each promised behavior
as one line before you check anything.

Give each criterion one of three dispositions:

- **met**: cite the line of code that delivers it and the test that asserts it. If
  the card carries a proof command, run it and quote the result.
- **partly met**: say what is missing. This is a Flag.
- **not met**: nothing in the diff delivers it. This is a Fix, unless the PR text
  says the criterion is deferred, in which case it is a Note naming where the
  deferral is recorded.

The same demonstration discipline applies here as everywhere else: "the handler
looks like it does this" is not a disposition for **met**.

## Effects the requirement does not ask for

The diff may do things no criterion covers. The Screen does not drop them on intent
grounds. Each one continues through the Screen and the gates like any other
candidate, and most will drop there as harmless. The ones that survive are the
behavior changes nobody asked for, which is the reason for this step.
