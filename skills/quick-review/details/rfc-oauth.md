# Auth-surface RFC compliance

When the diff touches any module/file whose path contains `oauth`, `auth`, `token`, `session`, `saml`, `oidc`, `lti`, `ws_auth`, `signin`, `signout`, OR introduces routes under `/oauth`, `/auth`, `/sso`, `/lti`, `/saml`, `/.well-known/`, treat the diff as "auth surface" and consult the relevant RFCs by name BEFORE running the other passes:

- **RFC 6749** (OAuth 2.0 core): §5.2 error responses, §6 refresh, §3.3 scope
- **RFC 6750** (Bearer tokens)
- **RFC 7009** (Token Revocation)
- **RFC 7636** (PKCE)
- **RFC 7662** (Token Introspection)
- **RFC 8252** (Native Apps)
- **RFC 9700** (OAuth 2.0 for Browser-Based Apps BCP)
- **RFC 7515-7519** (JWT family)
- **RFC 8628** (Device Code)
- **SAML 2.0** (OASIS)
- **LTI 1.3**
- **OpenID Connect Core**

List the specific RFC sections that govern each touched endpoint as a comment in the review's mission line. Skipping this trigger means RFC compliance gets caught only when a reviewer happens to read the relevant spec. **Brush up on the spec first, THEN review** — review without spec context is creativity, review with spec context is verification.

---

## RFC 6749 §5.2 status-code vocabulary

`invalid_client` returns **401** ONLY when the client attempted authentication via the `Authorization` header (Basic or Bearer) — the 401 is paired with `WWW-Authenticate`.

`invalid_client` from BODY-credential failure (client_id/client_secret in form params) returns **400**.

All other token-endpoint errors (`invalid_request`, `invalid_grant`, `invalid_scope`, `unsupported_grant_type`, `unauthorized_client`) return **400** unconditionally.

A handler that emits 401 for `invalid_client` on body-credential failure is over-eager and trips client retry/refresh stacks expecting `WWW-Authenticate`. Flag mismatches as Fix-class spec compliance, not style.

---

## RFC parameter completeness (per endpoint)

For each RFC-bound endpoint, enumerate every spec-defined parameter and verify each is either honored or explicitly rejected. **Silent ignore is a spec violation, not a defensive default.**

### Token endpoint, refresh grant (RFC 6749 §6)

- **Required:** `grant_type`, `refresh_token`
- **OPTIONAL:** `scope` — must be subset of original. Server MAY narrow but never widen. Silently ignoring `params["scope"]` means a client requesting narrower scope gets the broader original scope back — the client thinks it scoped down, but didn't.

### Revocation endpoint (RFC 7009 §2.1)

- **Required:** `token`
- **OPTIONAL:** `token_type_hint` (`access_token` | `refresh_token`). When omitted, server MUST search across all supported token types. Rejecting a request without `token_type_hint` is a spec violation.

### Token endpoint, authorization_code grant (RFC 6749 §4.1.3)

- **Required:** `grant_type`, `code`, `redirect_uri` (when sent in the auth request), `client_id` (for public clients).

### Authorization endpoint (RFC 6749 §4.1.1, §4.2.1)

- **Required:** `response_type`, `client_id`
- **OPTIONAL:** `redirect_uri`, `scope`, `state`

**Method:** list the RFC parameters in a comment in the controller action, then grep the body to confirm each is read. A parameter that the body never references is silently dropped — pick honor (parse, validate, route through the chain) or reject (`invalid_request`/`invalid_scope` with a description). Document the choice.

---

## Spec-permitted value wrongly rejected

Enumerate each RFC-defined parameter's ACCEPT-SET (values the spec MUST or MAY allow) AND REJECT-SET (values the spec REQUIRES rejection of) before classifying the implementation as compliant. A deviation in EITHER direction is Fix-class spec compliance, not style.

### RFC 6749 §6 refresh scope (worked example)

"The requested scope MUST NOT include any scope not originally granted... if omitted is treated as equal to the scope originally granted." Subset (narrowing) MUST be accepted — only widening is `invalid_scope`. A `validate_refresh_scope/2` that rejects any non-set-equal scope (including a proper subset) violates the spec.

A moduledoc or inline comment saying "scope-down on refresh is not supported" is a documented deviation, not a license to deviate. The narrowed scope must persist on the new token, not the original — verify the rotation path threads the requested (narrowed) scope into the mint call, not the carry-forward original.

### RFC 6749 §3.3 scope syntax

`scope` is a space-delimited set; order is not significant. Comparing as sorted sets, not ordered strings, is mandatory.

### RFC 7636 PKCE `code_challenge_method`

Servers MUST accept `S256`; MAY accept `plain`. A server that accepts ONLY `S256` and rejects `plain` is fine; a server that rejects `S256` is a spec violation.

### RFC 7009 §2.1 token_type_hint

When omitted, server MUST search across all supported token types. Rejecting a request without `token_type_hint` is a spec violation.

### RFC 6749 §4.1.3 redirect_uri exact-match

Path comparison MUST be exact (including trailing slash, case, and query if registered). A normalization that lowercases the path, strips trailing slashes, or ignores query is a spec deviation in BOTH directions — it accepts URIs the RFC forbids AND rejects URIs the RFC requires.

### OIDC scope `openid`

When present in an OAuth2-with-OIDC flow, the response MUST include `id_token`. Treating `openid` as opaque scope without ID-token issuance is non-conformant.

**Method:** for every RFC-bound endpoint touched by the diff, write the spec's accept-set and reject-set as a comment AT REVIEW TIME (in your reasoning, not necessarily in the code), then walk the implementation's validators against both sets. Author comments justifying the deviation ("supported posture", "deliberate narrower contract", "library default") are NOT exemptions — see the "Author-acknowledged deviation is not exempt" rule under Classify.

---

## CORS preflight for browser-callable auth endpoints

RFC 9700 (OAuth 2.0 for Browser-Based Apps) recommends CORS support on token endpoints for SPA clients using authorization-code + PKCE. See Pass 5.10 for the three valid CORS-handling patterns.

---

## Bearer-token consumer correctness (RFC 6750)

Three places to check:

1. **Token presentation** — `Authorization: Bearer <token>` is the canonical form. Query parameter (`?access_token=...`) and form body (`access_token=...`) are also defined but discouraged. If the diff adds a non-header consumption path, ensure it's gated behind a deliberate use-case.
2. **Audience** — the consumer must verify the token's audience matches its own resource server identifier. A token minted for resource server A accepted by resource server B is a confused-deputy hazard.
3. **Scope** — verify the consumer enforces the scope. Per Pass 1.15b Scope asymmetry: token has `scope:admin` but resolver only checks `current_user.is_admin` — scope is decorative, not load-bearing.

---

## JWT (RFC 7515-7519)

If the diff mints or consumes JWTs:

- **Algorithm** — verify `alg` is constrained. The `alg: none` attack is the canonical break.
- **Key rotation** — if `kid` is present, the verifier must use the kid-indexed key, not a hard-coded one.
- **Expiry** — `exp` claim must be checked and the clock skew tolerance documented.
- **Audience** — same as Bearer token audience above.
