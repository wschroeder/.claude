# Pass 5 — Conventions

Module patterns, naming, def/defp visibility, sibling function symmetry. ARIA contracts in `details/accessibility-aria.md`. RFC compliance in `details/rfc-oauth.md`.

## 5.1 Sibling-endpoint consistency

When the diff adds a new public action (controller action, route, GraphQL resolver, RPC handler) to a module that ALREADY has sibling actions of the same shape (e.g. `/oauth/refresh` and `/oauth/revoke` joining `/oauth/token`), enumerate the conventions the existing siblings establish before the new one is reviewed:

- **Parameter source** — body params vs query params vs header params; multipart vs JSON; `conn.body_params` vs `conn.query_params` vs `get_req_header/2`. New siblings must consume params the same way unless an explicit reason exists.
- **Auth scheme** — Basic vs Bearer vs HMAC vs no-auth; which plug pipeline is mounted; which fields the auth helper extracts. A new endpoint mounted on a different pipeline than its siblings is a maintainability and DX bug — clients reusing their auth pattern from one endpoint break on the other. Auth scheme also covers in-action behavior, not just pipeline mounting: if a sibling action calls a helper to merge Basic-header credentials into params (`merge_basic_auth_credentials`, `extract_bearer`, `parse_jwt_header`), the new action MUST call the same helper. Mounting the same pipeline does NOT propagate the helper call — it must be invoked explicitly inside each action body.
- **Response shape** — top-level keys (`{access_token, refresh_token, expires_in}`), success status codes (200 vs 201 vs 204), encoding (JSON vs form-encoded), header conventions (`Cache-Control`, `Pragma`).
- **Error vocabulary** — RFC 6749 error codes (`invalid_grant`, `invalid_client`), HTTP status mapping, error body shape (`{error, error_description}` vs `{errors: [...]}` vs `{message}`). Sibling endpoints that emit different error shapes for the same failure class force every client to branch.
- **Helper functions called** — same `validate_*`, `authorize_*`, `audit_*` helpers as siblings; not a parallel reimplementation.

List the siblings' conventions explicitly before classifying findings; an unjustified deviation is a Fix-class maintainability finding (per the "yes to any" gate).

## 5.2 RFC parameter completeness

Status-code vocabulary (5.4) is one slice of RFC compliance; PARAMETER vocabulary is the other. When implementing an RFC-defined endpoint, enumerate every spec-defined parameter for that endpoint from the RFC and verify each one is either honored or explicitly rejected. **Silent ignore is a spec violation, not a defensive default.**

Method: list the RFC parameters in a comment in the controller action, then grep the body to confirm each is read. A parameter that the body never references is silently dropped — pick honor (parse, validate, route through the chain) or reject (`invalid_request`/`invalid_scope` with a description). Document the choice.

The same discipline applies to SCIM filter/sort params, OneRoster filter/sort params, JSON:API query params, OData $filter/$select. Surveying the spec is one-time work; missing a parameter creates a long-tail compatibility bug for one specific integrator who reads the RFC carefully.

See `details/rfc-oauth.md` for worked examples on OAuth2 endpoints specifically.

## 5.3 Spec-permitted value wrongly rejected

RFC parameter completeness (5.2) catches SILENT IGNORE (the body never reads `params["scope"]`). The companion failure mode is WRONG REJECTION — the body reads the parameter, runs validation, and rejects values the spec explicitly permits, usually with a deliberate comment justifying the choice.

Enumerate each RFC-defined parameter's ACCEPT-SET (values the spec MUST or MAY allow) AND REJECT-SET (values the spec REQUIRES rejection of) before classifying the implementation as compliant. A deviation in EITHER direction is Fix-class spec compliance, not style.

Author comments justifying the deviation ("supported posture", "deliberate narrower contract", "library default") are NOT exemptions — the "Author-acknowledged deviation is not exempt" rule in Classify applies.

See `details/rfc-oauth.md` for the OAuth-specific accept-set / reject-set enumerations.

## 5.4 RFC 6749 §5.2 status-code vocabulary

