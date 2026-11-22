# Codebase Audit — Curriculum Curator

**Date:** 2026-11-22
**Scope:** Whole codebase — backend (FastAPI/SQLAlchemy), frontend (React/TypeScript),
desktop (Electron), deployment (Docker/GitHub Actions), and privacy/data flows.
Audited the current working tree, including uncommitted privacy-copy changes.
**Method:** Six parallel read-only audit agents inspected implementation and test
bodies by area. A skeptic agent then tried to falsify every CRITICAL/HIGH
finding. Severities below are the post-critic severities. No finding was fully
refuted. One sub-claim (unbounded plugin content) was refuted by the global
10 MB request cap. No live exploitation was performed; all verdicts are from
code inspection.

## Verification actually run (parent, this session)

| Gate | Result |
|---|---|
| Backend `ruff check .` | Pass, 0 errors |
| Backend `basedpyright` | Pass, 0 errors / 0 warnings |
| Backend `pytest -q` | **1180 passed, 2 failed, 24 skipped** (60s) |
| Frontend `npm run lint` | Pass, 0 errors |
| Frontend `npm run type-check` | Pass, 0 errors |
| Frontend `npm run format:check` | Pass |
| Frontend `npm test -- --run` | 76 passed (13 files) |

The 2 backend failures are pre-existing (no backend code was changed this
session) and are themselves an audit-relevant symptom; see
*LLM configuration split-brain* below:

- `tests/test_llm_service.py::TestLLMService::test_check_providers_with_openai_key`
- `tests/test_llm_service.py::TestLLMService::test_check_providers_with_anthropic_key`

Both patch environment API keys and expect `service.providers` to populate;
the service no longer resolves providers that way.

## Remediation status (2026-11-22)

Fixes applied in the working tree, in the suggested order. All listed gates
were re-run after the changes: backend `ruff`, `basedpyright`, `pytest`
(**1231 passed, 24 skipped**); frontend `lint`, `type-check`,
`format:check`, `vitest`.

**Done**

1. **AuthZ** — plugin list/config/validate/remediate now require auth (config
   is admin-only) with rate limits; CrossRef lookup requires auth, validates
   and quotes the DOI, and is rate-limited; batch status uses `get_owned_task`.
   Regression tests: `tests/test_audit_step1_authz.py`.
2. **Secrets** — `SECRET_KEY` is required at runtime (all known placeholders,
   `docker-dev-secret-key-*` and <32 chars rejected; `TESTING` exempt);
   startup fails with `LOCAL_MODE` + `PUBLIC_DOMAIN`; Docker no longer bakes a
   key; compose requires one; `.env.example` ships empty. Seeded local user gets
   a random unusable password and is disabled when `LOCAL_MODE` is off. LLM API
   keys and bearer tokens are Fernet-encrypted at rest (`secret_crypto.py`) and
   decrypted at use. `init_db.py` generates one-time passwords and
   `test_integration.py` no longer contains personal/fixed credentials.
   Tests: `tests/test_audit_step2_secrets.py`.
3. **Registration** — whitelist fails closed when enabled-but-empty; the first
   account needs a one-time setup token (`SETUP_TOKEN` or the `setup_token`
   file beside the DB) and creation is serialised by a lock; the registration
   modal asks for it. Tests: `tests/test_audit_step3_registration.py`.
4. **Input safety** — package import enforces entry-count, per-entry,
   total-uncompressed and compression-ratio caps before reading; URL
   verification validates the URL and every redirect hop through
   `assert_public_url` and no longer disables TLS verification; material
   uploads are read in bounded chunks (50 MiB); imported assessment HTML is
   bleached with the same allowlist as material HTML.
5. **Ownership** — every AI-context entry point validates body-supplied
   `unitId`, `designId` and `sourceMaterialIds`; research sources require unit
   ownership; batch task status is owner-scoped.
6. **Session** — web logins now set an httpOnly `cc_session` cookie plus a
   readable `cc_csrf` double-submit token; cookie-authenticated state changes
   require `X-CSRF-Token`; desktop keeps the Bearer token. Access tokens reject
   `type=refresh`; tokens carry a `tv` claim checked against
   `User.token_version`, which is bumped on password change/reset;
   `/auth/logout` revokes the JTI and clears cookies; the 401 interceptor resets
   the auth store; verify-email tokens are now IP-bound.
7. **Desktop** — a per-install `SECRET_KEY` is generated into `userData`
   (0600) and `DEBUG=false`; production uses a fresh free loopback port and a
   per-launch `X-Desktop-Token` required by `LOCAL_MODE`; single-instance lock;
   sandbox and context isolation on, node integration off; `openExternal` and
   `will-navigate` allowlist http/https/mailto; IPC handlers check the sender;
   startup fails visibly instead of showing a dead window.
8. **Deploy/CI** — both compose files bind app and Ollama to 127.0.0.1;
   production compose pins image `0.7.10` and drops the Watchtower auto-update
   label; Dockerfile uses `python:3.13-slim`, `uv sync --frozen --no-dev`,
   `npm ci`, and `.dockerignore` excludes `**/.env`; CI actions are pinned by
   commit SHA, PRs build the Docker image and desktop app, image publishing
   reuses CI as a required job, and pushes carry SBOM/provenance; the reusable
   release workflow is pinned to a commit SHA and passes `GH_OWNER`.
