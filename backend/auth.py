from __future__ import annotations

from functools import wraps
from urllib.parse import urlparse
import uuid

import jwt
from flask import current_app, g, jsonify, request
from jwt import PyJWKClient
from sqlalchemy import select, text

from backend.extensions import db
from backend.identity import identity_digest
from backend.models import Membership


def _unauthorized(message: str = "Authentication required.", status: int = 401):
    response = jsonify(error=message)
    response.status_code = status
    if status == 401:
        response.headers["WWW-Authenticate"] = 'Bearer realm="deeplitics-api"'
    return response


def _decode_token(token: str) -> dict:
    issuer = current_app.config.get("OIDC_ISSUER", "")
    audience = current_app.config.get("OIDC_AUDIENCE", "")
    jwks_url = current_app.config.get("OIDC_JWKS_URL", "")
    if not issuer or not audience or not jwks_url:
        raise RuntimeError("OIDC is not configured.")
    parsed = urlparse(jwks_url)
    if parsed.scheme != "https" or not parsed.netloc:
        raise RuntimeError("OIDC JWKS URL must use HTTPS.")
    client = current_app.extensions.get("deeplitics_jwks_client")
    if client is None:
        client = PyJWKClient(jwks_url, cache_jwk_set=True, timeout=5)
        current_app.extensions["deeplitics_jwks_client"] = client
    signing_key = client.get_signing_key_from_jwt(token)
    return jwt.decode(
        token,
        signing_key.key,
        algorithms=["RS256"],
        audience=audience,
        issuer=issuer,
        options={"require": ["exp", "iat", "sub", "iss", "aud"]},
    )


def require_tenant(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        authorization = request.headers.get("Authorization", "")
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() != "bearer" or not token.strip():
            return _unauthorized()
        try:
            claims = _decode_token(token.strip())
        except RuntimeError:
            current_app.logger.error("OIDC authentication is not configured")
            return _unauthorized("Authentication service is not configured.", 503)
        except Exception:
            return _unauthorized("Invalid or expired access token.")

        tenant_id = request.headers.get("X-Tenant-ID", "")
        issuer = claims.get("iss", "")
        subject = claims.get("sub")
        if not tenant_id or not subject:
            return _unauthorized("A tenant membership is required.", 403)
        try:
            tenant_id = str(uuid.UUID(tenant_id))
        except ValueError:
            return _unauthorized("A valid tenant UUID is required.", 403)
        try:
            subject_digest = identity_digest(issuer, subject)
        except RuntimeError:
            current_app.logger.error("Identity lookup key is not configured")
            return _unauthorized("Authentication service is not configured.", 503)

        # Establish the transaction-local tenant before reading membership
        # metadata. RLS on memberships prevents cross-tenant enumeration.
        if db.engine.dialect.name == "postgresql":
            db.session.execute(
                text("SELECT set_config('app.current_tenant', :tenant_id, true)"),
                {"tenant_id": tenant_id},
            )
        membership = db.session.execute(
            select(Membership).where(
                Membership.tenant_id == tenant_id,
                Membership.issuer == issuer,
                Membership.subject_digest == subject_digest,
                Membership.active.is_(True),
            )
        ).scalar_one_or_none()
        if membership is None:
            db.session.rollback()
            return _unauthorized("You are not an active member of this workspace.", 403)

        # Personal preferences are visible only inside this exact membership.
        if db.engine.dialect.name == "postgresql":
            db.session.execute(
                text("SELECT set_config('app.current_membership', :membership_id, true)"),
                {"membership_id": membership.id},
            )

        g.identity = {"issuer": issuer, "subject": subject}
        g.membership = membership
        g.tenant_id = tenant_id
        g.request_id = uuid.uuid4().hex
        return view(*args, **kwargs)

    return wrapped


def require_role(*roles: str):
    def decorator(view):
        @wraps(view)
        @require_tenant
        def wrapped(*args, **kwargs):
            if g.membership.role not in roles:
                return jsonify(error="Insufficient workspace role."), 403
            return view(*args, **kwargs)

        return wrapped

    return decorator
