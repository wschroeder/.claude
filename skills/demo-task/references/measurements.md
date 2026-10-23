# Measurements behind demo-task's rules

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
