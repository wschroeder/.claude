# Pass 3 — Error handling / information exposure

Failure modes, pattern-match style, sibling consistency, observability of failure paths. Angle numbering matches SKILL.md.

## 3.1 Error propagation trace

For each `{:error, reason}` or Logger call in new code, follow the error through the full `with`/`case` chain to its terminal handler (the place that finally acts on it — logs, returns to caller, retries). Check for duplicate logging at multiple levels of the chain. If the inner function logs and the outer function also logs the same error, flag the duplication.

## 3.2a Logging discipline (Elixir — codebase convention)

This codebase uses TWO log levels only — `Logger.info` and `Logger.error`. There is no "warning that's not an error" tier, and tracing belongs in telemetry / `:dbg` / `:recon` / dev-only `IO.inspect`, not in `Logger.debug`. For every `Logger.<level>` call introduced, modified, or relocated by the diff, classify the level:

- `Logger.info` — operationally visible state change a human should see (acceptable).
- `Logger.error` — problem requiring investigation (acceptable).
- `Logger.warning` / `Logger.warn` — flag for replacement. Decide per-site: (a) if it should be visible and acted on, change to `Logger.error`; (b) if it shouldn't be visible to humans (it's a metric or a trace), delete the call and emit telemetry instead. "Warning" is not a tier here.
- `Logger.debug` — flag for replacement. Either delete (the runtime cost of debug-level logs is real even when the level is filtered) or move to a dev-only `IO.inspect` / `:dbg.tp` / explicit telemetry counter. Production tracing uses Erlang's tracing primitives, not `Logger.debug`.
- Bare `Logger.log(level, ...)` with a runtime level — flag for the same audit; the level may resolve to `:warning` or `:debug`.

Apply the same audit to test files: `Logger.warning` / `Logger.error` calls intentionally emitted by code under test must be wrapped in `capture_log/1` (per `code-quality-checklist`), or the suite leaks new warnings/errors. A test that triggers an expected error path without `capture_log` violates the project guideline regardless of whether the assertions pass.

## 3.2b Logging discipline (TS/JS)

Every `console.log` / `console.error` introduced by the diff: structured key only, never raw identifier values, never tokens, never cookies, never auth headers, never password-shaped strings. Test fixtures may use synthetic identifiers today, but the log destination (CI artifacts, journald, screen recordings, build dashboards) is durable and often public for OSS projects.

The fix is mechanical: replace `console.log(\`[op:${fixture.key}] X (${fixture.identifier})\`)` with `console.log(\`[op:${fixture.key}] X\`)` — the fixture key alone identifies the row in CI without leaking the underlying email/username.

## 3.3 Shell-trace credential exposure (`set -x` / `bash -x`)

Any script that runs with xtrace enabled (`set -x`, `set -ex`, shebang `#!/bin/bash -x`, `BASH_XTRACEFD`, `sh -x`, PowerShell `Set-PSDebug -Trace 2`, fish `--debug`) echoes every command it executes (post-expansion) to stderr. If the script subsequently writes a secret via `echo "$TOKEN" > file`, `curl -H "Authorization: Bearer $TOKEN"`, `aws ... --value "$TOKEN"`, `printf "%s\n" "$TOKEN"`, or any here-doc that interpolates the secret, the FULL command including the secret lands in whatever sink consumes stderr.

For every shell script generated or modified by the diff:
1. Locate the xtrace toggle (`set -x` / `set -ex` / shebang `-x` / explicit `set +x`/`set -x` pairs).
2. List every command in the script that handles a secret — token, password, API key, database URL with embedded creds, Stripe/Twilio/etc. key, OAuth client_secret, JWT, SSH private key, signed-URL emit.
3. If any secret-handling command runs while xtrace is enabled, the secret hits stderr. Required fix: wrap the secret-handling block in `set +x` ... `set -x` (or stop using xtrace entirely if the trace adds no operator value). Inline rationale: `# set +x: avoid token in xtrace -> CloudWatch / journal / cloud-init log`.

## 3.4 Cloud-init / user-data / systemd / launch-script log sinks

Shell traces don't disappear — they get shipped. Enumerate the script's stderr destinations:

- **Cloud-init (AWS / GCP / Azure):** xtrace output goes to `/var/log/cloud-init-output.log` AND `/var/log/cloud-init.log` on the instance. Both are typically shipped by the CloudWatch Agent / Stackdriver / Azure Monitor agent if installed. Retention often 30+ days.
- **systemd unit `ExecStart=`/`ExecStartPre=`:** stderr routed to journald; shows in `journalctl -u <unit>`. Journals persist across reboots if `Storage=persistent` is set.
- **AWS SSM SendCommand:** stdout/stderr captured in Run Command output and (if configured) shipped to S3 / CloudWatch.
- **EC2 launch-template user-data:** retained in `/var/lib/cloud/instance/user-data.txt` (0600 root); also readable via IMDS by any process unless IMDSv2 + correct hop-limit are enforced.
- **Kubernetes init containers / pod log streams:** any `kubectl logs` viewer can read xtrace output.
- **Buildkite / GitHub Actions / CircleCI / Jenkins job logs:** xtrace-traced scripts in a CI step land in the build log, often with public-read visibility for OSS projects.