9. **LLM store** — `LLMConfiguration` is authoritative (default-first), with
   legacy `User.llm_config` fallback and the `allow_user_api_keys` kill-switch
   honoured; the two previously failing LLM tests were repaired against the
   real resolution path.
10. **Privacy copy** — README, landing, download, login, about, export and LLM
    settings wording now matches behaviour; operator mailto is only sent when
    `CONTACT_EMAIL` is set explicitly; the Download page discloses its GitHub
    release fetch; quiz, branching, lesson-plan, speaker-notes and AI-assistant
    panels show a point-of-use recipient notice. Academic search now honours a
    per-user provider selection (OpenAlex / Semantic Scholar / CrossRef) saved
    in Research Settings, instead of always querying all three.

**Residual LOW/MEDIUM fixes applied**

- Re-enabled admin rate limits; verification/reset codes are now stored as
  keyed HMAC hashes (never plaintext), still single-use with a per-account
  attempt cap; removed the deterministic "alternative verification" backdoor
  and the admin plaintext-code relay; escaped LIKE wildcards in unit search;
  made unit totals reflect the full result set, not the page.
- Background import and token-usage logging use dedicated sessions; SQLite
  foreign keys are enabled; router import failures now fail startup; the SPA
  file route is path-contained; API docs are disabled outside debug/local/test.
- `CamelModel` rejects unknown fields; Canvas `module_meta.xml` parse failures
  no longer 500 an import; raw parser/LLM exception text is no longer returned.
- Mermaid renders at `securityLevel: strict` and its SVG is DOMPurify-sanitised;
  YouTube/embed links are http(s)/YouTube-embed allowlisted and iframes are
  sandboxed.
- Docker images and both JS dependency trees are digest/lockfile pinned; the
  Dockerfile is multi-stage with a checksum-verified Typst download.
- Desktop release follows the app-hq signing model (pinned shared workflow,
  canonical Apple secrets, `signing-mode: custom`, API-key notarization).
  `notarize.js` now fails CI when credentials are missing and validates the
  staple/signature instead of silently shipping an unnotarized app.
- Password updates reject >72-byte inputs (bcrypt truncation); `update_user`
  uses a field allowlist; whitelist patterns normalise to `@domain` on edit;
  the sidecar script picks the host Mac architecture.

**Still open**

- Transactional git+DB import; dependency CVE scanning beyond Dependabot;
  passkeys/MFA for admin accounts; magic-link (rather than 6-digit) email
  verification as a future UX step.

## Executive verdict

**Not safe to expose publicly as shipped.** Two CRITICAL clusters survive
adversarial review:

1. An unauthenticated endpoint can rewrite global plugin configuration.
2. Deployments can run with a known, image-readable JWT signing key because
   the production validator only rejects one literal placeholder string.

Below that sits a broad HIGH tier: the `LOCAL_MODE` auth bypass (safe only
while loopback-bound and never combined with a public deploy), a persisted
seeded account with a public password, fail-open registration controls,
plaintext LLM API keys at rest, AI-context IDOR, SSRF in URL verification,
a zip-bomb path in package import, JWTs in `localStorage`, and a desktop
sidecar that, by code inspection, fails startup validation on a clean
machine.

The core seams are good. Ownership checks centralised in
`backend/app/api/deps.py` (404-not-403, admin bypass), JWT verification
(pinned HS256, DB re-check of role/active per request), the SSRF-safe page
fetcher in `backend/app/utils/url_safety.py`, defused XML parsing, real-DB
service tests, and the absence of any telemetry SDK are genuine strengths.
The risk concentrates at the edges: a few routes that bypass those seams,
deployment defaults, and claims made in UI copy that the code does not
fully back.

**Fix order matters:** the two CRITICALs plus the registration/secret
cluster should be fixed before any public or institutional deployment.

---

## CRITICAL — fix before any public deployment

### C1. Unauthenticated plugin configuration write

`PATCH /api/plugins/{name}` has **no authentication dependency** and persists
changes to global plugin configuration in the database
([plugins.py](/Volumes/Crucial X9/Projects/curriculum-curator/backend/app/api/routes/plugins.py:72);
router mounted without dependencies in
[main.py](/Volumes/Crucial X9/Projects/curriculum-curator/backend/app/main.py:453)).

Impact: any unauthenticated remote caller can disable or reprioritise the
content quality validators/remediators for **all users**.

Fix: require `Depends(get_current_admin_user)`; add anonymous/non-admin
regression tests. Related: `POST /api/plugins/validate` and `/remediate`
are also unauthenticated (MEDIUM; anonymous CPU, bounded by the 10 MB cap).

### C2. Known / baked `SECRET_KEY` passes the production validator

- The Docker image bakes `SECRET_KEY=docker-dev-secret-key-$(date +%s|sha256sum)`
  and `DEBUG=true` into a layer-readable `/app/backend/.env`
  ([Dockerfile](/Volumes/Crucial X9/Projects/curriculum-curator/Dockerfile:56)).
  Anyone who can pull the GHCR image can read the key.
