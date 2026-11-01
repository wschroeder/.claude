# How-to and help guides

A how-to guide walks a person through a task in a product, usually with
screenshots. People open one when they are stuck, scan for their problem, and
leave, so every rule below serves a reader who arrived mid-task.

## Draft every guide as text before you build any of them

If the set holds more than one guide, write all of them as one text draft
first, through tier three: dump every topic, derive the guides from the graph,
and write the cross-references between them. Mark each screenshot with a
placeholder that says what the shot shows. Build the pages and take the
screenshots only after the operator has read that draft and accepted it.

The text draft is the storyboard. Moving a topic from one guide to another
costs an edit there and a re-shoot nowhere. Writing guides one at a time, each
finished with its screenshots, keeps reopening the guides already done.

## The rules a guide follows

- Start each guide and each section from a task the reader has.
- Set out a task as numbered steps. Each step ends on what the person then
  sees, so they can tell the step worked.
- Name each later section for a problem the reader has. The section says how
  to spot the problem, how to find its cause, and how to fix it, and it sits
  next to the step where the problem arises.
- Show the reader each screen before they read more than one paragraph about
  it. A list of steps counts as one paragraph.
- Give a problem section a screenshot of the problem as it appears on screen
  and of the control that fixes it.
- Give a section every screenshot its text needs. Never send the reader to a
  screenshot in another section.
- Tell the reader what the screen cannot show them: what the product does
  behind it, what to do next, and why. Do not restate the screen's labels.
- Explain each task in one place, and link there from anywhere else that needs
  it.
- Name the guide or section a link opens. Never refer to one by its number or
  its position, because each guide may ship as its own page, and a reader who
  lands on one has never seen the others' order.
- Use the words the product's own screens use. Translate every backend code,
  type number, column name, and internal ID into the name the reader sees, and
  ask the reader to match only numbers they already know.
- Leave out anything about how the guide itself was made, such as a note about
  how its screenshots were taken.
- Leave the reader with no open question. A reassurance such as "most of these
  need nothing from you" says exactly when it holds and what happens instead,
  or it goes.

## Review it backwards

Review the finished draft one guide or chapter at a time, starting from the
last. Read in order, each section borrows context from the one before it, and
a gap a reader landing there would fall into stays hidden.

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

Measured on 2026-11-01: an operator reviewing a drafted set of help guides
corrected it for a line about how its screenshots were taken, several
paragraphs before the first screenshot, an unexplained "need nothing from you",
screenshots kept in another section, backend type numbers, links by chapter
number, and a sentence that ended on a flourish. Each of those corrections is
now one of the rules above.
