"""Integration tests for AI SEO Optimization Endpoints, RBAC, and Tenant Isolation."""

from __future__ import annotations

from unittest.mock import MagicMock

from app.models.crawl_job import CrawlJob
from app.models.crawled_page import CrawledPage
from app.models.seo_audit_finding import SEOAuditFinding
from app.models.seo_audit_run import SEOAuditRun
from app.models.website_project import WebsiteProject
from services.worker.celery_app import celery_app


def test_ai_single_generate_and_review_flow(client, db_session):
    owner_token = "Bearer dev_token_usr_ai_owner::alice@domain-ai.com"
    headers = {"Authorization": owner_token}

    # 1. Create org and site
    org = client.post(
        "/api/v1/organizations",
        json={"name": "AI Test Org", "slug": "ai-test-org"},
        headers=headers,
    ).json()
    org_id = org["id"]

    site = client.post(
        f"/api/v1/organizations/{org_id}/websites",
        json={"name": "AI Site", "domain_or_url": "https://ai-example.com"},
        headers=headers,
    ).json()
    site_id = site["id"]

    # 2. Add crawl and page
    project = db_session.get(WebsiteProject, site_id)
    project.is_verified = True
    crawl = CrawlJob(
        project_id=site_id,
        organization_id=org_id,
        status="completed",
        pages_crawled=1,
        config_json={},
    )
    db_session.add(crawl)
    db_session.commit()
    db_session.refresh(crawl)

    page = CrawledPage(
        job_id=crawl.id,
        project_id=site_id,
        url="https://ai-example.com/services",
        normalized_url="https://ai-example.com/services",
        status_code=200,
        title="Bad Title",
        meta_description="Old generic description",
        headings_json={"h1": ["Enterprise SEO Intelligence Services"]},
    )
    db_session.add(page)
    db_session.commit()
    db_session.refresh(page)

    # 3. Add audit run & finding
    audit_run = SEOAuditRun(
        organization_id=org_id,
        website_project_id=site_id,
        crawl_job_id=crawl.id,
        status="completed",
    )
    db_session.add(audit_run)
    db_session.commit()
    db_session.refresh(audit_run)

    finding = SEOAuditFinding(
        audit_run_id=audit_run.id,
        organization_id=org_id,
        website_project_id=site_id,
        rule_id="RULE_TITLE_GENERIC",
        severity="high",
        category="metadata",
        title="Generic Page Title",
        description="The title tag is too generic and fails to convey the page focus.",
        recommendation="Replace with descriptive title reflecting H1.",
        finding_fingerprint="fp_title_123",
    )
    db_session.add(finding)
    db_session.commit()
    db_session.refresh(finding)

    # 4. Generate recommendation
    gen_resp = client.post(
        f"/api/v1/organizations/{org_id}/websites/{site_id}/ai/generate",
        json={
            "page_url": "https://ai-example.com/services",
            "recommendation_type": "title_optimization",
            "audit_run_id": audit_run.id,
            "finding_id": finding.id,
        },
        headers=headers,
    )
    assert gen_resp.status_code == 201
    rec_data = gen_resp.json()
    rec_id = rec_data["id"]
    assert rec_data["status"] == "needs_review"
    assert rec_data["priority"] == "high"
    assert "Enterprise SEO Intelligence" in rec_data["suggested_value"]
    assert rec_data["current_version_number"] == 1

    # 5. List recommendations for website
    list_resp = client.get(
        f"/api/v1/organizations/{org_id}/websites/{site_id}/ai/recommendations",
        headers=headers,
    )
    assert list_resp.status_code == 200
    assert list_resp.json()["total"] >= 1

    # 6. Edit proposal
    edit_resp = client.patch(
        f"/api/v1/organizations/{org_id}/ai/recommendations/{rec_id}",
        json={"suggested_value": "Custom Edited SEO Title | AI Example"},
        headers=headers,
    )
    assert edit_resp.status_code == 200
    assert edit_resp.json()["suggested_value"] == "Custom Edited SEO Title | AI Example"
    assert edit_resp.json()["current_version_number"] == 2

    # 7. Approve proposal
    appr_resp = client.post(
        f"/api/v1/organizations/{org_id}/ai/recommendations/{rec_id}/approve",
        headers=headers,
    )
    assert appr_resp.status_code == 200
    assert appr_resp.json()["status"] == "approved"
    assert appr_resp.json()["approved_by"] is not None

    # 8. Regenerate proposal with guidance
    regen_resp = client.post(
        f"/api/v1/organizations/{org_id}/ai/recommendations/{rec_id}/regenerate",
        json={"user_guidance": "Make it under 50 characters"},
        headers=headers,
    )
    assert regen_resp.status_code == 200
    assert regen_resp.json()["status"] == "needs_review"  # Reset from approved to needs_review
    assert regen_resp.json()["current_version_number"] == 3

    # 9. Check version history
    hist_resp = client.get(
        f"/api/v1/organizations/{org_id}/ai/recommendations/{rec_id}/history",
        headers=headers,
    )
    assert hist_resp.status_code == 200
    versions = hist_resp.json()
    assert len(versions) == 3
    assert versions[0]["version_number"] == 3

    # 10. Reject proposal
    rej_resp = client.post(
        f"/api/v1/organizations/{org_id}/ai/recommendations/{rec_id}/reject",
        json={"reason": "Testing rejection"},
        headers=headers,
    )
    assert rej_resp.status_code == 200
    assert rej_resp.json()["status"] == "rejected"