- The only guard rejects the exact string
  `dev-secret-key-change-in-production` and only when `DEBUG=false`
  ([config.py](/Volumes/Crucial X9/Projects/curriculum-curator/backend/app/core/config.py:145)).
  The shipped placeholders
  `your-secret-key-change-this-in-production`
  ([docker-compose.yml](/Volumes/Crucial X9/Projects/curriculum-curator/docker-compose.yml:25),
  [.env.example](/Volumes/Crucial X9/Projects/curriculum-curator/.env.example:6))
  and the baked Docker key all pass. `DEBUG=true` disables the check entirely.

Impact: JWT forgery for any user, including admins, on any deployment that
did not override the key with a real secret.

Fix: never generate a secret at build time. Require `SECRET_KEY` at runtime,
reject all known placeholders unconditionally outside TESTING, enforce at
least 32 random characters, and fail startup otherwise. Note
[setup.sh](/Volumes/Crucial X9/Projects/curriculum-curator/setup.sh:33)
already does this correctly (`openssl rand -hex 32`, `DEBUG=false`) —
align Docker/compose with it.

---

## HIGH

### H1. `LOCAL_MODE` authentication bypass (misconfiguration-dependent)

`get_current_user` returns the seeded local user with no credential check,
and `HTTPBearer` is optional, whenever `LOCAL_MODE` is set
([deps.py](/Volumes/Crucial X9/Projects/curriculum-curator/backend/app/api/deps.py:36),
[deps.py](/Volumes/Crucial X9/Projects/curriculum-curator/backend/app/api/deps.py:62)).
Nothing refuses `LOCAL_MODE` combined with `PUBLIC_DOMAIN` or a non-loopback
bind; the Docker image binds `0.0.0.0`
([Dockerfile](/Volumes/Crucial X9/Projects/curriculum-curator/Dockerfile:99)).
Defaults are safe (`LOCAL_MODE=false`; desktop binds 127.0.0.1), which is
why the critic reduced this from CRITICAL to HIGH.

Desktop exposure: the sidecar always runs `LOCAL_MODE=true` on fixed port
8000 ([backend.ts](/Volumes/Crucial X9/Projects/curriculum-curator/desktop/src/main/backend.ts:7)),
so any local process or other OS user on a shared machine gets the full API
unauthenticated.

Fix: fail startup when `LOCAL_MODE` is combined with a public/non-loopback
deployment. On desktop use an ephemeral random port plus a per-launch
renderer token (or a Unix socket/named pipe), and take a single-instance lock.

### H2. Seeded local account has a public password and persists

`_seed_local_user` creates `local@curriculum-curator.app` with the hardcoded
password `local-mode-no-password`, verified and active
([main.py](/Volumes/Crucial X9/Projects/curriculum-curator/backend/app/main.py:97)).
The row survives switching `LOCAL_MODE` off, and normal login only checks
`is_active` ([auth.py](/Volumes/Crucial X9/Projects/curriculum-curator/backend/app/api/routes/auth.py:426)).
Anyone who reads the (open) source can log in as that account on a database
that ever ran local mode, inheriting its units.

Fix: seed an unusable random password hash; disable or delete the local user
when `LOCAL_MODE` is off. Also fix the log line claiming the user is
`(admin)` while its role is `lecturer`
([main.py](/Volumes/Crucial X9/Projects/curriculum-curator/backend/app/main.py:99)).

### H3. Registration controls fail open; first-user-admin race

- `is_email_whitelisted` returns `True` when no active patterns exist
  ([user_repo.py](/Volumes/Crucial X9/Projects/curriculum-curator/backend/app/repositories/user_repo.py:304)),
  while `enable_email_whitelist` defaults to `True`
  ([security_settings.py](/Volumes/Crucial X9/Projects/curriculum-curator/backend/app/core/security_settings.py:31)).
  An enabled-but-empty whitelist silently means open registration.
- The first registrant is auto-promoted to admin and auto-verified without
  proving email ownership, via a non-atomic count-then-create
  ([auth.py](/Volumes/Crucial X9/Projects/curriculum-curator/backend/app/api/routes/auth.py:187)).
  Unauthenticated `GET /auth/config` publicly reports `hasUsers`
  ([auth.py](/Volumes/Crucial X9/Projects/curriculum-curator/backend/app/api/routes/auth.py:49)),
  advertising fresh deployments to race.

Fix: fail closed when the whitelist is enabled and empty (or surface
"empty = open" in the admin UI). Gate first-admin creation behind a one-time
setup token or CLI command, and make promotion atomic.

### H4. LLM API keys stored in plaintext despite "(encrypted)" claims

Keys are stored verbatim in three places — `LLMConfiguration.api_key` /
`bearer_token` text columns, `User.llm_config` JSON, and
`SystemSettings.value` — while column descriptions claim "(encrypted)" and
save comments say "Should be encrypted in production"
([llm_config.py](/Volumes/Crucial X9/Projects/curriculum-curator/backend/app/api/routes/llm_config.py:177),
[llm_config model](/Volumes/Crucial X9/Projects/curriculum-curator/backend/app/models/llm_config.py:33)).
No encryption code exists in `backend/app`. Anyone with the SQLite file, a
backup, or SQL read access obtains every user's billable provider keys.
This directly contradicts the BYOK trust story on shared servers.

