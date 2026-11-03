"""Create the tenant-aware API schema and enable row-level security."""

from alembic import op
import sqlalchemy as sa

revision = "0001_tenant_safe_backend"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "tenants",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name_key_id", sa.String(100), nullable=False),
        sa.Column("name_nonce", sa.LargeBinary(12), nullable=False),
        sa.Column("name_ciphertext", sa.LargeBinary(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "tenant_memberships",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("issuer", sa.String(500), nullable=False),
        sa.Column("subject_digest", sa.String(64), nullable=False),
        sa.Column("role", sa.String(16), nullable=False, server_default="member"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "issuer", "subject_digest", name="uq_membership_tenant_issuer_subject"),
        sa.CheckConstraint("role IN ('owner', 'admin', 'member')", name="ck_membership_role"),
    )
    op.create_index("ix_membership_identity", "tenant_memberships", ["issuer", "subject_digest", "tenant_id"])

    op.create_table(
        "workspace_items",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_by_membership_id", sa.String(36), sa.ForeignKey("tenant_memberships.id", ondelete="SET NULL"), nullable=True),
        sa.Column("title_key_id", sa.String(100), nullable=False),
        sa.Column("title_nonce", sa.LargeBinary(12), nullable=False),
        sa.Column("title_ciphertext", sa.LargeBinary(), nullable=False),
        sa.Column("content_key_id", sa.String(100), nullable=False),
        sa.Column("content_nonce", sa.LargeBinary(12), nullable=False),
        sa.Column("content_ciphertext", sa.LargeBinary(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_workspace_items_tenant_created", "workspace_items", ["tenant_id", "created_at"])

    op.create_table(
        "audit_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("actor_membership_id", sa.String(36), sa.ForeignKey("tenant_memberships.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action", sa.String(80), nullable=False),
        sa.Column("resource_id", sa.String(36), nullable=True),
        sa.Column("request_id", sa.String(36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_audit_events_tenant_created", "audit_events", ["tenant_id", "created_at"])

    # Fail closed if application code forgets its tenant filter. The runtime
    # DB role must not be a superuser or BYPASSRLS role.
    tenant_scoped_tables = {
        "tenants": "id",
        "tenant_memberships": "tenant_id",
        "workspace_items": "tenant_id",
        "audit_events": "tenant_id",
    }
    for table, tenant_column in tenant_scoped_tables.items():
        op.execute(sa.text(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY"))
        op.execute(sa.text(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY"))
        op.execute(sa.text(
            f"CREATE POLICY tenant_isolation ON {table} "
            f"USING ({tenant_column} = current_setting('app.current_tenant', true)) "
            f"WITH CHECK ({tenant_column} = current_setting('app.current_tenant', true))"
        ))


def downgrade():
    for table in ("tenants", "tenant_memberships", "workspace_items", "audit_events"):
        op.execute(sa.text(f"DROP POLICY IF EXISTS tenant_isolation ON {table}"))
    op.drop_index("ix_audit_events_tenant_created", table_name="audit_events")
    op.drop_table("audit_events")
    op.drop_index("ix_workspace_items_tenant_created", table_name="workspace_items")
    op.drop_table("workspace_items")
    op.drop_index("ix_membership_identity", table_name="tenant_memberships")
    op.drop_table("tenant_memberships")
    op.drop_table("tenants")
