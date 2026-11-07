---
name: subagents
description: Whether to hand work to a subagent, and what its prompt must carry. One question answers the first half — will you open the same material after it returns? The second half is a fixed contract: file paths, output format, scope, failure instructions, and a footer forbidding the agent from delegating onward. Also holds the standing exception that investigation is done directly, the cases where delegating genuinely pays, when a fork is the right tool and when it is the wrong one, and how to match the model to the task. Use before spawning an agent, a fork or a workflow, before handing a review, search, migration or investigation to one, and whenever deciding whether to delegate at all.
---

# subagents — whether to hand it over, and what to say if you do

Other skills cite this one rather than restating it: `session-loop`, `writing-code`, `quick-review`, `security-review`, and `design-gap-task`.

## The one question

Before every subagent or workflow, ask:

> After this agent returns, will I open the same material it opened?

1. If yes, do not delegate, because you would pay for the material twice.

## When delegating pays

1. Delegate research against sources you will never open yourself.
2. Delegate wide or mechanical searches where only the answer comes back.
3. Delegate independent checking of a list of claims, where you read only a yes or no for each.

## When it does not

1. Do not delegate a change you will then review line by line.
2. Do not hand `quick-review` or `security-review` to a subagent, because you read and apply every finding anyway.
3. Never delegate investigation, such as tracing where a config value, an env var, a secret, or a deployment behavior comes from; follow the chain to its end yourself.

## A fork is a continuation, not a delegation

1. Use `subagent_type: "fork"` only when the agent needs the conversation rather than a specification, such as exploring a branch of work you are inside, a second opinion on a judgment made in context, or trying the other road at a decision point.
2. Spawn a fresh agent whenever the job can be written down, such as research, a wide search, a migration, or a review of a named diff.
3. Never fan out with forks, and never keep two forks alive at once, because each fork acts as the orchestrator and messages its siblings.
4. Run fresh agents in parallel by spawning them in a single message.
5. Remember that a fork always runs on your model and ignores a model override.

## After you spawn, end the turn

1. Say in one line what you are waiting for, and stop; you are notified when the agent completes.
2. Do not call `ListAgents`, spawn an agent to report another is idle, or schedule a wakeup.
3. Do not start work on the agent's topic while it runs.

## Matching the model

1. Use Haiku for wide or mechanical passes where only the answer matters.
2. Use Sonnet for work needing judgment you will not re-read yourself.
3. Keep the driver model for reasoning you are holding in this session.
4. When the choice is close, take the more capable model, because a wrong result is redone at full price.

## What the prompt must carry

Every delegation prompt carries these:

1. Specific file paths, never a description such as "the auth module".
2. The expected output format.
3. Scope boundaries: what the agent must not touch or decide.
4. Failure instructions in this form: "if X fails, stop and report — do not retry with variations."
5. The footer, verbatim:

   ```
   You are a subagent. Do all work directly — do NOT use the Task tool to delegate.
   ```

6. Where the work follows a code change, also hand over the callers, comments, tests, and outside references that the pre-edit scan in `writing-code` found.

## What this skill does not cover

Session handoffs and the context ceiling belong to `session-loop`, review passes to `quick-review` and `security-review`, and the choice between a script and a skill to `systematize`.