Fix: encrypt at rest (AEAD/Fernet with a key from env/secret file outside
the DB; OS keychain on desktop), migrate and rotate existing keys, and
remove the false "(encrypted)" wording until done.

### H5. LLM configuration split-brain (also the 2 failing tests)

Generation resolves keys only from `User.llm_config` JSON and
`SystemSettings` ([llm_service.py](/Volumes/Crucial X9/Projects/curriculum-curator/backend/app/services/llm_service.py:129)).
It never queries the `LLMConfiguration` table written by the
`/llm-config/configurations` CRUD API. Keys saved through Settings look
configured but generation falls back to system keys or fails. The related
`allow_user_api_keys` admin kill-switch is loaded but never checked
([llm_service.py](/Volumes/Crucial X9/Projects/curriculum-curator/backend/app/services/llm_service.py:90))
(MEDIUM).

Fix: make one store authoritative for `_get_llm_config` (honouring
`is_default`/`is_active` and the kill-switch), delete or migrate the other,
and repair `tests/test_llm_service.py` to test the real resolution path.

### H6. Zip-bomb / decompression DoS in package import

`PackageImportService._open_zip` checks only `BadZipFile` — no per-entry,
total-uncompressed, entry-count, or compression-ratio caps — then reads
entries whole into memory
([package_import_service.py](/Volumes/Crucial X9/Projects/curriculum-curator/backend/app/services/package_import_service.py:1220)).
The 500 MB route cap is on *compressed* bytes, checked after a full read.
A small crafted `.imscc`/`.zip` can expand to gigabytes in RAM and OOM the
worker. Zip-slip itself is **not** exploitable (nothing extracts to disk;
the one disk helper re-checks containment and caps).

Fix: enforce infolist-based total/count/ratio limits before any `zf.read()`,
reusing the pattern in `file_import_service._safe_extract_all`.
Related MEDIUM: single-file material import reads uploads fully with no
size cap and extension-only validation
([material_import.py](/Volumes/Crucial X9/Projects/curriculum-curator/backend/app/api/routes/material_import.py:164)).

### H7. AI-context IDOR (needs known UUIDs)

`POST /api/ai/generate` passes body-supplied `unit_id`, `design_id`, and
`source_material_ids` straight to context building with no ownership check
([ai.py](/Volumes/Crucial X9/Projects/curriculum-curator/backend/app/api/routes/ai.py:192)).
Materials are fetched by bare ID and inlined into the LLM prompt
([curriculum_context.py](/Volumes/Crucial X9/Projects/curriculum-curator/backend/app/services/curriculum_context.py:84));
designs likewise
([design_context.py](/Volumes/Crucial X9/Projects/curriculum-curator/backend/app/services/design_context.py:37)).
An authenticated user who learns another user's UUIDs can exfiltrate their
material/design content through streamed LLM output. Existence is not
leaked by guessing (UUIDs), which is why this is HIGH, not CRITICAL.

Fix: thread `current_user` through `build_context`/`get_design_context`;
filter via `Unit.owner_id` or `load_owned_or_404`/`require_unit_owner`.
Note `ai.py` lines 320–1384 (other generate/enhance endpoints) were not
fully inspected; other call sites likely share the pattern (one at
`ai.py:251` confirmed by the api agent).

### H8. SSRF in URL verification (driven by an unauthenticated endpoint)

`URLVerifier` fetches every http(s) URL extracted from content server-side
with `follow_redirects=True` and no private-IP/metadata check
([url_verifier.py](/Volumes/Crucial X9/Projects/curriculum-curator/backend/app/plugins/url_verifier.py:201)),
and is reachable via the unauthenticated plugins validate route (C1 area).
A crafted link — or a public URL redirecting internally — makes the server
request `169.254.169.254`, `localhost`, or internal services. Its client
also sets `verify=False` (MEDIUM).

Fix: run the initial URL and every redirect hop through
`app.utils.url_safety.assert_public_url` (the page fetcher already does
this correctly), disable auto-redirects, and drop `verify=False`.
Related MEDIUMs: SSRF via user-supplied custom LLM `api_url`
([llm_service.py](/Volumes/Crucial X9/Projects/curriculum-curator/backend/app/services/llm_service.py:1124))
and via per-user SearXNG URLs on shared servers.

### H9. JWT in `localStorage`; logout does not revoke

The token is persisted in `localStorage` at login and local-session
bootstrap ([authStore.ts](/Volumes/Crucial X9/Projects/curriculum-curator/frontend/src/stores/authStore.ts:51)).
Any XSS in the origin can exfiltrate a Bearer [REDACTED] valid until expiry.
Logout only clears local state
([authStore.ts](/Volumes/Crucial X9/Projects/curriculum-curator/frontend/src/stores/authStore.ts:23));
the backend JTI blacklist exists but `blacklist_token` has **zero
callers** and there is no logout endpoint
([security.py](/Volumes/Crucial X9/Projects/curriculum-curator/backend/app/core/security.py:23)),
so logout, password change, and password reset never revoke outstanding
tokens. Impact is bounded by the 30-minute expiry, hence HIGH for the
cluster (MEDIUM for each arm alone).

Fix: httpOnly + SameSite cookie with CSRF protection (or in-memory token +
rotating refresh cookie); add a logout endpoint; revoke on password
change/reset; persist the blacklist or use a per-user token version.

