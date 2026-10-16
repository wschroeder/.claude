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

## Why a browser that will not start stops the demo

Measured on S11 (2026-10-15): Chrome refused to open a tab with "The browser is
already running for …/chrome-devtools-mcp/chrome-profile", for a worker at
13:25:53 and for the supervisor at 13:34:22. The worker switched to a curl
capture at 13:26:06. The supervisor said "I'll drive the app over HTTP instead"
at 13:34:24 and posted the demo as walked. Neither session quoted a rule for it.
The operator asked at 17:42, "Where are your demo screenshots?" The later walk
in a real browser had to reword two steps that curl could not show: a hover
tooltip and a collapsed disclosure. The lock belonged to a chrome-devtools-mcp
instance started on 2026-10-07, whose Chrome had started at 10:33 that morning.
