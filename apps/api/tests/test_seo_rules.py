"""Unit tests for all 8 categories of SEO audit rules."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

from app.services.audit.rules.canonical_rules import (
    BrokenCanonicalRule,
    CanonicalLoopRule,
    ExternalCanonicalRule,
    InvalidCanonicalFragmentRule,
    RedirectCanonicalRule,
)
from app.services.audit.rules.heading_rules import (
    HeadingHierarchySkipRule,
    MissingH1Rule,
    MultipleH1Rule,
)
from app.services.audit.rules.http_redirect_rules import (
    InternalDeadLinkRule,
    InternalRedirectLinkRule,
    InternalServerErrorLinkRule,
    SlowPageLatencyRule,
)
from app.services.audit.rules.image_rules import (
    GenericImageAltRule,
    MissingImageAltRule,
)
from app.services.audit.rules.indexability_rules import (
    MetaRobotsNofollowRule,
    MetaRobotsNoindexRule,
    SitemapUrlNoindexRule,
    XRobotsTagNoindexRule,
)
from app.services.audit.rules.metadata_rules import (
    DuplicateTitleRule,
    EmptyMetaDescriptionRule,
    EmptyTitleRule,
    MissingMetaDescriptionRule,
    MissingTitleRule,
    TitleLengthRule,
)
from app.services.audit.rules.site_structure_rules import (
    DeepCrawlDepthRule,
    EmptyAnchorTextRule,
    OrphanPageRule,
)
from app.services.audit.rules.structured_data_sitemap_rules import (
    MalformedJsonLdRule,
    MissingSchemaTypeRule,
    SitemapErrorRule,
)
from app.services.audit.types import AuditEvaluationContext


def make_page(
    url: str,
    status_code: int = 200,
    title: Any = "Valid Page Title That Has Good Length",
    meta_description: Any = "A valid meta description that provides enough context for users and search bots.",
    canonical_url: Any = None,
    meta_robots: Any = None,
    x_robots_tag: Any = None,
    h1_count: int = 1,
    headings_json: Any = None,
    images_count: int = 0,
    images_json: Any = None,
    structured_data_json: Any = None,
    redirect_chain_json: Any = None,
    links_json: Any = None,
    depth: int = 1,
    discovery_method: str = "hyperlink",
    response_time_ms: float = 120.0,
):
    headings = headings_json or {
        "h1": {"count": h1_count, "items": [{"text": "Main Heading"}] if h1_count else []},
        "h2": {"count": 1, "items": [{"text": "Section Two"}]},
        "h3": {"count": 0, "items": []},
    }
    return SimpleNamespace(
        url=url,
        normalized_url=url.rstrip("/"),
        status_code=status_code,
        title=title,
        meta_description=meta_description,
        canonical_url=canonical_url or url,
        meta_robots=meta_robots,
        x_robots_tag=x_robots_tag,
        h1_count=h1_count,
        headings_json=headings,
        images_count=images_count,
        images_missing_alt_count=0,
        images_json=images_json or [],
        structured_data_json=structured_data_json or [],
        redirect_chain_json=redirect_chain_json or [],
        links_json=links_json or [],
        depth=depth,
        discovery_method=discovery_method,
        response_time_ms=response_time_ms,
    )


# ---------------- METADATA RULES ----------------
def test_missing_title_rule():
    pages = [
        make_page("https://example.com/", title=None),
        make_page("https://example.com/about", title="About Us - RankForge"),
    ]
    ctx = AuditEvaluationContext.from_crawl_data("p1", "example.com", pages, [])
    res = MissingTitleRule().evaluate(ctx)
    assert not res.passed
    assert len(res.findings) == 1
    assert res.findings[0].page_url == "https://example.com/"


def test_empty_title_rule():
    pages = [
        make_page("https://example.com/empty", title="   "),
        make_page("https://example.com/valid", title="Valid Title"),
    ]
    ctx = AuditEvaluationContext.from_crawl_data("p1", "example.com", pages, [])
    res = EmptyTitleRule().evaluate(ctx)
    assert not res.passed
    assert len(res.findings) == 1


def test_duplicate_title_rule():
    pages = [
        make_page("https://example.com/a", title="Same Title"),
        make_page("https://example.com/b", title="Same Title"),
        make_page("https://example.com/c", title="Unique Title"),
    ]
    ctx = AuditEvaluationContext.from_crawl_data("p1", "example.com", pages, [])
    res = DuplicateTitleRule().evaluate(ctx)
    assert not res.passed
    assert len(res.findings) == 2  # Both a and b flagged


def test_title_length_rule():
    pages = [
        make_page("https://example.com/short", title="Short"),
        make_page("https://example.com/long", title="A" * 70),
        make_page("https://example.com/good", title="This is a great title with 36 chars"),
    ]
    ctx = AuditEvaluationContext.from_crawl_data("p1", "example.com", pages, [])
    res = TitleLengthRule().evaluate(ctx)
    assert not res.passed
    assert len(res.findings) == 2


def test_missing_and_empty_meta_description():
    pages = [
        make_page("https://example.com/no-desc", meta_description=None),
        make_page("https://example.com/empty-desc", meta_description="   "),
    ]
    ctx = AuditEvaluationContext.from_crawl_data("p1", "example.com", pages, [])
    res_missing = MissingMetaDescriptionRule().evaluate(ctx)
    res_empty = EmptyMetaDescriptionRule().evaluate(ctx)
    assert len(res_missing.findings) == 1
    assert len(res_empty.findings) == 1


# ---------------- HEADING RULES ----------------
def test_heading_rules():
    pages = [
        make_page("https://example.com/no-h1", h1_count=0),
        make_page("https://example.com/multi-h1", h1_count=2),
        make_page(
            "https://example.com/skip-h2",
            h1_count=1,
            headings_json={
                "h1": {"count": 1, "items": [{"text": "Title"}]},
                "h2": {"count": 0, "items": []},
                "h3": {"count": 2, "items": [{"text": "Sub"}, {"text": "Sub 2"}]},
            },
        ),
    ]
    ctx = AuditEvaluationContext.from_crawl_data("p1", "example.com", pages, [])
    assert not MissingH1Rule().evaluate(ctx).passed
    assert not MultipleH1Rule().evaluate(ctx).passed
    assert not HeadingHierarchySkipRule().evaluate(ctx).passed


# ---------------- INDEXABILITY RULES ----------------
def test_indexability_rules():
    pages = [
        make_page("https://example.com/meta-noindex", meta_robots="noindex, follow"),
        make_page("https://example.com/header-noindex", x_robots_tag="noindex"),
        make_page("https://example.com/nofollow", meta_robots="nofollow"),
        make_page("https://example.com/sitemap-noindex", meta_robots="noindex", discovery_method="sitemap"),
    ]
    ctx = AuditEvaluationContext.from_crawl_data("p1", "example.com", pages, [])
    assert not MetaRobotsNoindexRule().evaluate(ctx).passed
    assert not XRobotsTagNoindexRule().evaluate(ctx).passed
    assert not MetaRobotsNofollowRule().evaluate(ctx).passed
    assert not SitemapUrlNoindexRule().evaluate(ctx).passed


# ---------------- CANONICAL RULES ----------------
def test_canonical_rules():
    p_broken = make_page("https://example.com/404", status_code=404)
    p_redirect = make_page("https://example.com/301", status_code=301)
    p1 = make_page("https://example.com/a", canonical_url="https://example.com/b")
    p2 = make_page("https://example.com/b", canonical_url="https://example.com/a")
    p_frag = make_page("https://example.com/frag", canonical_url="https://example.com/home#section")
    p_ext = make_page("https://example.com/external", canonical_url="https://external.org/page")
    p_canon_broken = make_page("https://example.com/has-broken-canon", canonical_url="https://example.com/404")
    p_canon_redir = make_page("https://example.com/has-redir-canon", canonical_url="https://example.com/301")

    pages = [p_broken, p_redirect, p1, p2, p_frag, p_ext, p_canon_broken, p_canon_redir]
    ctx = AuditEvaluationContext.from_crawl_data("p1", "example.com", pages, [])

    assert not InvalidCanonicalFragmentRule().evaluate(ctx).passed
    assert not BrokenCanonicalRule().evaluate(ctx).passed
    assert not RedirectCanonicalRule().evaluate(ctx).passed
    assert not CanonicalLoopRule().evaluate(ctx).passed
    assert not ExternalCanonicalRule().evaluate(ctx).passed


# ---------------- LINKS & HTTP RULES ----------------
def test_http_link_rules():
    dead = make_page("https://example.com/dead", status_code=404)
    crashed = make_page("https://example.com/crashed", status_code=500)
    redir = make_page("https://example.com/old", status_code=301)
    source = make_page(
        "https://example.com/source",
        links_json=[
            {"target_url": "https://example.com/dead", "is_internal": True, "anchor_text": "Dead"},
            {"target_url": "https://example.com/crashed", "is_internal": True, "anchor_text": "Error"},
            {"target_url": "https://example.com/old", "is_internal": True, "anchor_text": "Old"},
        ],
    )
    slow = make_page("https://example.com/slow", response_time_ms=3200.0)
    chained = make_page(
        "https://example.com/chained",
        redirect_chain_json=[{"from_url": "https://example.com/1", "to_url": "https://example.com/2", "status_code": 301}],
    )

    pages = [dead, crashed, redir, source, slow, chained]
    ctx = AuditEvaluationContext.from_crawl_data("p1", "example.com", pages, [])

    assert not InternalDeadLinkRule().evaluate(ctx).passed
    assert not InternalServerErrorLinkRule().evaluate(ctx).passed
    assert not InternalRedirectLinkRule().evaluate(ctx).passed
    assert not SlowPageLatencyRule().evaluate(ctx).passed


# ---------------- SITE STRUCTURE RULES ----------------
def test_site_structure_rules():
    deep = make_page("https://example.com/deep", depth=5)
    orphan = make_page("https://example.com/orphan", depth=1, discovery_method="sitemap")
    empty_anchor = make_page(
        "https://example.com/page",
        links_json=[{"target_url": "https://example.com/other", "is_internal": True, "anchor_text": "   "}],
    )
    pages = [deep, orphan, empty_anchor]
    ctx = AuditEvaluationContext.from_crawl_data("p1", "example.com", pages, [])

    assert not DeepCrawlDepthRule().evaluate(ctx).passed
    assert not OrphanPageRule().evaluate(ctx).passed
    assert not EmptyAnchorTextRule().evaluate(ctx).passed


# ---------------- IMAGE RULES ----------------
def test_image_rules_and_decorative_alt_handling():
    # Decorative alt="" should NOT be flagged as missing alt!
    p_decorative = make_page(
        "https://example.com/decor",
        images_count=1,
        images_json=[{"src": "/decor.png", "alt": "", "has_alt": True, "is_empty_alt": True}],
    )
    # Missing alt tag (has_alt=False) SHOULD be flagged
    p_missing = make_page(
        "https://example.com/missing-alt",
        images_count=1,
        images_json=[{"src": "/hero.jpg", "alt": None, "has_alt": False, "is_empty_alt": False}],
    )
    # Generic alt like "photo"
    p_generic = make_page(
        "https://example.com/generic-alt",
        images_count=1,
        images_json=[{"src": "/logo.svg", "alt": "photo", "has_alt": True, "is_empty_alt": False}],
    )

    pages = [p_decorative, p_missing, p_generic]
    ctx = AuditEvaluationContext.from_crawl_data("p1", "example.com", pages, [])

    res_missing = MissingImageAltRule().evaluate(ctx)
    assert not res_missing.passed
    assert len(res_missing.findings) == 1
    assert res_missing.findings[0].page_url == "https://example.com/missing-alt"

    res_generic = GenericImageAltRule().evaluate(ctx)
    assert not res_generic.passed
    assert len(res_generic.findings) == 1
    assert res_generic.findings[0].page_url == "https://example.com/generic-alt"


# ---------------- STRUCTURED DATA & SITEMAP RULES ----------------
def test_structured_data_and_sitemap_rules():
    p_sd_err = make_page(
        "https://example.com/sd-err",
        structured_data_json=[{"is_valid_json": False, "error_message": "Unexpected comma"}],
    )
    p_sd_notype = make_page(
        "https://example.com/sd-notype",
        structured_data_json=[{"is_valid_json": True, "types": []}],
    )
    pages = [p_sd_err, p_sd_notype]
    sitemaps = [
        SimpleNamespace(url="https://example.com/sitemap.xml", status="failed", status_code=500, error_details="500 Server Error"),
    ]
    ctx = AuditEvaluationContext.from_crawl_data("p1", "example.com", pages, sitemaps)

    assert not MalformedJsonLdRule().evaluate(ctx).passed
    assert not MissingSchemaTypeRule().evaluate(ctx).passed
    assert not SitemapErrorRule().evaluate(ctx).passed
