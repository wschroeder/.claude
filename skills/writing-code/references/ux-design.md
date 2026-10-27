# User interface design: match the app first

Conventions for building or changing a control a person uses: a button, a form,
a dialog, a list row's actions, an inline edit. Consistency is the first and main
point here, and everything else is subordinate to it. Behaviour at different
widths belongs to `responsive-design`, and this file does not restate it, apart
from where a page's own contents list goes on a phone.

## Contents

- Match how the app already does it
- Fall back to outside conventions only where the app has none
- Say why when you depart
- Build from the app's own pieces
- Put a control inside the component it acts on
- Show an example in every input
- Multi-select with a bulk action
- Carry only the destination's own parameters
- Show a page's contents list above its text on a phone
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

## Put a control inside the component it acts on

Where a control acts on one component, such as an × that clears a field,
removes a tag, or dismisses a warning, draw it inside that component's visible
border, at its trailing end. Never place it beside the component. People read
whatever sits inside one border as one thing, and a border outweighs closeness,
so an × outside the border reads as acting on whatever else sits near it.

When you copy the app's pattern for an action, copy where its control sits as
well as which control it is. A spec or a handoff that says "beside the warning"
names the control's neighbour, not its layout, so draw the control inside.

Measured: on 2026-10-20 an operator said of a date input's clear button "The x
needs to be inside the input", and on 2026-10-27 of a warning label's clear
button "Shouldn't the X be inside the label?" The second build had cited the
app's tag pill as its pattern, and the tag pill draws its × inside the pill.

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

## Carry only the destination's own parameters

Build every link, redirect, and form action from the parameters its destination
route reads, named one by one. Never copy the incoming query string into a URL
for another route, or into a sort or paging link on the same page, unless you
can say why the destination needs each parameter it carries. A copied query
string carries whatever the previous page sent: a client framework's state, a
token, a filter, or a dialog's choice. The page it lands on may then act on that
value or show it, though it never meant to accept it. Parse the parameters you
keep where the request enters, and hand the view only those. Measured
(2026-10-24): a list page copied every incoming parameter into its sort and
paging links, so a previous page's dialog state rode along into every link, and
the operator asked for the rule.

## Show a page's contents list above its text on a phone

Where a long page carries links to its own sections, and the app has no pattern
of its own for them yet, then at phone width:

- Put the links in a plain list at the top of the page, one link per line, under
  a short "On this page" heading. Keep the list visible: never fold it behind a
  tap, never stick it to the top of the screen, and never replace it with
  accordion sections.
- Keep the page title's introduction to one short line, so the list starts on
  the first screen.
- Keep the list short enough that the first section starts on the first screen
  too. If a page outgrows that, merge or cut sections before you fold the list.
- On a wide screen, the same list can sit in a column beside the text.

This overrides `responsive-design`'s default of collapsing a nav that holds more
than about four controls. That default is meant for filters and toolbars.

People use links they can see on a phone more often than links behind a tap,
and they miss a folded contents bar stuck to the top of the screen. No
peer-reviewed study compares these options at phone width, so the support comes
from practitioner usability research and counts as moderate. Measured
(2026-10-26): an operator looked at one real page at 390 pixels wide with its
contents shown four ways (a plain list, wrapping chips, a folded bar, and
accordion sections) and chose the plain list as the rule for the whole app.

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
- The control matches the app's existing control for the same action, where it
  sits included, and you cited the file.
- A control that acts on one component sits inside that component's border.
- Every link, redirect, and form action names the parameters it carries, and
  none copies the incoming query string.
- At phone width, a page's contents list sits visible above its text, one link
  per line, neither folded nor sticky.

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
- Nielsen Norman Group, [The Principle of Common Region: Containers Create Groupings](https://www.nngroup.com/articles/common-region/):
  "items within a boundary are perceived as a group", and "Creating a clear
  boundary is a strong visual cue that can overpower other grouping principles
  such as proximity or similarity."
- Nielsen Norman Group, [Proximity Principle in Visual Design](https://www.nngroup.com/articles/gestalt-proximity/):
  "Design elements near each other are perceived as related, while elements
  spaced apart are perceived as belonging to separate groups."
- Carbon Design System draws the × inside the component it acts on: a
  [dismissible tag](https://carbondesignsystem.com/components/tag/usage/)
  carries "an additional close icon" in its anatomy, a
  [search field](https://carbondesignsystem.com/components/search/usage/)'s
  close icon "Acts as a function to clear the search field", and on an
  [inline notification](https://carbondesignsystem.com/components/notification/usage/)
  "A small 'x' in the top right corner is used to dismiss inline
  notifications."
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
- Nielsen Norman Group, [Tables of Contents: The Ultimate Guide to Design](https://www.nngroup.com/articles/table-of-contents/)
  (2023): on small screens, "The simplest solution is to move the table of
  contents to the main body of the article", with the warning that "even a
  short, 1-paragraph introduction to the page can push the table of contents
  below the fold". Of a collapsed contents bar stuck to the top of the page:
  "In testing, many users failed to notice the sticky table of contents in these
  implementations." The article gives no test method or sample size.
- Nielsen Norman Group, [Hamburger Menus and Hidden Navigation Hurt UX Metrics](https://www.nngroup.com/articles/hamburger-menus/)
  (2016): 179 participants on 6 sites. On phones, people used hidden navigation
  in 57% of cases and partly visible navigation in 86%, and were "15% slower
  when the navigation was hidden". It tested site menus, so it applies to a
  contents list only by inference.
- Nielsen Norman Group, [Accordions on Mobile](https://www.nngroup.com/articles/mobile-accordions/)
  (2015): a page should carry "an in-page table of contents (or mini-IA) that is
  salient and visible right away, when the user first lands on the page".
  Expanding an accordion can make "the users think that they navigated to a new
  page."
