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
3. If one file alone is larger than a stage, split it at its own section boundaries, such as a section-marker comment, a top-level class, or a top-level function, and never inside one. Name each part by the boundary text it starts at, never by line numbers, and fingerprint it as the text between its two boundaries piped through `shasum`.
4. Put a test file in the same stage as the code it tests when both fit; otherwise give the tests a stage of their own that names the production stage it checks.
5. Make the last stage **cross-group**: the angles that follow a value, a state, or a rule across groups, which are 1.2, 1.4, 1.19, 2.18, 2.19, 5.7, 6.7, 6.8, 6.9, 7.4, 7.7, and 9.9. It works from the earlier stages' notes and targeted greps, and never re-reads a whole group's diff.
6. Keep the cross-group stage's inputs under the same third, with the notes taking at most half of it; before it starts, measure the notes file with `wc -c` and convert at the ratio from "Size it".
7. If the notes take more than half that cap, split the stage in two: the first walks 1.2, 1.4, 1.19, 2.18, 2.19, and 5.7, and the second walks 6.7, 6.8, 6.9, 7.4, 7.7, and 9.9. Each part reads the stage plan and only the `cross-group` marks for its own angles.
8. Before each part starts, measure its marks by listing its angles in one pattern:

  ```bash
  grep -E '^cross-group (1\.2|1\.3|1\.4|1\.19|2\.18|2\.19|5\.7):' <notes> | wc -c
  ```

9. If a part's marks still take more than half the cap, split its angles in two again until every part's marks fit or a part holds one angle.
10. If a one-angle part's marks still do not fit, walk them in batches of whole lines, each under half the cap, and write what each batch found to the notes before the next batch starts.
11. Have whichever part walks 1.4 also read the 1.3 marks, keep 1.3 in its pattern, and run the caller trace from "After a fix".
12. Read every mention of the cross-group stage, here or in `SKILL.md`, as every part of a split one.

## Run the stages

1. Have each stage walk every pass over its own files and mark each angle only the cross-group stage can check, on its own line in the notes, at the first column with no bullet, as `cross-group <angle>: <the symbol or rule to follow there>`.
2. Give each changed function its own `cross-group 1.3` mark.
3. After each stage, write it to the notes file and run `--self`; if the next stage fits in the room left, start it, and if not, hand off naming the notes file and the next stage, and nothing else about the review.
4. Run Classify and Output once, after the cross-group stage, over every stage's candidates.
5. Write a handoff between stage sessions as a staged review alone: name `quick-review`, the notes file, and the next stage, and leave out the skill that called the review, so the next session loads only `quick-review` and its stage's details files.
6. Record the calling skill and the step it resumes at in the notes file's header, and return to it after Output.

## Run the stages in parallel

1. If the plan has two or more stages before the cross-group stage, you may run them as fresh agents spawned in one message; keep the cross-group stage, Classify, Output, and every fix in this session.
2. Write the stage plan, with each stage's files and fingerprint, to the notes file before you spawn.
3. Size each stage under a third of the room a fresh agent has after reading `quick-review`'s SKILL.md, this file, and its stage's details files.
4. Give each agent its own notes file beside the main one, `<notes without .md>.stage-<name>.md`, and append them to the main notes file in plan order once every agent returns; never let two agents write one file.
5. Tell each agent to edit no file and to run no test, mutation, server, or container; it writes each run an angle owes as its own line, `owed-run <stage> <angle>: <command, and what its output must show>`.
6. After the batch, run the `owed-run` lines one at a time in this session, and write each result under its stage before the cross-group stage starts.
7. Ask each agent to return one line naming its notes file and its candidate count, and leave its notes unread until the cross-group stage.
8. Run each agent on the driver model.
9. Write each prompt to `subagents` "What the prompt must carry", naming the repository path, the merge base, the stage's files, the details files the stage calls for, the notes file to write, and the limits in this section.
10. If an agent fails or returns without its notes file, run that stage in this session; do not respawn it with variations.
11. After a fix, re-run the changed stages the same way, as "After a fix" says.

## After a fix

1. Record each stage's fingerprint in the notes file: `git diff <merge-base> -- <its files> | shasum`.
2. In the next round, re-run every stage whose fingerprint changed, keep the result of every stage whose fingerprint matches, and always re-run the cross-group stage.
3. Add the targeted re-checks from [review-fix-loop.md](review-fix-loop.md) to the stage that holds the fix.
4. If the cross-group stage's trace of each changed function's callers (1.3) or each new state's readers (1.4) leads into a kept stage, re-run that stage too.
