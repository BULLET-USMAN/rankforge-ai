"""001_initial_schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-11-08 18:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. profiles
    op.create_table(
        'profiles',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('full_name', sa.String(255), nullable=True),
        sa.Column('avatar_url', sa.String(1024), nullable=True),
        sa.Column('role', sa.String(50), nullable=False, server_default='member'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_profiles_email', 'profiles', ['email'])

    # 2. organizations
    op.create_table(
        'organizations',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(100), nullable=False, unique=True),
        sa.Column('plan_tier', sa.String(50), nullable=False, server_default='starter'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_organizations_slug', 'organizations', ['slug'])

    # 3. organization_members
    op.create_table(
        'organization_members',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('organization_id', sa.String(36), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('profiles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role', sa.String(50), nullable=False, server_default='member'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('organization_id', 'user_id', name='uq_org_member'),
    )
    op.create_index('ix_organization_members_org_id', 'organization_members', ['organization_id'])
    op.create_index('ix_organization_members_user_id', 'organization_members', ['user_id'])

    # 4. website_projects
    op.create_table(
        'website_projects',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('organization_id', sa.String(36), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('domain', sa.String(255), nullable=False),
        sa.Column('primary_url', sa.String(1024), nullable=False),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('verification_token', sa.String(128), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('organization_id', 'domain', name='uq_org_domain'),
    )
    op.create_index('ix_website_projects_org_id', 'website_projects', ['organization_id'])
    op.create_index('ix_website_projects_domain', 'website_projects', ['domain'])

    # 5. website_verifications
    op.create_table(
        'website_verifications',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('project_id', sa.String(36), sa.ForeignKey('website_projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('method', sa.String(50), nullable=False),
        sa.Column('token', sa.String(128), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_website_verifications_project_id', 'website_verifications', ['project_id'])

    # 6. audit_jobs
    op.create_table(
        'audit_jobs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('project_id', sa.String(36), sa.ForeignKey('website_projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('organization_id', sa.String(36), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('job_type', sa.String(50), nullable=False, server_default='preflight'),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('celery_task_id', sa.String(128), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.String(1024), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_audit_jobs_project_id', 'audit_jobs', ['project_id'])
    op.create_index('ix_audit_jobs_status', 'audit_jobs', ['status'])

    # 7. audit_results
    op.create_table(
        'audit_results',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('job_id', sa.String(36), sa.ForeignKey('audit_jobs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('project_id', sa.String(36), sa.ForeignKey('website_projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('url', sa.String(1024), nullable=False),
        sa.Column('status_code', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('response_time_ms', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('headers_json', sa.JSON(), nullable=False),
        sa.Column('ssl_info_json', sa.JSON(), nullable=False),
        sa.Column('robots_txt_found', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('sitemap_found', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('issues_json', sa.JSON(), nullable=False),
        sa.Column('score', sa.Integer(), nullable=False, server_default='100'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_audit_results_job_id', 'audit_results', ['job_id'])
    op.create_index('ix_audit_results_project_id', 'audit_results', ['project_id'])

    # 8. seo_recommendations
    op.create_table(
        'seo_recommendations',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('project_id', sa.String(36), sa.ForeignKey('website_projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('audit_result_id', sa.String(36), sa.ForeignKey('audit_results.id', ondelete='SET NULL'), nullable=True),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('severity', sa.String(50), nullable=False, server_default='warning'),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('suggested_fix', sa.Text(), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='open'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_seo_recommendations_project_id', 'seo_recommendations', ['project_id'])

    # 9. subscriptions
    op.create_table(
        'subscriptions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('organization_id', sa.String(36), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('stripe_customer_id', sa.String(128), nullable=True),
        sa.Column('stripe_subscription_id', sa.String(128), nullable=True),
        sa.Column('plan', sa.String(50), nullable=False, server_default='starter'),
        sa.Column('status', sa.String(50), nullable=False, server_default='active'),
        sa.Column('current_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_subscriptions_org_id', 'subscriptions', ['organization_id'])

    # 10. usage_events
    op.create_table(
        'usage_events',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('organization_id', sa.String(36), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('count', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('metadata_json', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_usage_events_org_id', 'usage_events', ['organization_id'])
    op.create_index('ix_usage_events_event_type', 'usage_events', ['event_type'])

    # 11. activity_logs
    op.create_table(
        'activity_logs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('organization_id', sa.String(36), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('profiles.id', ondelete='SET NULL'), nullable=True),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('entity_type', sa.String(100), nullable=False),
        sa.Column('entity_id', sa.String(36), nullable=True),
        sa.Column('details_json', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_activity_logs_org_id', 'activity_logs', ['organization_id'])


def downgrade() -> None:
    op.drop_table('activity_logs')
    op.drop_table('usage_events')
    op.drop_table('subscriptions')
    op.drop_table('seo_recommendations')
    op.drop_table('audit_results')
    op.drop_table('audit_jobs')
    op.drop_table('website_verifications')
    op.drop_table('website_projects')
    op.drop_table('organization_members')
    op.drop_table('organizations')
    op.drop_table('profiles')
