# Worked examples for the security categories

The shapes behind the bullets under "Security categories to examine". Read the section for each bullet that is live in the diff before you mark it `clear`.

Reference taxonomies: CWE Top 25 (https://cwe.mitre.org/top25/), OWASP Top 10 (web), OWASP API Security Top 10, SANS Top 25.

Contents:

- Injection, SSRF, and protocol
- Authentication and authorization
- Data exposure
- Arithmetic and neutralization at the boundary

## Injection, SSRF, and protocol

### CWE-89 SQL Injection

Raw SQL, string interpolation into queries, `Repo.query` with user input. In Elixir, `Ecto.Query.fragment("...#{user_input}...")` is the canonical leak shape; in TS/JS, raw `pool.query("... " + x)` or template-string concatenation into `SELECT`.

### CWE-79 XSS

Unescaped user input into HTML/JSX, `dangerouslySetInnerHTML`, `innerHTML`, `v-html`. React escapes by default for JSX text but NOT for `dangerouslySetInnerHTML={{ __html: x }}`.

### CWE-94 Code Injection

`eval`, `Function()`, dynamic `require`, `Code.eval_string`.

### CWE-918 SSRF

HTTP client with user-controlled URL; allowlist applied after parse. Check the order: parse first, then allowlist — never the reverse, or a URL like `http://allowed.com@evil.com/` passes a string-prefix allowlist but resolves to `evil.com`.

### CWE-601 Open Redirect

Response `Location` from user input without allowlist. Compare the parsed origin, never a string prefix.

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

## Authentication and authorization

### CWE-284 / CWE-285 Improper Authorization

Missing or wrong permission check before action.

### CWE-287 Improper Authentication

Weak authn, bypassable session check.

### CWE-306 Missing Authentication

Endpoint with no authn at all.

### CWE-639 Authorization Bypass via User-Controlled Key (IDOR)

`GET /orders/:id` where `:id` is not scoped to the caller. Sibling to the lookup-then-filter leak below.

### CWE-862 Missing Authorization

Authn present, authz absent.

### CWE-863 Incorrect Authorization

Authz present but logic-wrong (role check uses stale claim, etc.).

### Pre-auth information oracles

For any endpoint that performs both a resource lookup (by caller-supplied identifier) AND authentication, check the ORDER of those operations. If the resource lookup runs first and its failure modes produce distinguishable error messages or status codes ("already used" vs "expired" vs "not found" vs "invalid signature"), an unauthenticated caller who can enumerate or guess identifiers gets an oracle into internal state — token/code lifecycle, user existence, session status.

Fix is either to authenticate before any resource-state disclosure, or to collapse all pre-auth failure modes into a single opaque error. Applies to OAuth token endpoints, password-reset flows, session-validation endpoints, and any lookup-then-auth pattern.

### Lookup-then-filter cardinality leak

When a function performs a wide lookup (e.g., `Repo.get_by(Token, value: x)`, `Repo.one(from t in Token, where: t.value == ^x)`, `find_by_email/1` searching the entire users table) and THEN filters the result by an authorization predicate (`client_id`, `tenant_id`, `owner_id`, `org_id`, ABAC subject scope), the response distinguishes "doesn't exist anywhere" from "exists but you can't see it". That distinction is information disclosure — an authenticated caller learns about records belonging to OTHER tenants/clients/owners just by getting a different error code or status.

**Concrete shape:** `lookup_revocation_target/1` searches the entire `oauth_user_access_tokens` table → `check_revocation_ownership/2` returns `invalid_client` when `app_id` doesn't match → any client can probe whether a token belongs to a different client.

Fix is to scope the lookup query by the authorization predicate at the DATABASE level, not after the fetch — `get_by_token_for(token, application_id)` uses `WHERE value = ? AND application_id = ?`, so cross-tenant hits return `nil` and look identical to "doesn't exist". RFC 7009 §2.2 specifically requires this collapse for token revocation.

Once folded, the post-fetch authorization check often becomes dead code — remove it.

## Data exposure

### CWE-209 Error message contains sensitive info

Unredacted response bodies, stack traces, secrets in error strings. Per the redaction completeness rule: when a variable is redacted before one sink, EVERY sink must use the redacted form. One unredacted sink defeats the redaction.

### CWE-532 Log exposes sensitive info

Tokens, PII, passwords, session IDs in Logger calls. Check every sink the value reaches, as `quick-review` 4.3 does for redaction.

### CWE-497 Exposure of System Data

Internal hostnames, pod IDs, DB errors returned to untrusted callers. The `error: err.message` pattern is the canonical leak — error messages often contain stack frames, file paths, library version strings, or DB query text that aid an attacker's recon.

## Arithmetic and neutralization at the boundary

### CWE-190 Integer Overflow / Wraparound

Arithmetic on untrusted bounds, 32-bit counters.

### CWE-707 Improper Neutralization

Input that reaches an interpreter, a file path, or markup without being neutralized at the system boundary where it entered.
