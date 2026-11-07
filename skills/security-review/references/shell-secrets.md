# Shell scripts and the secrets they print

1. Read this when the diff adds or changes a shell script, or code that generates one: cloud-init, user-data, a Dockerfile `RUN`, a pod-spec command, or any `<wrapper> -c '<compound>'`.

Contents:

- Shell-trace credential exposure
- Where a shell trace lands
- CWE-78 OS command injection

## Shell-trace credential exposure (`set -x` / `bash -x`)

For every shell script generated or modified by the diff:

1. Locate the xtrace toggle: `set -x`, `set -ex`, a shebang with `-x`, `BASH_XTRACEFD`, `sh -x`, PowerShell `Set-PSDebug -Trace 2`, fish `--debug`, and explicit `set +x`/`set -x` pairs.
2. List every command in the script that handles a secret, such as a token, password, API key, database URL with embedded credentials, OAuth client_secret, JWT, SSH private key, or signed URL, including an `echo`, `curl -H`, `printf`, CLI `--value`, or here-doc that interpolates it.
3. If any secret-handling command runs while xtrace is enabled, require the block wrapped in `set +x` ... `set -x`, or xtrace dropped entirely, with an inline comment such as `# set +x: avoid token in xtrace -> CloudWatch / journal / cloud-init log`.

## Where a shell trace lands: cloud-init, user-data, systemd, and launch-script log sinks

1. List the script's stderr destinations, which commonly include:

- **Cloud-init (AWS / GCP / Azure):** xtrace output goes to `/var/log/cloud-init-output.log` AND `/var/log/cloud-init.log` on the instance. Both are typically shipped by the CloudWatch Agent / Stackdriver / Azure Monitor agent if installed. Retention often 30+ days.
- **systemd unit `ExecStart=`/`ExecStartPre=`:** stderr routed to journald; shows in `journalctl -u <unit>`. Journals persist across reboots if `Storage=persistent` is set.
- **AWS SSM SendCommand:** stdout/stderr captured in Run Command output and (if configured) shipped to S3 / CloudWatch.
- **EC2 launch-template user-data:** retained in `/var/lib/cloud/instance/user-data.txt` (0600 root); also readable via IMDS by any process unless IMDSv2 + correct hop-limit are enforced.
- **Kubernetes init containers / pod log streams:** any `kubectl logs` viewer can read xtrace output.
- **Buildkite / GitHub Actions / CircleCI / Jenkins job logs:** xtrace-traced scripts in a CI step land in the build log, often with public-read visibility for OSS projects.

2. When the diff generates a script from a template, such as `cloud-init.ts`, `user-data.sh.tmpl`, a Dockerfile `RUN`, or a K8s pod-spec command, grep the template for `set -x`, `set -ex`, `bash -x`, and a shebang `-x`, and check each secret-handling site against the xtrace mask.
3. Treat a missing `# set +x` cap as a finding, never optional.

## CWE-78 OS Command Injection (compound-string in single outer quote)

1. Flag `spawn`, `exec`, and `System.cmd` with user input.
2. Flag a compound shell string whose variables are concatenated inside one outer quoter, such as `shellQuote(...)`, `JSON.stringify(...)`, or `q(...)`, when a wrapper hands the string to a new shell that re-parses it:

```ts
scriptLines.push(
  `su - ec2-user -c ${shellQuote("if [ -d /home/x/dev/" + safeName + " ]; then cd /home/x/dev/" + safeName + " && git pull; fi")}`
);
```

3. Count a sanitizer that strips only control characters as no defense.
4. Give the fix as `shellQuote`, or a strict allowlist, on every inner variable before the outer wrap:

```ts
const dir = "/home/x/dev/" + safeName;
scriptLines.push(
  `su - ec2-user -c ${shellQuote("if [ -d " + shellQuote(dir) + " ]; then cd " + shellQuote(dir) + " && git pull; fi")}`
);
```

5. Grep `-c "` and `-c '` in script-generation code, covering `su -c`, `sudo -u user -- bash -c`, `ssh user@host '...'`, `kubectl exec -- bash -c`, `docker exec -it container bash -c`, and any `<wrapper> -c '<compound>'`, and for each hit confirm every inner variable passes through an inner quoter.
