# Secure backend foundation

This is an initial application-security foundation for company workspaces. It is **not a declaration of GDPR compliance**. Do not use the local example encryption key, local database password, or a development identity provider for production or real customer data.

## What is implemented

- A separate Flask API package at `backend/`, leaving the static demo and fixture-based `v2/` application separate.
- PostgreSQL-only configuration; production requires verified TLS (`sslmode=verify-full` or `verify-ca`).
- OIDC bearer-token verification against an HTTPS JWKS endpoint, with issuer, audience, expiry, issue time, subject, and fixed `RS256` algorithm validation. The database stores a keyed digest of the OIDC subject rather than the subject or email address.
- Explicit tenant membership lookup on every protected request. The `X-Tenant-ID` header selects a workspace only after the authenticated OIDC subject is found as an active member of that workspace.
- PostgreSQL row-level security (RLS) on tenant metadata, memberships, workspace content, member preferences, and audit events. The migration enables and forces RLS. Personal preferences require both transaction-local tenant and membership settings. App queries also include explicit scope predicates.
- Workspace names, item titles, and item text encrypted using AES-GCM with per-tenant derived keys and field/record associated data. The identity-digest key is separate. A key ring permits content-key rotation: add a new key, set it active, re-encrypt existing records, then remove the old key only after confirming no records reference it. Keep the identity key stable or plan a controlled membership re-digest migration before rotating it.
- Per-member app preferences (saved public story IDs and topic filters) encrypted before reaching Postgres. A member can read, update, and erase only their own preference row; another user in the same company cannot read it.
- Workspace item listing, creation, retrieval, and deletion; a workspace-scoped audit-event view for owners/admins.
- OIDC Authorization Code + PKCE sign-in from the prototype profile and the parallel v3 reading app. Access tokens stay in browser memory; only the short-lived PKCE verifier/state and workspace ID use `sessionStorage`. No email or profile name is requested or persisted.
- A minimal non-root Gunicorn image (`Dockerfile.backend`) and an opt-in local Compose app profile. The application port binds to loopback.
- No production public registration, cookie session, password handling, cross-tenant content search, or file upload. A separate local-only Keycloak fixture can enable account creation solely for a synthetic test workspace.
- Strict CORS allowlisting when `CORS_ORIGINS` is set; wildcard origins are rejected.
- GitHub Actions input validation for `max_stories`, plus workflow concurrency to prevent overlapping story-update pushes.

## Local setup

Requirements: Python 3.11 or newer, PostgreSQL, and an OIDC identity provider that can issue access tokens with the API audience configured below. The repository includes a loopback-only Keycloak realm for synthetic local account-flow checks.

For local sign-up and sign-in testing without an external identity provider, use
the isolated Keycloak realm in [`deploy/local-auth/realm.json`](../deploy/local-auth/realm.json).
Its registration flow and automatic membership provisioning are enabled only
when `APP_ENV=development`, `STAGING_SIGNUP_ENABLED=true`, and the app is
reached through loopback. Never enable that setting on Vercel or with real
company data. The local synthetic story snapshot is selected through
`STORIES_PATH`. Build the prototype preview, then serve it from the same-origin
local API at `http://127.0.0.1:8000/prototype/`; the registration callback must
use that exact URI.

1. Start the local Postgres database:

   ```sh
   docker compose -f docker-compose.backend.yml up -d
   ```

2. Create a virtual environment and install the API dependencies:

   ```sh
   python3 -m venv .venv
   . .venv/bin/activate
   pip install -r backend/requirements.txt
   ```

