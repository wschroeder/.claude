# Measurements behind pr-create-task's rules

The skill body states each rule. This file holds the run that prompted it, for a reader who disputes one.

## Why the runners CI skips run against the rebased head

Measured: a browser spec passed on 2026-10-16, main then changed the table cell it read, and PR prep ran only the unit and integration tests after the rebase. An outside reviewer found the failing spec.

Measured (2026-10-28): the rule then said to run every test runner after any rebase. A PR prep started the full unit and integration suite locally, though the project's CI runs those same suites on every pull request and runs no browser tests, and the operator stopped it as wasted time. As worded, the rule also ran every suite after a rebase that brought in nothing, where TDD had already run them against the same base.

## Why a rebase compares the numbers of files both sides added

Measured (2026-10-30): the branch added a numbered migration, and while it was in review the base merged a different migration with the same number. The two files had different names, so the rebase replayed with no conflict. PR prep then ran only the browser tests, leaving the unit and integration suites to CI, and the browser tests' setup applies migrations by sorted filename without checking for a repeated number, so they passed. The whole-branch review ran the integration suite, whose migration tool refused the directory with "duplicate migration file", and 307 tests failed at setup. That finding ended PR prep for the round.

## Why a resolution that writes new code gets the spec search and the mutation test

Measured (2026-10-28): a rebase brought in a base commit that listed the in-flight states of a background job, both in code and in one spec sentence. The session resolving the conflict added the branch's new state to the code's list, and it ran a mutation test on that line. Its only spec search looked for a word the branch had renamed, so the sentence still left the new state out. In a second conflict, the session moved a base call into a branch helper and ran no test that fails without the call. The whole-branch review caught both, and its findings ended PR prep for that round.

## Why a fold resolves its conflicts instead of splitting a claim

Measured (2026-10-24): a fold planned eleven groups, aborted at each of four conflicts instead of resolving them, and shipped fifteen commits with three claims split in two.

## Why a branch built one card at a time is folded without asking

Measured: a push gate listed 20 commits and raised nothing, and the operator had to ask; the fold then made two.

## Why a later review run re-walks only the code that changed

Measured: on one branch, a session read the whole 2,486-line diff again for its third round and climbed past the 170,000 handoff ceiling. The next bounded it this way to 8 files.

## Why a test file is never diffed for the body

Measured: two sessions read a 3,257-line diff in full for one PR, and each climbed past the 170,000 handoff ceiling; tests made up 60% of its changed lines.

## Why every sentence of the body is checked against the code

Measured (2026-10-21): the body said a record read from an outside system is flagged "until a second source confirms it". The session checked only the two Deploying claims, the code never cleared the flag, and the outside reviewer found it.
