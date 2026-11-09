---
name: system-map
description: Builds a single-file HTML map of a whole system that a newcomer can click and zoom — an overview of regions, one zoomed scene per region, a side panel that describes each box, numbered "stories" that light one path across every region, a searchable glossary, and a shareable address for every view. Starts from a working template whose engine already routes lines around boxes, places labels and step badges without overlap, animates the zoom, and keeps Back and shared links honest. Use when asked for an interactive architecture diagram, a zoomable or clickable system map, an explainer of how laptops, source control, CI, cloud environments, permissions, and outside services fit together, or "a high-level map I can click into". Differs from `dashboard-task`, which argues a point with data or reports whether things are running.
---

## Purpose

1. Use this skill to build an explainer map that someone new to the system can read alone: what the parts are, how they connect, and which path a change, a sign-in, or a request takes.
2. The output is one self-contained `.html` file with no build step and no server, kept in the project beside its other runbook or docs pages.

## Process

### 1. Agree the scope with the operator

1. Ask who reads it, and write for that reader; for a beginner, spell out every acronym where it first appears and in the glossary.
2. Leave out secret values, cloud ids, file paths, and code references unless the operator asks for them.
3. Use two diagram levels, an overview and one scene per zoomable region, plus the side panel as a third level.
4. Carry each cross-cutting concern, such as a deploy, a sign-in, permissions, or network exposure, as a story rather than as another level.
5. Read the real configuration, such as infrastructure files and workflow files, for every permission, size, and schedule the page states, and mark anything you could not check as a question for the operator.

### 2. Start from the template

1. Copy `~/.claude/skills/system-map/references/template.html` to the project path, then replace its data and keep its engine.
2. Fill these tables in the data section, in this order: `GLOSSARY`, `REGIONS`, `OVERVIEW_FRAMES`, `NODES` (through `node()`), `EDGES` (through `edge()`), `SCENES`, `LENSES`; then `REGION_TEXT` and `showIntro` in the side-panel section, and the title, heading, and legend in the markup.
3. Give each region a color token pair (`--<color>` and `--<color>-bg`) in all three theme blocks: light, the `prefers-color-scheme: dark` block, and `:root[data-theme="dark"]`.
4. If you move or resize a region on the overview, retune `LANE` in `overviewRoute`, because its lanes are fixed coordinates between the regions.
5. Mark an edge that passes through a part, such as a private endpoint, with `via`, and an identity relationship with `identity: true`.
6. Give a scene a stub slot for every outside part its lines reach; a line whose far end has no slot is left out of that scene.
7. Put `net: 'open' | 'fw' | 'private'` on nodes only when a story has `net: true` and the legend explains the three colors.

### 3. Keep the display rules the template already holds

1. Draw every line faint and unlabelled until a story is chosen or a box is clicked, and light nothing while nothing is selected.
2. While something is lit, ghost the unlit lines further and draw the lit lines and their text stronger.
3. Unselect and restore the view when the reader clicks empty space or presses Escape.
4. Drop a line's label when it has no clear spot beside its own line, rather than placing it where it overlaps or floats apart; the panel's "Connects to" list still names every line.
5. Join labels that share one line as "first label +N", with the full text on hover.
6. Shrink box text to fit its box rather than letting it overflow.
7. Keep the glossary alphabetical and searchable by the word, never by text inside a definition.
8. Choose category colors that stay distinct from each other in both light and dark mode and keep 3:1 contrast against the surface; check each pair in both modes before you show it.

### 4. Keep the address honest

1. Write every view into the hash with readable keys: `zoom`, `story`, `step` (1-based), and `box`.
2. Push a history entry for each click, and replace instead of push for the first write after an address opens, so tidying a hand-typed link adds no Back step.
3. Never push from inside the `popstate` handler.
4. Stop any running zoom animation when a new view starts, whether from Back, a box click, or a second zoom.
5. Accept only keys that name a real scene, story, step, or node, through `Object.hasOwn`, never the `in` operator.

### 5. Verify in the browser after every edit

1. Treat the page as a screen-only change: it gets browser checks, not automated tests.
2. After every edit, extract the script and check its syntax:

```bash
awk '/<script>/{f=1;next}/<\/script>/{f=0}f' <page>.html > <scratchpad>/map.js && node --check <scratchpad>/map.js && echo SYNTAX-OK
```

3. Open the file in Chrome DevTools and run this walk through `evaluate_script`; every scene must report 0 lit lines with nothing selected, `errors` must be empty, and each dropped label is a candidate to fix by moving boxes or shortening the label:

```js
async () => {
  const wait = (ms) => new Promise((r) => setTimeout(r, ms));
  const errors = []; window.addEventListener('error', (e) => errors.push(e.message));
  const lit = () => document.querySelectorAll('#stage .edge:not(.quiet):not(.dim) > path').length;
  const out = { views: 0, litWithNothingSelected: {}, dropped: [] };
  for (const scene of ['overview', ...Object.keys(SCENES)]) {
    for (const story of [null, ...LENSES.map((l) => l.id)]) {
      location.hash = new URLSearchParams({ ...(scene !== 'overview' && { zoom: scene }), ...(story && { story }) }).toString();
      await wait(150); out.views++;
      if (!story) out.litWithNothingSelected[scene] = lit();
      if (story && scene !== 'overview') {
        const hot = document.querySelectorAll('#stage .edge.hot > path').length, tags = document.querySelectorAll('#stage .tag .elabel').length;
        if (tags !== hot) out.dropped.push(`${scene}/${story}: ${tags} labels for ${hot} lines`);
      }
    }
    if (scene !== 'overview') for (const id of Object.keys(NODES).filter((n) => NODES[n].region === scene)) {
      location.hash = `zoom=${scene}&box=${id}`; await wait(100); out.views++;
      if (document.querySelector('#panel h2')?.textContent !== NODES[id].label) errors.push(`panel ${id}`);
    }
  }
  location.hash = ''; await wait(150);
  return { ...out, errors };
}
```

4. Take a screenshot of the overview, one zoomed scene with a story, and one with a clicked box, in light and dark mode, at about 1400×900 and at 320×568.
5. Test Back by wrapping `history.pushState` with a counter and reading `location.hash` after each `history.back()`, because Chrome caps `history.length` at 50.
6. Run `responsive-design`'s checklist, then the reviews `writing-code` owes, then a `writing-prose` pass over the panel and story text.

### 6. Hand it over

1. Commit the page as one commit through `git-commit`.
2. Ask before publishing it anywhere, under `~/.claude/CLAUDE.md`'s publishing rule.

## Rules

1. If a navigation changes only the hash of the same file, then reload the bare URL with the cache ignored before you probe, because DevTools does not reload the document.
2. Wait about 1000 ms after a zoom and 400 ms after a box or story click before you read the page.
3. Skip the dashed stubs when a probe clicks through boxes, because a stub jumps to another scene.
4. Count lit lines with `#stage .edge:not(.quiet):not(.dim) > path`, because labels and badges move to a separate top layer.
5. Select clickable boxes with `[role="button"][aria-label]`.
6. Make string edits to the page with the Edit tool rather than a Python or sed replace, which can break JavaScript quoting; run the syntax check after each one.
7. Save probes as files beside the work rather than retyping them, and load only the skill the next step needs, because this work has run four sessions out of context.

## Autonomous behaviour

1. Build, probe, and fix layout problems without asking.
2. Stop and ask before you add a level, drop a story, change what the page leaves out, or name anything sensitive.
3. Report each check you ran with its output, and list every question about the real system you could not answer from its configuration.
