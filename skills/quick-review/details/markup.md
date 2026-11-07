# Markup and text a person reads

Read this file now, before Pass 1, when the diff changes markup, a browser event handler, or text a person reads on a screen.

## Contents

  - 1.11 Documented-placeholder behavior is itself a finding
  - 2.23 Cancelled browser default
  - 5.13 ARIA role/contract correctness
  - 5.14 Button hygiene (`type` attribute + icon-only accessible name)
- ARIA contracts in full (5.13)
  - Direction A — declared role without keyboard/focus contract
  - Direction B — component IS a role but does not declare it
  - Anti-anchor

Each angle below belongs to the pass its number names. Walk it in that pass, give it a disposition, and print its line in the Checklist under that pass.

```
Pass 5:
  5.13  ARIA contract                    a declared role delivers its keyboard and
                                          focus contract; a widget shaped like a role
                                          declares it (both directions below)
  5.14  Button hygiene                   type attribute; icon-only accessible name
```

## Checklist lines

```
Pass 1:
  1.11  Documented-placeholder UX        silent-zero-row UX is itself the finding
Pass 2:
  2.23  Cancelled browser default        each preventDefault, stopPropagation, or
                                          `return false` the diff adds: list every
                                          element the handler reaches and what the
                                          browser does there by default (a label
                                          focuses or toggles its field, a link
                                          navigates, a summary toggles, a submit
                                          button submits); drive one of each with
                                          real input and quote what happened
Pass 5:
```

### 1.11 Documented-placeholder behavior is itself a finding

When a function or branch in the diff carries a comment that describes intentionally-broken-pending-followup behavior — "silent zero-row", "always returns false until P6.5", "Q1=A interim", "no-op until X lands", "placeholder until the column re-keys" — treat the placeholder as a finding to surface. The deviation is NOT the diff drifting from the placeholder's claim; the deviation is the placeholder's existence in production code.

Three valid paths, pick one:
- **(a) Hide behind a feature flag** so the placeholder can't fire for real users.
- **(b) Replace with an actionable error** that tells the user what's happening (`503 "Imports are temporarily unavailable while we migrate identity sources"` beats a silently-empty list).
- **(c) Document the visible impact** in the user-facing empty state ("DAs may see no imports until the identity migration completes — see <link>") so the placeholder's UX surface is honest.

A silent placeholder that compiles to misleading UX is Fix-class regardless of how well-documented it is in the source. The "Author-acknowledged deviation is not exempt" rule handles the in-source comment side; this rule handles the user-facing UX side. A row that's in the DB but not in the UI is a bug from the user's perspective, even if the comment says so.

### 2.23 Cancelled browser default

A handler that cancels an event's default action stops whatever the browser would have done next, on every element the handler reaches, not only the one the author had in mind. List each kind of element the handler's selector can match and write down its default for that event: a `<label>` moves focus into its field or toggles its checkbox, a link navigates, a `<summary>` opens its `<details>`, and a submit button submits its form. Then drive one of each with the browser tool's own click or key press and quote what happened. Reading the selector and finding no link or checkbox under it does not answer the angle, because the defaults you did not list are the ones that break.

Measured (2026-10-29): a fix cancelled the click on any label that opens a definition popover, so that a click on a label wrapping a text field would stop closing the popover it had just opened. Before the fix, the builder drove the page and wrote that focus moved to the input, which was that default at work. The review checked labels inside links, `<summary>` elements, and checkbox labels, wrote that it found none, and passed the commit without running the browser tests. Clicking a text field's label no longer put the cursor in the field. The demo walk caught it. The next fix dropped the cancel and ignored the one click the browser forwards to the field.

### 5.13 ARIA role/contract correctness

ARIA roles are contracts the component must deliver on. See "ARIA contracts in full" below for the full Direction A (declared role without keyboard/focus contract) and Direction B (component IS a role but does not declare it) worked examples, plus the path-(a)/(b)/(c) decision tree.

### 5.14 Button hygiene (`type` attribute + icon-only accessible name)

Two cheap regressions that ARIA reviews tend to skip:

