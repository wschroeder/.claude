---
name: status-page
description: Lays out a status or health page — the page that answers "is everything running?" — as one summary line followed by one row per check, with colour only on each row's icon and status word, a tinted notice only where a status needs explaining, the detail behind a link on its own page, and no tiles, tinted cards, subtitles, or tooltips. Use before building a status page, a health page, a system-status or uptime view, or an ops "is it working" screen, and before any edit to such a page's markup or styles. Differs from `dashboard-task`, which builds a page that argues a story the operator picks; a status page always tells the same story, so there is no story to pick.
---

## Purpose

1. Build every status page, which answers only "is everything running?", to the fixed layout below.
2. Take behaviour at different widths from `responsive-design`; this skill says what goes on the page and in what order.

## The layout

1. **One summary line, first.** A green check with "Everything is running", or a
   red cross with "N problems". Put no subtitle and no explanation of the page
   above it.
2. **One row per check.** Each row holds an icon, the check's name, a detail
   line underneath the name, and a status word on the right.
3. **In a row, colour goes on the icon and the status word only.** Show green
   when a check is healthy too. Do not tint the row, a card, or a tile. Give a
   notice that explains why a check reads red or stale the status colour as a
   light tint behind its icon and its words, never grey. See
   [references/measurements.md](references/measurements.md).
4. **Pair every colour with a shape and a word.** The icon is a check or a
   cross with an `aria-label` such as "OK" or "Problem", and the status word
   says the same thing in text (WCAG 1.4.1).
5. **The detail lives on its own page.** Where a check counts failures, the
   count itself is the link, underlined, with an `aria-label` that says where it
   goes, such as "2 failed, view failures" (WCAG 2.4.4).
6. **No tooltips.** Put anything a reader needs into the detail line or onto
   the linked page.
7. **Copy the app's own table and notice markup.** Build each table from the
   markup the app's other tables already use, header row included, and each
   notice from the app's own notice of the same status. Name the view you
   copied.

## What to avoid

- A grid of green and red tiles, one per area.
- Choosing a story, a chart, or a hero number. The summary line is the only
  headline the page has.
- Hiding a failure's detail inside a hover state or an expander on the same row.

## Autonomous behaviour

1. Build to this layout without asking.
2. Stop and ask only when the operator wants something the layout rules out, such as tiles or a tooltip, and say which rule above it breaks.
