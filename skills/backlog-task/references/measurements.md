# Measurements behind backlog-task's rules

The skill body states each rule. This file holds the run that prompted it, for a reader who disputes one.

## Why a session past the ceiling hands off before starting the template

Measured: a session printed "turn 72, context 231,229 of 170,000 — hand off", quoted that line back in its own evidence block, created ten cards over the next two hours, printed the same line again at 251,737, and ended at 263,205.

## Why the status key is cleared with an empty string

Measured: unsetting that key reports success and leaves the status registered, and only setting it to an empty string removes it.

## What the markdown file form stores

Measured: in that shape it stores all six, and `bd show` prints the acceptance criteria under its own heading.

## Why the build runs as a session-loop run

Measured: across two projects in one month, twenty-nine handoffs were written by hand and the loop was invoked zero times; one of those builds closed seven cards over five sessions, four of them closing exactly one card each, while a session that kept going closed its second and third cards for 21,239 and 14,670 tokens against the 114,028 its first one cost.

## Why bd export runs right before staging the cards

Measured: a commit of six new cards held one of them, and the rest arrived later as the change that stopped the loop's first launch.

## Why session-loop is invoked in this turn rather than named in a handoff

Measured: one planning session wrote a handoff naming `session-loop` zero times, and the operator pasted eleven more prompts over the thirteen hours that followed.
