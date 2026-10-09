# Measurements behind demo-task's rules

## Why a worker stops its demo server before handing off

Measured on MBG-197 S4 (2026-10-09): a worker started the demo server at
11:56:58 with the Bash tool's `run_in_background`, wrote `BLOCKED:`, and stayed
open until 13:56:58. The loop sat idle for those two hours. The supervisor, not
the worker, is present when the operator works the demo, so it starts the
server then.