### H10. Desktop sidecar likely fails startup on a clean machine (inferred)

The desktop env sets no `SECRET_KEY`/`DEBUG`
([backend.ts](/Volumes/Crucial X9/Projects/curriculum-curator/desktop/src/main/backend.ts:17)),
while `Settings` raises when `DEBUG=false` (the default) and `SECRET_KEY`
is the code default
([config.py](/Volumes/Crucial X9/Projects/curriculum-curator/backend/app/core/config.py:147)).
Corroborating evidence: the build script must inject
`SECRET_KEY=ci-test-secret` just to health-check the sidecar
([build-sidecar.sh](/Volumes/Crucial X9/Projects/curriculum-curator/scripts/build-sidecar.sh:55)).
On failure the app merely logs and opens a window against a dead backend
([index.ts](/Volumes/Crucial X9/Projects/curriculum-curator/desktop/src/main/index.ts:59)).
**Not runtime-verified** — an inherited env var or stray `.env` could mask
it — but code strongly implies packaged installs break on clean machines.

Fix: generate and persist a random `SECRET_KEY` in `userData` on first
launch; show a fatal error dialog if the backend never becomes healthy.
Verify by running the packaged sidecar with a scrubbed environment.

### H11. Ollama (and the app) published on all interfaces

Both compose files publish `'11434:11434'` unbound
([docker-compose.yml](/Volumes/Crucial X9/Projects/curriculum-curator/docker-compose.yml:59),
[deploy/docker-compose.yml](/Volumes/Crucial X9/Projects/curriculum-curator/deploy/docker-compose.yml:38)).
Ollama is unauthenticated: anyone who can reach a VPS with
`--profile local-ai` can run/pull models and burn compute. The app's
`'8081:8000'` plain-HTTP mapping can likewise bypass Caddy (MEDIUM).

Fix: `127.0.0.1:11434:11434` or no host port (the app reaches Ollama over
the compose network); `127.0.0.1:8081:8000` for the app.

---

## MEDIUM (grouped)

**Auth & session**
- JWT IP-binding only applies when the token carries an `ip` claim; tokens
  from verify-email and local-session have `ip=None` and work from any IP
  ([security.py](/Volumes/Crucial X9/Projects/curriculum-curator/backend/app/core/security.py:153)). Issue with `client_ip` everywhere; reject missing-ip tokens where binding is expected.
- `decode_access_token` never checks token `type`; 7-day refresh tokens would
  work as access tokens if ever issued (currently no callers)
  ([security.py](/Volumes/Crucial X9/Projects/curriculum-curator/backend/app/core/security.py:142)).
- Verification/reset codes stored in plaintext and readable by admins via
  pending-verifications; 10^6 space with per-IP limits only, no per-account
  attempt cap ([user_repo.py](/Volumes/Crucial X9/Projects/curriculum-curator/backend/app/repositories/user_repo.py:166),
  [admin.py](/Volumes/Crucial X9/Projects/curriculum-curator/backend/app/api/routes/admin.py:281)). Hash codes; cap attempts per user.
- Admin endpoint rate limiters are commented out throughout
  ([admin.py](/Volumes/Crucial X9/Projects/curriculum-curator/backend/app/api/routes/admin.py:43));
  LLM generation has no limiter. Re-enable (monitoring routes show the pattern).
- Unauthenticated CrossRef lookup proxies an unvalidated DOI into the upstream
  path with no rate limit ([crossref.py](/Volumes/Crucial X9/Projects/curriculum-curator/backend/app/api/routes/crossref.py:98)).
  No internal SSRF (host is hardcoded); require auth, validate/quote the DOI, add a limiter.
- `research_sources` stores a body-supplied `unit_id` without
  `require_unit_owner` — write pollution of another user's unit reference
  (no cross-read demonstrated)
  ([research_sources.py](/Volumes/Crucial X9/Projects/curriculum-curator/backend/app/api/routes/research_sources.py:122)).

**Data & services**
- Background unified import runs on the request-scoped SQLAlchemy session
  (closed on response; task reference overwritten each import)
  ([unified_import_service.py](/Volumes/Crucial X9/Projects/curriculum-curator/backend/app/services/unified_import_service.py:427)).
  Use a fresh `SessionLocal` inside the task.
- `_log_usage` commits/rolls back the *caller's* transaction after every LLM
  call ([llm_service.py](/Volumes/Crucial X9/Projects/curriculum-curator/backend/app/services/llm_service.py:1025)).
  Use a dedicated session.
- SQLite `PRAGMA foreign_keys=ON` is never set, so FK cascades/integrity are
  unenforced on the default deployment
  ([database.py](/Volumes/Crucial X9/Projects/curriculum-curator/backend/app/core/database.py:16)).
- Git/DB import persistence is non-atomic: failures leave orphan git commits
  or DB rows missing images
  ([unified_import_service.py](/Volumes/Crucial X9/Projects/curriculum-curator/backend/app/services/unified_import_service.py:737)).
- Imported assessment HTML bypasses the bleach allowlist and is re-exported
  unescaped into IMSCC/SCORM pages
  ([package_import_service.py](/Volumes/Crucial X9/Projects/curriculum-curator/backend/app/services/package_import_service.py:1363),
  [imscc_service.py](/Volumes/Crucial X9/Projects/curriculum-curator/backend/app/services/imscc_service.py:492)).
  Whether it also renders as in-app HTML (stored XSS) is unverified — see Gaps.

