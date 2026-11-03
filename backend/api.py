from __future__ import annotations

import json
import re
import uuid
from pathlib import Path

from flask import Blueprint, current_app, g, jsonify, request
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy import select, text

from backend.auth import _decode_token, require_role, require_tenant
from backend.crypto import EncryptionConfigurationError, EncryptedValue, decrypt_text, encrypt_text
from backend.extensions import db
from backend.identity import identity_digest
from backend.models import AuditEvent, MemberPreference, Membership, Tenant, WorkspaceItem, new_id, utcnow

api = Blueprint("api_v1", __name__, url_prefix="/api/v1")
_PREFERENCE_TOPICS = {"security", "diplomacy", "trade", "rights", "conflict", "surveillance"}
_DEFAULT_PREFERENCES = {"saved_story_ids": [], "topics": []}


def _audit(action: str, resource_id: str | None = None) -> None:
    db.session.add(AuditEvent(
        tenant_id=g.tenant_id,
        actor_membership_id=g.membership.id,
        action=action,
        resource_id=resource_id,
        request_id=g.request_id,
    ))


def _decrypt(item: WorkspaceItem) -> str:
    return decrypt_text(
        item.tenant_id,
        item.id,
        EncryptedValue(item.content_key_id, item.content_nonce, item.content_ciphertext),
    )


@api.get("/health")
def health():
    try:
        db.session.execute(select(1))
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Database health check failed")
        return jsonify(status="unavailable"), 503
    return jsonify(status="ok")


@api.get("/public-config")
def public_config():
    """Expose only browser-safe OIDC client settings; never return a client secret."""
    client_fields = (
        "OIDC_CLIENT_ID",
        "OIDC_AUTHORIZATION_ENDPOINT",
        "OIDC_TOKEN_ENDPOINT",
        "OIDC_REDIRECT_URI",
    )
    auth_enabled = all(current_app.config.get(key) for key in client_fields) and all(
        current_app.config.get(key) for key in ("OIDC_ISSUER", "OIDC_AUDIENCE", "OIDC_JWKS_URL")
    )
    config = {
        "auth_enabled": auth_enabled,
        "default_tenant_id": current_app.config.get("DEFAULT_TENANT_ID") or None,
        "signup_enabled": bool(current_app.config.get("STAGING_SIGNUP_ENABLED")),
        "environment": "staging" if current_app.config.get("STAGING_SIGNUP_ENABLED") else current_app.config.get("APP_ENV"),
    }
    if auth_enabled:
        config["oidc"] = {
            "client_id": current_app.config["OIDC_CLIENT_ID"],
            "authorization_endpoint": current_app.config["OIDC_AUTHORIZATION_ENDPOINT"],
            "token_endpoint": current_app.config["OIDC_TOKEN_ENDPOINT"],
            "redirect_uri": current_app.config["OIDC_REDIRECT_URI"],
            "issuer": current_app.config["OIDC_ISSUER"],
            "audience": current_app.config["OIDC_AUDIENCE"],
        }
    return jsonify(config)


@api.post("/staging-signup")
def staging_signup():
    """Create a member only in the disposable, loopback-only development workspace."""
    if (current_app.config.get("APP_ENV") != "development"
            or not current_app.config.get("STAGING_SIGNUP_ENABLED")
            or request.remote_addr not in {"127.0.0.1", "::1"}):
        return jsonify(error="Not found."), 404

    authorization = request.headers.get("Authorization", "")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        return jsonify(error="Authentication required."), 401
    try:
        claims = _decode_token(token.strip())
    except RuntimeError:
        return jsonify(error="Authentication service is not configured."), 503
    except Exception:
        return jsonify(error="Invalid or expired access token."), 401

    tenant_id = current_app.config.get("DEFAULT_TENANT_ID")
    issuer = claims.get("iss", "")
    subject = claims.get("sub")
    if (not tenant_id or request.headers.get("X-Tenant-ID") != tenant_id
            or not issuer or not subject):
        return jsonify(error="A valid staging workspace and identity are required."), 403

    try:
        subject_digest = identity_digest(issuer, subject)
    except RuntimeError:
        return jsonify(error="Authentication service is not configured."), 503

    if db.engine.dialect.name == "postgresql":
        db.session.execute(
            text("SELECT set_config('app.current_tenant', :tenant_id, true)"),
            {"tenant_id": tenant_id},
        )
    if db.session.get(Tenant, tenant_id) is None:
        db.session.rollback()
        return jsonify(error="The staging workspace is not initialized."), 503

    existing = db.session.execute(select(Membership).where(
        Membership.tenant_id == tenant_id,
        Membership.issuer == issuer,
        Membership.subject_digest == subject_digest,
    )).scalar_one_or_none()
    if existing:
        active = existing.active
        db.session.rollback()
        if active:
            return jsonify(status="already-active"), 200
        return jsonify(error="This identity is not an active member of the staging workspace."), 403

    membership = Membership(
        tenant_id=tenant_id,
        issuer=issuer,
        subject_digest=subject_digest,
        role="member",
        active=True,
    )
    db.session.add(membership)
    db.session.flush()
    db.session.add(AuditEvent(
        tenant_id=tenant_id,
        actor_membership_id=membership.id,
        action="membership.staging_self_registered",
        resource_id=None,
        request_id=uuid.uuid4().hex,
    ))
    db.session.commit()
    return jsonify(status="created"), 201


