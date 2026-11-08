"""Unit and integration tests for RankForge Crawler Engine and APIs."""

from unittest.mock import patch

from app.models.website_project import WebsiteProject
from app.models.website_verification import WebsiteVerification
from app.services.crawler.page_parser import PageParser
from app.services.crawler.robots_service import RobotsPolicy
from app.services.crawler.safe_fetcher import SafeFetchResult
from app.services.crawler.sitemap_service import SitemapService
from app.services.crawler.url_normalizer import UrlNormalizer


def test_url_normalizer():
    # Base URL joining & fragment stripping
    norm = UrlNormalizer.normalize_url("/about#team", base_url="https://example.com/blog/")
    assert norm == "https://example.com/about"

    # Tracking query parameters removal & parameter sorting
    norm2 = UrlNormalizer.normalize_url("https://example.com/page?utm_source=google&b=2&a=1&fbclid=xyz")
    assert norm2 == "https://example.com/page?a=1&b=2"

    # Default port normalization
    norm3 = UrlNormalizer.normalize_url("https://example.com:443/docs")
    assert norm3 == "https://example.com/docs"

    # In-scope check
    assert UrlNormalizer.is_in_scope("https://example.com/features", "example.com") is True
    assert UrlNormalizer.is_in_scope("https://www.example.com/features", "example.com") is True
    assert UrlNormalizer.is_in_scope("https://sub.example.com/features", "example.com") is False
    assert UrlNormalizer.is_in_scope("https://sub.example.com/features", "example.com", allow_subdomains=True) is True
    assert UrlNormalizer.is_in_scope("https://evil.com/page", "example.com") is False

    # Trap / sensitive resource detection
    is_crawlable, reason = UrlNormalizer.is_crawlable_resource("https://example.com/login")
    assert not is_crawlable
    assert "sensitive_path" in reason

    is_crawlable, reason = UrlNormalizer.is_crawlable_resource("https://example.com/assets/logo.png")
    assert not is_crawlable
    assert "excluded_extension" in reason


def test_robots_parser_rfc9309():
    raw_robots = """
User-agent: *
Disallow: /admin/
Disallow: /private/
Allow: /private/public-doc

User-agent: RankForgeBot
Disallow: /bot-forbidden/
Allow: /admin/read-only

Sitemap: https://example.com/sitemap.xml
Crawl-delay: 2
"""
    policy = RobotsPolicy(raw_content=raw_robots, status_code=200)

    # RankForgeBot specific rules take precedence
    assert policy.can_fetch("https://example.com/admin/read-only") is True
    assert policy.can_fetch("https://example.com/bot-forbidden/page") is False
    assert policy.crawl_delay == 2.0
    assert "https://example.com/sitemap.xml" in policy.sitemaps


def test_sitemap_parser_defusedxml():
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://example.com/page-1</loc>
  </url>
  <url>
    <loc>https://example.com/page-2</loc>
  </url>
  <url>
    <loc>https://external.com/page-3</loc>
  </url>
</urlset>"""

    page_urls, nested, error = SitemapService.parse_sitemap_xml(
        xml_content, target_domain="example.com", sitemap_url="https://example.com/sitemap.xml"
    )

    assert error is None
    assert len(page_urls) == 2
    assert "https://example.com/page-1" in page_urls
    assert "https://example.com/page-2" in page_urls
    assert "https://external.com/page-3" not in page_urls  # Filtered out of scope


def test_page_parser():
    html_sample = """<!DOCTYPE html>
<html>
<head>
    <title>RankForge SEO Platform</title>
    <meta name="description" content="AI powered technical SEO platform for businesses.">
    <link rel="canonical" href="/canonical-target">
    <meta name="robots" content="index, follow">
</head>
<body>
    <h1>Main Page Heading</h1>
    <a href="/pricing">Pricing Plans</a>
    <a href="https://external.com/partner" rel="nofollow">Partner Site</a>
