# Measurements behind demo-task's rules

- Why a worker stops its demo server before handing off
- Why a session that did not take the captures walks the demo again
- Why a page script's click is not a person's click
- Why the operate-it steps are written first and then followed literally
- Why the Chrome tool comes first and Playwright last
- What S11 showed when the browser would not start
- Why the ask says which links the walk did not check
- Why a handoff's dead end does not excuse trying the Chrome tool
- Why the agent leaves the demo server running at the desktop too
- Why the worker runs the demo file's own commands, written on one line
- Why every capture is the whole page and is opened before it is sent
- Why a fault the slice made is fixed in the demo phase, with no card
- Why a walk is recorded on disk and may span sessions
- Why an acceptance that asks something is answered first
- Why a demo driver and its captures stay out of the repository
- Why everything the operator reads is plain English
- Why an id is a tag, never part of the sentence
- Why a session past the ceiling hands off before starting the template
- Why looking is not suspended in rapid mode
- Why rapid mode does not commit
- Why rapid mode has no size limit
- Why `beads` and `proof` come from `bd show`
- Why the steps are printed in full in the message
- Why you start what the demo needs yourself
- Why you do the setup a phone cannot do
- Why the captures are set beside what the operator said during the spec
- Why each capture before an action is read as a newcomer
- Why a suspected fault is compared with the default branch before posting
- Why the record names what the definition of released names and what you drove
- Why you play on until the thing the slice changed happens
- Why you show yourself driving it, not one frame
- Why being unable to drive it is a finding
- Why the demo output is pasted and sent, not only read
- Why a new way to reach the product sends you back to Section 3
- Why a handoff's question is searched for in the design documents first
- Why a demo after a background run sends one push, last
- Why a worker writes `BLOCKED:` only once the drive is complete
- Why a request to do something in this phase is done in this phase
- Why a decision about the product goes into the design document in this run
- Why the operator's own promise to check stops the hand to the retro

## Why a worker stops its demo server before handing off

Measured (2026-10-09): a worker started the demo server at
11:56:58 with the Bash tool's `run_in_background`, wrote `BLOCKED:`, and stayed
open until 13:56:58. The loop sat idle for those two hours. The supervisor, not
the worker, is present when the operator works the demo, so it starts the
server then.

## Why a session that did not take the captures walks the demo again

Measured (2026-10-13): the supervisor resumed a worker's
`BLOCKED:` demo at Section 4 and said at 17:52:14, "I didn't drive the app at
all. A worker session took the screenshots". Later in the same run, a session
committed 91234f1 mid-stop and at 19:29:24 sent one new screenshot without
walking the demo again.

Measured again on S12 (2026-10-16): the handoff written at 01:16 CDT said
"resume at Section 4. Post … the walk results from .tmp/demo-s12/WALK.md". The
next session wrote at 01:17 CDT, "The template asks a new session to walk every
step again. I did not". The operator asked at 03:04 CDT, "Have you walked
through and made screenshots?" The session quoted the rule and followed the
handoff instead, so demo-task and clear-task now both say how a handoff
written before Section 4 words its first step.

## Why a page script's click is not a person's click

Measured on S12 (2026-10-16): at 01:14 CDT a demo session walked the merge
dialog with `evaluate_script` calling `b.click()` and wrote the step up as
walked.

## Why the operate-it steps are written first and then followed literally

Measured (2026-10-13): no session in the run loaded
`writing-prose`, and the session that posted the demo said at 17:52:14 "I
didn't drive the app at all", so nobody had walked the steps the operator was
handed.

## Why the Chrome tool comes first and Playwright last

The operator said on 2026-10-19, at the S14 retro: "playwright is slow,
awkward, and token-expensive in comparison to using Chrome MCP." The rule this
replaced stopped the demo and asked the operator to free the browser profile.
That rule treated a collision as something the operator had to clear, while the
collision came from every chrome-devtools-mcp instance sharing one profile
directory. The tool's own error names the fix: "Use --isolated to run multiple
browser instances." Its `--help` says `--isolated` "creates a temporary
user-data-dir that is automatically cleaned up after the browser is closed".
Since 2026-10-19 the chrome-devtools entry in `~/.claude.json` runs with
`--isolated` and `--headless`, so a second session gets its own profile rather
than the first one's lock.

The S11 measurement below still holds for the HTTP fallback: a fetched page is
not a walk.

## What S11 showed when the browser would not start

Measured on S11 (2026-10-15): Chrome refused to open a tab with "The browser is
already running for …/chrome-devtools-mcp/chrome-profile", for a worker at
13:25:53 and for the supervisor at 13:34:22. The worker switched to a curl
capture at 13:26:06. The supervisor said "I'll drive the app over HTTP instead"
at 13:34:24 and posted the demo as walked. Neither session quoted a rule for it.
The operator asked at 17:42, "Where are your demo screenshots?" The later walk
in a real browser had to reword two steps that curl could not show: a hover
tooltip and a collapsed disclosure. The lock belonged to a chrome-devtools-mcp
instance started on 2026-10-07, whose Chrome had started at 10:33 that morning.

