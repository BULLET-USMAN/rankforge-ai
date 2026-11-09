"""Integration tests for Phase 4 SEO Technical Audit Engine APIs and multi-tenant security."""

from __future__ import annotations

from app.models.crawl_job import CrawlJob
from app.models.crawled_page import CrawledPage
from app.models.website_project import WebsiteProject
from app.models.website_verification import WebsiteVerification


def test_audit_verification_gate(client, db_session):
    """Unverified website cannot trigger an audit."""
    owner_token = "Bearer dev_token_usr_audit_gate@domain.com"
    headers = {"Authorization": owner_token}

    org = client.post(
        "/api/v1/organizations",
        json={"name": "Audit Gate Org", "slug": "audit-gate-org"},
        headers=headers,
    ).json()
    org_id = org["id"]

    site = client.post(
        f"/api/v1/organizations/{org_id}/websites",
        json={"name": "Unverified Site", "domain_or_url": "https://unverified.com"},
        headers=headers,
    ).json()
    site_id = site["id"]

    # Trigger audit should fail with 403
    resp = client.post(
        f"/api/v1/organizations/{org_id}/websites/{site_id}/audits",
        json={},
        headers=headers,
    )
    assert resp.status_code == 403
    assert "ownership must be verified" in resp.json()["detail"]


def test_audit_no_crawls_gate(client, db_session):
    """Verified website with no completed crawl jobs returns 400."""
    owner_token = "Bearer dev_token_usr_audit_nocrawl@domain.com"
    headers = {"Authorization": owner_token}

    org = client.post(
        "/api/v1/organizations",
        json={"name": "Audit No Crawl Org", "slug": "audit-nocrawl-org"},
        headers=headers,
    ).json()
    org_id = org["id"]

    site = client.post(
        f"/api/v1/organizations/{org_id}/websites",
        json={"name": "Verified No Crawl", "domain_or_url": "https://verified-nocrawl.com"},
        headers=headers,
    ).json()
    site_id = site["id"]

    # Manually verify
    project = db_session.query(WebsiteProject).filter(WebsiteProject.id == site_id).first()
    project.is_verified = True
    verif = WebsiteVerification(
        project_id=project.id,
        method="dns_txt",
        token="token-verif",
        status="verified",
    )
    db_session.add(verif)
    db_session.commit()

    resp = client.post(
        f"/api/v1/organizations/{org_id}/websites/{site_id}/audits",
        json={},
        headers=headers,
    )
    assert resp.status_code == 400
    assert "No crawl snapshots found" in resp.json()["detail"]


