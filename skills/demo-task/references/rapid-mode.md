# Rapid mode — when the operator pauses the formality

Read from `demo-task`'s "Rapid mode" section once the operator turns the mode on.

The operator can suspend most of this template at any point in the demo
phase, including before Section 1, by saying so in their own words: "let's do
some rapid stuff here", "quick tweak", "just try it and I'll look", "skip the
formality for a minute". There is no keyword to wait for. When they ask for
speed over rigor, the mode is on, and your next message says in one line that
it is on, so they can see you heard them.

While it is on:

- **Section 2's proof commands and Section 3's capture machinery are
  suspended.** Do not run the suite, do not build a capture record, and do
  not write a reproduction command. The operator is sitting in front of the
  thing, and they are the test.
- **CLAUDE.md's "Always use TDD principles for code additions, changes, and
  deletions." is suspended too.** CLAUDE.md says so itself, at that line, so
  that the two rules do not have to be settled by whichever one sits nearer
  the work. Write the change now; the tests come after they approve.
- **Design guidance is not suspended.** The mode pauses tests and captures
  only. Before your first edit to a page's layout, read the pattern its design
  skill holds for that kind of page, such as `status-page` for a status page,
  and build to it.
- **Your whole job is to make the change and tell the operator it is ready to
  look at.** A sentence or two: what you changed, and what to look at. Not a
  record, not an evidence table of proof commands you did not run.
- **Looking is not suspended.** Before you say a change is ready, drive it once
  in the browser tool the way you will ask the operator to, and say in one line
  what you saw. Never say a tool will not load unless it returned an error in
  this turn. See [references/measurements.md](measurements.md).
- **Do not commit.** They have approved nothing yet, and a commit made during
  the mode takes that decision away from them. See [references/measurements.md](measurements.md).
- **There is no size limit on what the mode may cover.** A colour change and a
  rework of how the product records an entire behaviour are both allowed in
  it. The operator decides what is small enough to take this way, so do not
  argue that a request has outgrown the mode. See [references/measurements.md](measurements.md).

**The operator turns the mode off by approving.** Their approval is the
signal — not the passage of time, not a number of rounds, and not your own
sense that the change has grown. Until they approve, stay in the mode, however
many tweaks it takes.

**Their approval is what starts the polish**, in this order, in this session:

1. Write the tests the changes should have had. They are late, and that was
   the operator's call to make.
2. Load `quick-review` over everything the mode produced, then
   `security-review` when `writing-code`'s list says the diff needs one, and
   apply what they find under the review skill's own gate.
3. Commit, through `git-commit`.
4. Go back to Section 2, run the proof commands over the changed product,
   rebuild Section 3's demo record from what they print, and carry on to
   Section 4's stop.

Those four are not optional and are not the next session's. The mode buys the
operator speed while they are trying ideas; it does not delete the work.
