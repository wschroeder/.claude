---
name: subagents
description: Whether to hand work to a subagent, and what its prompt must carry. One question settles the first half — will you open the same material after it returns? The second half is a fixed contract: file paths, output format, scope, failure instructions, and a footer forbidding the agent from delegating onward. Also holds the standing exception that investigation is done directly, the cases where delegating genuinely pays, and how to match the model to the task. Use before spawning an agent or a workflow, before handing a review, search, migration or investigation to one, and whenever deciding whether to delegate at all.
---

# subagents — whether to hand it over, and what to say if you do

Other skills cite this one rather than restating it: `session-loop` for the
loop's own thresholds, `writing-code` for the review sequence, `quick-review`,
`security-review` and `design-gap-task` for work they keep in-session.

## The one question

Before every subagent or workflow, ask:

> After this agent returns, will I open the same material it opened?

If yes, do not delegate. You pay the agent's climb from an empty context up to
a full one, and then your own reading on top. The material gets read twice and
you are charged for both.

That is the whole test. Everything below is the cases it resolves to.

## When delegating pays

The agent's context genuinely replaces one you would otherwise have loaded:

- research against sources you will never open yourself
- wide or mechanical searches where only the answer comes back
- independent checking of a list of claims, where you read verdicts and not
  the material behind them

## When it does not

**When you will review the result.** Building a change you then read line by
line puts the diff in your context regardless, so the delegation saved nothing.
If the working agreement says you review every change, handing that change to
an agent cannot pay — the standard is right, and the delegation is what goes.

**The reviews are the case this keeps catching.** A session that hands
`quick-review` and `security-review` to subagents still reads every finding and
applies it, so the diff lands in its context either way. This one is measured,
not argued: `session-loop/references/driver-loop.md`, "Why handing the reviews
to a subagent does not pay", has the run that settled it.

**Investigation, always.** Tracing where a config value, an env var, a secret or
a deployment behavior actually comes from means following the chain to its end.
An agent that returns the first plausible match has spent the search without
producing the answer, and you cannot tell which you got without redoing it.

## Matching the model

Haiku for wide or mechanical passes where only the answer matters. Sonnet for
work needing judgment you will not re-read yourself. Keep the driver model for
reasoning you are holding in this session. Where the choice is close, take the
more capable model — a wrong result is redone at full price, so saving tokens on
a close call buys nothing.

## What the prompt must carry

Every delegation prompt, without exception:

1. **Specific file paths.** Not "the auth module" — the paths.
2. **The expected output format.** What shape the answer comes back in, so you
   are not parsing prose.
3. **Scope boundaries.** What the agent is not to touch or decide.
4. **Failure instructions**, in this form: "if X fails, stop and report — do not
   retry with variations." Without it an agent burns its context rediscovering
   that something is broken.
5. **The footer**, verbatim:

   ```
   You are a subagent. Do all work directly — do NOT use the Task tool to delegate.
   ```

Where the work follows a code change, hand over what the pre-edit scan in
`writing-code` already turned up — the callers, comments, tests and outside
references it found — so none of it is rediscovered mid-task.

## What this skill does not cover

Where a session hands off and what its context ceiling is (`session-loop`).
What the review passes look for (`quick-review`, `security-review`). Whether a
repeated piece of work should become a script or a skill (`systematize`).
