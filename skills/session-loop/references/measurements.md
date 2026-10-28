# Measurements behind session-loop's rules

The skill body states each rule. This file holds the run that prompted it, for a reader who disputes one.

## Why the last review's findings are fixed before the demo ask

Measured on one project's S3: the run stopped for a demo with a test in the last commit that could not fail, and the operator was asked to watch a demo resting on it.

Measured earlier: a run ended with two findings in `findings-20260910T010228-5.md`, and what carried them forward was an attended session writing its handoff by hand, not anything here.

## Why the supervisor reads the handoff's open questions

Measured: an S16 worker asked whether a grey area in one demo capture mattered; the supervisor read only `head -3 HANDOFF.md`, and the operator never saw the question.

## Why the supervising session checks the worker's captures instead of walking again

Measured on 2026-10-28: a supervising session rebuilt the demo database and walked all six steps of a worker's demo on an unchanged commit. Every step matched the worker's walk, and the walk took its context from 75,343 to 154,124 in three minutes. The session then had no room to start the retro, and the retro needed a session of its own. The rule to walk every step again had come from the retro before, and this was its first firing.
