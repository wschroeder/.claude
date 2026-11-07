# Driving the demo walk

1. Read this file from `demo-task` Section 3 before you drive anything.

Contents:

- Drive the real UI yourself, with the Chrome tool first
- A page only a script can produce is still a browser demo
- A bug your own driving finds means the demo is not ready
- Drive the thing the definition of released names, play on until the change happens, and name any link you cannot reach
- Show the reproduction command, and show yourself driving it with the input a person sends
- Keep demo drivers and captures out of the repository
- When you cannot drive it, cannot produce an artifact, or a capture fails

## Rules

1. Drive the real UI yourself, in a tight loop, on whatever platform the product runs, before you show the operator anything.
2. Drive a browser demo with the Chrome MCP tool (`mcp__chrome-devtools__*`) first, and with Playwright only as a last resort.
3. If the Chrome tool will not start, quote the error it returned in this session, drive the walk with Playwright, and say on its own line in the demo that Playwright drove it and why; a dead end a handoff recorded is not a try.
4. Never fetch the pages over HTTP in place of a browser walk.
5. If the walk needs data only a script or test helper writes, have the script save the page's HTML, serve it from the app's own public folder beside its built assets, capture it with the Chrome tool, and delete the copies afterwards; saved HTML is not a capture.
6. Treat a bug your own driving finds, or a reviewer finding nobody has fixed yet, as a demo that is not ready: do not post it or file it for later.
7. Check whether the default branch shows the same fault on screen to a person using it, comparing what the screen shows, not the line of code.
8. If the default branch does not show it, send the work back to build through `tdd-cycle`, which builds the fix with no card, and start again at Section 2 once the fix is committed.
9. Send a fault to the backlog only when the default branch also shows it, and say so in the post.
10. Give a fault you only suspect, or guess is older than this slice, the same comparison before you post or hand off, and never leave the suspicion only in a closing message.
11. Read Section 4's "do not start fixing anything" as covering what the operator finds, not what you find before they see it.
12. Drive the thing the definition of released names, whether a local script, a local server, a remote service, or an operator in a cluster, never a stand-in for it.
13. Record which thing the definition names and which thing you drove, and if they differ, say so on its own line.
14. If the slice changes something met only later in play, such as under fire or after losses, drive the product until that moment arrives and capture it.
15. If the change shows only when certain data exists, such as an old run or a failed row, put that data in place yourself and capture before and after.
16. Never post a demo that says nothing changed on screen, and never hand the operator a check you could drive yourself.
17. If you cannot reach the released thing, such as a sign-in a person completes, a cluster only they reach, or hardware on their desk, name each link from what you drove to what the definition names, say which you proved, and make the unproven one the thing you ask the operator to do at Section 4.
18. Run both commands in Section 3's record, because the reproduction command is part of the demo.
19. If the definition of released says you operate the thing too, capture it, send it an input such as a key, a request, or a typed command, capture it again, and name the input between the two captures.
20. Send the input a person sends, never a call to the code's own method written up as a press or a drag.
21. In a browser, use the tool's own click, such as `mcp__chrome-devtools__click`, never a page script such as `element.click()`, `dispatchEvent`, or `element.focus()`, even as a setup step.
22. If `project-drive` appears in the available skills, load it for how to send this product real input; if nothing is listed, work it out and say in one line what you did.
23. Write any driver, capture harness, or fixture generator of your own in the walk's folder, `/.tmp/demos/<date>-<slug>/`, beside the captures.
24. Never commit the demo file, a browser test written to show the demo, a directory of past captures, or a caption sheet.
25. If the definition of released says the operator operates the thing and you cannot send it the input a person sends, report the slice as not built as the demo's result, leave the requirement's status where the measurement puts it, and let Planning place the work.
26. If the slice cannot produce an artifact a person can look at, say so plainly, name what is missing, and report it as work cut along module lines for Planning to correct.
27. Paste the demo output into your message and send the file to the operator with `SendUserFile`; a path the operator has to open is not a demo.
28. Send a file beyond the operator only on their word, per CLAUDE.md "Local Files by Default".
29. If a capture fails, exhaust the program's own capture before writing that no artifact exists, such as a framebuffer grab, a service's response, or a command-line tool's output written to a file, and say which call produced the file.
30. Treat a Chrome tool that will not start under the Playwright rule, not as a failed capture.

The reasons and the measured cases behind these rules are in [references/measurements.md](measurements.md).
