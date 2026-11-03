"""Add encrypted preferences scoped to one tenant membership."""

from alembic import op
import sqlalchemy as sa

revision = "0002_member_preferences"
down_revision = "0001_tenant_safe_backend"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "member_preferences",
        sa.Column(
            "membership_id",
            sa.String(36),
            sa.ForeignKey("tenant_memberships.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "tenant_id",
            sa.String(36),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("key_id", sa.String(100), nullable=False),
        sa.Column("nonce", sa.LargeBinary(12), nullable=False),
        sa.Column("ciphertext", sa.LargeBinary(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(
        "ix_member_preferences_tenant_updated",
        "member_preferences",
        ["tenant_id", "updated_at"],
    )
    op.execute(sa.text("ALTER TABLE member_preferences ENABLE ROW LEVEL SECURITY"))
    op.execute(sa.text("ALTER TABLE member_preferences FORCE ROW LEVEL SECURITY"))
    op.execute(sa.text(
        "CREATE POLICY membership_isolation ON member_preferences "
        "USING (tenant_id = current_setting('app.current_tenant', true) "
        "AND membership_id = current_setting('app.current_membership', true)) "
        "WITH CHECK (tenant_id = current_setting('app.current_tenant', true) "
        "AND membership_id = current_setting('app.current_membership', true))"
    ))


def downgrade():
    op.execute(sa.text("DROP POLICY IF EXISTS membership_isolation ON member_preferences"))
    op.drop_index("ix_member_preferences_tenant_updated", table_name="member_preferences")
    op.drop_table("member_preferences")
