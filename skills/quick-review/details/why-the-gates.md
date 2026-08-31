# Why the gates are shaped the way they are

Read this when a gate feels arbitrary, or when deciding whether to loosen one.
Nothing here is needed to run a review — SKILL.md carries every rule.

## Why a disposition has to be an observation

The 108-attempt floor fights one failure: stopping at the first finding. It does
not fight the other. `NONE FOUND because the guard above runs first` is prose
*about* absence, and it is satisfiable by writing a plausible sentence. That is
the slot real bugs slip through.

So a disposition is an observation, not a verdict — the same rule the Evidence
Format applies to every other claim, turned on the review itself. CodeRabbit
out-catches a read-only review because it runs scripts against the repo before
each finding: its dispositions are demonstrated rather than narrated.

## Why the artifact has to be the right shape

Requiring an artifact is the easy half. Requiring the *right* artifact is the
hard half. A grep that finds no literal `DROP` does not prove "no SQL
injection", because interpolation is the vector, not the keyword. A decorative
artifact is no better than prose — it just costs more to produce.

## Why the destructive gate is a ratchet

Rows excluded by a filter are legitimate data outside the caller's view. The
vocabulary of leakage — "leaked rows", "stale data", "ghost records",
"abandoned data" — is itself the smell: it pattern-matches a filter change into
a constraint change and licenses destruction the diff never authorized.

The shape of the diff is evidence of intent. If the developer had wanted the
rows deleted, they would have written that change.

## Why an acknowledged deviation still gets flagged

The most expensive miss in this class is a documented tradeoff treated as a
settled question, because each review round reads the comment as evidence that
the team already weighed it. The comment is the trigger to weigh the tradeoff
again, every round, against the current state of the code — not a record that
weighing has happened.