**API shape**
- Raw exception text returned to clients on several 500/ValueError paths
  ([ai.py](/Volumes/Crucial X9/Projects/curriculum-curator/backend/app/api/routes/ai.py:157) and siblings). Log server-side; return generic detail.
- Unbounded list endpoints (`.all()` with no pagination) and `GET /units`
  reporting `total = page size`
  ([units.py](/Volumes/Crucial X9/Projects/curriculum-curator/backend/app/api/routes/units.py:70)).
- `CamelModel` lacks `extra='forbid'` (~312 schema classes silently ignore
  unknown fields); sampled inputs lack bounds
  ([base.py](/Volumes/Crucial X9/Projects/curriculum-curator/backend/app/schemas/base.py:25)).
- Startup swallows router import failures (try/ImportError → warning), so a
  broken import silently 404s whole route families
  ([main.py](/Volumes/Crucial X9/Projects/curriculum-curator/backend/app/main.py:286)).
  Fail fast; smoke-test route presence.
- SPA catch-all joins a user path onto `dist` with no resolve/containment
  check ([main.py](/Volumes/Crucial X9/Projects/curriculum-curator/backend/app/main.py:649)).
  Exploitability depends on Starlette normalisation; add
  `resolve()` + `is_relative_to` regardless.
- `/docs` + OpenAPI exposed unauthenticated in production by default
  ([main.py](/Volumes/Crucial X9/Projects/curriculum-curator/backend/app/main.py:178)).
  Disable outside DEBUG/LOCAL_MODE.
- Divergent hand-rolled ownership checks (units.py, material_import,
  import_content) vs the deps seam; wrong `User` vs `UserResponse`
  annotations in older routes. Converge on the seam.

**Frontend**
- Mermaid SVG is injected via the codebase's single `dangerouslySetInnerHTML`
  with no DOMPurify and no explicit mermaid `securityLevel`
  ([MermaidView.tsx](/Volumes/Crucial X9/Projects/curriculum-curator/frontend/src/components/Editor/MermaidView.tsx:98)).
  Set `securityLevel: 'strict'` and sanitise the SVG.
- Embed nodes round-trip arbitrary iframe/`href` URLs (incl. `javascript:` /
  `data:`) from imported content without re-validation, unsandboxed
  ([YoutubeNode.ts](/Volumes/Crucial X9/Projects/curriculum-curator/frontend/src/components/Editor/YoutubeNode.ts:38),
  [InteractiveVideoEmbedView.tsx](/Volumes/Crucial X9/Projects/curriculum-curator/frontend/src/components/Editor/InteractiveVideoEmbedView.tsx:188)).
  Re-derive embeds from IDs; http(s)-only allowlist; add `sandbox`.
- 401 interceptor deletes the token but never resets the auth store, leaving
  a stale authenticated UI until reload
  ([api.ts](/Volumes/Crucial X9/Projects/curriculum-curator/frontend/src/services/api.ts:38)).
- `initializeAuth` can hang on the spinner forever on a 200/empty
  `/auth/me` (LOW) ([authStore.ts](/Volumes/Crucial X9/Projects/curriculum-curator/frontend/src/stores/authStore.ts:88)).
- Explicit `any` escapes at API boundaries persist despite strict TS and the
  project's no-`any` rule; no lint rule enforces it
  ([analyticsApi.ts](/Volumes/Crucial X9/Projects/curriculum-curator/frontend/src/services/analyticsApi.ts:31)).

**Desktop, Docker & CI**
- Electron: `sandbox: false`, `webviewTag: true`, implicit isolation flags;
  `shell.openExternal` with no scheme allowlist and no `will-navigate`
  guard; IPC handlers (incl. `save-file`, `install-update`) don't validate
  the sender frame
  ([index.ts](/Volumes/Crucial X9/Projects/curriculum-curator/desktop/src/main/index.ts:18)).
  On macOS, close-window kills the sidecars and Dock-reopen shows a dead UI.
- Reusable release workflow pinned to `@main` while receiving Apple signing
  secrets ([desktop-release.yml](/Volumes/Crucial X9/Projects/curriculum-curator/.github/workflows/desktop-release.yml:18)).
  Same-owner repo, so MEDIUM — pin to a commit SHA anyway.
- `GH_OWNER` is never set for electron-builder publish, so `app-update.yml`
  may have an empty owner and auto-update may silently fail
  ([electron-builder.yml](/Volumes/Crucial X9/Projects/curriculum-curator/desktop/electron-builder.yml:58)).
  Notarization silently no-ops without credentials; make release builds
  hard-fail instead.
- Docker build integrity: lockfile deleted + `npm install --force`; unfrozen
  `uv` installs; unverified `curl | bash` installers and a checksum-free
  Typst tarball; mutable base tag; `python:3.11-slim` vs declared
  `requires-python >= 3.13`
  ([Dockerfile](/Volumes/Crucial X9/Projects/curriculum-curator/Dockerfile:2)).
  The tested dependency set is not what ships. Use `npm ci`,
  `uv sync --frozen`, digest/checksum pinning, `python:3.13-slim`,
  multi-stage runtime image, `DEBUG=false`, and ignore `**/.env*`.
