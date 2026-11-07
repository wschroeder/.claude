# Probing a boundary before you build on it

1. Read this, the detail behind **Probe before you build** in `writing-code`, when a disposition is disputed, when deciding whether a piece of work is exempt, or when labelling a Probe section in a report.

## What counts as a probe

1. Count as a probe only something that ran on this machine in the last few minutes and put its real output in the chat, such as a curl, a SQL query, an IEx snippet, or a small script.

## What is exempt

1. Exempt only mechanical work that crosses no boundary and rests on no unmeasured runtime, algorithm, or logic assumption, such as a refactor of code you wrote this session or an addition structurally identical to siblings you just defined.
2. Never exempt an algorithmic or logical claim in code you own unless you measured it this session.

## Labelling a Probe section

1. Put in every section labelled "Probe", wherever it appears, both the literal command, query, or snippet that ran and its captured output.
2. Never label file reads, grep output, diff reads, or paraphrase as a Probe.
3. When no probe is practical, such as live production infrastructure, a complex seed, or multi-service orchestration, write `UNPROBED — <impracticality reason>`.
4. Before writing that you may not call a service, read the installed CLI or SDK code that builds the request, run its serializer on a sample input, and name that check and its result in the `UNPROBED` line.
5. When no boundary is crossed, such as a pure syntactic finding or a refactor of code from this session, write `EXEMPT — <reason>`.
