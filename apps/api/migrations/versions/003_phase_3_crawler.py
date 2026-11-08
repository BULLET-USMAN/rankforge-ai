"""003_phase_3_crawler

Revision ID: 003_phase_3_crawler
Revises: 002_phase_2_auth_workspaces
Create Date: 2026-11-08 20:10:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '003_phase_3_crawler'
down_revision: Union[str, None] = '002_phase_2_auth_workspaces'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Update website_verifications: add enhanced challenge & tracking attributes
    op.add_column('website_verifications', sa.Column('txt_record_name', sa.String(255), nullable=True))
    op.add_column('website_verifications', sa.Column('txt_record_value', sa.String(255), nullable=True))
    op.add_column('website_verifications', sa.Column('file_path', sa.String(255), nullable=True))
    op.add_column('website_verifications', sa.Column('file_content', sa.String(255), nullable=True))
    op.add_column('website_verifications', sa.Column('last_checked_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('website_verifications', sa.Column('failure_reason', sa.String(512), nullable=True))
    op.add_column('website_verifications', sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('website_verifications', sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True))

    # 2. Create crawl_jobs table
    op.create_table(
        'crawl_jobs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('project_id', sa.String(36), sa.ForeignKey('website_projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('organization_id', sa.String(36), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='queued'),
        sa.Column('celery_task_id', sa.String(128), nullable=True),
        sa.Column('max_pages', sa.Integer(), nullable=False, server_default='50'),
        sa.Column('max_depth', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('pages_crawled', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('pages_discovered', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('pages_failed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('pages_blocked', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.String(1024), nullable=True),
        sa.Column('config_json', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_crawl_jobs_project_id', 'crawl_jobs', ['project_id'])
    op.create_index('ix_crawl_jobs_org_id', 'crawl_jobs', ['organization_id'])
    op.create_index('ix_crawl_jobs_status', 'crawl_jobs', ['status'])

    # 3. Create crawled_pages table
    op.create_table(
        'crawled_pages',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('job_id', sa.String(36), sa.ForeignKey('crawl_jobs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('project_id', sa.String(36), sa.ForeignKey('website_projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('url', sa.String(1024), nullable=False),
        sa.Column('normalized_url', sa.String(1024), nullable=False),
        sa.Column('status_code', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('response_time_ms', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('content_type', sa.String(255), nullable=True),
        sa.Column('byte_size', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('depth', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('discovery_method', sa.String(50), nullable=False, server_default='hyperlink'),
        sa.Column('title', sa.String(512), nullable=True),
        sa.Column('meta_description', sa.Text(), nullable=True),
        sa.Column('canonical_url', sa.String(1024), nullable=True),
        sa.Column('meta_robots', sa.String(255), nullable=True),
        sa.Column('h1_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('internal_links_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('external_links_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('links_json', sa.JSON(), nullable=False),
        sa.Column('content_hash', sa.String(64), nullable=True),
        sa.Column('error_details', sa.String(1024), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_crawled_pages_job_id', 'crawled_pages', ['job_id'])
    op.create_index('ix_crawled_pages_project_id', 'crawled_pages', ['project_id'])
    op.create_index('ix_crawled_pages_url', 'crawled_pages', ['url'])
    op.create_index('ix_crawled_pages_normalized_url', 'crawled_pages', ['normalized_url'])

    # 4. Create sitemap_documents table
    op.create_table(
        'sitemap_documents',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('project_id', sa.String(36), sa.ForeignKey('website_projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('job_id', sa.String(36), sa.ForeignKey('crawl_jobs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('url', sa.String(1024), nullable=False),
        sa.Column('discovery_source', sa.String(50), nullable=False, server_default='robots'),
        sa.Column('status_code', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('status', sa.String(50), nullable=False, server_default='discovered'),
        sa.Column('urls_found', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('error_details', sa.String(1024), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_sitemap_documents_project_id', 'sitemap_documents', ['project_id'])
    op.create_index('ix_sitemap_documents_job_id', 'sitemap_documents', ['job_id'])


def downgrade() -> None:
    op.drop_table('sitemap_documents')
    op.drop_table('crawled_pages')
    op.drop_table('crawl_jobs')
    op.drop_column('website_verifications', 'revoked_at')
    op.drop_column('website_verifications', 'verified_at')
    op.drop_column('website_verifications', 'expires_at')
    op.drop_column('website_verifications', 'failure_reason')
    op.drop_column('website_verifications', 'last_checked_at')
    op.drop_column('website_verifications', 'file_content')
    op.drop_column('website_verifications', 'file_path')
    op.drop_column('website_verifications', 'txt_record_value')
    op.drop_column('website_verifications', 'txt_record_name')
