from __future__ import annotations

from datetime import datetime, timezone
import uuid

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, LargeBinary, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.extensions import db


def new_id() -> str:
    return str(uuid.uuid4())


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Tenant(db.Model):
    __tablename__ = "tenants"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    name_key_id: Mapped[str] = mapped_column(String(100), nullable=False)
    name_nonce: Mapped[bytes] = mapped_column(LargeBinary(12), nullable=False)
    name_ciphertext: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow, server_default=func.now())


class Membership(db.Model):
    __tablename__ = "tenant_memberships"
    __table_args__ = (
        UniqueConstraint("tenant_id", "issuer", "subject_digest", name="uq_membership_tenant_issuer_subject"),
        CheckConstraint("role IN ('owner', 'admin', 'member')", name="ck_membership_role"),
        Index("ix_membership_identity", "issuer", "subject_digest", "tenant_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    issuer: Mapped[str] = mapped_column(String(500), nullable=False)
    subject_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    role: Mapped[str] = mapped_column(String(16), nullable=False, default="member")
    active: Mapped[bool] = mapped_column(nullable=False, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow, server_default=func.now())


class WorkspaceItem(db.Model):
    __tablename__ = "workspace_items"
    __table_args__ = (
        Index("ix_workspace_items_tenant_created", "tenant_id", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    created_by_membership_id: Mapped[str] = mapped_column(
        ForeignKey("tenant_memberships.id", ondelete="SET NULL"), nullable=True
    )
    title_key_id: Mapped[str] = mapped_column(String(100), nullable=False)
    title_nonce: Mapped[bytes] = mapped_column(LargeBinary(12), nullable=False)
    title_ciphertext: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    content_key_id: Mapped[str] = mapped_column(String(100), nullable=False)
    content_nonce: Mapped[bytes] = mapped_column(LargeBinary(12), nullable=False)
    content_ciphertext: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow, server_default=func.now())


class AuditEvent(db.Model):
    __tablename__ = "audit_events"
    __table_args__ = (Index("ix_audit_events_tenant_created", "tenant_id", "created_at"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    actor_membership_id: Mapped[str | None] = mapped_column(
        ForeignKey("tenant_memberships.id", ondelete="SET NULL"), nullable=True
    )
    action: Mapped[str] = mapped_column(String(80), nullable=False)
    resource_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    request_id: Mapped[str] = mapped_column(String(36), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow, server_default=func.now())


class MemberPreference(db.Model):
    """Encrypted, per-membership settings; never shared with other tenant users."""

    __tablename__ = "member_preferences"
    __table_args__ = (Index("ix_member_preferences_tenant_updated", "tenant_id", "updated_at"),)

    membership_id: Mapped[str] = mapped_column(
        ForeignKey("tenant_memberships.id", ondelete="CASCADE"), primary_key=True
    )
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    key_id: Mapped[str] = mapped_column(String(100), nullable=False)
    nonce: Mapped[bytes] = mapped_column(LargeBinary(12), nullable=False)
    ciphertext: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow, server_default=func.now()
    )
