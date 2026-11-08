"""002_phase_2_auth_workspaces

Revision ID: 002_phase_2_auth_workspaces
Revises: 001_initial_schema
Create Date: 2026-11-08 19:15:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '002_phase_2_auth_workspaces'
down_revision: Union[str, None] = '001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Update profiles: add display_name
    op.add_column('profiles', sa.Column('display_name', sa.String(255), nullable=True))

    # 2. Update organizations: add created_by
    op.add_column('organizations', sa.Column('created_by', sa.String(36), sa.ForeignKey('profiles.id', ondelete='SET NULL'), nullable=True))

    # 2b. Update organization_members: add invited_by
    op.add_column('organization_members', sa.Column('invited_by', sa.String(36), sa.ForeignKey('profiles.id', ondelete='SET NULL'), nullable=True))

    # 3. Create organization_invitations table
    op.create_table(
        'organization_invitations',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('organization_id', sa.String(36), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('invited_email', sa.String(255), nullable=False),
        sa.Column('invited_role', sa.String(50), nullable=False, server_default='viewer'),
        sa.Column('invited_by', sa.String(36), sa.ForeignKey('profiles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('token_hash', sa.String(64), nullable=False, unique=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('accepted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_organization_invitations_org_id', 'organization_invitations', ['organization_id'])
    op.create_index('ix_organization_invitations_email', 'organization_invitations', ['invited_email'])
    op.create_index('ix_organization_invitations_token_hash', 'organization_invitations', ['token_hash'])

    # 4. Update website_projects: add description, created_by, verification_status, archived_at
    op.add_column('website_projects', sa.Column('description', sa.Text(), nullable=True))
    op.add_column('website_projects', sa.Column('created_by', sa.String(36), sa.ForeignKey('profiles.id', ondelete='SET NULL'), nullable=True))
    op.add_column('website_projects', sa.Column('verification_status', sa.String(50), nullable=False, server_default='pending'))
    op.add_column('website_projects', sa.Column('archived_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('website_projects', 'archived_at')
    op.drop_column('website_projects', 'verification_status')
    op.drop_column('website_projects', 'created_by')
    op.drop_column('website_projects', 'description')
    op.drop_table('organization_invitations')
    op.drop_column('organization_members', 'invited_by')
    op.drop_column('organizations', 'created_by')
    op.drop_column('profiles', 'display_name')
