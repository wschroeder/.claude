# Class Checklist — CWE deep dives

Discovery methods and worked examples for the CWE classes named in SKILL.md's Class Checklist. Each in-scope class becomes a mandatory angle in its pass; this file holds the worked-example shapes for the ones whose discovery is non-obvious.

Reference taxonomies: CWE Top 25 (https://cwe.mitre.org/top25/), OWASP Top 10 (web), OWASP API Security Top 10, SANS Top 25.

---

## Pass 2 — Injection / SSRF / protocol

### CWE-89 SQL Injection

Raw SQL, string interpolation into queries, `Repo.query` with user input. In Elixir, `Ecto.Query.fragment("...#{user_input}...")` is the canonical leak shape; in TS/JS, raw `pool.query("... " + x)` or template-string concatenation into `SELECT`.

### CWE-79 XSS

Unescaped user input into HTML/JSX, `dangerouslySetInnerHTML`, `innerHTML`, `v-html`. React escapes by default for JSX text but NOT for `dangerouslySetInnerHTML={{ __html: x }}`.

### CWE-78 OS Command Injection (compound-string in single outer quote)

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

Even when the input is admin-curated (an `available_repos` table, a tenant config, a build matrix), this is Fix-class — the boundary of trust may shift (admin compromise, DB-write attack, future user-facing form), and the cost of inner quoting is trivial.

The same shape appears in `su -c`, `sudo -u user -- bash -c`, `ssh user@host '...'`, `kubectl exec -- bash -c`, `docker exec -it container bash -c`, and any `<wrapper> -c '<compound>'` invocation. **Discovery:** grep `-c "` and `-c '` in script-generation code; for each hit, list inner-variable injections and confirm they pass through an inner quoter.

### CWE-94 Code Injection

`eval`, `Function()`, dynamic `require`, `Code.eval_string`.

### CWE-918 SSRF

HTTP client with user-controlled URL; allowlist applied after parse. Check the order: parse first, then allowlist — never the reverse, or a URL like `http://allowed.com@evil.com/` passes a string-prefix allowlist but resolves to `evil.com`.

### CWE-601 Open Redirect

Response `Location` from user input without allowlist. The same `.origin` vs `.startsWith` rule from Pass 2 / Pass 4 applies.

### CWE-300 / CWE-319 MITM / Cleartext Transmission

Scheme downgrade, `http://` allowed where `https://` expected, mixed-content in trusted-host comparisons.

### CWE-295 Improper Certificate Validation

Disabled TLS verification, custom cert handling, `rejectUnauthorized: false`.

### CWE-352 CSRF

State-changing requests without token/SameSite cookie.

### CWE-22 Path Traversal

User input into filesystem paths, `path.join` without a resolve guard. Check that `path.resolve(base, user_input)` is followed by `if (!resolved.startsWith(base))` validation.

### CWE-502 Insecure Deserialization

`JSON.parse`, `yaml.load`, `:erlang.binary_to_term` on user data. The Erlang case is particularly dangerous because deserialized atoms persist and can exhaust the atom table.

### CWE-611 XXE

XML parsing with entity resolution enabled.

---

## Pass 1/2 — Access control

### CWE-284 / CWE-285 Improper Authorization

Missing or wrong permission check before action.

### CWE-287 Improper Authentication

Weak authn, bypassable session check.

### CWE-306 Missing Authentication

Endpoint with no authn at all.

### CWE-639 Authorization Bypass via User-Controlled Key (IDOR)

`GET /orders/:id` where `:id` is not scoped to the caller. Sibling to Pass 2 Lookup-then-filter cardinality leak.

### CWE-862 Missing Authorization

Authn present, authz absent.

### CWE-863 Incorrect Authorization

Authz present but logic-wrong (role check uses stale claim, etc.). The role-discriminator twin check in Pass 1 catches the common branch-asymmetry shape.

---

## Pass 2/3 — Concurrency / state

### CWE-362 TOCTOU race

Check-then-act separated by an event boundary; unique-constraint races that decouple checked payload from stored payload. **Severity escalation:** races over auth, single-use tokens, billing, or any duplicable-state surface are Fix-class. See Pass 2.5 "Shared-state race severity escalation."

### CWE-400 Uncontrolled Resource Consumption

Work-per-request proportional to user input without bound.

### CWE-770 Allocation Without Limits

Unbounded array, memory, connection, file descriptor, or DB pool growth.

---

## Pass 3 — Error handling / info exposure

### CWE-209 Error message contains sensitive info

Unredacted response bodies, stack traces, secrets in error strings. Pair with Pass 4.3 Redaction completeness.

### CWE-532 Log exposes sensitive info

Tokens, PII, passwords, session IDs in Logger calls. Pair with Pass 3.2a/3.2b Logging discipline.

### CWE-497 Exposure of System Data

Internal hostnames, pod IDs, DB errors returned to untrusted callers.

### CWE-754 Improper Check for Unusual Conditions

Dead guards, always-truthy checks, distinguishable error classes collapsed into one fallback. Pattern-matches the template-literal-masks-nil shape (Pass 4.4).

---

## Pass 4 — Data correctness

### CWE-190 Integer Overflow / Wraparound

Arithmetic on untrusted bounds, 32-bit counters.

### CWE-193 Off-by-one

Slice sizes, loop bounds, buffer lengths.

### CWE-697 Incorrect Comparison

Type coercion (`==` vs `===`), loose equality, template-literal truthiness over `undefined`. Cross-references Pass 4.4 (template-literal masks nil) and Pass 2.9 (identifier parse/comparison asymmetry).

### CWE-707 Improper Neutralization

Missing input validation at the system boundary.

### CWE-20 Improper Input Validation

Trusting shape/type/range of an input without a check.
