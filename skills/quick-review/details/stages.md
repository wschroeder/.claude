# Staging a review too big for one session

1. When the diff is bigger than the room a session has left, plan the review as stages at Pass 0, before you read any of the diff.

## Size it

1. Measure the diff per file, in characters:

   ```bash
   git diff --numstat <merge-base>..HEAD
   git diff <merge-base>..HEAD -- <file> | wc -c
   ```

2. Read the context in use with `python3 ~/.claude/skills/session-loop/scripts/session_budget.py . --self`. The room left is 170,000 minus that figure.
3. Convert characters to tokens at about 3.5 characters per token. After the first diff read, check that ratio against `--self` and use the measured one.
4. If the whole diff takes more than a third of the room left, stage the review. Otherwise, review in one go and skip the rest of this file.

## Cut the stages

1. Group files the way the code is layered, so that each stage reads a caller and its callee together where it can, such as domain with application, then server routes with their views, then tests, then docs, specs, and data.
2. Keep each stage's diff under a third of the room a fresh session has after loading this skill, and split a group that is too big by directory, never through the middle of a file.
3. Put a test file in the same stage as the code it tests when both fit; otherwise give the tests a stage of their own that names the production stage it checks.
4. Make the last stage **cross-group**: the angles that follow a value, a state, or a rule across groups, which are 1.2, 1.4, 1.19, 2.18, 2.19, 5.7, 6.7, 6.8, 6.9, 7.4, 7.7, and 9.9. It works from the earlier stages' notes and targeted greps, and never re-reads a whole group's diff.
5. Keep the cross-group stage's inputs under the same third, with the notes taking at most half of it; before it starts, measure the notes file with `wc -c` and convert at the ratio from "Size it".
6. If the notes take more than half that cap, split the stage in two: the first walks 1.2, 1.4, 1.19, 2.18, 2.19, and 5.7, and the second walks 6.7, 6.8, 6.9, 7.4, 7.7, and 9.9. Each part reads the stage plan and only the `cross-group` marks for its own angles.
7. Before each part starts, measure its marks by listing its angles in one pattern:

  ```bash
  grep -E '^cross-group (1\.2|1\.3|1\.4|1\.19|2\.18|2\.19|5\.7):' <notes> | wc -c
  ```

8. If a part's marks still take more than half the cap, split its angles in two again until every part's marks fit or a part holds one angle.
9. If a one-angle part's marks still do not fit, walk them in batches of whole lines, each under half the cap, and write what each batch found to the notes before the next batch starts.
10. Have whichever part walks 1.4 also read the 1.3 marks, keep 1.3 in its pattern, and run the caller trace from "After a fix".
11. Read every mention of the cross-group stage, here or in `SKILL.md`, as every part of a split one.

## Run the stages

1. Have each stage walk every pass over its own files and mark each angle only the cross-group stage can check, on its own line in the notes, at the first column with no bullet, as `cross-group <angle>: <the symbol or rule to follow there>`.
2. Give each changed function its own `cross-group 1.3` mark.
3. After each stage, write it to the notes file and run `--self`; if the next stage fits in the room left, start it, and if not, hand off naming the notes file and the next stage, and nothing else about the review.
4. Run Classify and Output once, after the cross-group stage, over every stage's candidates.

## After a fix

1. Record each stage's fingerprint in the notes file: `git diff <merge-base> -- <its files> | shasum`.
2. In the next round, re-run every stage whose fingerprint changed, keep the result of every stage whose fingerprint matches, and always re-run the cross-group stage.
3. Add the targeted re-checks from [review-fix-loop.md](review-fix-loop.md) to the stage that holds the fix.
4. If the cross-group stage's trace of each changed function's callers (1.3) or each new state's readers (1.4) leads into a kept stage, re-run that stage too.
