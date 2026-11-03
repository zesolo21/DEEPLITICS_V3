# Vercel staging preview

The Vercel staging deployment serves the existing `frontend/` prototype UI with only the explicitly synthetic records in `deploy/staging-stories.json`. The build replaces the prototype's bundled story data before publishing it, so the real-content snapshot in `data/stories.json` is not included. The page displays a staging banner. Sign-in, the API, PostgreSQL, and account features are not connected.

Vercel builds the static output with `python3 deploy/build_vercel_staging.py` and publishes `public/`. The root URL and `/app` open the prototype interface. Its layout and styling come from `frontend/index.template.html` and `frontend/app.js`; the build injects the fictional demo records and labels the page as staging. The real-content build `frontend/index.html` and local authentication fixture are excluded from Vercel's build upload.

To view the same preview on a laptop before Vercel is connected, run:

```sh
python3 deploy/build_vercel_staging.py
python3 deploy/preview_server.py
```

Then open `http://localhost:4173/` in a browser. Stop the local server with `Ctrl+C`.

This deployment is for interface review only. It does not exercise the authenticated API or validate database migrations, OIDC, encryption-key handling, RLS, or production operations. The story content is synthetic, and profile, history, and saved-story state stays in the current browser session. Do not add company or user data to this preview.

## Full API-backed staging later

Once an EU staging PostgreSQL database and an OIDC test tenant are available, replace the static output build with the Flask deployment configuration, set the Vercel Function region to Frankfurt (`fra1`), add the environment variables listed in `.env.backend.example` and `docs/SAFE_BACKEND.md` through Vercel's environment-variable settings, and run the schema migration with a dedicated migration role before enabling the API. Keep the app runtime role separate and restricted. Register the exact callback URL `https://<staging-domain>/app/` with the OIDC provider.

The static preview does not establish GDPR compliance. Review Vercel and database-provider terms, data flows, retention, and access controls before putting personal or company data into any environment.
