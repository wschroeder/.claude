# How-to and help guides

1. Write every rule below for a reader who arrived mid-task, scans for their problem, and leaves.

## Draft every guide as text before you build any of them

1. If the set holds more than one guide, write all of them as one text draft first, through tier three: dump every topic, derive the guides from the graph, and write the cross-references between them.
2. Mark each screenshot with a placeholder that says what the shot shows.
3. Build the pages and take the screenshots only after the operator has read that draft and accepted it.

## The rules a guide follows

1. Start each guide and each section from a task the reader has.
2. Set out a task as numbered steps, each ending on what the person then sees, so they can tell the step worked.
3. Name each later section for a problem the reader has, say how to spot it, find its cause, and fix it, and place it next to the step where the problem arises.
4. Show the reader each screen before they read more than one paragraph about it, counting a list of steps as one paragraph.
5. Give a problem section a screenshot of the problem as it appears on screen and of the control that fixes it.
6. Give a section every screenshot its text needs, and never send the reader to a screenshot in another section.
7. Tell the reader what the screen cannot show them, such as what the product does behind it, what to do next, and why, and never restate the screen's labels.
8. Explain each task in one place, and link there from anywhere else that needs it.
9. Name the guide or section a link opens, never its number or position, because each guide may ship as its own page.
10. Use the words the product's own screens use, translate every backend code, type number, column name, and internal id into the name the reader sees, and ask the reader to match only numbers they already know.
11. Leave out anything about how the guide itself was made, such as how its screenshots were taken.
12. Leave the reader with no open question: a reassurance such as "most of these need nothing from you" says exactly when it holds and what happens instead, or it goes.
13. If the operator's notes give a path they followed to success, then write that path alone, with no problem sections and no steps past where the notes end.
14. Label each code block with the shell or program it runs in.
15. Say at which step the reader knows the setup works, and where a long run may be stopped early, say so at that step.

## Review it backwards

1. Review the finished draft one guide or chapter at a time, starting from the last.

## Where the rules come from

- Hans van der Meij and John Carroll, "Principles and heuristics for designing
  minimalist instruction", *Technical Communication* 42(2), 1995: start from
  real tasks, get the reader acting quickly, cut explanation they do not need
  yet, and support recognizing and recovering from errors.
- Ard Lazonder and Hans van der Meij, *International Journal of
  Human-Computer Studies* 42(2), 1995: readers whose manual helped them detect,
  diagnose, and correct errors finished training faster and corrected errors
  better, and learned the task itself just as well.
- Mark Gellevij and Hans van der Meij, "Empirical Proof for Presenting Screen
  Captures in Software Documentation", *Technical Communication* 51(2), 2004.
  Only the title was checked, not the method or the results.
- David Novick and Karen Ward, "Why don't people read the manual?", SIGDOC
  2006: the 25 users interviewed had trouble navigating help, especially
  finding search terms, which argues for headings phrased as problems.

## Runbooks

### Who each runbook is for

1. Write a short overview that says which support tier does what. Give each tier one runbook that has everything its people need, even where that repeats the overview or another tier's runbook.
2. Keep the overview to who does what and how a problem passes between tiers; leave out people who do no support work, such as the business owner and daily users, and any section comparing it with the previous runbook.
3. Write for the team that runs the system, and leave out the procedures of the vendor that built it.
4. Name a team by its department or role, never by a person's name.
5. List each tier's tools and permissions first, then give each problem to the lowest tier whose own tools can fix it.
6. Label each problem with a severity, and give one list that matches each severity to a response time, instead of asking the reader to judge the severity.
7. Give each tier its own section of scheduled duties, such as a yearly key rotation, as a short table of when and what that links to each duty's steps; leave out every reaction to an incident and every duty nobody asked for, and offer the schedule as a proposal.
8. Before a tier hands a problem off, give it the safe fix its own tools allow, such as a restart, and have the reader save what the screen shows before trying it, such as a chart, so the next tier can see the trend.
9. End a tier's troubleshooting at the point where it escalates: say when to hand off and to whom, and leave out guesses at the cause. Say whom to tell and what to tell them, such as how old the data now is, only at that hand-off.
10. Leave out arrangements the organization has not decided, such as who releases what.
11. Leave out security reminders for messages that already travel over the reader's own secure network.
12. Leave the developer documents as they are where a runbook gives administrators a different way to do the same task.

### Steps

1. Give exact click paths in the screens the reader actually uses.
2. Give every procedure the same detail down to its last step, and name every place a changed value lives, such as each system that keeps a copy of a rotated key.
3. If a procedure changes something in a portal that infrastructure code also manages, then check that the next apply leaves the change alone, and change the code if it would not.
4. Repeat a short step inside each procedure that needs it, so each procedure runs top to bottom in one place.
5. In HTML, make every mention of another section or page a link, and link every outside tool the reader opens to its address.
6. Call a section a section, and call it a page only when it is one.
7. Use the plain headings a reader expects, such as "Troubleshooting".
8. Cut every paragraph about the runbook itself, such as what a part includes.
9. Give every sentence a source in the system or from the operator, and delete a sentence whose source is missing.
10. Run every step before the runbook ships, or settle it with a read-only probe. Never put an UNTESTED note in front of the reader; report a step you could not run to the operator as a blocker.
11. In a release procedure, have the reader check the test environment before production.

### Screenshots

1. Take each shot from the environment the reader works in, by reading only; if a shot needs access, take temporary access and remove it afterward.
2. If the reader would have to break something to see a failure, then show the healthy screen at the place they would look.
3. If you cannot reach a screen, then use the vendor's published screenshot, with names redrawn to match; if the vendor has none, then describe the screen in words.
4. Leave out screenshots of a tool that the reader's team already runs every day.
5. Before saving a shot, paint over every secret, account id, and tenant id; replace each person's name with "Person N", and dim their avatar.
6. Where a real value cannot appear, paint in realistic made-up numbers.
7. Size every shot to fill the text column, link it to its full-size file, and name the file after its caption.
8. Write each caption to describe exactly what the shot shows.

### Building it

1. Build the HTML pages from Markdown with one stylesheet that copies the colors and feel of the organization's existing documents.
2. Serve the pages over local HTTP to review them because `file://` pages block scripts.
3. Rebuild every HTML page and PDF from its source before each commit, and check that the committed files match a fresh build.
4. Scan every built page for duplicate ids, missing images, broken links, and Markdown left unconverted.
5. Make PDFs only after the operator is confident in the HTML.
6. Make one PDF for the whole set, with a title page and a table of contents built from the HTML menu.
7. Write the title page's tagline for the reader's organization, and leave out the name of the firm that wrote the runbook.

### Reviewing with the operator

1. Send a draft or outline for review only after every open question in it is answered.
2. When the operator corrects one runbook, look for the same problem in each sibling runbook and fix it there before sending any of them back.
3. With each revision, list every wording change and the section it is in.
