# Worked examples for the security categories

1. Read the section for each bullet under "Security categories to examine" that is live in the diff before you mark it `clear`.

Reference taxonomies: CWE Top 25 (https://cwe.mitre.org/top25/), OWASP Top 10 (web), OWASP API Security Top 10, SANS Top 25.

Contents:

- Injection, SSRF, and protocol
- Authentication and authorization
- Data exposure
- Arithmetic and neutralization at the boundary

## Injection, SSRF, and protocol

### CWE-89 SQL Injection

1. Flag user input interpolated into raw SQL, such as `Ecto.Query.fragment("...#{user_input}...")`, `Repo.query` with user input, or `pool.query("... " + x)` and template strings built into a `SELECT`.

### CWE-79 XSS

1. Flag user input reaching HTML unescaped, such as through `dangerouslySetInnerHTML={{ __html: x }}`, `innerHTML`, or `v-html`; JSX text is escaped by default.

### CWE-94 Code Injection

1. Flag `eval`, `Function()`, dynamic `require`, and `Code.eval_string` on input.

### CWE-918 SSRF

1. Flag an HTTP client whose URL the user controls unless it parses the URL first and then applies an allowlist to the parsed host, never a string-prefix check.

### CWE-601 Open Redirect

1. Flag a response `Location` built from user input unless it compares the parsed origin against an allowlist, never a string prefix.

### CWE-300 / CWE-319 MITM / Cleartext Transmission

1. Flag a scheme downgrade, `http://` accepted where `https://` is expected, and mixed schemes in trusted-host comparisons.

### CWE-295 Improper Certificate Validation

1. Flag disabled TLS verification, such as `rejectUnauthorized: false`, and custom certificate handling.

### CWE-352 CSRF

1. Flag a state-changing request with neither a token nor a SameSite cookie.

### CWE-22 Path Traversal

1. Flag user input reaching a filesystem path unless `path.resolve(base, user_input)` is followed by a check that the result still starts with `base`.

### CWE-502 Insecure Deserialization

1. Flag `JSON.parse`, `yaml.load`, and `:erlang.binary_to_term` on user data, treating `binary_to_term` as the most dangerous because its atoms can exhaust the atom table.

### CWE-611 XXE

1. Flag XML parsing with entity resolution enabled.

## Authentication and authorization

### CWE-284 / CWE-285 Improper Authorization

1. Flag a missing or wrong permission check before an action.

### CWE-287 Improper Authentication

1. Flag weak authentication and a session check that can be bypassed.

### CWE-306 Missing Authentication

1. Flag an endpoint with no authentication at all.

### CWE-639 Authorization Bypass via User-Controlled Key (IDOR)

1. Flag a lookup by a caller-supplied key, such as `GET /orders/:id`, that is not scoped to the caller.

### CWE-862 Missing Authorization

1. Flag an endpoint that authenticates and does not authorize.

### CWE-863 Incorrect Authorization

1. Flag an authorization check whose logic is wrong, such as a role check on a stale claim.

### Pre-auth information oracles

1. For any endpoint that both looks up a resource by a caller-supplied identifier and authenticates, check which runs first.
2. If the lookup runs first and its failures give distinct errors or statuses, such as "already used", "expired", "not found", and "invalid signature", flag it.
3. Give the fix as authenticating before any resource state is disclosed, or as one opaque error for every failure before authentication.
4. Apply this to OAuth token endpoints, password-reset flows, session-validation endpoints, and any lookup-then-auth pattern.

### Lookup-then-filter cardinality leak

1. Flag a wide lookup, such as `Repo.get_by(Token, value: x)` or a `find_by_email/1` over the whole table, followed by a filter on an authorization predicate, such as `client_id`, `tenant_id`, `owner_id`, `org_id`, or an ABAC scope, when "does not exist" and "exists but not yours" give different responses.
2. Give the fix as scoping the query by the predicate in the database, such as `WHERE value = ? AND application_id = ?`, so a hit for another tenant returns `nil`; RFC 7009 §2.2 requires this for token revocation.
3. Remove the post-fetch authorization check once it becomes dead code.

## Data exposure

### CWE-209 Error message contains sensitive info

1. Flag unredacted response bodies, stack traces, and secrets in error strings.
2. When a value is redacted before one sink, require every sink to use the redacted form.

### CWE-532 Log exposes sensitive info

1. Flag tokens, PII, passwords, and session ids in Logger calls, checking every sink the value reaches, as `quick-review` 4.3 does for redaction.

### CWE-497 Exposure of System Data

1. Flag internal hostnames, pod ids, and database errors returned to untrusted callers, including `error: err.message`.

## Arithmetic and neutralization at the boundary

### CWE-190 Integer Overflow / Wraparound

1. Flag arithmetic on untrusted bounds and 32-bit counters.

### CWE-707 Improper Neutralization

1. Flag input that reaches an interpreter, a file path, or markup without being neutralized at the boundary where it entered.
