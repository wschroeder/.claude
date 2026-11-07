# Auth-surface RFC compliance

1. Treat the diff as auth surface when it touches a module or file whose path contains `oauth`, `auth`, `token`, `session`, `saml`, `oidc`, `lti`, `ws_auth`, `signin`, or `signout`, or adds routes under `/oauth`, `/auth`, `/sso`, `/lti`, `/saml`, or `/.well-known/`.
2. On auth surface, read the governing specs before you walk the categories:

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

3. List in the scope line the RFC sections that govern each touched endpoint.

---

## RFC 6749 §5.2 status-code vocabulary

1. Require **401** with `WWW-Authenticate` for `invalid_client` only when the client authenticated through the `Authorization` header (Basic or Bearer).
2. Require **400** for `invalid_client` when body credentials (client_id/client_secret in form params) failed.
3. Require **400** for every other token-endpoint error: `invalid_request`, `invalid_grant`, `invalid_scope`, `unsupported_grant_type`, and `unauthorized_client`.
4. Flag a mismatch as Fix-class spec compliance, not style.

---

## RFC parameter completeness (per endpoint)

1. For each RFC-bound endpoint, list every spec-defined parameter and check that each is honored or explicitly rejected; flag a parameter silently ignored.

### Token endpoint, refresh grant (RFC 6749 §6)

- **Required:** `grant_type`, `refresh_token`
- **OPTIONAL:** `scope` — must be a subset of the original. The server MAY narrow but never widen.

### Revocation endpoint (RFC 7009 §2.1)

- **Required:** `token`
- **OPTIONAL:** `token_type_hint` (`access_token` | `refresh_token`). When omitted, the server MUST search across all supported token types.

### Token endpoint, authorization_code grant (RFC 6749 §4.1.3)

- **Required:** `grant_type`, `code`, `redirect_uri` (when sent in the auth request), `client_id` (for public clients).

### Authorization endpoint (RFC 6749 §4.1.1, §4.2.1)

- **Required:** `response_type`, `client_id`
- **OPTIONAL:** `redirect_uri`, `scope`, `state`

For every endpoint above:

1. List the RFC parameters in a comment in the controller action.
2. Grep the handler body to confirm it reads each listed parameter.
3. For each parameter it never reads, require honoring it (parse, validate, and route it through the chain) or rejecting it (`invalid_request` or `invalid_scope` with a description), and record the choice.

---

## Spec-permitted value wrongly rejected

1. For each RFC-defined parameter, write the values the spec must or may accept and the values it requires rejecting, then walk the validators against both sets.
2. Flag a deviation in either direction as Fix-class spec compliance, not style.
3. Never exempt a deviation because a comment names it, such as "supported posture", "deliberate narrower contract", or "library default"; the comment is the reason to check it.

### RFC 6749 §6 refresh scope (worked example)

1. Require a refresh to accept a requested scope that is a proper subset of the original, reject only widening with `invalid_scope`, and treat an omitted scope as the original.
2. Check that the rotation path passes the narrowed scope into the mint call, not the original.

### RFC 6749 §3.3 scope syntax

1. Require scopes to be compared as space-delimited sets, never as ordered strings.

### RFC 7636 PKCE `code_challenge_method`

1. Require the server to accept `S256`; accepting or rejecting `plain` are both compliant.

### RFC 7009 §2.1 token_type_hint

1. Require the server to search every supported token type when `token_type_hint` is omitted, never to reject the request.

### RFC 6749 §4.1.3 redirect_uri exact-match

1. Require an exact comparison, including trailing slash, case, and a registered query, and flag any normalization of the path or query.

### OIDC scope `openid`

1. Require an `id_token` in the response when an OAuth2-with-OIDC flow requests `openid`.

---

## CORS preflight for browser-callable auth endpoints

1. Check CORS support on token endpoints that SPA clients call with authorization code and PKCE, per RFC 9700, against the three patterns in `quick-review` 5.10.

---

## Bearer-token consumer correctness (RFC 6750)

1. **Token presentation** — if the diff accepts a token anywhere but `Authorization: Bearer <token>`, such as `?access_token=...` or a form body, require a deliberate use case to gate it.
2. **Audience** — require the consumer to verify that the token's audience matches its own resource server identifier.
3. **Scope** — require the consumer to enforce the token's scope, not only a user attribute such as an admin flag.

---

## JWT (RFC 7515-7519)

1. If the diff mints or consumes JWTs, check each of these:

- **Algorithm** — `alg` is constrained, and `alg: none` is refused.
- **Key rotation** — if `kid` is present, the verifier uses the kid-indexed key, not a hard-coded one.
- **Expiry** — the `exp` claim is checked, and the clock skew tolerance is documented.
- **Audience** — the same check as Bearer token audience above.
