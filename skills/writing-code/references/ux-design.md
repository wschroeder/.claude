# User interface design: match the app first

Read this before building or changing a control a person uses, such as a button, a form, a dialog, a list row's actions, or an inline edit. Consistency with the app comes first, and every other rule here gives way to it. Behaviour at different widths belongs to `responsive-design`, apart from where a page's own contents list goes on a phone.

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
- State facts only in help text
- Review list
- Sources

## Match how the app already does it

1. Before you build a control, find every place the app already does the same action, such as edit, add, delete, merge, rename, confirm, or cancel.
2. Open those views and read which element triggers the action, whether it opens inline or in a dialog, its icon, where the control sits in the row, its wording, and how a refusal shows.
3. Copy the pattern you found, and cite the file you copied it from in your report to the operator. If you cannot cite a file, then you have not looked.
4. Never count driving the app to see a control work as this check, because a working control can still look and behave unlike every other control of its kind.

## Fall back to outside conventions only where the app has none

1. If the app has no pattern for the action yet, then follow the convention people know from other products.
2. Never let an outside convention win over a pattern the app already has.

## Say why when you depart

1. If you build a control differently from the app's existing pattern, then state the reason where the operator sees it: in the demo, the card note, or the report.
2. Give a reason that names what the existing pattern cannot do for this task; "it looked better" is not one.

## Build from the app's own pieces

1. Use the app's existing components, layout helpers, icon set, spacing, and utility classes.
2. Never write a new button, dialog, or icon when the app already has one.
3. Count a widget library that the project's CLAUDE.md prefers as one of the app's own pieces.

## Put a control inside the component it acts on

1. Draw a control that acts on one component, such as an × that clears a field, removes a tag, or dismisses a warning, inside that component's visible border at its trailing end, never beside it.
2. When you copy the app's pattern for an action, copy where its control sits as well as which control it is.
3. Read "beside the warning" in a spec or a handoff as naming the control's neighbour, not its layout, and draw the control inside.

## Show an example in every input

1. Give every text input in a form that adds a record a placeholder holding an example of what a person would actually type, such as `XXXX1234` for a masked card number or `25,000.00` for an amount.
2. Never let the placeholder repeat the field's label or replace it, because it disappears the moment someone types.

## Multi-select with a bulk action

Where a person picks several rows and acts on them at once, and the app has no pattern of its own for it yet:

1. Put a checkbox on every row, and a header checkbox with three states (none, some, and all) that selects the rows the current filter shows.
2. Once anything is selected, show a bar directly above the table naming the count and the action, such as "2 files selected: [Download]", and reserve its height so the table does not jump.
3. Count what a row is: where one row is one file, the bar counts files.
4. Give a selected row that the action cannot take its reason as visible text beside it, never in a tooltip and never by colour alone, and have the bar say how many are blocked, such as "1 of 2 selected can't be downloaded".
5. Grey the action button with `aria-disabled="true"`, never `disabled`, so a keyboard still reaches it.
6. Have the server refuse a request whose selection includes a blocked row, never dropping that row silently.
7. Ask the operator whether a filter change clears the selection.

## Carry only the destination's own parameters

1. Build every link, redirect, and form action from the parameters its destination route reads, named one by one.
2. Never copy the incoming query string into a URL for another route, or into a sort or paging link on the same page, unless you can say why the destination needs each parameter it carries.
3. Parse the parameters you keep where the request enters, and hand the view only those.

## Show a page's contents list above its text on a phone

Where a long page carries links to its own sections, and the app has no pattern of its own for them yet, then at phone width:

1. Put the links in a plain list at the top of the page, one link per line, under a short "On this page" heading.
2. Keep the list visible: never fold it behind a tap, stick it to the top of the screen, or replace it with accordion sections.
3. Keep the page title's introduction to one short line, so the list starts on the first screen.
4. Keep the list short enough that the first section starts on the first screen too; if a page outgrows that, then merge or cut sections before you fold the list.
5. On a wide screen, let the same list sit in a column beside the text.
6. Follow this over `responsive-design`'s default of collapsing a nav that holds more than about four controls, which is meant for filters and toolbars.

## State facts only in help text

1. Write a definition or help text as facts only: what the thing means and how the app sets or uses it, with no promise about later, no opinion, and no advice. A word that names a band the app shows in color, such as "high", counts as a fact.
2. When you reword one definition in a list, keep the form that the entries next to it use.
3. Keep help in a tooltip to meaning alone, because a tooltip disappears.
4. Let a pill or flag that marks something a person has to handle end with one sentence the screen does not show: what an action does, such as "Resume picks up at the failed step and keeps the work done before it", or where a fix outside the app lives, such as "Correct the record in the source system".
5. Never end with a sentence that only names a control the reader can already see, such as "Retry processing." beside a Retry button.
6. Read the code behind the action before you say what it does.

## Review list

Check each control against these before you call it done:

1. An icon-only button carries an `aria-label`.
2. A form control carries a `<label>` or an `aria-label`.
3. Each text input in an add form shows an example value as its placeholder.
4. A destructive action asks for confirmation or offers an undo window, and never happens on the first click.
5. A pointer target meets `responsive-design`'s target size.
6. A blocked row's reason is visible text, not a tooltip or a colour alone.
7. A greyed button uses `aria-disabled="true"`, not `disabled`.
8. A disabled control says why it is disabled in a tooltip shown on hover, such as the permission it needs or what has to happen first, and an enabled icon-only control names its action in a tooltip.
9. The control matches the app's existing control for the same action, where it sits included, and you cited the file.
10. A control that acts on one component sits inside that component's border.
11. Every link, redirect, and form action names the parameters it carries, and none copies the incoming query string.
12. At phone width, a page's contents list sits visible above its text, one link per line, neither folded nor sticky.
13. Each definition and help passage carries no promise, opinion, or advice, apart from the closing sentence a flag may carry.
14. A flag's closing sentence, where it has one, says what an action does or where the fix lives, and never only names a control that is already on screen.

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
