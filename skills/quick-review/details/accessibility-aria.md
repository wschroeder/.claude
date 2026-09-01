# ARIA role / contract correctness (UI components)

ARIA roles are contracts the component must deliver on. The same Conventions / sibling-consistency reasoning that catches "module A declares `@behaviour X` and module B doesn't" applies to UI components: a component declaring an ARIA role takes on the keyboard and focus contract that role implies, and a component shaped like a dialog/disclosure/listbox owes its users the corresponding role declaration. Both directions are Fix-class — the Yes-to-any gate fires on spec compliance.

---

## Direction A — declared role without keyboard/focus contract

A component that declares `role="menu"`, `role="listbox"`, `role="dialog"`, `role="combobox"`, `role="tab"`, `role="tablist"`, or similar without the keyboard interactions and focus management the role REQUIRES (per WAI-ARIA Authoring Practices) is a false promise to assistive-tech users — screen readers announce the role but users cannot navigate as expected.

For each ARIA role introduced or modified by the diff, list the role's required keyboard behaviors and focus management; verify the component implements them. Common required pairs:

- **`role="menu"` / `role="menuitem"`** — arrow keys (Up/Down), Home/End, Enter/Space activation, focus trapped within the menu, focus restored to the trigger on close. `aria-haspopup="menu"` on the trigger.
- **`role="dialog"` (modal)** — `aria-modal="true"`, `aria-labelledby` pointing at the title `id`, focus trapped inside until close, focus restored to the opener on close, Escape closes.
- **`role="listbox"` / `role="option"`** — arrow keys, `aria-selected`, single/multi-select semantics, `aria-activedescendant` if focus stays on the listbox.
- **`role="tab"` / `role="tablist"` / `role="tabpanel"`** — arrow keys traverse tabs, `aria-selected`, `aria-controls` pointing at the panel id.
- **`role="combobox"`** — `aria-expanded`, `aria-controls`, `aria-activedescendant`.

If the component declares the role but lacks the contract, three paths are valid; pick one with reason:

### Path (a) — Implement the contract

Best when the contract's effort matches the component's blast radius (a destructive modal earns Escape + backdrop-click + focus-on-open + focus-trap + focus-restore; a lightweight popover may not).

### Path (b) — Drop the role and use simpler semantics

Best when the contract is overkill for current use — a one-item dropdown does not need full WAI-ARIA menu navigation; a plain `<button>` + `<ul>` is honest. A plain `<button>` + region with `aria-expanded`/`aria-controls` is honest for a non-`role="dialog"` overlay.

### Path (c) — Match the codebase's partial-contract baseline

Best when *every* sibling component of the same role-class in this codebase ships the same partial contract (e.g., every modal in the app declares `role="dialog"` + `aria-modal` + `aria-labelledby` but none implement focus trap, focus restore, or Escape). In that case, aligning the new component to the same baseline is the right scope for one PR; diverging upward or downward in isolation creates an inconsistent island. Closing the broader gap is its own ticket.

**Verify the precedent with a repo-wide grep, not by reading one nearby file** — and document the precedent in the review output so the team can revisit holistically.

Do NOT use "consistent with other code" as a generic dismissal. Path (c) requires the precedent to apply specifically to the role-class in question, verified by enumeration. The deletion test for path (c): if the precedent is removed (every other sibling is upgraded to the full contract), is the new component's partial contract still defensible? If no, path (c) is just procrastination — pick (a) or (b).

Even when path (c) is justified for the heavy parts of the contract (focus trap, focus restore), small deviations from the sibling (sibling closes on backdrop click; new component does not) are still Fix-class — that's parity, not contract-completion. The "yes to any" gate fires whenever the *new* component diverges from siblings in either direction.

---

## Direction B — component IS a role but does not declare it

Inversely: an overlay `<div>` that traps clicks behind a backdrop, holds focus, has a title and a dismiss control IS a `role="dialog"` whether or not it spells it out — and a screen reader without the role sees only a div. A `<button>` that toggles a visible/hidden region without `aria-expanded` and `aria-controls` is an incomplete disclosure pattern.

For every modal/popover/disclosure/tablist/listbox-shaped component in the diff, verify the corresponding role + aria-* attributes are declared:

- **Modal overlays** → `role="dialog"` + `aria-modal="true"` + `aria-labelledby` (or `aria-label`) on the dialog container; matching `id` on the title element.
- **Disclosure buttons** (any "click to expand a region") → `aria-expanded={open}` + `aria-controls={regionId}` on the trigger; matching `id` on the controlled region.
- **Tabs** → `role="tablist"` on the bar, `role="tab"` on each tab, `aria-selected`, `aria-controls` to the panel; `role="tabpanel"` on the panel with `aria-labelledby` back to the tab.
- **Replacement listbox/select** → `role="listbox"` + `role="option"` + `aria-selected`.

The "looks like, walks like" test: if the component traps clicks behind a backdrop, holds focus, has a title and a dismiss control, it is a `role="dialog"` whether it declares it or not — declare it. Use React's `useId` hook for stable id generation across SSR/hydration when wiring `aria-labelledby` / `aria-controls` / `aria-describedby`.

---

## Anti-anchor

"Minor accessibility nit, out of scope" / "consistent with the codebase" / "other components do this too" are NOT acceptable Note-class downgrades for either direction. Self-introduced ARIA contract violations (the diff added the role; the diff added the modal-shaped component) are Fix-class regardless of what the rest of the codebase does.

**Deletion test:** if you remove the declared role (or the component-shape behavior the user can observe), does the user lose the contract they were promised? If yes, fix.