## Why the ask says which links the walk did not check

Measured (2026-10-16): the walk checked each cut PDF with
`qpdf --check`, `pdffonts`, and `pdftotext` only, although `pdftoppm` was on
PATH. The demo ask still said, "Check that the text still looks like the
original. It should, because qpdf copies the pages instead of redrawing them."
The operator replied on 2026-10-19 at 08:40, "You're asking me to compare this
to the original, but you did exactly that, correct? The images were nearly byte
identical in your runthrough?" The walk had compared no images.

## Why a handoff's dead end does not excuse trying the Chrome tool

Measured (2026-10-19): a handoff written on 2026-10-16 recorded
"Dead end: the chrome-devtools MCP fails with 'The browser is already
running'", and every S16 worker's handoff copied it. The demo worker called no
Chrome tool and wrote "Playwright drove the walk: the Chrome devtools tool
fails here with 'The browser is already running'". Three minutes later the
supervising session opened the tool with an isolated context, and it worked.

## Why the agent leaves the demo server running at the desktop too

Measured (2026-10-19): twice in one day the supervising session
walked the demo, stopped its own server, and handed the operator a start
command. For S15 the operator replied at 10:53, "Go ahead and set up and start
the server, please." For S18 they replied at 13:27, "Start the server.", 29
minutes after the ask. The S18 steps also told the operator to press Ctrl-C to
restart the app. Once the agent had started the server, that key reached
nothing, and nobody restarted the app before the operator accepted at 13:31.

## Why the worker runs the demo file's own commands, written on one line

Measured (2026-10-19): the worker walked the demo and served
the app from scratch scripts in `/tmp` that set every variable. It then wrote
a walk command into the demo file that left out three required settings, and
edited the copied `serve.sh` without running it again. At the demo stop the
worktree guard refused `bash test-results/s19-chrome-demo/serve.sh` as too
complex to verify. The supervisor fell back to `node --env-file`. The shell
already exported the main checkout's `DATABASE_URL`, and `--env-file` does not
override a variable that is set, so two starts failed against the wrong
database. A single command line that set every variable itself was accepted
and came up. Reaching it took four and a half minutes, and the operator
cancelled once by accident while the starts were failing.

## Why every capture is the whole page and is opened before it is sent

Measured (2026-10-21): the supervisor took its three captures
with `take_screenshot` and the `uid` of the "Verification review" heading, so
each image held only those two words. It checked each step against the page
snapshot's text, sent the images at 15:13 CDT without opening any, and the
operator replied at 15:23 CDT, "Those screenshots don't look like page
screenshots at all. Did you really run the demo?"

## Why a fault the slice made is fixed in the demo phase, with no card

Measured (2026-10-23): a demo session's own walk found that an activity page
named a merged-away record by its raw id. It filed a backlog card, told the
operator "It's in the backlog and outside" the slice, and said it had not
checked whether the default branch did the same. The default branch had
neither of the two events involved; this branch added both. A later session
filed a second card and offered to file a third, though the operator had
already said the slice's faults get fixed. The operator rejected the demo:
"you noticed stuff created during this slice and then chose to defer it. Fix
it." The second fault's line of code was on the default branch too, but only
the slice's new data reached it.

## Why a walk is recorded on disk and may span sessions

Measured (2026-10-23): a fifteen-step browser walk began at 53,786 tokens of
context and reached the handoff point at step 14. The next session walked all
fifteen steps again and fit them only by posting at 150,820 of 170,000, past
the budget's "finish the step you are on". Nothing had been committed between
the two walks.

## Why an acceptance that asks something is answered first

Measured (2026-10-23): the operator accepted a demo with "Accepted. Ready to
move to a PR? It was just a one line change, right?" The session's reasoning
already held the answer, six files and 38 added lines, but its only reply was
a question asking whether to open the pull request or run the retro first.
Section 7's "hand to `retro-task` now… do not ask whether to run it" and the
operator's request covered the same moment, and the session asked instead of
choosing. The operator answered the sequencing question by removing the
version check scripts the change should not have carried.

## Why a demo driver and its captures stay out of the repository

The operator said on 2026-10-27, "we aren't committing demo scripts!" Two
slices in a row had committed the walk written for their demo as a browser
test, and the operator had both removed from the branch. A walk written to show
one demo describes that slice's screens and is dead once the demo is over.
Earlier, of five slices of past captures kept in the tree, the operator said
"Useless. This work is in the past."

This replaced an older rule that committed the driver and sent it through
`quick-review` and `security-review` before the commit. With nothing committed,
there is nothing for those reviews to read.

## Why everything the operator reads is plain English

Measured: one run opened its demo with twelve refs and ten labelled records, and the operator's whole reply was that they did not understand any of it. The records were correct. Nobody could read them.

## Why an id is a tag, never part of the sentence

Measured: an S4 demo told the operator "I could not drive the one continuous run that [R23] describes". Writing it as "I could not drive a single run from the world map into a battle and back out [R23]" costs one clause and no lookup.

