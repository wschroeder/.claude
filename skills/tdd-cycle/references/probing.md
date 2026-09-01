# Probing a boundary before you build on it

Detail behind **Probe before you build** in `writing-code`. Read when a
disposition is disputed, when deciding whether a piece of work is exempt, or when
labelling a Probe section in a report.

## What counts as a probe

Something that ran on this machine in the last few minutes and produced output that is now in the chat — a curl, a SQL query, an IEx snippet, a small script. The output is real, not paraphrased. The probe is throwaway; its purpose is to verify the shape of the territory before you build on it.

## What is exempt

Mechanical work that introduces no new algorithmic or logical claim — refactors of code you wrote in this session, additions to modules whose shape you just defined where the addition is structurally identical to existing siblings, anything that doesn't cross a boundary AND doesn't depend on an unmeasured runtime, algorithm, or logic assumption. Algorithmic or logical claims in code you own are NOT exempt unless you've already measured them this session. Tests cover the mechanical surface, not probes.

## Labelling a Probe section

When you label a section "Probe" — in a skill template, a per-finding cycle, an Evidence block, anywhere — the body of that section MUST contain BOTH (a) the literal command, query, or snippet that ran AND (b) the actual captured output from running it. A "Probe" section whose body contains only file reads, grep output, diff reads, or prose paraphrasing what you observed is mis-labeled: those are static-artifact reads, not probes. The mislabeling is the failure mode this rule prevents — the header creates the appearance of a probe having run, and the absence of measurement hides under the heading. When no probe is practical (live prod infra, complex seed, multi-service orchestration), write `UNPROBED — <impracticality reason>` in the section body. When no boundary is crossed (pure syntactic finding, refactor of code from this session), write `EXEMPT — <reason>`. Both `UNPROBED` and `EXEMPT` are honest disposition states; staging static reads under the Probe label is not.

## Why the rule exists

The Evidence block catches false claims *after* they reach the user. Pre-hoc probes prevent false starts *before* they get baked into the code. The "code looks right but doesn't do what we said" failure mode almost always traces back to a boundary assumption that nobody verified during construction. A three-line probe in chat costs ten seconds; the same assumption discovered in code review costs the round trip plus a fix.