</body>
</html>"""

    data = PageParser.parse_html(html_sample, "https://example.com/product", "example.com")

    assert data.title == "RankForge SEO Platform"
    assert data.meta_description == "AI powered technical SEO platform for businesses."
    assert data.canonical_url == "https://example.com/canonical-target"
    assert data.meta_robots == "index, follow"
    assert data.h1_count == 1
    assert data.primary_h1 == "Main Page Heading"
    assert data.internal_links_count == 1
    assert data.external_links_count == 1
    assert "https://example.com/pricing" in data.internal_links
    assert data.content_hash is not None


def test_crawler_verification_gate(client):
    owner_token = "Bearer dev_token_usr_crawler_gate@domain.com"
    headers = {"Authorization": owner_token}

    # Setup Org
    org = client.post(
        "/api/v1/organizations",
        json={"name": "Gate Org", "slug": "gate-org"},
        headers=headers,
    ).json()
    org_id = org["id"]

    # Setup Website (unverified)
    site = client.post(
        f"/api/v1/organizations/{org_id}/websites",
        json={"name": "Unverified Site", "domain_or_url": "https://unverified-gate.com"},
        headers=headers,
    ).json()
    site_id = site["id"]

    # Attempting to start crawl on unverified site should fail with 403 Forbidden
    resp = client.post(
        f"/api/v1/organizations/{org_id}/websites/{site_id}/crawls",
        json={"max_pages": 10, "max_depth": 2},
        headers=headers,
    )
    assert resp.status_code == 403
    assert "not verified" in resp.json()["detail"].lower()


def test_crawler_full_execution_sync(client, db_session):
    owner_token = "Bearer dev_token_usr_crawler_sync@domain.com"
    headers = {"Authorization": owner_token}

    # Setup Org
    org = client.post(
        "/api/v1/organizations",
        json={"name": "Verified Org", "slug": "verified-crawl-org"},
        headers=headers,
    ).json()
    org_id = org["id"]

    # Setup Website
    site = client.post(
        f"/api/v1/organizations/{org_id}/websites",
        json={"name": "Crawl Test Site", "domain_or_url": "https://crawltest.com"},
        headers=headers,
    ).json()
    site_id = site["id"]

    # Manually verify in database for the test
    project = db_session.query(WebsiteProject).filter(WebsiteProject.id == site_id).first()
    project.is_verified = True
    project.verification_status = "verified"

    verif = WebsiteVerification(
        project_id=project.id,
        method="dns_txt",
        token="token-verified",
        status="verified",
    )
    db_session.add(verif)
    db_session.commit()

    # Mock responses for crawl
    mock_homepage_html = """<!DOCTYPE html>
<html>
<head><title>Home Page</title></head>
<body>
<h1>Welcome to CrawlTest</h1>
<a href="/about">About Us</a>
</body>
</html>"""

    mock_about_html = """<!DOCTYPE html>
<html>
<head><title>About Us</title><meta name="description" content="Company info"></head>
<body>
<h1>About Us</h1>
</body>
</html>"""

    def fake_fetch_sync(url, **kwargs):
        if "robots.txt" in url:
            return SafeFetchResult(is_success=True, status_code=200, text_content="User-agent: *\nAllow: /\n")
        elif "sitemap" in url:
            return SafeFetchResult(is_success=False, status_code=404, error_details="Not found")
        elif "/about" in url:
            return SafeFetchResult(is_success=True, status_code=200, text_content=mock_about_html, content_type="text/html")
        else:
            return SafeFetchResult(is_success=True, status_code=200, text_content=mock_homepage_html, content_type="text/html")

    with patch("app.services.crawler.safe_fetcher.SafeHttpFetcher.fetch_sync", side_effect=fake_fetch_sync):
        # Create crawl job with execute_sync=True
        resp = client.post(
            f"/api/v1/organizations/{org_id}/websites/{site_id}/crawls?execute_sync=true",
            json={"max_pages": 5, "max_depth": 2},
            headers=headers,
        )
        assert resp.status_code == 201
        job_data = resp.json()
        assert job_data["status"] == "completed"
        assert job_data["pages_crawled"] >= 2

        # Verify pages endpoint returns discovered pages
        job_id = job_data["id"]
        pages_resp = client.get(
            f"/api/v1/organizations/{org_id}/crawls/{job_id}/pages",
            headers=headers,
        )
        assert pages_resp.status_code == 200
        pages_data = pages_resp.json()
        assert pages_data["total"] >= 2
        titles = [p["title"] for p in pages_data["items"]]
        assert "Home Page" in titles
        assert "About Us" in titles
