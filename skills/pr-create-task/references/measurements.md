# Measurements behind pr-create-task's rules

The skill body states each rule. This file holds the run that prompted it, for a reader who disputes one.

## Why every test runner runs against the rebased head

Measured: a browser spec passed on 2026-10-16, main then changed the table cell it read, and PR prep ran only the unit and integration tests after the rebase. An outside reviewer found the failing spec.

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