def test_audit_sync_execution_and_findings(client, db_session):
    """Executes a full technical SEO audit against a crawl snapshot with known issues."""
    owner_token = "Bearer dev_token_usr_audit_exec@domain.com"
    headers = {"Authorization": owner_token}

    org = client.post(
        "/api/v1/organizations",
        json={"name": "Audit Exec Org", "slug": "audit-exec-org"},
        headers=headers,
    ).json()
    org_id = org["id"]

    site = client.post(
        f"/api/v1/organizations/{org_id}/websites",
        json={"name": "Audited Site", "domain_or_url": "https://auditme.com"},
        headers=headers,
    ).json()
    site_id = site["id"]

    # Verify site
    project = db_session.query(WebsiteProject).filter(WebsiteProject.id == site_id).first()
    project.is_verified = True
    db_session.add(
        WebsiteVerification(
            project_id=project.id,
            method="dns_txt",
            token="token-verif",
            status="verified",
        )
    )

    # Seed a completed CrawlJob with CrawledPages
    crawl = CrawlJob(
        project_id=project.id,
        organization_id=org_id,
        status="completed",
        pages_crawled=2,
        pages_discovered=2,
        config_json={},
    )
    db_session.add(crawl)
    db_session.commit()
    db_session.refresh(crawl)

    # Page 1: Healthy home page
    p1 = CrawledPage(
        job_id=crawl.id,
        project_id=project.id,
        url="https://auditme.com/",
        normalized_url="https://auditme.com",
        status_code=200,
        response_time_ms=180.0,
        title="RankForge Test - Official Site",
        meta_description="A descriptive and helpful meta description for the test homepage.",
        canonical_url="https://auditme.com/",
        h1_count=1,
        headings_json={"h1": {"count": 1, "items": [{"text": "Welcome"}]}},
        images_count=1,
        images_json=[
            {
                "src": "/hero.png",
                "alt": "Hero visual banner",
                "has_alt": True,
                "is_empty_alt": False,
            }
        ],
        structured_data_json=[{"is_valid_json": True, "types": ["Organization"]}],
        links_json=[
            {
                "target_url": "https://auditme.com/broken",
                "is_internal": True,
                "anchor_text": "Broken Link",
            }
        ],
    )

    # Page 2: Problematic page (Missing title, missing H1, image missing alt)
    p2 = CrawledPage(
        job_id=crawl.id,
        project_id=project.id,
        url="https://auditme.com/about",
        normalized_url="https://auditme.com/about",
        status_code=200,
        response_time_ms=250.0,
        title=None,  # Missing title!
        meta_description=None,  # Missing meta description!
        canonical_url="https://auditme.com/about",
        h1_count=0,  # Missing H1!
        headings_json={"h1": {"count": 0, "items": []}},
        images_count=1,
        images_json=[
            {"src": "/team.jpg", "alt": None, "has_alt": False, "is_empty_alt": False}
        ],  # Missing alt!
        structured_data_json=[],
        links_json=[],
    )

    # Page 3: 404 Target
    p3 = CrawledPage(
        job_id=crawl.id,
        project_id=project.id,
        url="https://auditme.com/broken",
        normalized_url="https://auditme.com/broken",
        status_code=404,
        response_time_ms=50.0,
        links_json=[],
    )

    db_session.add_all([p1, p2, p3])
    db_session.commit()

    # Trigger Audit
    audit_resp = client.post(
        f"/api/v1/organizations/{org_id}/websites/{site_id}/audits?execute_sync=true",
        json={"crawl_job_id": crawl.id},
        headers=headers,
    )
    assert audit_resp.status_code == 201
    audit_data = audit_resp.json()
    assert audit_data["status"] == "completed"
    assert audit_data["score"] is not None
    assert audit_data["score"] < 100  # Penalties applied for issues
    audit_id = audit_data["id"]

    # 1. Test List Audits
    list_resp = client.get(
        f"/api/v1/organizations/{org_id}/websites/{site_id}/audits",
        headers=headers,
    )
    assert list_resp.status_code == 200
    assert list_resp.json()["total"] >= 1

    # 2. Test Get Single Audit
    single_resp = client.get(
        f"/api/v1/organizations/{org_id}/audits/{audit_id}",
        headers=headers,
    )
    assert single_resp.status_code == 200
    assert single_resp.json()["id"] == audit_id

    # 3. Test List Findings with filtering
    findings_resp = client.get(
        f"/api/v1/organizations/{org_id}/audits/{audit_id}/findings",
        headers=headers,
    )
    assert findings_resp.status_code == 200
    findings_data = findings_resp.json()
    assert findings_data["total"] >= 4
    rule_ids = [f["rule_id"] for f in findings_data["items"]]
    assert "META-001" in rule_ids  # Missing title
    assert "HEAD-001" in rule_ids  # Missing H1
    assert "HTTP-001" in rule_ids  # Broken link to 404
    assert "IMG-001" in rule_ids  # Missing alt

    # Filter findings by category
    meta_findings = client.get(
        f"/api/v1/organizations/{org_id}/audits/{audit_id}/findings?category=metadata",
        headers=headers,
    ).json()
    for item in meta_findings["items"]:
        assert item["category"] == "metadata"

    # 4. Test Category Scores
    scores_resp = client.get(
        f"/api/v1/organizations/{org_id}/audits/{audit_id}/scores",
        headers=headers,
    )
    assert scores_resp.status_code == 200
    scores = scores_resp.json()
    assert len(scores) == 8  # Exactly 8 categories

    # 5. Test Audited Pages
    pages_resp = client.get(
        f"/api/v1/organizations/{org_id}/audits/{audit_id}/pages",
        headers=headers,
    )
    assert pages_resp.status_code == 200
    audited_pages = pages_resp.json()
    assert len(audited_pages) == 3