@api.get("/stories")
def list_stories():
    """Serve the published story snapshot; this material is public, not tenant data."""
    path = Path(current_app.config["STORIES_PATH"])
    try:
        with path.open("r", encoding="utf-8") as story_file:
            payload = json.load(story_file)
        if (current_app.config.get("APP_ENV") == "development"
                and isinstance(payload, dict)
                and payload.get("environment") == "staging"):
            stories = payload.get("stories")
        else:
            stories = payload
        if not isinstance(stories, list) or any(not isinstance(story, dict) for story in stories):
            raise ValueError("Story snapshot must be a JSON array.")
    except (OSError, ValueError, json.JSONDecodeError):
        current_app.logger.exception("Published story snapshot could not be read")
        return jsonify(error="Stories are temporarily unavailable."), 503
    public_stories = [{key: value for key, value in story.items() if key != "_pipeline_meta"} for story in stories]
    response = jsonify(stories=public_stories)
    response.headers["Cache-Control"] = "public, max-age=300, stale-while-revalidate=600"
    return response


@api.get("/me")
@require_tenant
def me():
    tenant = db.session.get(Tenant, g.tenant_id)
    if tenant is None:
        return jsonify(error="Workspace not found."), 404
    try:
        tenant_name = decrypt_text(
            tenant.id, "tenant-name",
            EncryptedValue(tenant.name_key_id, tenant.name_nonce, tenant.name_ciphertext),
            field="name",
        )
    except Exception:
        current_app.logger.exception("Workspace name decryption failed")
        return jsonify(error="Workspace is unavailable."), 503
    return jsonify(
        user={"role": g.membership.role},
        workspace={"id": tenant.id, "name": tenant_name},
    )