def test_ai_bulk_generate_and_cancellation(client, db_session, monkeypatch):
    mock_task = MagicMock(id="mock-celery-task-id-123")
    monkeypatch.setattr(celery_app, "send_task", lambda *args, **kwargs: mock_task)
    owner_token = "Bearer dev_token_usr_ai_bulk::bob@domain-ai.com"
    headers = {"Authorization": owner_token}

    org = client.post(
        "/api/v1/organizations",
        json={"name": "Bulk Org", "slug": "bulk-ai-org"},
        headers=headers,
    ).json()
    org_id = org["id"]

    site = client.post(
        f"/api/v1/organizations/{org_id}/websites",
        json={"name": "Bulk Site", "domain_or_url": "https://bulk-example.com"},
        headers=headers,
    ).json()
    site_id = site["id"]

    bulk_resp = client.post(
        f"/api/v1/organizations/{org_id}/websites/{site_id}/ai/bulk-generate",
        json={
            "recommendation_types": ["title_optimization", "meta_description"],
            "page_limit": 5,
        },
        headers=headers,
    )
    assert bulk_resp.status_code == 202
    job_data = bulk_resp.json()
    job_id = job_data["id"]
    assert job_data["status"] == "queued"

    # Inspect job
    job_get = client.get(
        f"/api/v1/organizations/{org_id}/ai/jobs/{job_id}",
        headers=headers,
    )
    assert job_get.status_code == 200
    assert job_get.json()["id"] == job_id

    # Cancel job
    cancel_resp = client.post(
        f"/api/v1/organizations/{org_id}/ai/jobs/{job_id}/cancel",
        headers=headers,
    )
    assert cancel_resp.status_code == 200
    assert cancel_resp.json()["status"] == "cancelled"


def test_ai_cross_tenant_isolation(client, db_session):
    owner_a_token = "Bearer dev_token_usr_org_a::alice@org-a.com"
    owner_b_token = "Bearer dev_token_usr_org_b::bob@org-b.com"

    # Create Org A and recommendation
    org_a = client.post(
        "/api/v1/organizations",
        json={"name": "Org A", "slug": "org-a-ai"},
        headers={"Authorization": owner_a_token},
    ).json()
    org_a_id = org_a["id"]

    site_a = client.post(
        f"/api/v1/organizations/{org_a_id}/websites",
        json={"name": "Site A", "domain_or_url": "https://site-a.com"},
        headers={"Authorization": owner_a_token},
    ).json()
    site_a_id = site_a["id"]

    # Seed crawled page
    crawl_a = CrawlJob(project_id=site_a_id, organization_id=org_a_id, status="completed", config_json={})
    db_session.add(crawl_a)
    db_session.commit()
    page_a = CrawledPage(
        job_id=crawl_a.id, project_id=site_a_id, url="https://site-a.com/page",
        normalized_url="https://site-a.com/page", status_code=200, title="Org A Title"
    )
    db_session.add(page_a)
    db_session.commit()

    rec_a = client.post(
        f"/api/v1/organizations/{org_a_id}/websites/{site_a_id}/ai/generate",
        json={"page_url": "https://site-a.com/page", "recommendation_type": "title_optimization"},
        headers={"Authorization": owner_a_token},
    ).json()
    rec_a_id = rec_a["id"]

    # User B belongs to Org B
    org_b = client.post(
        "/api/v1/organizations",
        json={"name": "Org B", "slug": "org-b-ai"},
        headers={"Authorization": owner_b_token},
    ).json()
    org_b_id = org_b["id"]

    # User B attempts to access Org A's recommendation -> 403 or 404
    resp_get = client.get(
        f"/api/v1/organizations/{org_a_id}/ai/recommendations/{rec_a_id}",
        headers={"Authorization": owner_b_token},
    )
    assert resp_get.status_code == 403

    # User B attempts to access Org A's recommendation via Org B path -> 404
    resp_cross = client.get(
        f"/api/v1/organizations/{org_b_id}/ai/recommendations/{rec_a_id}",
        headers={"Authorization": owner_b_token},
    )
    assert resp_cross.status_code == 404

    # User B attempts to approve Org A's recommendation -> 403
    resp_approve = client.post(
        f"/api/v1/organizations/{org_a_id}/ai/recommendations/{rec_a_id}/approve",
        headers={"Authorization": owner_b_token},
    )
    assert resp_approve.status_code == 403


def test_ai_usage_and_quota_endpoints(client, db_session):
    owner_token = "Bearer dev_token_usr_ai_usage::carol@domain-ai.com"
    headers = {"Authorization": owner_token}

    org = client.post(
        "/api/v1/organizations",
        json={"name": "Usage Query Org", "slug": "usage-query-org"},
        headers=headers,
    ).json()
    org_id = org["id"]

    usage_resp = client.get(f"/api/v1/organizations/{org_id}/ai/usage", headers=headers)
    assert usage_resp.status_code == 200
    usage_data = usage_resp.json()
    assert "daily_requests_used" in usage_data
    assert "monthly_tokens_used" in usage_data
    assert "monthly_estimated_cost_usd" in usage_data

    quota_resp = client.get(f"/api/v1/organizations/{org_id}/ai/quotas", headers=headers)
    assert quota_resp.status_code == 200
    quota_data = quota_resp.json()
    assert quota_data["daily_requests_limit"] > 0
    assert quota_data["monthly_token_limit"] > 0
    assert "model" in quota_data
