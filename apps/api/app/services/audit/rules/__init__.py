"""Audit rule exports."""

from app.services.audit.rules.canonical_rules import (
    BrokenCanonicalRule,
    CanonicalLoopRule,
    ExternalCanonicalRule,
    InvalidCanonicalFragmentRule,
    MissingCanonicalRule,
    RedirectCanonicalRule,
)
from app.services.audit.rules.heading_rules import (
    DuplicateH1Rule,
    EmptyH1Rule,
    HeadingHierarchySkipRule,
    MissingH1Rule,
    MultipleH1Rule,
)
from app.services.audit.rules.http_redirect_rules import (
    InternalDeadLinkRule,
    InternalRedirectLinkRule,
    InternalServerErrorLinkRule,
    RedirectChainRule,
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
    DuplicateMetaDescriptionRule,
    DuplicateTitleRule,
    EmptyMetaDescriptionRule,
    EmptyTitleRule,
    MetaDescriptionLengthRule,
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
    SitemapDuplicateUrlRule,
    SitemapErrorRule,
)

ALL_RULES = [
    # Metadata
    MissingTitleRule,
    EmptyTitleRule,
    DuplicateTitleRule,
    TitleLengthRule,
    MissingMetaDescriptionRule,
    EmptyMetaDescriptionRule,
    DuplicateMetaDescriptionRule,
    MetaDescriptionLengthRule,
    # Headings
    MissingH1Rule,
    MultipleH1Rule,
    EmptyH1Rule,
    HeadingHierarchySkipRule,
    DuplicateH1Rule,
    # Indexability
    MetaRobotsNoindexRule,
    XRobotsTagNoindexRule,
    MetaRobotsNofollowRule,
    SitemapUrlNoindexRule,
    # Canonical
    MissingCanonicalRule,
    InvalidCanonicalFragmentRule,
    BrokenCanonicalRule,
    RedirectCanonicalRule,
    CanonicalLoopRule,
    ExternalCanonicalRule,
    # Links & HTTP
    InternalDeadLinkRule,
    InternalServerErrorLinkRule,
    InternalRedirectLinkRule,
    RedirectChainRule,
    SlowPageLatencyRule,
    # Site Structure
    DeepCrawlDepthRule,
    OrphanPageRule,
    EmptyAnchorTextRule,
    # Images
    MissingImageAltRule,
    GenericImageAltRule,
    # Structured Data & Sitemaps
    MalformedJsonLdRule,
    MissingSchemaTypeRule,
    SitemapErrorRule,
    SitemapDuplicateUrlRule,
]

__all__ = [
    "ALL_RULES",
    "MissingTitleRule",
    "EmptyTitleRule",
    "DuplicateTitleRule",
    "TitleLengthRule",
    "MissingMetaDescriptionRule",
    "EmptyMetaDescriptionRule",
    "DuplicateMetaDescriptionRule",
    "MetaDescriptionLengthRule",
    "MissingH1Rule",
    "MultipleH1Rule",
    "EmptyH1Rule",
    "HeadingHierarchySkipRule",
    "DuplicateH1Rule",
    "MetaRobotsNoindexRule",
    "XRobotsTagNoindexRule",
    "MetaRobotsNofollowRule",
    "SitemapUrlNoindexRule",
    "MissingCanonicalRule",
    "InvalidCanonicalFragmentRule",
    "BrokenCanonicalRule",
    "RedirectCanonicalRule",
    "CanonicalLoopRule",
    "ExternalCanonicalRule",
    "InternalDeadLinkRule",
    "InternalServerErrorLinkRule",
    "InternalRedirectLinkRule",
    "RedirectChainRule",
    "SlowPageLatencyRule",
    "DeepCrawlDepthRule",
    "OrphanPageRule",
    "EmptyAnchorTextRule",
    "MissingImageAltRule",
    "GenericImageAltRule",
    "MalformedJsonLdRule",
    "MissingSchemaTypeRule",
    "SitemapErrorRule",
    "SitemapDuplicateUrlRule",
]
