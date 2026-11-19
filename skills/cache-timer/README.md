# cache-timer

cache-timer is a Claude Code mod that shows how long the prompt cache has left. After each
turn ends, the mod writes a label at the end of the hint row under the prompt,
for example "… ← for agents · Cache 60m". The label disappears when the next
turn starts.

## What the label says

- With more than 5 minutes left, the label changes every 5 minutes: "Cache 60m", then "Cache 55m".
- With 5 minutes or less, it changes every minute: "Cache 4m".
- With 1 minute or less, it changes every second: "Cache 59s".
- At zero it reads "Cache expired".

The wide steps keep the row still for most of the hour. The label rounds up, so
"Cache 55m" means that between 50 and 55 minutes are left.

## When the countdown starts

The provider counts a cache entry's lifetime from the start of the request that
wrote or read it. A turn can send several requests, so the mod counts from the
start of the turn's last request that came back with a usage count. The mod
ignores requests that subagents send.

The first label appears after the first turn that had such a request.

## The lifetime setting

The mod assumes a one-hour cache. To count five minutes instead, add this to
`~/.claude/settings.json`:

```json
{ "pluginConfigs": { "cache-timer": { "options": { "ttl": "5m" } } } }
```

Any other `ttl` value gives one hour.

## Why the label sits on the hint row

A mod cannot make Claude Code run the status line command again. A countdown in the status line would need `refreshInterval` in
the `statusLine` setting, which runs the command on a timer. William turned
that down at 1, 10, and 60 seconds because of what each run costs. Do not add
`refreshInterval` for this mod.

A mod can redraw the hint row itself. This mod stores the label in its own
state and hands it to the `PromptHint` component as `tail`, so the row redraws
only when the label changes.

## Run the tests

```
claude plugin test ~/.claude/skills/cache-timer
claude plugin validate ~/.claude/skills/cache-timer
```
