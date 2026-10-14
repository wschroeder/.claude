# Measurements behind demo-task's rules

## Why a worker stops its demo server before handing off

Measured on MBG-197 S4 (2026-10-09): a worker started the demo server at
11:56:58 with the Bash tool's `run_in_background`, wrote `BLOCKED:`, and stayed
open until 13:56:58. The loop sat idle for those two hours. The supervisor, not
the worker, is present when the operator works the demo, so it starts the
server then.

## Why a session that did not take the captures walks the demo again

Measured on MBG-197 S8 (2026-10-13): the supervisor resumed a worker's
`BLOCKED:` demo at Section 4 and said at 17:52:14, "I didn't drive the app at
all. A worker session took the screenshots". Later in the same run, a session
committed 91234f1 mid-stop and at 19:29:24 sent one new screenshot without
walking the demo again.

## Why the operate-it steps are written first and then followed literally

Measured on MBG-197 S8 (2026-10-13): no session in the run loaded
`writing-prose`, and the session that posted the demo said at 17:52:14 "I
didn't drive the app at all", so nobody had walked the steps the operator was
handed.
