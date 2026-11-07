# Playing a Godot 4 game on an iPhone through its browser

Read this when a person has to play a Godot game on their phone and nobody has an Apple signing identity. A web export served from this machine over the local network reaches the phone's browser with no certificate, no Xcode account, and no app store. Measured on Godot 4.5 with an iPhone running Brave and Safari's engine underneath it.

## Contents

- [Export a build the phone will start](#export-a-build-the-phone-will-start)
- [Serve it to the phone](#serve-it-to-the-phone)
- [Tell a phone from a desktop](#tell-a-phone-from-a-desktop)
- [A touch number can arrive negative](#a-touch-number-can-arrive-negative)
- [Drive a thumb yourself before you send the link](#drive-a-thumb-yourself-before-you-send-the-link)
- [Walk a character with a driver that stays open](#walk-a-character-with-a-driver-that-stays-open)
- [Dead ends](#dead-ends)

## Export a build the phone will start

1. Install the export templates for Godot's exact version before running `--export-release`.
2. Give the project a Web preset with these options:

```
variant/extensions_support=false
variant/thread_support=false
html/head_include="<script>Object.defineProperty(window, 'isSecureContext', { value: true });</script>"
html/canvas_resize_policy=2
html/focus_canvas_on_start=true
```

3. Set the web audio driver to the silent one in `project.godot`:

```
[audio]
driver/driver.web="Dummy"
```

4. Keep all three settings, because each one left out fails silently or misleadingly:
   - The `head_include` line tells the page it is in a secure context, which a phone grants only to HTTPS and `localhost`.
   - The single-threaded export avoids the cross-origin isolation headers a plain file server does not send.
   - The Dummy driver avoids the AudioWorklet, which needs a real secure context; without it the engine dies at boot with `TypeError: Cannot read properties of undefined (reading 'addModule')`.
5. If the game plays sound, then serve it over HTTPS with a real audio driver instead.
6. Exclude tests and test addons from the pack with `exclude_filter`.

## Serve it to the phone

1. Export, serve, and find the address the phone opens, on port 8000:

```
godot --headless --path <project> --export-release "Web" build/web/index.html
python3 -m http.server 8000 --bind 0.0.0.0 --directory build/web
ipconfig getifaddr en0        # the address the phone opens, on port 8000
```

2. Bind to `0.0.0.0`, because the default listens only to this machine.
3. Before you tell the person a fix is on their phone, read the server log for a `GET /index.pck` from their phone's address later than the export, because a phone holds on to the old build.

## Tell a phone from a desktop

1. Check `web_ios`, `web_android`, and `mobile` with `OS.has_feature` to decide when to show touch controls, because a phone's browser reports one of the first two and not `mobile`.

## A touch number can arrive negative

1. Never use a negative `InputEventScreenTouch.index` to mean "no finger is down", because Godot's web runtime copies each `touch.identifier` into a 32-bit signed integer (`setHeapValue(ids+i*4, touch.identifier, "i32")` in the exported `index.js`) and an iPhone hands out identifiers above 2,147,483,647.
2. Keep a separate boolean for whether a finger is held, and compare indexes only for equality.

## Drive a thumb yourself before you send the link

1. Before you hand the address to anyone, send real touches and capture the frames either side of them; a title screen proves only that the build starts.
2. Drive Playwright's WebKit, the engine an iPhone browser runs, rather than Chrome.
3. Build touch events by hand, because `new Touch(...)` throws "Illegal constructor" there.
4. Set `TOUCH_ID` above 2147483647 to reproduce the iPhone's large identifiers.
5. Install Playwright with `npm i playwright` and `npx playwright install webkit`, then run the script below as `TOUCH_ID=3000000000 node wktouch.mjs <url> <outdir> "<steps>" landscape`. The steps are `wait:<ms>`, `shot:<name>`, `tap:<x>:<y>`, `down:<x>:<y>`, `move:<x>:<y>`, and `up`, separated by commas, with coordinates in the page's own CSS pixels:

```js
import { webkit, devices } from 'playwright';
const [,, url, outdir, steps, orient] = process.argv;
const browser = await webkit.launch();
const d = devices['iPhone 15'];
const vp = orient === 'portrait' ? d.viewport : { width: d.viewport.height, height: d.viewport.width };
const ctx = await browser.newContext({ ...d, viewport: vp });
const page = await ctx.newPage();
page.on('console', m => console.log('console:', m.text()));
page.on('pageerror', e => console.log('pageerror:', e.message));
await page.goto(url);
const ID = Number(process.env.TOUCH_ID || 1);
const fire = (type, x, y) => page.evaluate(([type, x, y, ID]) => {
  const c = document.querySelector('canvas');
  const t = { identifier: ID, target: c, clientX: x, clientY: y, pageX: x, pageY: y, screenX: x, screenY: y };
  const mk = a => Object.assign([...a], { item: i => a[i] });
  const list = type === 'touchend' ? [] : [t];
  const e = new Event(type, { bubbles: true, cancelable: true });
  Object.defineProperties(e, { touches: { value: mk(list) }, targetTouches: { value: mk(list) }, changedTouches: { value: mk([t]) } });
  c.dispatchEvent(e);
}, [type, x, y, ID]);
let last = [0, 0];
for (const s of steps.split(',')) {
  const [k, a, b] = s.split(':');
  if (k === 'wait') await page.waitForTimeout(+a);
  else if (k === 'shot') { await page.screenshot({ path: `${outdir}/${a}.png` }); console.log('shot', a); }
  else if (k === 'tap') { await page.touchscreen.tap(+a, +b); }
  else if (k === 'down') { last = [+a, +b]; await fire('touchstart', +a, +b); }
  else if (k === 'move') { last = [+a, +b]; await fire('touchmove', +a, +b); }
  else if (k === 'up') await fire('touchend', ...last);
}
console.log('viewport', JSON.stringify(vp));
await browser.close();
```

6. Wait about twelve seconds after loading before the first touch, because the engine takes that long to boot headless.
7. Read the captures yourself, and look for the control appearing under the thumb and the character moving between them.

## Walk a character with a driver that stays open

1. To walk a character somewhere, keep one browser open and send it a few steps at a time, taking a capture and looking at it before choosing the next steps, because a one-shot run with fixed hold times ends somewhere different each run.
2. Start the driver in the background and give it about sixteen seconds to boot:

```
TOUCH_ID=3000000000 node wkrepl.mjs http://localhost:8000/ <outdir>
```

3. Send steps with `send.sh <outdir> <n> "<steps>"`, in the same form as `wktouch.mjs`'s, growing `n` by one on every call; `send.sh` returns when the driver writes `n` into `done.txt`.
4. Send `quit` to close the browser, and discard that call's output, because the driver writes no `done.txt` line for `quit` and the call times out.

```js
import { webkit, devices } from 'playwright';
import fs from 'fs';
const [,, url, outdir] = process.argv;
const browser = await webkit.launch();
const d = devices['iPhone 15'];
const vp = { width: d.viewport.height, height: d.viewport.width };
const ctx = await browser.newContext({ ...d, viewport: vp });
const page = await ctx.newPage();
page.on('pageerror', e => console.log('pageerror:', e.message));
await page.goto(url);
const ID = Number(process.env.TOUCH_ID || 1);
const fire = (type, x, y) => page.evaluate(([type, x, y, ID]) => {
  const c = document.querySelector('canvas');
  const t = { identifier: ID, target: c, clientX: x, clientY: y, pageX: x, pageY: y, screenX: x, screenY: y };
  const mk = a => Object.assign([...a], { item: i => a[i] });
  const list = type === 'touchend' ? [] : [t];
  const e = new Event(type, { bubbles: true, cancelable: true });
  Object.defineProperties(e, { touches: { value: mk(list) }, targetTouches: { value: mk(list) }, changedTouches: { value: mk([t]) } });
  c.dispatchEvent(e);
}, [type, x, y, ID]);
let last = [0, 0], seen = '';
const cmd = `${outdir}/cmd.txt`, done = `${outdir}/done.txt`;
fs.writeFileSync(done, 'ready\n');
for (;;) {
  await page.waitForTimeout(200);
  if (!fs.existsSync(cmd)) continue;
  const text = fs.readFileSync(cmd, 'utf8').trim();
  if (!text || text === seen) continue;
  seen = text;
  const [n, steps] = text.split('|');
  if (steps === 'quit') break;
  for (const s of steps.split(',')) {
    const [k, a, b] = s.split(':');
    if (k === 'wait') await page.waitForTimeout(+a);
    else if (k === 'shot') await page.screenshot({ path: `${outdir}/${a}.png` });
    else if (k === 'tap') await page.touchscreen.tap(+a, +b);
    else if (k === 'down') { last = [+a, +b]; await fire('touchstart', +a, +b); }
    else if (k === 'move') { last = [+a, +b]; await fire('touchmove', +a, +b); }
    else if (k === 'up') await fire('touchend', ...last);
  }
  fs.writeFileSync(done, `${n}\n`);
}
await browser.close();
```

```bash
#!/bin/bash
# send.sh <outdir> <n> <steps>: run steps in the open browser and wait for them to finish
echo "$2|$3" > "$1/cmd.txt"
for i in $(seq 1 300); do [ "$(cat "$1/done.txt" 2>/dev/null)" = "$2" ] && exit 0; sleep 0.2; done; echo timeout; exit 1
```

## Dead ends

1. Never use headless Chrome with `--virtual-time-budget`, which never gets past the Godot splash.
2. Hold the phone sideways for a landscape game, because upright letterboxes it into a strip and a press in the black band still reaches the game as a touch that nobody sees drawn.
