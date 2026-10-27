# Measurements behind systematize's rules

The skill body states each rule. This file holds the run that prompted it, for a reader who disputes one.

## Why an existing script is extended rather than a new one written

Measured on the session that prompted this rule: it worked out where a run's tokens had gone using throwaway python, while `session-loop/scripts/session_budget.py` already read those same transcripts and was named in that skill's own description, which had been in context since the first turn.

## Why a skill edit is committed in the same turn

Measured (2026-10-14): a CLAUDE.md paragraph approved at 14:27 was still uncommitted at the retro, five hours and twenty handoffs later.

## Why every added line is read before a commit in `~/.claude`

Measured (2026-10-23): retros, reviews of missed findings, and examples had written one client's ticket keys, repository name, system names, and business vocabulary into 27 files and about 60 commit messages, and the repository had been public the whole time.

## Why the global set is capped

Measured, in *More Skills, Worse Agents? Skill Shadowing Degrades Performance When Expanding Skill Libraries* (Databricks, 2026): pass rate dropped 21% going from a small useful set to 202 skills, shadowing accounted for up to 68% of the loss and was the only statistically significant effect, and the share of runs choosing the right skill fell from 88.0% to 52.6%. Degradation was already measurable at 52 skills and rose monotonically with size.
