# User interface design: match the app first

Conventions for building or changing a control a person uses: a button, a form,
a dialog, a list row's actions, an inline edit. Consistency is the first and main
point here, and everything else is subordinate to it. Behaviour at different
widths belongs to `responsive-design`, and this file does not restate it.

## Contents

- Match how the app already does it
- Fall back to outside conventions only where the app has none
- Say why when you depart
- Build from the app's own pieces
- Review list
- Sources

## Match how the app already does it

Before you build a control, find every place the app already does the same
action: edit, add, delete, merge, rename, confirm, cancel. Open those views and
read how each one does it: which element triggers it, whether it opens inline or
in a dialog, what the icon is, where the control sits in the row, what the
wording says, and how a refusal shows.

Copy the pattern you found, and cite the file you copied it from in your report
to the operator, for example "the delete dialog copies
`server/features/clients/views.tsx`'s confirm dialog". If you cannot cite a file,
you have not looked.

Driving the app to check that a control works does not answer this. A control
can work and still look and behave unlike every other control of its kind.
Measured: build sessions drove /firms and confirmed each control worked, and the
operator then called the controls "extremely sloppy and inconsistent", which cost
a redesign from 08:15 to 10:48.

## Fall back to outside conventions only where the app has none

If the app has no pattern for the action yet, follow the convention people know
from other products. That fallback is second, never first: a familiar outside
pattern that disagrees with the app's own still reads as inconsistent inside the
app.

## Say why when you depart

If you build a control differently from the app's existing pattern, state the
reason where the operator sees it: in the demo, the card note, or the report.
"It looked better" is not a reason. A reason names what the existing pattern
cannot do for this task.

## Build from the app's own pieces

Use the app's existing components, layout helpers, icon set, spacing, and
utility classes. Do not write a new button, dialog, or icon when the app already
has one. Where a project's CLAUDE.md names the widget library it prefers, that
library is part of the app's own pieces.

## Review list

Check each control against these before you call it done:

- An icon-only button carries an `aria-label`.
- A form control carries a `<label>` or an `aria-label`.
- A destructive action asks for confirmation or offers an undo window, and never
  happens on the first click.
- A pointer target meets `responsive-design`'s target size.
- The control matches the app's existing control for the same action, and you
  cited the file.

## Sources

- Nielsen Norman Group, [Consistency and Standards](https://www.nngroup.com/articles/consistency-and-standards/):
  heuristic #4 splits internal consistency, within one product, from external
  consistency, with other products. It says to break a convention only when
  doing so is "absolutely necessary to the task or will improve efficiency".
- Jakob Nielsen, [Jakob's Law](https://jakobnielsenphd.substack.com/p/jakobs-law):
  "Users spend most of their time on other websites, so they expect your site
  to work like all the other sites they already know."
- Brad Frost, [Interface Inventory](https://bradfrost.com/blog/post/interface-inventory/):
  catalog the patterns an interface already has before designing new ones.
- Vercel, [Web Interface Guidelines](https://raw.githubusercontent.com/vercel-labs/web-interface-guidelines/main/command.md):
  "Icon-only buttons need `aria-label`", "Form controls need `<label>` or
  `aria-label`", and "Destructive actions need confirmation modal or undo
  window—never immediate". The guidelines have no rule about matching the app's
  own patterns, so they serve here as a review list and not as a design method.
