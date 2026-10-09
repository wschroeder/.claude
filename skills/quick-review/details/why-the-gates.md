# Why the gates are shaped the way they are

Read this when a gate feels arbitrary, or when deciding whether to loosen one.
Nothing here is needed to run a review — SKILL.md carries every rule.

## Why a disposition has to be an observation

Walking every live angle fights one failure: stopping at the first finding. It
does not fight the other. `NONE FOUND because the guard above runs first` is prose
*about* absence, and it is satisfiable by writing a plausible sentence. That is
the slot real bugs slip through.

So a disposition is an observation, not a conclusion — the same rule the Evidence
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

## Why a changed rule pulls in code the diff never touched

"Pre-existing and not made worse" asks whether the old code got worse. When the
diff changes the rule that code answers to, the code did not change and is now
wrong, so the question passes it every time.

Measured on 2026-10-07: a change let statement holdings be negative everywhere,
at the operator's direction. Its review listed the seed import, the deposit
balance, and the fallback holdings, all still dropping negative values, as Notes
under "pre-existing and not made worse", and printed no Fixes. A Copilot review of
the pull request raised all three, plus two aggregates still filtering on
collateral value above zero and a rollback that left statements verified. All
four of its findings were fixed in the same pull request.

## Why the receipt is a checklist

A count of candidates can be written without running a single pass, and so can a
line saying the review found nothing. A list of every angle with what was seen
at each cannot be written without at least walking the angles, and the angle
numbers exist only in this skill, so a session that never loaded it cannot fill
the list in. `security-review` already ends with the same two lists, a checklist
and a file list.

Measured on MBG-208: six loads of this skill, and no session printed the Output
block; each wrote an Evidence block with a one-line "found nothing" instead.
CLAUDE.md then gained an exception letting the block print after the Evidence
block. Measured on MBG-197 S4, after that change: three sessions loaded the
skill and none printed the block. Three of five card notes carried a Coverage
count no session had printed; one of those drivers never loaded the skill.
Earlier, two workers on one slice wrote "quick-review clean" into bd 29 and 51
seconds after loading the skill, and neither printed an Output block.

The review stays in the session that wrote the change. A subagent reviewing
without the mission and the card's context raises false alarms it cannot
filter, and reloads material the driver already holds.