def _normalise_preferences(payload: object) -> dict | None:
    if not isinstance(payload, dict) or set(payload) - {"saved_story_ids", "topics"}:
        return None

    saved_ids = payload.get("saved_story_ids", [])
    topics = payload.get("topics", [])
    if not isinstance(saved_ids, list) or len(saved_ids) > 500:
        return None
    if any(not isinstance(item, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", item) for item in saved_ids):
        return None
    if not isinstance(topics, list) or len(topics) > len(_PREFERENCE_TOPICS):
        return None
    if any(not isinstance(topic, str) or topic not in _PREFERENCE_TOPICS for topic in topics):
        return None
    return {
        "saved_story_ids": list(dict.fromkeys(saved_ids)),
        "topics": sorted(set(topics)),
    }


@api.get("/me/preferences")
@require_tenant
def get_preferences():
    preference = db.session.execute(
        select(MemberPreference).where(
            MemberPreference.tenant_id == g.tenant_id,
            MemberPreference.membership_id == g.membership.id,
        )
    ).scalar_one_or_none()
    if preference is None:
        return jsonify(preferences=_DEFAULT_PREFERENCES)
    try:
        raw = decrypt_text(
            preference.tenant_id,
            preference.membership_id,
            EncryptedValue(preference.key_id, preference.nonce, preference.ciphertext),
            field="member-preferences",
        )
        preferences = _normalise_preferences(json.loads(raw))
        if preferences is None:
            raise ValueError("Stored preference document has an unsupported shape.")
    except Exception:
        current_app.logger.exception("Member preferences could not be decrypted")
        return jsonify(error="Preferences are temporarily unavailable."), 503
    return jsonify(preferences=preferences)


@api.put("/me/preferences")
@require_tenant
def save_preferences():
    payload = request.get_json(silent=True)
    preferences = _normalise_preferences(payload)
    if preferences is None:
        return jsonify(error="Preferences contain unsupported or oversized values."), 400
    serialized = json.dumps(preferences, ensure_ascii=False, separators=(",", ":"))
    if len(serialized.encode("utf-8")) > 64_000:
        return jsonify(error="Preferences exceed the configured size limit."), 413
    try:
        encrypted = encrypt_text(
            g.tenant_id,
            g.membership.id,
            serialized,
            field="member-preferences",
        )
    except EncryptionConfigurationError:
        current_app.logger.exception("Preference encryption is not configured")
        return jsonify(error="Preference storage is not configured."), 503

    statement = pg_insert(MemberPreference).values(
        membership_id=g.membership.id,
        tenant_id=g.tenant_id,
        key_id=encrypted.key_id,
        nonce=encrypted.nonce,
        ciphertext=encrypted.ciphertext,
        updated_at=utcnow(),
    )
    statement = statement.on_conflict_do_update(
        index_elements=[MemberPreference.membership_id],
        set_={
            "tenant_id": g.tenant_id,
            "key_id": encrypted.key_id,
            "nonce": encrypted.nonce,
            "ciphertext": encrypted.ciphertext,
            "updated_at": utcnow(),
        },
    )
    db.session.execute(statement)
    db.session.commit()
    return jsonify(preferences=preferences)


@api.delete("/me/preferences")
@require_tenant
def delete_preferences():
    preference = db.session.execute(
        select(MemberPreference).where(
            MemberPreference.tenant_id == g.tenant_id,
            MemberPreference.membership_id == g.membership.id,
        )
    ).scalar_one_or_none()
    if preference is not None:
        db.session.delete(preference)
        db.session.commit()
    return "", 204


@api.get("/workspace-items")
@require_tenant
def list_items():
    try:
        limit = min(max(int(request.args.get("limit", "25")), 1), 50)
        offset = min(max(int(request.args.get("offset", "0")), 0), 5000)
    except ValueError:
        return jsonify(error="limit and offset must be integers."), 400
    items = db.session.execute(
        select(WorkspaceItem)
        .where(WorkspaceItem.tenant_id == g.tenant_id)
        .order_by(WorkspaceItem.created_at.desc(), WorkspaceItem.id)
        .limit(limit)
        .offset(offset)
    ).scalars()
    try:
        result = [{
            "id": item.id,
            "title": decrypt_text(
                item.tenant_id, item.id,
                EncryptedValue(item.title_key_id, item.title_nonce, item.title_ciphertext),
                field="title",
            ),
            "created_at": item.created_at.isoformat(),
            "updated_at": item.updated_at.isoformat(),
        } for item in items]
    except Exception:
        current_app.logger.exception("Workspace item title decryption failed")
        return jsonify(error="Workspace items are unavailable."), 503
    return jsonify(items=result, limit=limit, offset=offset)


@api.post("/workspace-items")
@require_tenant
def create_item():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify(error="Expected a JSON object."), 400
    title = payload.get("title")
    content = payload.get("content")
    if not isinstance(title, str) or not title.strip() or len(title.strip()) > 200:
        return jsonify(error="title must contain 1 to 200 characters."), 400
    if not isinstance(content, str) or len(content) > current_app.config["MAX_ITEM_CHARS"]:
        return jsonify(error="content must be text within the configured size limit."), 400
    item_id = new_id()
    try:
        encrypted_title = encrypt_text(g.tenant_id, item_id, title.strip(), field="title")
        encrypted = encrypt_text(g.tenant_id, item_id, content)
    except EncryptionConfigurationError:
        current_app.logger.exception("Workspace encryption is not configured")
        return jsonify(error="Workspace storage is not configured."), 503
    item = WorkspaceItem(
        id=item_id,
        tenant_id=g.tenant_id,
        created_by_membership_id=g.membership.id,
        title_key_id=encrypted_title.key_id,
        title_nonce=encrypted_title.nonce,
        title_ciphertext=encrypted_title.ciphertext,
        content_key_id=encrypted.key_id,
        content_nonce=encrypted.nonce,
        content_ciphertext=encrypted.ciphertext,
    )
    db.session.add(item)
    _audit("workspace_item.created", item.id)
    db.session.commit()
    return jsonify(id=item.id, title=title.strip(), created_at=item.created_at.isoformat()), 201


@api.get("/workspace-items/<item_id>")
@require_tenant
def get_item(item_id: str):
    item = db.session.execute(select(WorkspaceItem).where(
        WorkspaceItem.id == item_id,
        WorkspaceItem.tenant_id == g.tenant_id,
    )).scalar_one_or_none()
    if item is None:
        return jsonify(error="Workspace item not found."), 404
    try:
        content = _decrypt(item)
        title = decrypt_text(
            item.tenant_id, item.id,
            EncryptedValue(item.title_key_id, item.title_nonce, item.title_ciphertext),
            field="title",
        )
    except Exception:
        current_app.logger.exception("Workspace item decryption failed")
        return jsonify(error="Workspace item is unavailable."), 503
    return jsonify(id=item.id, title=title, content=content,
                   created_at=item.created_at.isoformat(), updated_at=item.updated_at.isoformat())


@api.delete("/workspace-items/<item_id>")
@require_tenant
def delete_item(item_id: str):
    item = db.session.execute(select(WorkspaceItem).where(
        WorkspaceItem.id == item_id,
        WorkspaceItem.tenant_id == g.tenant_id,
    )).scalar_one_or_none()
    if item is None:
        return jsonify(error="Workspace item not found."), 404
    _audit("workspace_item.deleted", item.id)
    db.session.delete(item)
    db.session.commit()
    return "", 204


@api.get("/admin/audit-events")
@require_role("owner", "admin")
def list_audit_events():
    try:
        limit = min(max(int(request.args.get("limit", "50")), 1), 100)
    except ValueError:
        return jsonify(error="limit must be an integer."), 400
    events = db.session.execute(
        select(AuditEvent)
        .where(AuditEvent.tenant_id == g.tenant_id)
        .order_by(AuditEvent.created_at.desc())
        .limit(limit)
    ).scalars()
    return jsonify(events=[{
        "id": event.id,
        "action": event.action,
        "resource_id": event.resource_id,
        "created_at": event.created_at.isoformat(),
    } for event in events])
