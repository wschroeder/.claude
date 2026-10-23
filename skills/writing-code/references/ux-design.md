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
- Show an example in every input
- Multi-select with a bulk action
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
Measured: build sessions drove one list page and confirmed each control worked, and the
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

## Show an example in every input

Give every text input in a form that adds a record a placeholder holding an
example of what a person would actually type there: `XXXX1234` for a masked
card number, `SKU-0042` for a product code, `25,000.00` for an amount. A
person who sees an example knows the format the app expects before they type.
The placeholder never repeats the field's label, and it never replaces the
label, because it disappears the moment someone types. Measured: an operator
saw example placeholders on an add panel and asked for them as the standard,
"at least with regard to showing an example what kind of text someone would
actually enter there."

## Multi-select with a bulk action

Where a person picks several rows and acts on them at once, and the app has no
pattern of its own for it yet:

- Put a checkbox on every row, and a header checkbox with three states (none,
  some, and all) that selects the rows the current filter shows.
- Show a bar directly above the table once anything is selected, naming the
  count and the action: "2 files selected: [Download]". Reserve its
  height, so the table does not jump when the bar appears.
- Count what a row is. Where one row is one file, the bar counts files.
- Give a selected row that the action cannot take its reason as visible text
  beside it. Never put the reason in a tooltip, and never show it by colour
  alone. The bar says how many are blocked: "1 of 2 selected can't be
  downloaded".
- Grey the action button with `aria-disabled="true"`, never `disabled`, so a
  keyboard still reaches it.
- Have the server refuse a request whose selection includes a blocked row. It
  never drops that row silently.
- Ask the operator whether a filter change clears the selection, because no
  strong outside source settles it. Measured: on one app's files page the operator
  chose "a filter change clears the selection".

## Review list

Check each control against these before you call it done:

- An icon-only button carries an `aria-label`.
- A form control carries a `<label>` or an `aria-label`.
- Each text input in an add form shows an example value as its placeholder.
- A destructive action asks for confirmation or offers an undo window, and never
  happens on the first click.
- A pointer target meets `responsive-design`'s target size.
- A blocked row's reason is visible text, not a tooltip or a colour alone.
- A greyed button uses `aria-disabled="true"`, not `disabled`.
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
- Carbon Design System, [Data table usage](https://carbondesignsystem.com/components/data-table/usage/):
  once rows are selected, "the batch action bar appears at the top of the
  table, presenting a set of possible actions to apply to all select items."
- PatternFly, [Bulk selection](https://www.patternfly.org/patterns/bulk-selection/):
  the bulk selector shows a partial state, which "Uses the minus icon to
  represent that the item is part of a partial selection, meaning that only some
  items are selected."
- Nielsen Norman Group, [Tooltip Guidelines](https://www.nngroup.com/articles/tooltip-guidelines/):
  "Remember that tooltips disappear, so instructions or other directly
  actionable information, like field requirements, shouldn't be in a tooltip."
- W3C WCAG 2.2, [Use of Color](https://www.w3.org/WAI/WCAG22/Understanding/use-of-color.html):
  "Color is not used as the only visual means of conveying information,
  indicating an action, prompting a response, or distinguishing a visual
  element."
- W3C ARIA Authoring Practices, [Keyboard Interface](https://www.w3.org/WAI/ARIA/apg/practices/keyboard-interface/):
  "Browsers remove HTML input elements with the `disabled` attribute from the
  tab sequence." An element that must stay discoverable takes
  `aria-disabled="true"` and keeps its focus.
- GOV.UK Design System, [Button](https://design-system.service.gov.uk/components/button/):
  "Disabled buttons have poor contrast and can confuse some users, so avoid them
  if possible."