## Why a session past the ceiling hands off before starting the template

Measured: a session printed "turn 72, context 231,229 of 170,000 — hand off", quoted that line back in its own evidence block, created ten cards over the next two hours, printed the same line again at 251,737, and ended at 263,205.

## Why looking is not suspended in rapid mode

Measured (2026-10-24): a session made a rapid fix, wrote "I couldn't load the browser again this turn" without calling it, and handed the check over; the operator answered half an hour later, "That's crazy. You can use a browser. Headless, isolated".

## Why rapid mode does not commit

Measured: a session committed mid-tweak and the operator's next turn was "Wait, I wasn't ready for commit! We were doing some quick experimenting/tweaking in our demo phase!"

## Why rapid mode has no size limit

Measured: the operator took a whole padding rework in rapid mode on purpose, and said afterwards they had prioritized speed over rigor knowing what it cost.

## Why `beads` and `proof` come from `bd show`

Measured: an S15 demo record put the enemy test under the wrong card, written by a session that had run no `bd` command at all, and both cards had to be closed twice.

## Why the steps are printed in full in the message

Measured: a demo sent its steps to the operator's phone, named the file's path, printed none of them, and the operator replied "I'll need to see the steps in full here."

## Why you start what the demo needs yourself

Measured: a demo's last step told an operator on a phone to run the serve command, and they replied "Haha somehow I doubt I can run that command on my phone with any effect."

## Why you do the setup a phone cannot do

Measured: a demo told an operator on a phone to put a damaged save into a Mac folder and run the game there, and they replied "you ask the impossible from a phone".

## Why the captures are set beside what the operator said during the spec

Measured: a demo's own phone capture showed the common room list the operator had called "really poor" and chosen to remove, the demo reported it as working, and the operator called it "a leftover thing".

## Why each capture before an action is read as a newcomer

Measured: a phone capture offered TALK while the party faced the man beside the companion, the demo reported it as matching the spec, and the operator talked to the wrong man.

## Why a suspected fault is compared with the default branch before posting

Measured (2026-10-23): a walk saw one record shown as two rows, wrote "this probably predates" this slice in its last message, and the handoff and the next session dropped it.

Measured: no build session in one run opened the app, and the demo's own first drive found two bugs.

## Why the record names what the definition of released names and what you drove

Measured: a session quoted a definition of released that named a URL, in the same evidence block that recorded it driving a container on localhost, and the operator caught it rather than the template.

## Why you play on until the thing the slice changed happens

Measured: an S12 demo told the operator to watch a column's smoke under fire because "this drive had no fighting in it", and they asked why the battle part could not be tested.

Measured: an S4 demo said "Nothing new appears on screen", and the operator replied "I don't see in the screenshots the proofs that you're asking me to do."

## Why you show yourself driving it, not one frame

Measured: a demo of a slice whose whole promise was landing the player in a named world showed two opening frames, sent the game no input, and left the operator asking whether the assistant could move the character at all.

## Why being unable to drive it is a finding

Measured: a demo wrote "dragged the first battalion 150 files forward" from a method call, admitted further down the same message that it could not send the window a keystroke, told the operator to drag a battalion, and shipped — and the operator's reply was that they could not drag anything at all.

## Why the demo output is pasted and sent, not only read

Measured: the operator saw nothing but the summary until they asked for the output.

## Why a new way to reach the product sends you back to Section 3

Measured: a demo built a phone web build mid-stop, sent the link after the title screen alone, and the operator found within minutes that the touch stick was invisible and that a tap walked through a door.

## Why a handoff's question is searched for in the design documents first

Measured (2026-10-24): a demo asked the operator what an imported value field holds, and the operator answered "We've already decided this." The spec said so, and the session searched it only after the reply.

## Why a demo after a background run sends one push, last

Measured: the S2 demo of one project waited 17.7 minutes for its first reply, and the S1 demo waited 385. A push sent in the same batch as the screenshots reached one operator 22 seconds before the steps, with nothing yet to do.

## Why a worker writes `BLOCKED:` only once the drive is complete

Measured: a worker blocked on the operator with Section 3 not started, and the attended session had to unblock it and relaunch the loop to build the demo.

Measured again: a worker short of room drove a turn's replay, wrote `BLOCKED:`, and handed the operator the look back at an earlier turn that the slice had also changed.

## Why a request to do something in this phase is done in this phase

Measured: "I highly recommend researching it and circling with me on this design. Now, I think that can naturally happen during this phase" became three later requirements and no research.

## Why a decision about the product goes into the design document in this run

Measured: one demo produced seventeen quoted records, six of which changed how the product behaves, and carrying them into the design took a hand-written commit outside every template because no template claimed the job.

## Why the operator's own promise to check stops the hand to the retro

Measured: the operator's turn ended "I'll doublecheck that the deployment matches", the session reported the deploy and handed to `retro-task` in the same message, and they replied, "I expected to look at the deployed demo, and suddenly we're doing retro."
