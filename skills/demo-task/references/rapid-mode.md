# Rapid mode — when the operator pauses the formality

1. Read this from `demo-task`'s "Rapid mode" section once the operator turns the mode on.
2. Turn the mode on whenever the operator asks in their own words for speed over rigor at any point in the demo phase, including before Section 1, such as "quick tweak" or "just try it and I'll look"; there is no keyword.
3. Say in one line in your next message that the mode is on.

While it is on:

1. Suspend Section 2's proof commands and Section 3's capture machinery: run no suite, build no capture record, and write no reproduction command.
2. Suspend CLAUDE.md's "Always use TDD principles for code additions, changes, and deletions.", as CLAUDE.md says at that line, and write the change now.
3. Keep design guidance: before your first edit to a page's layout, read the pattern its design skill holds for that kind of page, such as `dashboard-task` "A status or health page" for a status page, and build to it.
4. Tell the operator in a sentence or two what you changed and what to look at, with no record and no evidence table.
5. Before you say a change is ready, drive it once in the browser tool the way you will ask the operator to, and say in one line what you saw.
6. Never say a tool will not load unless it returned an error in this turn.
7. Do not commit.
8. Never argue that a request has outgrown the mode; the operator decides what it covers.

Turning it off:

1. Stay in the mode until the operator approves, however many tweaks it takes; only their approval turns it off.
2. On their approval, do these four in this order, in this session, never leaving them to the next one:

1. Write the tests the changes should have had, under `tdd-cycle`'s rule that
   a test asserts what a person reads, never the markup around it, so how a
   screen is put together gets a demo and not a test. Where every change
   is of that kind, write none and say so in one line. Tests that are owed are
   late, and that was the operator's call to make.
2. Load `quick-review` over everything the mode produced, then
   `security-review` when `writing-code`'s list says the diff needs one, and
   apply what they find under the review skill's own gate.
3. Commit, through `git-commit`.
4. Go back to Section 2, run the proof commands over the changed product,
   rebuild Section 3's demo record from what they print, and carry on to
   Section 4's stop.