3. Copy `.env.backend.example` to `.env.backend`; replace both example keys with fresh random 32-byte keys. For an external development provider, configure its issuer, audience, JWKS URL, and public browser client. Register Authorization Code + PKCE (S256), the exact redirect URI `http://127.0.0.1:8000/prototype/`, and allow the local app origin at the provider token endpoint. Do not create a browser client secret.

   For the included local Keycloak realm, set these values in `.env.backend`
   and keep Keycloak and Flask bound to `127.0.0.1`:

   ```dotenv
   OIDC_ISSUER=http://127.0.0.1:8080/realms/deeplitics-local
   OIDC_AUDIENCE=deeplitics-api
   OIDC_JWKS_URL=http://127.0.0.1:8080/realms/deeplitics-local/protocol/openid-connect/certs
   OIDC_CLIENT_ID=deeplitics-web
   OIDC_AUTHORIZATION_ENDPOINT=http://127.0.0.1:8080/realms/deeplitics-local/protocol/openid-connect/auth
   OIDC_TOKEN_ENDPOINT=http://127.0.0.1:8080/realms/deeplitics-local/protocol/openid-connect/token
   OIDC_REDIRECT_URI=http://127.0.0.1:8000/prototype/
   DEFAULT_TENANT_ID=11111111-1111-4111-8111-111111111111
   STAGING_SIGNUP_ENABLED=true
   STORIES_PATH=deploy/staging-stories.json
   ```

   Set `KEYCLOAK_HOME` to your local Keycloak installation, then import and
   start the isolated realm:

   ```sh
   cp deploy/local-auth/realm.json "$KEYCLOAK_HOME/data/import/deeplitics-local-realm.json"
   "$KEYCLOAK_HOME/bin/kc.sh" start-dev --http-host=127.0.0.1 --http-port=8080 --import-realm
   ```

   This realm permits registration only for local flow checks; it is not a
   production identity provider. Never enable `STAGING_SIGNUP_ENABLED` with
   customer data or outside the loopback-only development server. Load the
   file into the shell without committing it:

   ```sh
   set -a
   . ./.env.backend
   set +a
   ```

   Generate a local key (use once for each key setting) with:

   ```sh
   python3 -c 'import base64,secrets; print(base64.b64encode(secrets.token_bytes(32)).decode())'
   ```

4. Apply the checked-in schema migration and start the local API and prototype:

   ```sh
   flask --app backend.app db upgrade
   python3 deploy/build_vercel_staging.py
   flask --app backend.app run --host 127.0.0.1 --port 8000
   ```

   Open `http://127.0.0.1:8000/prototype/`. In the local realm, **Konto
   erstellen** registers an identity at Keycloak and adds it to the synthetic
   workspace; **Anmelden** uses the same OIDC provider and requires workspace
   membership. No email address or password is sent to the Deeplitics API.
   The Vercel static preview keeps auth disabled until a hosted OIDC provider,
   API, and managed database are configured.

5. With an external identity provider and self-sign-up disabled, create a
   workspace and grant a verified OIDC identity access. Obtain `sub` from the
   provider’s trusted token/user inspection process; never use an email
   address as the subject identifier:

   ```sh
   flask --app backend.app provision-tenant --id 11111111-1111-4111-8111-111111111111 --name "Example workspace"
   flask --app backend.app provision-member --tenant-id 11111111-1111-4111-8111-111111111111 --issuer "$OIDC_ISSUER" --subject 'provider|subject-id' --role owner
   ```

Revoke access when a user leaves a workspace:

   ```sh
   flask --app backend.app deactivate-member --tenant-id 11111111-1111-4111-8111-111111111111 --issuer "$OIDC_ISSUER" --subject 'provider|subject-id'
   ```

Deactivating membership also deletes that member's saved-story and topic
preferences. This keeps a former member's private app settings from being
retained unintentionally.

The API does not have an authentication bypass for local development. `/api/v1/health`, `/api/v1/stories`, `/api/v1/public-config`, and `/` are public; `/api/v1/me`, personal preference routes, and workspace routes require a valid OIDC access token and an active membership. Send the selected tenant as `X-Tenant-ID` and the token as `Authorization: Bearer …`.

## Routes