- Production deploys `:latest` with Watchtower auto-update — untested builds
  roll out with no digest pin or rollback point
  ([deploy/docker-compose.yml](/Volumes/Crucial X9/Projects/curriculum-curator/deploy/docker-compose.yml:10)).
- Both compose files require a pre-existing external `caddy_default`
  network that nothing in the repo creates; a fresh `docker compose up`
  fails, and the app/Ollama join a VPS-wide shared network.
- CI runs backend+frontend lint/types/tests but never builds the Dockerfile
  or desktop app on PRs, and image publishing is not gated on CI passing.
  Actions are pinned by mutable tags; no SBOM/provenance/scan on publish.

## LOW (selection)

Login timing enumeration (short-circuit bcrypt) and explicit 409 on
duplicate registration; lockout row-accounting quirks (first-row only,
success clears all IPs, IP limiter counts rows not attempts); admin
whitelist patterns not normalised to `@domain` (silently never match);
unbounded password length vs bcrypt 72-byte truncation; batch-import status
uses unowned `get_task()` (task-ID IDOR for progress/filenames);
`user_repo.update_user` mass-assignment footgun (allows `role`,
`password_hash` if a future caller passes request data); unescaped LIKE
wildcards in unit search; unguarded Canvas `module_meta.xml` parse can 500
an otherwise valid import; unauthenticated discovery endpoints fingerprint
the deployment; basedpyright in standard mode with Unknown/Any reporting
off and no ruff `S` (bandit) rules; coverage collected but no `fail_under`
gate; the shared test client overrides auth, so real JWT flows are thinly
covered; tests that cannot fail (e.g. a "raises" test asserting no raise);
streaming fetch sends `Bearer [REDACTED]`; client-only `/admin` gate (backend
remains authoritative); `apiBase` env-override precedence contradicts its
docstring; Docker entrypoint logs the raw `DATABASE_URL` despite a "masked"
comment; desktop fixed port with no single-instance lock; sidecar script
always downloads arm64 vendor binaries though x64 Macs are shipped;
process-wide search cache shared across users on a server; email codes
fall back to being printed to logs when email is misconfigured.

## Privacy story vs code (cross-cutting)

The product now markets "draft privately, share when ready" and "no
tracking". The audit found the **no-telemetry claim true** — no analytics
SDK or beacon exists anywhere; "analytics" is local reporting over the
app's own DB. The **"only providers you choose" claim is not fully true**:

- Tier-1 academic search is hard-coded always-available and is the default:
  every research query is sent to OpenAlex, Semantic Scholar and CrossRef
  (plus CORE) with no per-provider opt-in
  ([search_router.py](/Volumes/Crucial X9/Projects/curriculum-curator/backend/app/services/search_router.py:63)).
  General-web search silently falls back to DuckDuckGo scraping and can
  cascade one query across several keyed providers.
- OpenAlex/CrossRef queries include a `mailto:` that falls back to the
  operator's `FROM_EMAIL`, sending a linkable operator address with users'
  search terms ([config.py](/Volumes/Crucial X9/Projects/curriculum-curator/backend/app/core/config.py:66)).
- The public Download page auto-fetches GitHub's releases API on mount,
  disclosing visitor IP/UA to GitHub before any click; the Electron app
  checks GitHub for updates 3s after every launch with no opt-out found.
- LLM prompts silently include more than "the text you are working on":
  the full learning-design spec, week topic, and up to 5 source materials'
  titles/descriptions are prepended automatically
  ([curriculum_context.py](/Volumes/Crucial X9/Projects/curriculum-curator/backend/app/services/curriculum_context.py:41)).
  Settings copy should say "plus your unit's design context", and ideally
  offer an exclusion toggle.
- Point-of-use notices are still missing at most AI entry points (quiz,
  branching, lesson plan, AI assistant) and in research search (the tier is
  shown only after results return). URL extraction defaults AI-summarise
  **on**, forwarding up to 8,000 chars of a fetched page to the configured
  LLM with no in-panel notice.
- The new Ollama copy ("sent only to the address below") overpromises when
  the URL is remote or empty (hidden backend default), and on a shared
  server all AI calls transit that server. Qualify by actual host.
- Server mode logs identity, IP, user-agent and per-feature token/cost
  history ([security_logger.py](/Volumes/Crucial X9/Projects/curriculum-curator/backend/app/services/security_logger.py:34)).
  That is legitimate for a hosted service, but the landing hero pitches
  private drafting next to a hosted sign-in. (The new Login disclosure and
  Download "people who run that server can access the work" lines are the
  honest version — extend that scoping to the hero and document log
  retention for operators.)

Verified accurate: ExportDialog's "nothing is sent anywhere yet; you upload
the file yourself" matches the code; the genuine local path (desktop +
Ollama on localhost, no key, no cloud call) exists and works as described.

## Verified strengths (keep these)

- Ownership seam: uniform 404 (no existence leak), admin bypass, archived
  and via-unit handling, batch filter — all in one place
  ([deps.py](/Volumes/Crucial X9/Projects/curriculum-curator/backend/app/api/deps.py:147)).
  All admin routes sit behind `get_current_admin_user` with self-disable /
  self-delete guards.
