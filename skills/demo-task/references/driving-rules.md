# Driving the demo walk

Read from `demo-task` Section 3 before you drive anything.

Contents:

- Drive the real UI yourself, with the Chrome tool first
- A page only a script can produce is still a browser demo
- A bug your own driving finds means the demo is not ready
- Drive the thing the definition of released names, play on until the change happens, and name any link you cannot reach
- Show the reproduction command, and show yourself driving it with the input a person sends
- Keep demo drivers and captures out of the repository
- When you cannot drive it, cannot produce an artifact, or a capture fails

## Rules

- **Drive the real UI yourself, in a tight loop, before you show the operator
  anything**, on whatever platform the product runs.
- **Drive a browser demo with the Chrome MCP tool (`mcp__chrome-devtools__*`)
  first, and with Playwright only as a last resort.** Where the Chrome tool
  will not start, quote its error, and drive the walk with Playwright instead.
  The error you quote is one the tool returned in this session. A dead end a
  handoff recorded is not a try, so call the tool before you trust it.
  Then say in the demo, on its own line, that Playwright drove it and why the
  Chrome tool could not. Do not fetch the pages over HTTP in place of either: a
  fetched page shows no tooltip, no disclosure, and no click, so it is not a
  walk. Why: [references/measurements.md](measurements.md).
- **A page that only a script can produce is still a browser demo.** Where the
  walk needs data that a fake model or a test helper writes, have the script
  save the page's HTML, serve it from the app's own public folder beside its
  built assets, and capture it with the Chrome tool. Delete the copies
  afterwards. Saved HTML is not a capture, and "the page with the app's
  styles" is never a link the walk leaves unchecked while this is possible.
- **A bug your own driving finds means the demo is not ready**, and so does
  a reviewer finding nobody has fixed yet, such as the one a session loop
  names when it stops. Do not post
  it, and do not file it for later. Check whether the default branch shows
  the same fault to a person using it. Compare what the screen shows, not the
  line of code: an old line that only this slice's data reaches is still this
  slice's fault. If the default branch does not show it, send the work back
  to build, through `tdd-cycle`, which builds the fix with no card, and start
  again at Section 2 once the fix is committed. Only a fault the default
  branch also shows may go to the backlog, and the post says so. A fault you
  only suspect, or guess is older than this slice, takes the same check:
  compare with the default branch before you post or hand off, and never
  leave the suspicion only in a closing message. See [references/measurements.md](measurements.md).
  Section 4's "do not start fixing
  anything" covers what the operator finds, not what you find before they
  see it. See [references/measurements.md](measurements.md).
- **The artifact comes from the thing the definition of released names, not
  from a stand-in for it.** Read what that definition points at and drive
  that: on one project it is a script on this machine, on another a local
  server, on another a service behind a remote URL, on another an operator
  running in a cluster. None of those is more real than the others — what
  makes a demo wrong is driving something the definition does not name while
  reporting it as the slice being released. So the record says which thing
  the definition names and which thing you drove, and where they are not the
  same thing it says so on its own line rather than in a footnote. See [references/measurements.md](measurements.md).
- **Play on until the thing the slice changed happens.** Where the slice
  changes something a player only meets later in play, such as under fire,
  at contact, or after losses, drive the product until that moment arrives
  and capture it. Do not hand the operator a check you could drive yourself.
  See [references/measurements.md](measurements.md).
  The same holds where the change shows only when certain data exists, such
  as an old run or a failed row: put that data in place yourself and capture
  before and after. A post that says nothing changed on screen is not ready.
  See [references/measurements.md](measurements.md).
- **Where you cannot reach that thing, say which link is unproven and hand
  the last one to the operator.** Some released states cannot be driven from
  here at all — a sign-in a person completes, a cluster only they can reach,
  hardware on their desk. That is not a reason to demo the nearest reachable
  substitute and let it stand: name each link of the chain from what you
  drove to what the definition names, say which links you proved and which
  you did not, and make the unproven one the thing you ask the operator to do
  at Section 4.
- **The operator may drive it themselves, so the reproduction command is
  part of the demo.** An artifact nobody else can regenerate is a claim,
  not proof. Both commands in Section 3's record are required, and both have been run.
- **Show yourself driving it, not one frame of it.** Where the definition
  of released says you operate the thing too, one capture proves only that
  it started. Send it an input — a key, a request, a typed command — capture
  it again, and name the input between the two, so the pair shows the thing
  responding rather than sitting there. See [references/measurements.md](measurements.md).
- **The input has to be the one a person sends.** Calling the code's own
  method and writing the result up as a press or a drag is the failure this
  rule exists to catch, and the word in the record is not the act. In a
  browser, a page script that sends input or sets what input would set,
  such as `element.click()`, `dispatchEvent`, or `element.focus()`, is not
  the input a person sends either, even as a setup step before a real key
  press: use the browser tool's own click,
  such as `mcp__chrome-devtools__click`. If
  `project-drive` appears in the available skills, load it for how to send
  this product real input. If nothing is listed, work it out and say in one
  line what you did.
- **A demo driver and its captures never go into the repository.** Where the
  walk needs a script of your own, such as a driver, a capture harness, or a
  fixture generator, write it under a folder the project already ignores,
  beside the captures. Send the captures to the operator with `SendUserFile`.
  Do not commit a browser test written to show the demo, a directory of past
  captures, or a caption sheet describing them. See
  [references/measurements.md](measurements.md).
- **Being unable to drive it is a finding, not a caveat.** Where the
  definition of released says the operator operates the thing and you cannot
  send it the input a person sends, the slice is not built: say so as the
  demo's result, leave the requirement's status where the measurement puts
  it, and let Planning place the work. Do not fill the record in and carry
  on. See [references/measurements.md](measurements.md).
- If the slice cannot produce an artifact a person can look at, say so
  plainly and name what is missing. A slice with no demo is the finding —
  it means the work was cut along module lines rather than through the
  system, and Planning has to correct that for the next one.
- **Show it, do not name it.** Paste the demo output into your message and
  send the file with SendUserFile. Reading it with a tool puts it in your context only, not in front of the operator. See [references/measurements.md](measurements.md). A path the operator has to open themselves is
  not a demo. SendUserFile puts the file in front of the operator and nobody
  else; sending it anywhere beyond them needs their word first, per
  CLAUDE.md "Local Files by Default".
- **A capture that fails is not a slice that cannot be shown.** Exhaust the
  program's own capture before writing that no artifact exists: a graphical
  program can usually photograph its own framebuffer when the operating
  system refuses to photograph the screen, a service with no page a person
  uses can be asked for what it returns, and a command-line tool can be told
  to write its output to a file. A Chrome tool that will not start is not a
  capture that failed; the rule above about Playwright covers it. The rule
  above about a slice with no demo is for work cut along module lines, not
  for a capture tool that came back blank. Where the
  program's own capture works, say which call produced the file, so the next
  session does not rediscover it.
