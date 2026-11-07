# Markup and text a person reads

1. Read this file now, before Pass 1, when the diff changes markup, a browser event handler, or text a person reads on a screen.

## Contents

  - 1.11 Documented-placeholder behavior is itself a finding
  - 2.23 Cancelled browser default
  - 5.13 ARIA role/contract correctness
  - 5.14 Button hygiene (`type` attribute + icon-only accessible name)
- ARIA contracts in full (5.13)
  - Direction A — declared role without keyboard/focus contract
  - Direction B — component IS a role but does not declare it
  - Anti-anchor

1. Walk each angle below in the pass its number names, give it a disposition, and print its line in the Checklist under that pass.

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

1. When a comment in the diff describes behavior left broken until later work, such as "silent zero-row" or "no-op until X lands", report the placeholder's existence in production code as a finding.
2. Make it Fix-class when the placeholder is silent and shows the user misleading output, however well the source documents it.
3. Require one of three paths:
- **(a) Hide behind a feature flag** so the placeholder cannot fire for real users.
- **(b) Replace with an actionable error** that tells the user what is happening.
- **(c) Document the visible impact** in the user-facing empty state, with a link.
4. Leave the in-source comment to the "Author-acknowledged deviation is not exempt" rule; this angle covers what the user sees.

### 2.23 Cancelled browser default

1. For each handler that cancels an event's default, list every kind of element its selector can match and that element's default for the event: a `<label>` focuses or toggles its field, a link navigates, a `<summary>` opens its `<details>`, and a submit button submits its form.
2. Drive one of each with the browser tool's own click or key press, and quote what happened.
3. Never answer the angle by reading the selector and finding no link or checkbox under it.

### 5.13 ARIA role/contract correctness

1. Walk both directions in "ARIA contracts in full" below for every role or role-shaped component the diff adds or changes.

### 5.14 Button hygiene (`type` attribute + icon-only accessible name)

1. Grep `<button` in the diff, and for each occurrence check its `type=` attribute, whether its only child is an SVG or icon, and its accessibility props.
2. Flag, one by one, every `<button>` that is not a submit button and lacks `type="button"`, including buttons inside framework forms.
3. Flag every icon-only button without an accessible name, and accept any one of `aria-label`, `aria-labelledby`, a `sr-only` span inside the button, or a `<title>` inside the SVG.
4. Count a `title` attribute as no accessible name.
5. Treat each as Fix-class under the "yes to any" gate.

## ARIA contracts in full (5.13)

1. Treat both directions below as Fix-class under the Yes-to-any gate, on spec compliance.

---

### Direction A — declared role without keyboard/focus contract

1. For each ARIA role the diff adds or changes, list the keyboard behavior and focus management WAI-ARIA Authoring Practices require of it, and check that the component implements each:
- **`role="menu"` / `role="menuitem"`** — arrow keys (Up/Down), Home/End, Enter/Space activation, focus trapped within the menu, focus restored to the trigger on close. `aria-haspopup="menu"` on the trigger.
- **`role="dialog"` (modal)** — `aria-modal="true"`, `aria-labelledby` pointing at the title `id`, focus trapped inside until close, focus restored to the opener on close, Escape closes.
- **`role="listbox"` / `role="option"`** — arrow keys, `aria-selected`, single/multi-select semantics, `aria-activedescendant` if focus stays on the listbox.
- **`role="tab"` / `role="tablist"` / `role="tabpanel"`** — arrow keys traverse tabs, `aria-selected`, `aria-controls` pointing at the panel id.
- **`role="combobox"`** — `aria-expanded`, `aria-controls`, `aria-activedescendant`.
2. If the contract is missing, pick one path below and give the reason.

#### Path (a) — Implement the contract

1. Pick this when the contract's effort matches what the component can break, such as a destructive modal.

#### Path (b) — Drop the role and use simpler semantics

1. Pick this when the contract is more than current use needs, and use a plain `<button>` with a list, or with a region carrying `aria-expanded` and `aria-controls`.

#### Path (c) — Match the codebase's partial-contract baseline

1. Pick this only when every sibling component of the same role in the codebase ships the same partial contract, verified by a repository-wide grep, never by one nearby file.
2. Record the precedent in the review output.
3. Reject path (c) if the new component's partial contract would be indefensible once every sibling had the full contract.
4. Flag as Fix-class any difference from the siblings in either direction, such as a sibling that closes on a backdrop click when the new component does not.

---

### Direction B — component IS a role but does not declare it

1. For every component in the diff shaped like a modal, popover, disclosure, tablist, or listbox, check that it declares the matching role and attributes:
- **Modal overlays** → `role="dialog"` + `aria-modal="true"` + `aria-labelledby` (or `aria-label`) on the dialog container; matching `id` on the title element.
- **Disclosure buttons** (any "click to expand a region") → `aria-expanded={open}` + `aria-controls={regionId}` on the trigger; matching `id` on the controlled region.
- **Tabs** → `role="tablist"` on the bar, `role="tab"` on each tab, `aria-selected`, `aria-controls` to the panel; `role="tabpanel"` on the panel with `aria-labelledby` back to the tab.
- **Replacement listbox/select** → `role="listbox"` + `role="option"` + `aria-selected`.
2. Declare `role="dialog"` on any component that traps clicks behind a backdrop, holds focus, and has a title and a dismiss control.
3. Generate the ids for `aria-labelledby`, `aria-controls`, and `aria-describedby` with React's `useId`.

---

### Anti-anchor

1. Never downgrade an ARIA contract violation the diff introduced to a Note as a minor nit, out of scope, or consistent with the codebase.
2. Fix it if removing the declared role, or the behavior the user can observe, would take away a contract the user was promised.
