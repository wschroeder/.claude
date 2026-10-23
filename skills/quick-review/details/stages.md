# Staging a review too big for one session

A whole-branch review reads every file group once per round. When the diff is bigger than the room a session has left, plan the review as stages at Pass 0, before you read any of the diff. Without a plan, a session reads until the handoff hook stops it partway through a group, and the next session starts over on whatever the handoff remembered.

## Size it

1. Measure the diff per file, in characters:

   ```bash
   git diff --numstat <merge-base>..HEAD
   git diff <merge-base>..HEAD -- <file> | wc -c
   ```

2. Read the context in use with `python3 ~/.claude/skills/session-loop/scripts/session_budget.py . --self`. The room left is 170,000 minus that figure.
3. Convert characters to tokens at about 3.5 characters per token. After the first diff read, check that ratio against `--self` and use the measured one.
4. If the whole diff takes more than a third of the room left, stage the review. The other two thirds go to surrounding code, greps, probes, and the passes' own writing. Otherwise, review in one go and skip the rest of this file.

## Cut the stages

- Group files the way the code is layered, so that each stage reads a caller and its callee together where it can: for example, domain with application, then server routes with their views, then tests, then docs, specs, and data.
- Each stage's diff must stay under a third of the room a fresh session has after loading this skill. Split a group that is too big by directory, never through the middle of a file.
- Put a test file in the same stage as the code it tests when both fit. Otherwise give the tests a stage of their own, and have that stage name the production stage it checks.
- The last stage is always **cross-group**: angles that follow a value, a state, or a rule across groups. These are 1.2, 1.4, 1.19, 2.18, 2.19, 5.7, 6.7, 6.8, 6.9, 7.4, 7.7, and 9.9. It works from the earlier stages' notes and from targeted greps, and it never re-reads a whole group's diff.

## Run the stages

- Each stage walks every pass over its own files and marks an angle that only the cross-group stage can settle as `cross-group` in its notes, together with the symbol or rule to follow there.
- After each stage, write it to the notes file and run `--self`. If the next stage fits in the room left, start it. If it does not, hand off naming the notes file and the next stage, and nothing else about the review.
- Classify and Output run once, after the cross-group stage, over every stage's candidates.

## After a fix

Record each stage's fingerprint in the notes file: `git diff <merge-base> -- <its files> | shasum`. In the next round, re-run every stage whose fingerprint changed, and keep the result of every stage whose fingerprint still matches. Always re-run the cross-group stage. Add the targeted re-checks from [review-fix-loop.md](review-fix-loop.md) to the stage that holds the fix.

A fix can change how code in an unchanged stage behaves, for example by handing a caller a new state. The cross-group stage catches that by tracing each changed function's callers (1.3) and each new state's readers (1.4) into every stage, changed or not. If either trace leads into a kept stage, re-run that stage too.
