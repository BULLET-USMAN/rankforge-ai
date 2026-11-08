"""005_phase_5_ai_engine

Revision ID: 005_phase_5_ai_engine
Revises: 004_phase_4_audit_engine
Create Date: 2026-11-08 22:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '005_phase_5_ai_engine'
down_revision: Union[str, None] = '004_phase_4_audit_engine'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create ai_generation_jobs table
    op.create_table(
        'ai_generation_jobs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('organization_id', sa.String(36), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('website_project_id', sa.String(36), sa.ForeignKey('website_projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('audit_run_id', sa.String(36), sa.ForeignKey('seo_audit_runs.id', ondelete='SET NULL'), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='queued'),
        sa.Column('celery_task_id', sa.String(128), nullable=True),
        sa.Column('recommendation_types', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('total_items', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('completed_items', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('failed_items', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_by', sa.String(36), sa.ForeignKey('profiles.id', ondelete='SET NULL'), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_ai_generation_jobs_org_id', 'ai_generation_jobs', ['organization_id'])
    op.create_index('ix_ai_generation_jobs_website_id', 'ai_generation_jobs', ['website_project_id'])
    op.create_index('ix_ai_generation_jobs_audit_id', 'ai_generation_jobs', ['audit_run_id'])
    op.create_index('ix_ai_generation_jobs_status', 'ai_generation_jobs', ['status'])
    op.create_index('ix_ai_generation_jobs_celery', 'ai_generation_jobs', ['celery_task_id'])

    # 2. Create ai_recommendations table
    op.create_table(
        'ai_recommendations',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('organization_id', sa.String(36), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('website_project_id', sa.String(36), sa.ForeignKey('website_projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('audit_run_id', sa.String(36), sa.ForeignKey('seo_audit_runs.id', ondelete='SET NULL'), nullable=True),
        sa.Column('source_crawl_id', sa.String(36), sa.ForeignKey('crawl_jobs.id', ondelete='SET NULL'), nullable=True),
        sa.Column('source_finding_id', sa.String(36), sa.ForeignKey('seo_audit_findings.id', ondelete='SET NULL'), nullable=True),
        sa.Column('job_id', sa.String(36), sa.ForeignKey('ai_generation_jobs.id', ondelete='SET NULL'), nullable=True),
        sa.Column('page_url', sa.String(2048), nullable=False),
        sa.Column('recommendation_type', sa.String(64), nullable=False),
        sa.Column('status', sa.String(32), nullable=False, server_default='needs_review'),
        sa.Column('priority', sa.String(16), nullable=False, server_default='medium'),
        sa.Column('current_value', sa.Text(), nullable=True),
        sa.Column('suggested_value', sa.Text(), nullable=False),
        sa.Column('explanation', sa.Text(), nullable=False),
        sa.Column('evidence_json', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('limitations', sa.Text(), nullable=True),
        sa.Column('alternative_suggestions', sa.JSON(), nullable=True),
        sa.Column('prompt_template', sa.String(64), nullable=False, server_default='seo_title_v1'),
        sa.Column('prompt_version', sa.String(32), nullable=False, server_default='1.0'),
        sa.Column('model_identifier', sa.String(64), nullable=False, server_default='gemini-2.5-flash'),
        sa.Column('current_version_number', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_by', sa.String(36), sa.ForeignKey('profiles.id', ondelete='SET NULL'), nullable=True),
        sa.Column('approved_by', sa.String(36), sa.ForeignKey('profiles.id', ondelete='SET NULL'), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rejected_by', sa.String(36), sa.ForeignKey('profiles.id', ondelete='SET NULL'), nullable=True),
        sa.Column('rejected_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_ai_recommendations_org_id', 'ai_recommendations', ['organization_id'])
    op.create_index('ix_ai_recommendations_website_id', 'ai_recommendations', ['website_project_id'])
    op.create_index('ix_ai_recommendations_audit_id', 'ai_recommendations', ['audit_run_id'])
    op.create_index('ix_ai_recommendations_type', 'ai_recommendations', ['recommendation_type'])
    op.create_index('ix_ai_recommendations_status', 'ai_recommendations', ['status'])
    op.create_index('ix_ai_recommendations_priority', 'ai_recommendations', ['priority'])
    op.create_index('ix_ai_recommendations_page_url', 'ai_recommendations', ['page_url'])
    op.create_index('ix_ai_recs_org_status', 'ai_recommendations', ['organization_id', 'status'])
    op.create_index('ix_ai_recs_website_type', 'ai_recommendations', ['website_project_id', 'recommendation_type'])

    # 3. Create ai_recommendation_versions table
    op.create_table(
        'ai_recommendation_versions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('recommendation_id', sa.String(36), sa.ForeignKey('ai_recommendations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('suggested_value', sa.Text(), nullable=False),
        sa.Column('explanation', sa.Text(), nullable=True),
        sa.Column('user_guidance', sa.Text(), nullable=True),
        sa.Column('created_by', sa.String(36), sa.ForeignKey('profiles.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint('recommendation_id', 'version_number', name='uq_rec_version')
    )
    op.create_index('ix_ai_rec_versions_rec_id', 'ai_recommendation_versions', ['recommendation_id'])

    # 4. Create ai_usage_records table
    op.create_table(
        'ai_usage_records',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('organization_id', sa.String(36), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('profiles.id', ondelete='SET NULL'), nullable=True),
        sa.Column('job_id', sa.String(36), sa.ForeignKey('ai_generation_jobs.id', ondelete='SET NULL'), nullable=True),
        sa.Column('provider', sa.String(50), nullable=False, server_default='gemini'),
        sa.Column('model', sa.String(50), nullable=False, server_default='gemini-2.5-flash'),
        sa.Column('request_type', sa.String(50), nullable=False),
        sa.Column('input_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('output_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('estimated_cost', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('status', sa.String(32), nullable=False, server_default='success'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_ai_usage_records_org_id', 'ai_usage_records', ['organization_id'])
    op.create_index('ix_ai_usage_records_created_at', 'ai_usage_records', ['created_at'])
    op.create_index('ix_ai_usage_org_created', 'ai_usage_records', ['organization_id', 'created_at'])

    # 5. Create ai_quota_reservations table
    op.create_table(
        'ai_quota_reservations',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('organization_id', sa.String(36), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('job_id', sa.String(36), sa.ForeignKey('ai_generation_jobs.id', ondelete='CASCADE'), nullable=True),
        sa.Column('tokens_reserved', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('status', sa.String(32), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_ai_quota_res_org_id', 'ai_quota_reservations', ['organization_id'])
    op.create_index('ix_ai_quota_res_status', 'ai_quota_reservations', ['status'])


def downgrade() -> None:
    op.drop_table('ai_quota_reservations')
    op.drop_table('ai_usage_records')
    op.drop_table('ai_recommendation_versions')
    op.drop_table('ai_recommendations')
    op.drop_table('ai_generation_jobs')