For OAuth2 endpoints specifically, verify status codes match the RFC's narrow rules. `invalid_client` returns **401** ONLY when the client attempted authentication via the `Authorization` header (Basic or Bearer) — the 401 is paired with `WWW-Authenticate`. `invalid_client` from BODY-credential failure (client_id/client_secret in form params) returns **400**. All other token-endpoint errors (`invalid_request`, `invalid_grant`, `invalid_scope`, `unsupported_grant_type`, `unauthorized_client`) return **400** unconditionally.

A handler that emits 401 for `invalid_client` on body-credential failure is over-eager and trips client retry/refresh stacks expecting `WWW-Authenticate`. Flag mismatches as Fix-class spec compliance, not style.

## 5.5 Private-helper duplication

Sibling-endpoint consistency (5.1) focuses on PUBLIC actions; the same scrutiny applies to PRIVATE helpers within the same module (or its imports). Look for `defp` functions with substantially-identical bodies — same `case`/`cond` structure, same response shape, same control flow, same conditional branching on the same predicate (`basic_auth_attempted?/1`, `authenticated_via_header?/1`, etc.).

Differences in name (`send_token_error/3` vs `send_refresh_revoke_error/3`), in which siblings call them, or in their place in the file do NOT justify duplication. Two helpers that diverge only in name are one helper waiting to be collapsed.

**Deletion test:** line up the two bodies; if every line of one matches the corresponding line of the other (modulo cosmetic ordering), collapse to a single shared helper. The exception — and it must be argued explicitly — is when the helpers diverge MEANINGFULLY today (different realm strings, different default error codes, different tracing/telemetry tags). Speculation about future divergence ("we might want different behavior later") does not justify keeping duplicates; the future change can introduce the split.

## 5.6 Helper functions called

Same `validate_*`, `authorize_*`, `audit_*` helpers as siblings; not a parallel reimplementation. Grep for the helper name in the touched controller; if any sibling action calls it and the new one doesn't, that's the finding.

## 5.7 Same-module sibling consistency (static)

Grep sibling functions with similar signatures in the same file. If `find/3` has an `when is_binary(x)` guard and a fallback clause but `find_and_do/4` doesn't, the inconsistency is a latent bug even if nobody triggers it today. Don't wait for an upstream change to justify the finding — static inconsistency between siblings is itself the finding. Flag any same-module pair with asymmetric guards, asymmetric error shapes, or asymmetric fallback clauses.

## 5.8 Within-function return-shape consistency

For each function in the diff, statically enumerate its return paths across every branch (every `case`/`cond`/`if`/early-return/`with`-else). Verify all branches produce the same shape — either all `:ok` or all `{:ok, value}`, either all `{:error, reason}` or all `:error`, never a mix. Asymmetric branches force callers to handle multiple shapes; silent callers that pattern-match on only one shape crash with `MatchError` on the other.

Docstrings that paper over the mismatch ("safe to call if no row exists") do not fix the contract — they document the bug. This is the branch-level analogue of sibling consistency: the function is consistent with ITSELF across its own return paths.

## 5.9 Behaviour declaration consistency

