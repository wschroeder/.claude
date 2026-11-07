# Shell scripts and the secrets they print

Read this when the diff adds or changes a shell script, or code that generates one: cloud-init, user-data, a Dockerfile `RUN`, a pod-spec command, or any `<wrapper> -c '<compound>'`.

Contents:

- Shell-trace credential exposure
- Where a shell trace lands
- CWE-78 OS command injection

## Shell-trace credential exposure (`set -x` / `bash -x`)

Any script that runs with xtrace enabled (`set -x`, `set -ex`, shebang `#!/bin/bash -x`, `BASH_XTRACEFD`, `sh -x`, PowerShell `Set-PSDebug -Trace 2`, fish `--debug`) echoes every command it executes (post-expansion) to stderr. If the script subsequently writes a secret via `echo "$TOKEN" > file`, `curl -H "Authorization: Bearer $TOKEN"`, `aws ... --value "$TOKEN"`, `printf "%s\n" "$TOKEN"`, or any here-doc that interpolates the secret, the FULL command including the secret lands in whatever sink consumes stderr.

For every shell script generated or modified by the diff:
1. Locate the xtrace toggle (`set -x` / `set -ex` / shebang `-x` / explicit `set +x`/`set -x` pairs).
2. List every command in the script that handles a secret — token, password, API key, database URL with embedded creds, Stripe/Twilio/etc. key, OAuth client_secret, JWT, SSH private key, signed-URL emit.
3. If any secret-handling command runs while xtrace is enabled, the secret hits stderr. Required fix: wrap the secret-handling block in `set +x` ... `set -x` (or stop using xtrace entirely if the trace adds no operator value). Inline rationale: `# set +x: avoid token in xtrace -> CloudWatch / journal / cloud-init log`.

## Where a shell trace lands: cloud-init, user-data, systemd, and launch-script log sinks

Shell traces don't disappear — they get shipped. Enumerate the script's stderr destinations:

- **Cloud-init (AWS / GCP / Azure):** xtrace output goes to `/var/log/cloud-init-output.log` AND `/var/log/cloud-init.log` on the instance. Both are typically shipped by the CloudWatch Agent / Stackdriver / Azure Monitor agent if installed. Retention often 30+ days.
- **systemd unit `ExecStart=`/`ExecStartPre=`:** stderr routed to journald; shows in `journalctl -u <unit>`. Journals persist across reboots if `Storage=persistent` is set.
- **AWS SSM SendCommand:** stdout/stderr captured in Run Command output and (if configured) shipped to S3 / CloudWatch.
- **EC2 launch-template user-data:** retained in `/var/lib/cloud/instance/user-data.txt` (0600 root); also readable via IMDS by any process unless IMDSv2 + correct hop-limit are enforced.
- **Kubernetes init containers / pod log streams:** any `kubectl logs` viewer can read xtrace output.
- **Buildkite / GitHub Actions / CircleCI / Jenkins job logs:** xtrace-traced scripts in a CI step land in the build log, often with public-read visibility for OSS projects.

**Discovery:** when the diff generates a script via template (`cloud-init.ts`, `user-data.sh.tmpl`, `Dockerfile RUN`, K8s pod-spec command), grep for `set -x` / `set -ex` / `bash -x` / shebang `-x` in the template and trace each secret-handling site against the xtrace mask. The `# set +x` cap is NOT optional — the failure mode is silent, the log is durable, and the secret often has a long TTL.

## CWE-78 OS Command Injection (compound-string in single outer quote)

`spawn`/`exec`/`System.cmd` with user input. **Compound-string assembly inside a single outer quote** is the subtle shape: when N variables are concatenated into one long shell command and only the OUTER call (`shellQuote(...)`, `JSON.stringify(...)`, `q(...)`) wraps the whole compound, every inner variable is an injection point if the receiving shell re-parses the contents.

Classic shape:

```ts
scriptLines.push(
  `su - ec2-user -c ${shellQuote("if [ -d /home/x/dev/" + safeName + " ]; then cd /home/x/dev/" + safeName + " && git pull; fi")}`
);
```

The outer `shellQuote` wraps the whole `if ...` string in single quotes for the OUTER shell (the cloud-init script). When `su -c '...'` runs, it strips those outer quotes and passes the inner string to a NEW shell, which re-parses the contents — at which point `$(...)`, backticks, `${VAR}`, `;`, `&&`, `|`, `>`, and `<` all expand inside `safeName`. A `sanitizeValue` that only strips control characters (`\x00-\x1f\x7f`) does not block any of these metacharacters.

Fix: `shellQuote` (or strict allowlist) every inner variable BEFORE the outer wrap, so the inner shell sees `'safe_name_value'` as a literal:

```ts
const dir = "/home/x/dev/" + safeName;
scriptLines.push(
  `su - ec2-user -c ${shellQuote("if [ -d " + shellQuote(dir) + " ]; then cd " + shellQuote(dir) + " && git pull; fi")}`
);
```

The same shape appears in `su -c`, `sudo -u user -- bash -c`, `ssh user@host '...'`, `kubectl exec -- bash -c`, `docker exec -it container bash -c`, and any `<wrapper> -c '<compound>'` invocation. **Discovery:** grep `-c "` and `-c '` in script-generation code; for each hit, list inner-variable injections and confirm they pass through an inner quoter.