| Method | Route | Access |
|---|---|---|
| `GET` | `/api/v1/health` | Public, minimal health response |
| `GET` | `/api/v1/public-config` | Public browser OIDC settings; contains no secrets |
| `GET` | `/api/v1/stories` | Public published story snapshot; short cache |
| `POST` | `/api/v1/staging-signup` | Development only; loopback only; provisions a member in the synthetic local workspace |
| `GET` | `/api/v1/me` | Authenticated tenant member |
| `GET` | `/api/v1/me/preferences` | Authenticated member's encrypted settings |
| `PUT` | `/api/v1/me/preferences` | Replace validated personal settings |
| `DELETE` | `/api/v1/me/preferences` | Erase saved stories and topic settings |
| `GET` | `/api/v1/workspace-items` | Authenticated tenant member; metadata only, max page size 50 |
| `POST` | `/api/v1/workspace-items` | Authenticated tenant member; title and text limited, body encrypted before storage |
| `GET` | `/api/v1/workspace-items/{id}` | Authenticated tenant member; tenant-scoped lookup and decryption |
| `DELETE` | `/api/v1/workspace-items/{id}` | Authenticated tenant member; deletes the item and records an audit event |
| `GET` | `/api/v1/admin/audit-events` | Tenant owner/admin; bounded, content-free event list |

## Production deployment requirements

- Use a managed PostgreSQL service with TLS certificate verification, encrypted backups, private networking, and a tested restore process.
- Use **separate database roles**: a schema migration owner and an application role. The runtime role must not be a superuser and must not have `BYPASSRLS`. It should receive only the table permissions the API requires. RLS is defense in depth; it does not replace the application’s membership checks.
- Grant the runtime role only `SELECT` on `tenants` and `tenant_memberships`, `SELECT/INSERT/DELETE` on `workspace_items`, `SELECT/INSERT` on `audit_events`, and `SELECT/INSERT/UPDATE/DELETE` on `member_preferences`. Keep tenant/member provisioning and membership deactivation on a separate, audited operator connection; do not give the web process tenant or membership write permissions.
- Run `flask db upgrade` using the migration-owner connection. Start Gunicorn with the restricted runtime-role connection. The sample compose database uses one local-only role for convenience and is not a production role layout.
- Put OIDC settings, database credentials, and encryption keys in a secrets manager. Keep the encryption key ring separate from the database. Never reuse the example key. Keep old key IDs available until all corresponding ciphertext has been re-encrypted and verified.
- Set `APP_ENV=production`, configure HTTPS OIDC issuer/JWKS endpoints, and require verified database TLS. Serve through a production WSGI server and an HTTPS reverse proxy; do not expose Flask’s development server.
- Register a public OIDC web client with Authorization Code + PKCE (S256), an exact HTTPS redirect URI, and a token endpoint that allows the app origin. Never configure a client secret in the browser. Configure `OIDC_CLIENT_ID`, `OIDC_AUTHORIZATION_ENDPOINT`, `OIDC_TOKEN_ENDPOINT`, and `OIDC_REDIRECT_URI`; the app requests only `openid` plus the configured API audience.
- Redact request query strings at the reverse proxy. The OIDC callback briefly carries an authorization code in the URL; the provided Gunicorn image disables access logs and the app removes callback parameters after reading them.
- Set `CORS_ORIGINS` to exact trusted browser origins only. Put request-rate limits, network controls, and request-size limits at the ingress as well as in the application.
- Keep the application logs free of workspace text, access tokens, passwords, and raw prompts. Define a retention period for audit events and ensure it is reflected in company terms and deletion procedures.
- Provide a privacy notice, customer processing agreement, subprocessor list, rights-request process, retention schedule, incident playbook, and DPIA screening before accepting customer data. Review international data transfers and each AI provider’s retention/training terms.

## Deliberate gaps before customer launch

This foundation does not yet implement self-service account/workspace deletion, a complete export across membership and audit records, retention automation, file uploads, delegated support access, a reviewable administrator UI, AI processing of company content, key re-encryption jobs, rate limiting in the app, or a formal privacy/incident workflow. Decide retention and deletion behavior with the customer contract and privacy review before adding those paths. A DPIA, processing agreement, lawful-basis analysis, and vendor review are organizational/legal work, not something the code can certify.

The Raspberry Pis are suitable for synthetic-data staging and an encrypted
backup target. Keep real company data on an EU-hosted managed PostgreSQL
service. Use the MacBooks for development and operations rather than as
always-on production hosts. Hardware layout and limitations are documented in
[`v3/README.md`](../v3/README.md).