def test_audit_comparison_between_runs(client, db_session):
    """Tests differential comparison between two sequential audit snapshots."""
    owner_token = "Bearer dev_token_usr_audit_comp@domain.com"
    headers = {"Authorization": owner_token}

    org = client.post(
        "/api/v1/organizations",
        json={"name": "Comparison Org", "slug": "audit-comp-org"},
        headers=headers,
    ).json()
    org_id = org["id"]

    site = client.post(
        f"/api/v1/organizations/{org_id}/websites",
        json={"name": "Comparison Site", "domain_or_url": "https://compare.com"},
        headers=headers,
    ).json()
    site_id = site["id"]

    project = db_session.query(WebsiteProject).filter(WebsiteProject.id == site_id).first()
    project.is_verified = True
    db_session.add(
        WebsiteVerification(
            project_id=project.id,
            method="dns_txt",
            token="token-comp",
            status="verified",
        )
    )

    # Crawl 1: Problematic page with missing title
    crawl1 = CrawlJob(
        project_id=project.id,
        organization_id=org_id,
        status="completed",
        pages_crawled=1,
        config_json={},
    )
    db_session.add(crawl1)
    db_session.commit()
    db_session.refresh(crawl1)

    p_old = CrawledPage(
        job_id=crawl1.id,
        project_id=project.id,
        url="https://compare.com/page",
        normalized_url="https://compare.com/page",
        status_code=200,
        title=None,  # Missing title in run 1
        h1_count=1,
        headings_json={"h1": {"count": 1, "items": [{"text": "Heading"}]}},
        links_json=[],
    )
    db_session.add(p_old)
    db_session.commit()

    audit1_resp = client.post(
        f"/api/v1/organizations/{org_id}/websites/{site_id}/audits?execute_sync=true",
        json={"crawl_job_id": crawl1.id},
        headers=headers,
    )
    audit1_id = audit1_resp.json()["id"]

    # Crawl 2: Issue fixed (title added), but H1 removed
    crawl2 = CrawlJob(
        project_id=project.id,
        organization_id=org_id,
        status="completed",
        pages_crawled=1,
        config_json={},
    )
    db_session.add(crawl2)
    db_session.commit()
    db_session.refresh(crawl2)

    p_new = CrawledPage(
        job_id=crawl2.id,
        project_id=project.id,
        url="https://compare.com/page",
        normalized_url="https://compare.com/page",
        status_code=200,
        title="Fixed Title Now Present",
        h1_count=0,  # Missing H1 in run 2
        headings_json={"h1": {"count": 0, "items": []}},
        links_json=[],
    )
    db_session.add(p_new)
    db_session.commit()

    audit2_resp = client.post(
        f"/api/v1/organizations/{org_id}/websites/{site_id}/audits?execute_sync=true",
        json={"crawl_job_id": crawl2.id},
        headers=headers,
    )
    audit2_id = audit2_resp.json()["id"]

    # Compare Run 2 with Run 1
    comp_resp = client.get(
        f"/api/v1/organizations/{org_id}/audits/{audit2_id}/compare/{audit1_id}",
        headers=headers,
    )
    assert comp_resp.status_code == 200
    comp_data = comp_resp.json()
    assert comp_data["current_audit_id"] == audit2_id
    assert comp_data["previous_audit_id"] == audit1_id
    assert comp_data["new_findings_count"] >= 1  # The new missing H1
    assert comp_data["resolved_findings_count"] >= 1  # The resolved missing title


def test_audit_cross_tenant_isolation(client, db_session):
    """User in Org B cannot read or manage audits belonging to Org A."""
    token_a = "Bearer dev_token_usr_audit_a::alice@domain-a.com"
    token_b = "Bearer dev_token_usr_audit_b::bob@domain-b.com"

    org_a = client.post(
        "/api/v1/organizations",
        json={"name": "Org A", "slug": "audit-iso-a"},
        headers={"Authorization": token_a},
    ).json()
    client.post(
        "/api/v1/organizations",
        json={"name": "Org B", "slug": "audit-iso-b"},
        headers={"Authorization": token_b},
    )

    site_a = client.post(
        f"/api/v1/organizations/{org_a['id']}/websites",
        json={"name": "Site A", "domain_or_url": "https://site-a.com"},
        headers={"Authorization": token_a},
    ).json()

    # User B attempts to access Org A's audit endpoints -> 403 Forbidden
    resp = client.get(
        f"/api/v1/organizations/{org_a['id']}/websites/{site_a['id']}/audits",
        headers={"Authorization": token_b},
    )
    assert resp.status_code == 403
