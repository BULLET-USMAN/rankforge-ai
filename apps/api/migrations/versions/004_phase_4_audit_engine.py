"""004_phase_4_audit_engine

Revision ID: 004_phase_4_audit_engine
Revises: 003_phase_3_crawler
Create Date: 2026-11-08 21:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '004_phase_4_audit_engine'
down_revision: Union[str, None] = '003_phase_3_crawler'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Update crawled_pages with SEO & structure columns
    op.add_column('crawled_pages', sa.Column('x_robots_tag', sa.String(255), nullable=True))
    op.add_column('crawled_pages', sa.Column('headings_json', sa.JSON(), nullable=False, server_default='{}'))
    op.add_column('crawled_pages', sa.Column('images_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('crawled_pages', sa.Column('images_missing_alt_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('crawled_pages', sa.Column('images_json', sa.JSON(), nullable=False, server_default='[]'))
    op.add_column('crawled_pages', sa.Column('structured_data_json', sa.JSON(), nullable=False, server_default='[]'))
    op.add_column('crawled_pages', sa.Column('redirect_chain_json', sa.JSON(), nullable=False, server_default='[]'))

    # 2. Create seo_audit_runs table
    op.create_table(
        'seo_audit_runs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('organization_id', sa.String(36), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('website_project_id', sa.String(36), sa.ForeignKey('website_projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('crawl_job_id', sa.String(36), sa.ForeignKey('crawl_jobs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='queued'),
        sa.Column('celery_task_id', sa.String(128), nullable=True),
        sa.Column('ruleset_version', sa.String(50), nullable=False, server_default='v1.0.0'),
        sa.Column('scoring_version', sa.String(50), nullable=False, server_default='v1.0.0'),
        sa.Column('score', sa.Integer(), nullable=True),
        sa.Column('score_coverage', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('pages_evaluated', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('pages_not_evaluated', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('findings_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('critical_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('high_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('medium_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('low_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('info_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('summary_json', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('error_message', sa.String(1024), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.String(36), sa.ForeignKey('profiles.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_seo_audit_runs_org_id', 'seo_audit_runs', ['organization_id'])
    op.create_index('ix_seo_audit_runs_project_id', 'seo_audit_runs', ['website_project_id'])
    op.create_index('ix_seo_audit_runs_crawl_id', 'seo_audit_runs', ['crawl_job_id'])
    op.create_index('ix_seo_audit_runs_status', 'seo_audit_runs', ['status'])

    # 3. Create seo_audit_findings table
    op.create_table(
        'seo_audit_findings',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('audit_run_id', sa.String(36), sa.ForeignKey('seo_audit_runs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('organization_id', sa.String(36), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('website_project_id', sa.String(36), sa.ForeignKey('website_projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('rule_id', sa.String(100), nullable=False),
        sa.Column('rule_version', sa.String(50), nullable=False, server_default='v1.0.0'),
        sa.Column('page_url', sa.String(1024), nullable=True),
        sa.Column('severity', sa.String(50), nullable=False),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('evidence_json', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('recommendation', sa.Text(), nullable=False),
        sa.Column('finding_fingerprint', sa.String(64), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_seo_audit_findings_audit_run_id', 'seo_audit_findings', ['audit_run_id'])
    op.create_index('ix_seo_audit_findings_org_id', 'seo_audit_findings', ['organization_id'])
    op.create_index('ix_seo_audit_findings_project_id', 'seo_audit_findings', ['website_project_id'])
    op.create_index('ix_seo_audit_findings_rule_id', 'seo_audit_findings', ['rule_id'])
    op.create_index('ix_seo_audit_findings_page_url', 'seo_audit_findings', ['page_url'])
    op.create_index('ix_seo_audit_findings_severity', 'seo_audit_findings', ['severity'])
    op.create_index('ix_seo_audit_findings_category', 'seo_audit_findings', ['category'])
    op.create_index('ix_seo_audit_findings_fingerprint', 'seo_audit_findings', ['finding_fingerprint'])

    # 4. Create seo_audit_category_scores table
    op.create_table(
        'seo_audit_category_scores',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('audit_run_id', sa.String(36), sa.ForeignKey('seo_audit_runs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('score', sa.Integer(), nullable=False, server_default='100'),
        sa.Column('weight', sa.Float(), nullable=False, server_default='0.1'),
        sa.Column('findings_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('passed_checks_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('details_json', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_seo_audit_category_scores_audit_run_id', 'seo_audit_category_scores', ['audit_run_id'])
    op.create_index('ix_seo_audit_category_scores_category', 'seo_audit_category_scores', ['category'])

    # 5. Create seo_audit_comparisons table
    op.create_table(
        'seo_audit_comparisons',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('organization_id', sa.String(36), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('website_project_id', sa.String(36), sa.ForeignKey('website_projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('current_audit_id', sa.String(36), sa.ForeignKey('seo_audit_runs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('previous_audit_id', sa.String(36), sa.ForeignKey('seo_audit_runs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('score_change', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('new_findings_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('resolved_findings_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('persisting_findings_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('comparison_data_json', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_seo_audit_comparisons_org_id', 'seo_audit_comparisons', ['organization_id'])
    op.create_index('ix_seo_audit_comparisons_project_id', 'seo_audit_comparisons', ['website_project_id'])
    op.create_index('ix_seo_audit_comparisons_curr_audit', 'seo_audit_comparisons', ['current_audit_id'])
    op.create_index('ix_seo_audit_comparisons_prev_audit', 'seo_audit_comparisons', ['previous_audit_id'])


def downgrade() -> None:
    op.drop_table('seo_audit_comparisons')
    op.drop_table('seo_audit_category_scores')
    op.drop_table('seo_audit_findings')
    op.drop_table('seo_audit_runs')
    op.drop_column('crawled_pages', 'redirect_chain_json')
    op.drop_column('crawled_pages', 'structured_data_json')
    op.drop_column('crawled_pages', 'images_json')
    op.drop_column('crawled_pages', 'images_missing_alt_count')
    op.drop_column('crawled_pages', 'images_count')
    op.drop_column('crawled_pages', 'headings_json')
    op.drop_column('crawled_pages', 'x_robots_tag')