- **`<button>` without explicit `type="button"`.** The HTML default `type` for `<button>` inside a `<form>` is `submit`. A toolbar button or icon button rendered inside a parent form (even an ancestor several levels up — most React components don't know whether their consumer renders a form) silently submits the form on click. The fix is mechanical: every `<button>` in the diff that is NOT explicitly a submit button gets `type="button"`. Flag the omission per-occurrence, not "fix one and assume the rest." Same applies to native button elements inside `react-hook-form`, Remix `<Form>`, server-action forms, and any framework that intercepts the default submit.
- **Icon-only buttons without an accessible name.** A button whose visible content is an SVG icon (lucide-react, heroicons, custom inline SVG, font-awesome) has no accessible name — screen readers announce "button" with no further context. Required mitigations, any one of: `aria-label="Push token"`, `aria-labelledby={titleId}`, `<span className="sr-only">Push token</span>` inside the button, or a `<title>` element inside the SVG. The visible `title` HTML attribute is a TOOLTIP not an accessible name — most screen readers ignore it as the accessible name source.

**Discovery method:** grep `<button` in the diff. For each occurrence, check (a) `type=` attribute presence, (b) child content — is the only child an SVG/icon? — and (c) accessibility props. Fix-class per the "yes to any" gate.

## ARIA contracts in full (5.13)

ARIA roles are contracts the component must deliver on. The same Conventions / sibling-consistency reasoning that catches "module A declares `@behaviour X` and module B doesn't" applies to UI components: a component declaring an ARIA role takes on the keyboard and focus contract that role implies, and a component shaped like a dialog/disclosure/listbox owes its users the corresponding role declaration. Both directions are Fix-class — the Yes-to-any gate fires on spec compliance.

---

### Direction A — declared role without keyboard/focus contract

A component that declares `role="menu"`, `role="listbox"`, `role="dialog"`, `role="combobox"`, `role="tab"`, `role="tablist"`, or similar without the keyboard interactions and focus management the role REQUIRES (per WAI-ARIA Authoring Practices) is a false promise to assistive-tech users — screen readers announce the role but users cannot navigate as expected.

For each ARIA role introduced or modified by the diff, list the role's required keyboard behaviors and focus management; verify the component implements them. Common required pairs:

- **`role="menu"` / `role="menuitem"`** — arrow keys (Up/Down), Home/End, Enter/Space activation, focus trapped within the menu, focus restored to the trigger on close. `aria-haspopup="menu"` on the trigger.
- **`role="dialog"` (modal)** — `aria-modal="true"`, `aria-labelledby` pointing at the title `id`, focus trapped inside until close, focus restored to the opener on close, Escape closes.
- **`role="listbox"` / `role="option"`** — arrow keys, `aria-selected`, single/multi-select semantics, `aria-activedescendant` if focus stays on the listbox.
- **`role="tab"` / `role="tablist"` / `role="tabpanel"`** — arrow keys traverse tabs, `aria-selected`, `aria-controls` pointing at the panel id.
- **`role="combobox"`** — `aria-expanded`, `aria-controls`, `aria-activedescendant`.

If the component declares the role but lacks the contract, three paths are valid; pick one with reason:

#### Path (a) — Implement the contract

Best when the contract's effort matches the component's blast radius (a destructive modal earns Escape + backdrop-click + focus-on-open + focus-trap + focus-restore; a lightweight popover may not).

#### Path (b) — Drop the role and use simpler semantics

Best when the contract is overkill for current use — a one-item dropdown does not need full WAI-ARIA menu navigation; a plain `<button>` + `<ul>` is honest. A plain `<button>` + region with `aria-expanded`/`aria-controls` is honest for a non-`role="dialog"` overlay.

#### Path (c) — Match the codebase's partial-contract baseline

Best when *every* sibling component of the same role-class in this codebase ships the same partial contract (e.g., every modal in the app declares `role="dialog"` + `aria-modal` + `aria-labelledby` but none implement focus trap, focus restore, or Escape). In that case, aligning the new component to the same baseline is the right scope for one PR; diverging upward or downward in isolation creates an inconsistent island. Closing the broader gap is its own ticket.

**Verify the precedent with a repo-wide grep, not by reading one nearby file** — and document the precedent in the review output so the team can revisit holistically.

Do NOT use "consistent with other code" as a generic dismissal. Path (c) requires the precedent to apply specifically to the role-class in question, verified by enumeration. The deletion test for path (c): if the precedent is removed (every other sibling is upgraded to the full contract), is the new component's partial contract still defensible? If no, path (c) is just procrastination — pick (a) or (b).

Even when path (c) is justified for the heavy parts of the contract (focus trap, focus restore), small deviations from the sibling (sibling closes on backdrop click; new component does not) are still Fix-class — that's parity, not contract-completion. The "yes to any" gate fires whenever the *new* component diverges from siblings in either direction.

---

### Direction B — component IS a role but does not declare it

Inversely: an overlay `<div>` that traps clicks behind a backdrop, holds focus, has a title and a dismiss control IS a `role="dialog"` whether or not it spells it out — and a screen reader without the role sees only a div. A `<button>` that toggles a visible/hidden region without `aria-expanded` and `aria-controls` is an incomplete disclosure pattern.

For every modal/popover/disclosure/tablist/listbox-shaped component in the diff, verify the corresponding role + aria-* attributes are declared:

- **Modal overlays** → `role="dialog"` + `aria-modal="true"` + `aria-labelledby` (or `aria-label`) on the dialog container; matching `id` on the title element.
- **Disclosure buttons** (any "click to expand a region") → `aria-expanded={open}` + `aria-controls={regionId}` on the trigger; matching `id` on the controlled region.
- **Tabs** → `role="tablist"` on the bar, `role="tab"` on each tab, `aria-selected`, `aria-controls` to the panel; `role="tabpanel"` on the panel with `aria-labelledby` back to the tab.
- **Replacement listbox/select** → `role="listbox"` + `role="option"` + `aria-selected`.

The "looks like, walks like" test: if the component traps clicks behind a backdrop, holds focus, has a title and a dismiss control, it is a `role="dialog"` whether it declares it or not — declare it. Use React's `useId` hook for stable id generation across SSR/hydration when wiring `aria-labelledby` / `aria-controls` / `aria-describedby`.

---

### Anti-anchor

"Minor accessibility nit, out of scope" / "consistent with the codebase" / "other components do this too" are NOT acceptable Note-class downgrades for either direction. Self-introduced ARIA contract violations (the diff added the role; the diff added the modal-shaped component) are Fix-class regardless of what the rest of the codebase does.

**Deletion test:** if you remove the declared role (or the component-shape behavior the user can observe), does the user lose the contract they were promised? If yes, fix.
