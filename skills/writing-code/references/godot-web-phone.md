# Playing a Godot 4 game on an iPhone through its browser

Use this when a person has to play a Godot game on their phone and nobody has an
Apple signing identity. A web export served from this machine over the local
network reaches the phone's browser with no certificate, no Xcode account, and
no app store. Measured on Godot 4.5 with an iPhone running Brave and Safari's
engine underneath it.

## Contents

- [Export a build the phone will start](#export-a-build-the-phone-will-start)
- [Serve it to the phone](#serve-it-to-the-phone)
- [Tell a phone from a desktop](#tell-a-phone-from-a-desktop)
- [A touch number can arrive negative](#a-touch-number-can-arrive-negative)
- [Drive a thumb yourself before you send the link](#drive-a-thumb-yourself-before-you-send-the-link)
- [Walk a character with a driver that stays open](#walk-a-character-with-a-driver-that-stays-open)
- [Dead ends](#dead-ends)

## Export a build the phone will start

Godot needs the export templates for its exact version installed before
`--export-release` will run. Then give the project a Web preset with these
options:

```
variant/extensions_support=false
variant/thread_support=false
html/head_include="<script>Object.defineProperty(window, 'isSecureContext', { value: true });</script>"
html/canvas_resize_policy=2
html/focus_canvas_on_start=true
```

and set the web audio driver to the silent one in `project.godot`:

```
[audio]
driver/driver.web="Dummy"
```

Each of the three settings below is needed, and all of them fail silently or
misleadingly when you leave one out:

- **Godot's page refuses to start outside a secure context.** A phone grants one
  only to HTTPS and to `localhost`, and a phone reaching your laptop is neither.
  The `head_include` line tells the page it is secure.
- **The threaded build needs cross-origin isolation headers,** which a plain file
  server does not send. Export single-threaded instead.
- **Godot's web audio driver loads an AudioWorklet, which a browser hands out
  only in a real secure context.** The `head_include` trick does not fool it.
  Without the Dummy driver, the engine dies at boot with
  `TypeError: Cannot read properties of undefined (reading 'addModule')`. A game
  that plays sound needs HTTPS and a real driver instead.

Exclude tests and test addons from the pack with `exclude_filter`, because none
of that code runs on a phone.

## Serve it to the phone

```
godot --headless --path <project> --export-release "Web" build/web/index.html
python3 -m http.server 8000 --bind 0.0.0.0 --directory build/web
ipconfig getifaddr en0        # the address the phone opens, on port 8000
```

The bind to `0.0.0.0` matters, because the default listens only to this machine.

**Before you tell the person a fix is on their phone, read the server log for
their phone's address.** A phone holds on to the old build. Each request line
carries the source address and the time, so a `GET /index.pck` from the phone's
address that is later than the export proves they are playing the new build. In
one run the log showed the phone had last loaded the game four minutes before
the fixed build was written.

## Tell a phone from a desktop

A phone's browser reports the feature tag `web_ios` or `web_android`, and not
`mobile`. Check all three with `OS.has_feature` to decide when to show touch
controls.

## A touch number can arrive negative

Godot's web runtime copies each `touch.identifier` into a 32-bit signed integer
(`setHeapValue(ids+i*4, touch.identifier, "i32")` in the exported `index.js`).
An iPhone can hand out identifiers above 2,147,483,647, and those reach GDScript
as a negative `InputEventScreenTouch.index`. So never use a negative index to
mean "no finger is down". Keep a separate boolean for whether a finger is held,
and compare indexes only for equality. Measured: a virtual stick that treated a
negative index as "no finger" drew nothing and moved nobody on the operator's
iPhone, while desktop Chrome, whose identifiers stay small, worked fine. Keeping
a boolean fixed it on the phone.

## Drive a thumb yourself before you send the link

If the page loads and shows the title screen, you have proved only that the
build starts. Send real touches and capture the frames either side of them
before you hand the address to anyone. In one run, the link went out after the
title screen alone, and the operator found within minutes that the stick was
invisible and that a tap walked the party through a door. One drive would have
shown both.

Playwright's WebKit is the engine an iPhone browser runs, so drive that rather
than Chrome. `new Touch(...)` throws "Illegal constructor" there, so build the
touch events by hand. Set `TOUCH_ID` above 2147483647 to reproduce the iPhone's
large identifiers. Install Playwright with `npm i playwright` and
`npx playwright install webkit`, then run the script below as
`TOUCH_ID=3000000000 node wktouch.mjs <url> <outdir> "<steps>" landscape`. The
steps are `wait:<ms>`, `shot:<name>`, `tap:<x>:<y>`, `down:<x>:<y>`,
`move:<x>:<y>`, and `up`, separated by commas, with coordinates in the
page's own CSS pixels:

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

Wait about twelve seconds after loading before the first touch, because the engine
takes that long to boot headless. Read the captures yourself, and look for the
control appearing under the thumb and the character moving between them.

## Walk a character with a driver that stays open

To walk a character somewhere, keep one browser open and send it a few steps at
a time. Take a capture, look at it, and then choose the next steps. A one-shot
run with fixed hold times puts the character in a different place every run,
because the game's frames do not line up with the hold. In one demo, six
one-shot runs in a row each ended somewhere new, and a diagonal slid past the
door.

Start the driver in the background and give it about sixteen seconds to boot:

```
TOUCH_ID=3000000000 node wkrepl.mjs http://localhost:8000/ <outdir>
```

Then send steps with `send.sh <outdir> <n> "<steps>"`. The steps take the same
form as `wktouch.mjs`'s, and `n` must grow by one on every call. `send.sh`
returns when the driver writes `n` into `done.txt`. Send `quit` to close the
browser. The driver never writes a `done.txt` line for `quit`, so that one
call times out, and you should discard its output.

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

- Headless Chrome run with `--virtual-time-budget` never gets past the Godot splash.
- Holding the phone upright letterboxes a landscape game into a strip, and a
  press in the black band still reaches the game as a touch. Anything the game
  draws at that touch point falls outside the picture, so nobody sees it.
