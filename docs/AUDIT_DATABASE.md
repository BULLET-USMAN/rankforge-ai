# Technical SEO Audit Database Schema & Migrations

Alembic migration `004_phase_4_audit_engine` defines the Phase 4 database models and schema updates.

---

## 1. Table: `seo_audit_runs`

Tracks technical SEO audit execution runs evaluating completed crawl snapshots.

```sql
CREATE TABLE seo_audit_runs (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    organization_id VARCHAR(36) NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    website_project_id VARCHAR(36) NOT NULL REFERENCES website_projects(id) ON DELETE CASCADE,
    crawl_job_id VARCHAR(36) NOT NULL REFERENCES crawl_jobs(id) ON DELETE CASCADE,
    status VARCHAR(50) NOT NULL DEFAULT 'queued',
    celery_task_id VARCHAR(128),
    ruleset_version VARCHAR(50) NOT NULL DEFAULT 'v1.0.0',
    scoring_version VARCHAR(50) NOT NULL DEFAULT 'v1.0.0',
    score INTEGER,  -- 0-100 or NULL if insufficient coverage
    score_coverage FLOAT NOT NULL DEFAULT 1.0,
    pages_evaluated INTEGER NOT NULL DEFAULT 0,
    pages_not_evaluated INTEGER NOT NULL DEFAULT 0,
    findings_count INTEGER NOT NULL DEFAULT 0,
    critical_count INTEGER NOT NULL DEFAULT 0,
    high_count INTEGER NOT NULL DEFAULT 0,
    medium_count INTEGER NOT NULL DEFAULT 0,
    low_count INTEGER NOT NULL DEFAULT 0,
    info_count INTEGER NOT NULL DEFAULT 0,
    summary_json JSON NOT NULL DEFAULT '{}',
    error_message VARCHAR(1024),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_by VARCHAR(36) REFERENCES profiles(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL
);
CREATE INDEX ix_seo_audit_runs_org_id ON seo_audit_runs(organization_id);
CREATE INDEX ix_seo_audit_runs_project_id ON seo_audit_runs(website_project_id);
CREATE INDEX ix_seo_audit_runs_crawl_id ON seo_audit_runs(crawl_job_id);
CREATE INDEX ix_seo_audit_runs_status ON seo_audit_runs(status);
```

---

## 2. Table: `seo_audit_findings`

Stores discrete findings detected during an audit run.

```sql
CREATE TABLE seo_audit_findings (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    audit_run_id VARCHAR(36) NOT NULL REFERENCES seo_audit_runs(id) ON DELETE CASCADE,
    organization_id VARCHAR(36) NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    website_project_id VARCHAR(36) NOT NULL REFERENCES website_projects(id) ON DELETE CASCADE,
    rule_id VARCHAR(100) NOT NULL,
    rule_version VARCHAR(50) NOT NULL DEFAULT 'v1.0.0',
    page_url VARCHAR(1024),
    severity VARCHAR(50) NOT NULL,
    category VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    evidence_json JSON NOT NULL DEFAULT '{}',
    recommendation TEXT NOT NULL,
    finding_fingerprint VARCHAR(64) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL
);
CREATE INDEX ix_seo_audit_findings_audit_run_id ON seo_audit_findings(audit_run_id);
CREATE INDEX ix_seo_audit_findings_org_id ON seo_audit_findings(organization_id);
CREATE INDEX ix_seo_audit_findings_project_id ON seo_audit_findings(website_project_id);
CREATE INDEX ix_seo_audit_findings_rule_id ON seo_audit_findings(rule_id);
CREATE INDEX ix_seo_audit_findings_severity ON seo_audit_findings(severity);
CREATE INDEX ix_seo_audit_findings_category ON seo_audit_findings(category);
CREATE INDEX ix_seo_audit_findings_fingerprint ON seo_audit_findings(finding_fingerprint);
```

---

## 3. Table: `seo_audit_category_scores`

Stores the breakdown of scores, weights, and finding counts across the 8 categories.

```sql
CREATE TABLE seo_audit_category_scores (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    audit_run_id VARCHAR(36) NOT NULL REFERENCES seo_audit_runs(id) ON DELETE CASCADE,
    category VARCHAR(50) NOT NULL,
    score INTEGER NOT NULL DEFAULT 100,
    weight FLOAT NOT NULL DEFAULT 0.1,
    findings_count INTEGER NOT NULL DEFAULT 0,
    passed_checks_count INTEGER NOT NULL DEFAULT 0,
    details_json JSON NOT NULL DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL
);
CREATE INDEX ix_seo_audit_category_scores_audit_run_id ON seo_audit_category_scores(audit_run_id);
CREATE INDEX ix_seo_audit_category_scores_category ON seo_audit_category_scores(category);
```

---

## 4. Table: `seo_audit_comparisons`

Stores differential comparison between two sequential audit snapshots.

```sql
CREATE TABLE seo_audit_comparisons (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    organization_id VARCHAR(36) NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    website_project_id VARCHAR(36) NOT NULL REFERENCES website_projects(id) ON DELETE CASCADE,
    current_audit_id VARCHAR(36) NOT NULL REFERENCES seo_audit_runs(id) ON DELETE CASCADE,
    previous_audit_id VARCHAR(36) NOT NULL REFERENCES seo_audit_runs(id) ON DELETE CASCADE,
    score_change INTEGER NOT NULL DEFAULT 0,
    new_findings_count INTEGER NOT NULL DEFAULT 0,
    resolved_findings_count INTEGER NOT NULL DEFAULT 0,
    persisting_findings_count INTEGER NOT NULL DEFAULT 0,
    comparison_data_json JSON NOT NULL DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL
);
CREATE INDEX ix_seo_audit_comparisons_org_id ON seo_audit_comparisons(organization_id);
CREATE INDEX ix_seo_audit_comparisons_project_id ON seo_audit_comparisons(website_project_id);
CREATE INDEX ix_seo_audit_comparisons_curr ON seo_audit_comparisons(current_audit_id);
CREATE INDEX ix_seo_audit_comparisons_prev ON seo_audit_comparisons(previous_audit_id);
```

---

## 5. Extensions to `crawled_pages`

Phase 4 extended `crawled_pages` to capture rich structural SEO attributes:
- `x_robots_tag VARCHAR(255)`
- `headings_json JSON` (h1-h6 tag text arrays)
- `images_count INTEGER`
- `images_missing_alt_count INTEGER`
- `images_json JSON` (image src, alt, has_alt, is_empty_alt)
- `structured_data_json JSON` (JSON-LD syntax, schema types)
- `redirect_chain_json JSON` (intermediate redirect hops)
