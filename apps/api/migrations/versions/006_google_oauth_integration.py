"""006_google_oauth_integration

Revision ID: 006_google_oauth_integration
Revises: 005_phase_5_ai_engine
Create Date: 2026-11-09 13:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "006_google_oauth_integration"
down_revision: Union[str, None] = "005_phase_5_ai_engine"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "google_integrations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "organization_id",
            sa.String(36),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "website_project_id",
            sa.String(36),
            sa.ForeignKey("website_projects.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("google_account_email", sa.String(255), nullable=True),
        sa.Column("access_token_encrypted", sa.Text(), nullable=False),
        sa.Column("refresh_token_encrypted", sa.Text(), nullable=True),
        sa.Column("token_type", sa.String(32), nullable=False, server_default="Bearer"),
        sa.Column(
            "scopes_json",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
            server_default="[]",
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column(
            "created_by",
            sa.String(36),
            sa.ForeignKey("profiles.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "organization_id", "website_project_id", name="uq_org_project_google"
        ),
    )
    op.create_index(
        "ix_google_integrations_org_id", "google_integrations", ["organization_id"]
    )
    op.create_index(
        "ix_google_integrations_project_id",
        "google_integrations",
        ["website_project_id"],
    )
    op.create_index(
        "ix_google_integrations_is_active", "google_integrations", ["is_active"]
    )


def downgrade() -> None:
    op.drop_index(
        "ix_google_integrations_is_active", table_name="google_integrations"
    )
    op.drop_index(
        "ix_google_integrations_project_id", table_name="google_integrations"
    )
    op.drop_index(
        "ix_google_integrations_org_id", table_name="google_integrations"
    )
    op.drop_table("google_integrations")