**Discovery:** when the diff generates a script via template (`cloud-init.ts`, `user-data.sh.tmpl`, `Dockerfile RUN`, K8s pod-spec command), grep for `set -x` / `set -ex` / `bash -x` / shebang `-x` in the template and trace each secret-handling site against the xtrace mask. The `# set +x` cap is NOT optional — the failure mode is silent, the log is durable, and the secret often has a long TTL.

## 3.5 capture_log assertion shape — no-output paths

When `capture_log` wraps a path that should emit NO logs (a happy-path that the diff just made silent, a refactor that moved a Logger call), the assertion must be `assert log == ""`, not `refute log =~ "specific phrase"`. The `refute log =~ ...` shape only catches one specific phrase — any OTHER unexpected log (a new `Logger.error` from a side path, a noisy library, a fresh telemetry warning) slips through and the test passes silently. That defeats the entire purpose of `capture_log` as a regression guard.

The right shapes are:
- **Path should emit nothing:** `assert log == ""` (catches anything).
- **Path should emit a SPECIFIC line:** `assert log =~ "expected phrase"` (positive — fails if missing).
- **Path should NOT emit a SPECIFIC line, but other logs are tolerated:** `refute log =~ "phrase"` (rare; document why).

A `refute` over a path documented as "no output" is a test-quality gap, not a style choice. Flag every `refute log =~ ...` in the diff and ask whether the underlying intent is "no output" — if yes, change to `assert log == ""`.

## 3.6 Silent catch-alls at call boundaries

When function A calls function B (especially across module boundaries — controller calling a context module, a webhook handler calling business logic), read A's handling of B's return. If A uses a catch-all clause (`_ ->`, bare `rescue`, or `{:error, _}` without logging/re-raising), the error's identity is lost. Flag cases where B can return distinguishable errors but A treats them identically or ignores them. A webhook controller that returns `200 OK` regardless of what the called module returns is a bug, not defensive coding.

## 3.7 with-chain escape hatches

In `with` blocks, check the `else` clause. If the else matches `_ ->` or `{:error, _} ->` without distinguishing which step failed, errors from different steps are conflated. Each fallible step in the `with` should either produce a distinguishable error or the else must handle the union of all possible failures explicitly.

## 3.8 with-chain over-gating

When a non-critical step in a `with` chain (e.g., setting a customer default, sending a notification) gates a critical step (e.g., creating a subscription, completing a transaction), a failure in the optional step short-circuits the essential one. If a step is best-effort or self-healing, it should not be in the `with` chain — move it after the chain or wrap it in a separate error-handling block.

## 3.9 Error-class differentiation at catch boundaries

When a catch handles multiple distinguishable error classes, verify the response is correct for EACH class, not just the one the author had in mind. `AbortError`, `TypeError` (network), timeout, and domain errors (`OAuthConfigError`, `DBError`) signal different intents; a fallback correct for one is often wrong for another.

Gate fallbacks on `error instanceof <Expected>` and propagate the rest. Blanket `catch { return fallback }` over a call that can produce >1 error class is a bug unless every class should collapse to the same fallback.

## 3.10 CWE-209 Error message contains sensitive info

Unredacted response bodies, stack traces, secrets in error strings. Per the redaction completeness rule: when a variable is redacted before one sink, EVERY sink must use the redacted form. One unredacted sink defeats the redaction.

## 3.11 CWE-532 Log exposes sensitive info

Tokens, PII, passwords, session IDs in Logger calls. Apply the two-tier discipline (3.2a/3.2b) at the call site; check Pass 4 redaction-completeness (4.3) for cross-sink consistency.

## 3.12 CWE-497 Exposure of System Data

Internal hostnames, pod IDs, DB errors returned to untrusted callers. The `error: err.message` pattern is the canonical leak — error messages often contain stack frames, file paths, library version strings, or DB query text that aid an attacker's recon.

## 3.13 CWE-754 Improper Check for Unusual Conditions

Dead guards, always-truthy checks, distinguishable error classes collapsed into one fallback. Pattern-matches with the template-literal-masks-nil shape (Pass 4): `${maybeUndefined}` produces the truthy string `"undefined"`, defeating the `if (!x)` guard the author thought they wrote.
