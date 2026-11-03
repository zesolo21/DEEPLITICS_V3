# Vercel staging preview

The initial Vercel deployment is a static, public-facing preview of the v3 reading interface. It serves only the fictional records in `deploy/staging-stories.json`; it does not read `data/stories.json`, connect to PostgreSQL, or enable login and saved preferences. The page displays a staging banner so the synthetic content is clear.

Vercel builds the static output with `python3 deploy/build_vercel_staging.py` and publishes `public/`. The rewrites expose the browser's existing `/api/v1/public-config` and `/api/v1/stories` requests as static JSON files. The root URL opens the v3 app.

This deployment is for interface review only. It does not exercise the authenticated API or validate database migrations, OIDC, encryption-key handling, RLS, or production operations. Do not add company or user data to this preview.

## Full API-backed staging later

Once an EU staging PostgreSQL database and an OIDC test tenant are available, replace the static output build with the Flask deployment configuration, set the Vercel Function region to Frankfurt (`fra1`), add the environment variables listed in `.env.backend.example` and `docs/SAFE_BACKEND.md` through Vercel's environment-variable settings, and run the schema migration with a dedicated migration role before enabling the API. Keep the app runtime role separate and restricted. Register the exact callback URL `https://<staging-domain>/app/` with the OIDC provider.

The static preview does not establish GDPR compliance. Review Vercel and database-provider terms, data flows, retention, and access controls before putting personal or company data into any environment.