- JWT verification pins HS256 + expiry; role/active are reloaded from the DB
  every request, so demotion/deactivation bites within one token lifetime.
- Brute-force defences layer properly: per-IP rate limits, progressive
  lockout (to 4h/24h), cross-IP aggregate lock, enumeration-safe
  forgot/resend flows, `secrets.choice` codes with prior-code invalidation.
- Proxy headers honoured only with `TRUST_PROXY_HEADERS`, through one
  helper feeding rate limits, lockout and IP-binding. Explicit CORS and
  TrustedHost allowlists; `null` origin only in `LOCAL_MODE`.
- ORM bound parameters everywhere inspected (no string SQL); `defusedxml`
  for untrusted XML; exports build XML via Element text (no manifest
  breakout); bleach allowlist on imported material bodies; masked API-key
  previews in responses.
- The page fetcher is a model SSRF defence: DNS resolution with
  private/loopback/link-local/metadata blocking and per-redirect-hop
  revalidation ([url_safety.py](/Volumes/Crucial X9/Projects/curriculum-curator/backend/app/utils/url_safety.py:39)).
  Consolidate *all* outbound fetches through it.
- Git content storage: path containment, SHA-only revisions, argv (no
  shell) subprocess calls.
- Tests: real in-memory SQLite with per-test schema and rich factories;
  cross-owner 404, path-containment and SSRF suites exist. Frontend editor
  parses through the ProseMirror schema (no raw HTML injection) and AI
  content is applied as structured JSON.
- Electron process spawning uses argv arrays, loopback binds, sandboxed
  webview guests and a narrow contextBridge; the updater leaves signature
  verification at upstream defaults. CI uses placeholder secrets and
  scoped tokens; `setup.sh` generates real secrets correctly.

## Gaps — not audited / not verified

State these plainly; absence of a finding here means *not inspected*:

- `material_parsers` internals (pandoc subprocess, DOCX/PPTX/PDF parser
  XXE/decompression safety), `qti_service`, `citation_service`,
  `curtin_service`.
- ~17 route files beyond signatures (incl. `admin_config` generic config
  endpoints, `user_export`, `background_tasks`/`tasks`, `web_search`),
  `ai.py` lines 320–1384, and service-layer ownership below routes —
  further body-ID IDORs cannot be ruled out.
- `security_middleware.py` bodies (CSP/security headers, request-validation
  bypasses); no CSP is defined in `frontend/index.html`.
- Whether imported assessment/material HTML ever renders in-app as HTML
  (determines stored-XSS vs export-only impact).
- LiteLLM's own telemetry/phone-home defaults (the app sets only
  `drop_params`); full prompt contents at every other LLM call site
  (document analysis, outline synthesis, image generation).
- SecurityLog/TokenUsageLog retention, purge and user export/delete paths.
- The shared `app-hq` release workflow (another repo): `GH_OWNER`, signing
  enforcement, runner architectures. Branch-protection settings. `DEPLOYMENT.md`.
- Runtime behaviour never exercised by the audit agents: packaged sidecar
  startup (H10), Docker build, live auth requests, Mermaid sink under a
  real browser, SPA traversal against a running server.
- Not in scope for any agent: Alembic-vs-model drift, dependency CVE audit
  (Python/npm), git-history secret scan, backup/restore and data-deletion
  flows, prompt-injection via imported content into LLM/plugin pipelines.

## Suggested fix order

1. **AuthZ holes:** protect plugin routes (C1); add the OpenAPI sweep test
   (every non-allowlisted operation 401s anonymous, 404s cross-owner) so
   this class cannot regress.
2. **Secrets:** runtime `SECRET_KEY` enforcement (C2); unusable local-user
   password (H2); encrypt LLM keys at rest (H4); remove committed test
   credentials.
3. **Registration & modes:** fail-closed whitelist + setup-token first
   admin (H3); `LOCAL_MODE` startup guard; desktop ephemeral port + token
   (H1).
4. **Input safety:** zip caps (H6); route all fetches through
   `url_safety` (H8 + LLM/SearXNG bases); upload size caps + magic sniffing;
   bleach assessment HTML.
5. **Ownership convergence:** AI-context IDOR (H7) and all body-ID paths
   onto the deps seam; `research_sources`; batch-status `get_owned_task`.
6. **Session:** cookie migration + real logout/revocation (H9); 401 store
   reset; IP-binding at every issuance; token-type check.
7. **Desktop:** first-launch secret (H10), single-instance lock, Electron
   hardening (isolation flags, openExternal allowlist, sender checks),
   `GH_OWNER`/notarization hard-fail, per-arch vendor binaries.
8. **Deploy/CI:** loopback port bindings (H11), pinned images instead of
   `:latest`+Watchtower, reproducible Docker build, PR Docker/desktop
   builds, CI-gated publishing, SHA-pinned actions.
9. **LLM store:** single source of truth + kill-switch (H5); fix the 2
   failing tests against the real path.
10. **Privacy copy/code alignment:** per-provider search consent or claim
    rewording; drop the `mailto` fallback; point-of-use recipient notices
    at every AI/search action; disclose auto-included design context;
    GitHub fetch/update-check disclosure (+ opt-out); scope "draft
    privately" to desktop/self-hosted wherever it appears.