For modules implementing `init/1` and `call/2` (or other named behaviour callbacks), check whether sibling modules in the same package declare `@behaviour <Name>` and `@impl <Name>`. Asymmetric behaviour declarations (one plug declares, the next doesn't) prevent the compiler from catching callback drift on a future refactor — Fix-class maintainability, not Note-class.

## 5.10 CORS preflight for browser-callable endpoints

For any new POST/PUT/DELETE endpoint added to a scope that may be called from a browser (auth flows, public APIs, OAuth endpoints), enumerate how OPTIONS preflight is handled. Three valid patterns:

1. Endpoint-level CORS plug that intercepts OPTIONS before routing (e.g., `LolWeb.Plug.OAuthCORS` mounted in `endpoint.ex`)
2. Explicit `options "/path", CorsController, :noop` route in a cors-only scope
3. Corsica plug with `allow_methods: :all` mounted in the scope's pipeline

Verify ONE of these covers the new endpoint; do NOT assume the parent scope's `:cors` pipeline auto-handles OPTIONS. RFC 9700 (OAuth 2.0 for Browser-Based Apps) recommends CORS support on token endpoints for SPA clients using authorization-code + PKCE.

## 5.11 Pipeline shared-assign precedence

For any change to a Plug pipeline, enumerate every plug in the pipeline that writes a particular `conn.assigns[:key]` (commonly `:current_user`, `:current_account`, `:current_actor`, `:current_session`, `:tenant`, `:claims`). With N writers and no explicit precedence rules, the LAST plug that runs and matches its conditions wins.

A request carrying multiple credentials (Bearer header + cookie session + Tailscale identity + PlayerToken + LTI claims) executes all matching plugs in order — silent precedence inversion if a downstream plug overwrites an earlier valid identity. Concrete shape: `:graphql2` pipeline with order `Tailscale → PlayerToken → OAuth2BearerAdapter → TokenAuth` lets `TokenAuth` overwrite a Bearer-derived `:current_user` if the request also carries a cookie session — the bearer caller silently impersonates the cookie session, or vice versa.

For each plug that writes the shared assign, classify its behavior on dual-presence:
- **Overwrite** — replaces whatever was there. Last-writer-wins. Must be intentional.
- **No-op when already set** — checks `conn.assigns[:key]` and skips. Safe under multi-credential.
- **Fail-closed on dual presence** — halts with 400 if the assign is already set AND a fresh credential is presented. Most defensible.

Multiple "overwrite" writers without explicit precedence is a precedence-inversion risk — Fix-class. Document the intended winner inline (a comment naming the resolution rule), and add a fail-closed check or `no-op when set` guard at every writer not designated as the winner.

## 5.12 Config-block consistency

When the diff introduces a NEW `config :app, Module, ...` (or any keyword-list config block) ADJACENT to an existing block of the same shape (same module key, sibling app keys, same role), diff the key sets:

- For every key present in the sibling but absent in the new block, decide per-key: (a) flag for addition, OR (b) require an inline `# omitted because ...` comment explaining the omission.
- For every key present in the new block but absent in the sibling, ask whether the sibling needs the same key (parallel evolution) — symmetric to 5.1 same-module sibling logic.
- Pay attention to library-defined defaults: a missing key may not be inert. `ExOauth2Provider`, Guardian, Oban, Phoenix endpoint configs all have keys that change behavior silently when omitted (token TTLs, scopes, salts, secret material, default revocation policy). The sibling block is the ground truth for what the library expects in this codebase.

The diff between sibling config blocks IS the finding — surface it explicitly.

## 5.13 ARIA role/contract correctness

ARIA roles are contracts the component must deliver on. See `details/accessibility-aria.md` for the full Direction A (declared role without keyboard/focus contract) and Direction B (component IS a role but does not declare it) worked examples, plus the path-(a)/(b)/(c) decision tree.

## 5.14 Button hygiene (`type` attribute + icon-only accessible name)

Two cheap regressions that ARIA reviews tend to skip:

- **`<button>` without explicit `type="button"`.** The HTML default `type` for `<button>` inside a `<form>` is `submit`. A toolbar button or icon button rendered inside a parent form (even an ancestor several levels up — most React components don't know whether their consumer renders a form) silently submits the form on click. The fix is mechanical: every `<button>` in the diff that is NOT explicitly a submit button gets `type="button"`. Flag the omission per-occurrence, not "fix one and assume the rest." Same applies to native button elements inside `react-hook-form`, Remix `<Form>`, server-action forms, and any framework that intercepts the default submit.
- **Icon-only buttons without an accessible name.** A button whose visible content is an SVG icon (lucide-react, heroicons, custom inline SVG, font-awesome) has no accessible name — screen readers announce "button" with no further context. Required mitigations, any one of: `aria-label="Push token"`, `aria-labelledby={titleId}`, `<span className="sr-only">Push token</span>` inside the button, or a `<title>` element inside the SVG. The visible `title` HTML attribute is a TOOLTIP not an accessible name — most screen readers ignore it as the accessible name source.

**Discovery method:** grep `<button` in the diff. For each occurrence, check (a) `type=` attribute presence, (b) child content — is the only child an SVG/icon? — and (c) accessibility props. Fix-class per the "yes to any" gate.
