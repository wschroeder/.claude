# Measurements behind tdd-cycle's rules

The skill body states each rule. This file holds the run that prompted it, for a reader who disputes one.

## Why a change that only moves a setting gets no test

Measured: a test shipped with a change of an image-quality setting from 'high' to 'original' asserted the string 'original', and its name promised small digits would read better, which only a hand run against real documents could show. Nobody had tested 'high' either.

## Why a bug seen on screen is tested through the action it blocked

Measured: a spec written for a clipped button checked only that the button fit its cell and never clicked it. Its replacement clicks the button and checks the totals the person reads. Playwright still clicked the button when a cell one pixel wide hid it, and the test passed.

## Why every assertion a caller depends on is mutated

Measured: in one run, three assertions survived mutation — a four-cell shape cut to three cells, and an entire rotation state replaced with garbage, both left a 17-test suite fully green — and all three sat under assertions their author had judged not to matter.

## Why every clause of every criterion gets its own mutation

Measured: on one project, the reviewer failed the first review of every slice on a test that a mutation of one clause would have exposed, such as "ten or fewer" checked on one random round, and a float back that would still have passed as an instant jump.

## Why a mutated file is restored from a copy, not from git

Measured: a session wrote a new CSS rule, mutated the file a minute later, restored with `git checkout`, and the next two mutations in the same run died on an assertion that their search text was missing, because the rule was gone; it had to write the rule again from memory.

## Why the card moves only after the reviews

Measured: a session reviewed its first card, then committed three more straight to `demoable` with no review, and its handoff named none of them. One of the three carried a bug that left a job running forever, and only the loop's own reviewer between sessions caught it. On the next slice, with that rule in place below an example that went straight from commit to move, two sessions moved three cards with no review loaded.

## Why a card never moves without a commit

Measured: one run closed six issues while the tree held one commit — `bd init` — and five files that had never been committed at all.

## Why a turn takes the next step it names

Measured across one run: one turn ended on a sentence naming the next card it would pick up, another on "I will write it there verbatim", and the operator's next messages were "Are you working?" 46 minutes later and "? So what now?" two hours and thirteen minutes later.

## Why the budget check runs after every commit

Measured: two build sessions finished eight handoff tasks, with no commit, without one check and crossed the ceiling unwarned, until the hook stopped them at 170,788 and 173,797.

Measured: two build sessions ran without a single check, one of them to 374,944 tokens against a ceiling of 170,000, and when it did stop it asked to hand off instead of doing it, then sat idle for two hours until the operator answered.

## Why `keep going` means keep going

Measured: a session read "126,411 of 170,000 — keep going", reasoned that a full card cycle runs 126,000 to 141,000 tokens and would not fit, and handed off at 141,304 with two cards' room left. The session that followed reached its first commit at 114,028 and then closed a second and a third card for 21,239 and 14,670.
