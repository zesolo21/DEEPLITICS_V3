from __future__ import annotations

import os
import base64
import uuid
from pathlib import Path
from urllib.parse import urlparse

import click
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from sqlalchemy import select, text
from sqlalchemy.engine import make_url

from backend.crypto import EncryptionConfigurationError, _key_ring, encrypt_text
from backend.extensions import db, migrate
from backend.identity import identity_digest
from backend.models import AuditEvent, MemberPreference, Membership, Tenant


def _normalise_issuer(value: str) -> str:
    # OIDC issuer matching is exact; do not add/remove a trailing slash.
    return value.strip()


def create_app(test_config: dict | None = None) -> Flask:
    repository_root = Path(__file__).resolve().parent.parent
    app = Flask(__name__)
    app.config.update(
        MAX_CONTENT_LENGTH=1_048_576,
        MAX_ITEM_CHARS=200_000,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SQLALCHEMY_ENGINE_OPTIONS={"pool_pre_ping": True},
        OIDC_ISSUER=os.environ.get("OIDC_ISSUER", ""),
        OIDC_AUDIENCE=os.environ.get("OIDC_AUDIENCE", ""),
        OIDC_JWKS_URL=os.environ.get("OIDC_JWKS_URL", ""),
        OIDC_CLIENT_ID=os.environ.get("OIDC_CLIENT_ID", ""),
        OIDC_AUTHORIZATION_ENDPOINT=os.environ.get("OIDC_AUTHORIZATION_ENDPOINT", ""),
        OIDC_TOKEN_ENDPOINT=os.environ.get("OIDC_TOKEN_ENDPOINT", ""),
        OIDC_REDIRECT_URI=os.environ.get("OIDC_REDIRECT_URI", ""),
        DEFAULT_TENANT_ID=os.environ.get("DEFAULT_TENANT_ID", ""),
        STORIES_PATH=os.environ.get("STORIES_PATH") or str(repository_root / "data" / "stories.json"),
        V3_STATIC_DIR=str(repository_root / "v3"),
        PROTOTYPE_STATIC_DIR=str(repository_root / "public" / "app"),
        APP_ENV=os.environ.get("APP_ENV", "development").lower(),
        STAGING_SIGNUP_ENABLED=os.environ.get("STAGING_SIGNUP_ENABLED", "false").lower() == "true",
    )
    if test_config:
        app.config.update(test_config)

    if app.config["STAGING_SIGNUP_ENABLED"] and app.config["APP_ENV"] != "development":
        raise RuntimeError("Staging self-signup is only allowed with APP_ENV=development.")

    database_url = app.config.get("SQLALCHEMY_DATABASE_URI") or os.environ.get("DATABASE_URL", "")
    if database_url.startswith("postgres://"):
        database_url = "postgresql+psycopg://" + database_url[len("postgres://"):]
    elif database_url.startswith("postgresql://"):
        database_url = "postgresql+psycopg://" + database_url[len("postgresql://"):]
    if not database_url.startswith("postgresql+psycopg://"):
        raise RuntimeError("DATABASE_URL must point to PostgreSQL using the psycopg driver.")
    if app.config["APP_ENV"] == "production":
        sslmode = make_url(database_url).query.get("sslmode")
        if sslmode not in {"verify-full", "verify-ca"}:
            raise RuntimeError("Production DATABASE_URL must use PostgreSQL sslmode=verify-full or verify-ca.")
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url

    if app.config["APP_ENV"] == "production":
        required_oidc = (
            "OIDC_ISSUER", "OIDC_AUDIENCE", "OIDC_JWKS_URL", "OIDC_CLIENT_ID",
            "OIDC_AUTHORIZATION_ENDPOINT", "OIDC_TOKEN_ENDPOINT", "OIDC_REDIRECT_URI",
        )
        if any(not app.config.get(key) for key in required_oidc):
            raise RuntimeError("Production requires API and browser OIDC configuration.")
        if urlparse(app.config["OIDC_JWKS_URL"]).scheme != "https" or urlparse(app.config["OIDC_ISSUER"]).scheme != "https":
            raise RuntimeError("OIDC issuer and JWKS URL must use HTTPS in production.")
    for key in ("OIDC_AUTHORIZATION_ENDPOINT", "OIDC_TOKEN_ENDPOINT", "OIDC_REDIRECT_URI"):
        value = app.config.get(key, "")
        if value:
            parsed = urlparse(value)
            try:
                parsed.port
            except ValueError as exc:
                raise RuntimeError(f"{key} contains an invalid port.") from exc
            if (parsed.scheme not in {"https", "http"} or not parsed.hostname
                    or parsed.username or parsed.password or parsed.fragment):
                raise RuntimeError(f"{key} must be an absolute HTTP(S) URL without credentials or fragments.")
            if app.config["APP_ENV"] == "production" and parsed.scheme != "https":
                raise RuntimeError(f"{key} must use HTTPS in production.")
    if app.config.get("DEFAULT_TENANT_ID"):
        try:
            app.config["DEFAULT_TENANT_ID"] = str(uuid.UUID(app.config["DEFAULT_TENANT_ID"]))
        except ValueError as exc:
            raise RuntimeError("DEFAULT_TENANT_ID must be a UUID.") from exc
    try:
        encryption_keys, _active_key = _key_ring()
    except EncryptionConfigurationError as exc:
        raise RuntimeError("Configure DATA_ENCRYPTION_KEYS_JSON and DATA_ENCRYPTION_ACTIVE_KEY.") from exc
    try:
        identity_digest("https://identity.example/", "configuration-check")
    except RuntimeError as exc:
        raise RuntimeError("Configure IDENTITY_LOOKUP_KEY.") from exc
    if app.config["APP_ENV"] == "production":
        try:
            identity_key = base64.b64decode(os.environ["IDENTITY_LOOKUP_KEY"], validate=True)
        except (ValueError, KeyError) as exc:
            raise RuntimeError("Configure a valid production IDENTITY_LOOKUP_KEY.") from exc
        if any(not any(key) for key in encryption_keys.values()) or not any(identity_key):
            raise RuntimeError("Replace all-zero example keys before production.")

    db.init_app(app)
    migrate.init_app(app, db, directory="backend/migrations")

    allowed_origins = [
        origin.strip().rstrip("/")
        for origin in os.environ.get("CORS_ORIGINS", "").split(",")
        if origin.strip()
    ]
    if any("*" in origin for origin in allowed_origins):
        raise RuntimeError("Wildcard CORS origins are not permitted.")
    for origin in allowed_origins:
        parsed_origin = urlparse(origin)
        try:
            parsed_origin.port
        except ValueError as exc:
            raise RuntimeError("CORS_ORIGINS contains an invalid port.") from exc
        if (parsed_origin.scheme not in {"https", "http"} or not parsed_origin.hostname
                or parsed_origin.username or parsed_origin.password
                or parsed_origin.path not in {"", "/"} or parsed_origin.query or parsed_origin.fragment):
            raise RuntimeError("CORS_ORIGINS entries must be exact origins without paths or wildcards.")
        if app.config["APP_ENV"] == "production" and parsed_origin.scheme != "https":
            raise RuntimeError("Production CORS origins must use HTTPS.")
    if allowed_origins:
        CORS(
            app,
            resources={r"/api/*": {"origins": allowed_origins}},
            methods=["GET", "POST", "DELETE", "OPTIONS"],
            allow_headers=["Authorization", "Content-Type", "X-Tenant-ID"],
            supports_credentials=False,
            max_age=300,
        )

    from backend.api import api

    app.register_blueprint(api)

    @app.get("/app")
    @app.get("/app/")
    def deeplitics_next():
        return send_from_directory(app.config["V3_STATIC_DIR"], "index.html")

    @app.get("/app/<path:asset_path>")
    def deeplitics_next_asset(asset_path: str):
        return send_from_directory(app.config["V3_STATIC_DIR"], asset_path)

    @app.get("/prototype/")
    def deeplitics_prototype_preview():
        if app.config["APP_ENV"] != "development":
            return jsonify(error="Not found."), 404
        return send_from_directory(app.config["PROTOTYPE_STATIC_DIR"], "index.html")

    @app.get("/")
    def index():
        return jsonify(service="deeplitics-api", api_version="v1")

    @app.errorhandler(413)
    def too_large(_error):
        return jsonify(error="Request body exceeds the configured limit."), 413

    @app.errorhandler(500)
    def internal_error(_error):
        db.session.rollback()
        app.logger.exception("Unhandled API error")
        return jsonify(error="Internal server error."), 500

    @app.after_request
    def secure_api_response(response):
        if request.path.startswith("/api/"):
            if request.path == "/api/v1/stories" and request.method == "GET" and response.status_code == 200:
                response.headers["Cache-Control"] = "public, max-age=300, stale-while-revalidate=600"
            else:
                response.headers["Cache-Control"] = "no-store"
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["Referrer-Policy"] = "no-referrer"
            response.headers["X-Frame-Options"] = "DENY"
        if request.path == "/app" or request.path.startswith("/app/"):
            token_endpoint = urlparse(app.config.get("OIDC_TOKEN_ENDPOINT", ""))
            connect_sources = ["'self'"]
            if token_endpoint.scheme in {"https", "http"} and token_endpoint.netloc:
                connect_sources.append(f"{token_endpoint.scheme}://{token_endpoint.netloc}")
            response.headers["Cache-Control"] = "no-store"
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["Referrer-Policy"] = "no-referrer"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; script-src 'self'; style-src 'self'; "
                "img-src 'self' https: data:; connect-src " + " ".join(connect_sources) + "; "
                "base-uri 'self'; object-src 'none'; frame-ancestors 'none'; form-action 'self'"
            )
            response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        return response

    @app.cli.command("provision-tenant")
    @click.option("--id", "tenant_id", required=True, help="UUID for the new tenant.")
    @click.option("--name", "tenant_name", required=True, help="Company/workspace display name.")
    def provision_tenant(tenant_id: str, tenant_name: str):
        """Create a tenant. This command does not create a user or grant access."""
        try:
            tenant_id = str(uuid.UUID(tenant_id))
        except ValueError as exc:
            raise click.ClickException("--id must be a UUID.") from exc
        if not tenant_name.strip() or len(tenant_name.strip()) > 200:
            raise click.ClickException("--name must contain 1 to 200 characters.")
        db.session.execute(
            text("SELECT set_config('app.current_tenant', :tenant_id, true)"),
            {"tenant_id": tenant_id},
        )
        if db.session.get(Tenant, tenant_id):
            raise click.ClickException("That tenant already exists.")
        encrypted_name = encrypt_text(tenant_id, "tenant-name", tenant_name.strip(), field="name")
        db.session.add(Tenant(
            id=tenant_id,
            name_key_id=encrypted_name.key_id,
            name_nonce=encrypted_name.nonce,
            name_ciphertext=encrypted_name.ciphertext,
        ))
        db.session.commit()
        click.echo(f"Created tenant {tenant_id}.")

    @app.cli.command("provision-member")
    @click.option("--tenant-id", required=True)
    @click.option("--issuer", required=True, help="Exact OIDC issuer URL.")
    @click.option("--subject", required=True, help="OIDC sub claim; do not use email as an identifier.")
    @click.option("--role", type=click.Choice(["owner", "admin", "member"]), default="member")
    def provision_member(tenant_id: str, issuer: str, subject: str, role: str):
        """Grant a verified identity access to one tenant."""
        try:
            tenant_id = str(uuid.UUID(tenant_id))
        except ValueError as exc:
            raise click.ClickException("--tenant-id must be a UUID.") from exc
        issuer = _normalise_issuer(issuer)
        parsed_issuer = urlparse(issuer)
        local_development_issuer = (
            app.config["APP_ENV"] == "development"
            and parsed_issuer.scheme == "http"
            and parsed_issuer.hostname in {"localhost", "127.0.0.1", "::1"}
        )
        if ((parsed_issuer.scheme != "https" and not local_development_issuer)
                or not parsed_issuer.netloc or not subject.strip() or len(subject) > 300):
            raise click.ClickException("Issuer must be HTTPS and subject must be a non-empty OIDC sub.")
        db.session.execute(
            text("SELECT set_config('app.current_tenant', :tenant_id, true)"),
            {"tenant_id": tenant_id},
        )
        if db.session.get(Tenant, tenant_id) is None:
            raise click.ClickException("Tenant does not exist.")
        digest = identity_digest(issuer, subject.strip())
        existing = db.session.execute(select(Membership).where(
            Membership.tenant_id == tenant_id,
            Membership.issuer == issuer,
            Membership.subject_digest == digest,
        )).scalar_one_or_none()
        if existing:
            raise click.ClickException("That identity already has a membership in this tenant.")
        db.session.add(Membership(
            tenant_id=tenant_id,
            issuer=issuer,
            subject_digest=digest,
            role=role,
            active=True,
        ))
        db.session.flush()
        db.session.add(AuditEvent(
            tenant_id=tenant_id,
            actor_membership_id=None,
            action="membership.provisioned",
            resource_id=None,
            request_id=uuid.uuid4().hex,
        ))
        db.session.commit()
        click.echo(f"Granted {role} access in tenant {tenant_id}.")

    @app.cli.command("deactivate-member")
    @click.option("--tenant-id", required=True)
    @click.option("--issuer", required=True)
    @click.option("--subject", required=True)
    def deactivate_member(tenant_id: str, issuer: str, subject: str):
        """Revoke an identity's access to a tenant immediately."""
        try:
            tenant_id = str(uuid.UUID(tenant_id))
        except ValueError as exc:
            raise click.ClickException("--tenant-id must be a UUID.") from exc
        issuer = _normalise_issuer(issuer)
        digest = identity_digest(issuer, subject)
        db.session.execute(
            text("SELECT set_config('app.current_tenant', :tenant_id, true)"),
            {"tenant_id": tenant_id},
        )
        membership = db.session.execute(select(Membership).where(
            Membership.tenant_id == tenant_id,
            Membership.issuer == issuer,
            Membership.subject_digest == digest,
            Membership.active.is_(True),
        )).scalar_one_or_none()
        if membership is None:
            raise click.ClickException("No active membership found.")
        db.session.execute(
            text("SELECT set_config('app.current_membership', :membership_id, true)"),
            {"membership_id": membership.id},
        )
        preference = db.session.get(MemberPreference, membership.id)
        if preference is not None:
            db.session.delete(preference)
        membership.active = False
        db.session.add(AuditEvent(
            tenant_id=tenant_id,
            actor_membership_id=None,
            action="membership.deactivated",
            resource_id=membership.id,
            request_id=uuid.uuid4().hex,
        ))
        db.session.commit()
        click.echo(f"Deactivated membership in tenant {tenant_id}.")

    return app


app = create_app()
