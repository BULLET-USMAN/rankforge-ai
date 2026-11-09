"""Types, enums, and data transfer models for the SEO Audit Engine."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set


class AuditCategory(str, Enum):
    INDEXABILITY = "indexability"
    LINKS_HTTP = "links_http"
    CANONICAL = "canonical"
    METADATA = "metadata"
    SITE_STRUCTURE = "site_structure"
    HEADINGS = "headings"
    IMAGES = "images"
    STRUCTURED_DATA_SITEMAPS = "structured_data_sitemaps"


class FindingSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFORMATIONAL = "informational"


CATEGORY_WEIGHTS: Dict[AuditCategory, float] = {
    AuditCategory.INDEXABILITY: 0.25,
    AuditCategory.LINKS_HTTP: 0.20,
    AuditCategory.CANONICAL: 0.15,
    AuditCategory.METADATA: 0.15,
    AuditCategory.SITE_STRUCTURE: 0.10,
    AuditCategory.HEADINGS: 0.05,
    AuditCategory.IMAGES: 0.05,
    AuditCategory.STRUCTURED_DATA_SITEMAPS: 0.05,
}

SEVERITY_BASE_PENALTY: Dict[FindingSeverity, float] = {
    FindingSeverity.CRITICAL: 20.0,
    FindingSeverity.HIGH: 10.0,
    FindingSeverity.MEDIUM: 5.0,
    FindingSeverity.LOW: 2.0,
    FindingSeverity.INFORMATIONAL: 0.0,
}


@dataclass
class AuditFinding:
    rule_id: str
    rule_version: str
    category: AuditCategory
    severity: FindingSeverity
    title: str
    description: str
    recommendation: str
    evidence: Dict[str, Any]
    page_url: Optional[str] = None
    finding_fingerprint: str = ""

    def __post_init__(self) -> None:
        if not self.finding_fingerprint:
            # Generate deterministic fingerprint based on rule_id, page_url, and key evidence identifiers
            ev_id = ""
            for k in (
                "tag",
                "attribute",
                "target_url",
                "status_code",
                "broken_url",
                "img_src",
                "heading_text",
            ):
                if k in self.evidence:
                    ev_id = f"{k}={self.evidence[k]}"
                    break
            raw = f"{self.rule_id}:{self.page_url or 'site'}:{ev_id}"
            self.finding_fingerprint = hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "rule_version": self.rule_version,
            "category": self.category.value,
            "severity": self.severity.value,
            "title": self.title,
            "description": self.description,
            "recommendation": self.recommendation,
            "evidence": self.evidence,
            "page_url": self.page_url,
            "finding_fingerprint": self.finding_fingerprint,
        }


@dataclass
class RuleEvaluationResult:
    rule_id: str
    category: AuditCategory
    passed: bool
    status: str = "evaluated"  # evaluated, not_evaluated, skipped
    findings: List[AuditFinding] = field(default_factory=list)
    pages_checked: int = 0
    pages_passed: int = 0
    reason: Optional[str] = None


@dataclass
class AuditEvaluationContext:
    project_id: str
    primary_domain: str
    pages: List[Any]  # CrawledPage model instances
    sitemaps: List[Any]  # SitemapDocument model instances
    url_to_page: Dict[str, Any] = field(default_factory=dict)
    normalized_url_to_page: Dict[str, Any] = field(default_factory=dict)
    inlinks_map: Dict[str, Set[str]] = field(default_factory=dict)
    outlinks_map: Dict[str, Set[str]] = field(default_factory=dict)
    pages_evaluated: int = 0
    pages_not_evaluated: int = 0

    @classmethod
    def from_crawl_data(
        cls,
        project_id: str,
        primary_domain: str,
        pages: List[Any],
        sitemaps: List[Any],
    ) -> AuditEvaluationContext:
        url_to_page: Dict[str, Any] = {}
        normalized_url_to_page: Dict[str, Any] = {}
        inlinks_map: Dict[str, Set[str]] = {}
        outlinks_map: Dict[str, Set[str]] = {}

        for p in pages:
            url_to_page[p.url] = p
            normalized_url_to_page[p.normalized_url] = p
            if p.normalized_url not in inlinks_map:
                inlinks_map[p.normalized_url] = set()
            outlinks_map[p.normalized_url] = set()

        # Build inlinks & outlinks graphs
        for p in pages:
            links = p.links_json or []
            source_norm = p.normalized_url
            for link in links:
                target_url = link.get("target_url") or link.get("url")
                is_internal = link.get("is_internal", False)
                if target_url and is_internal:
                    outlinks_map[source_norm].add(target_url)
                    # if target is in our normalized set or exact set, map inlink
                    if target_url in inlinks_map:
                        inlinks_map[target_url].add(source_norm)

        # Count 2xx HTML pages as evaluated
        evaluated_count = sum(1 for p in pages if 200 <= getattr(p, "status_code", 0) < 300)
        not_evaluated_count = len(pages) - evaluated_count

        return cls(
            project_id=project_id,
            primary_domain=primary_domain,
            pages=pages,
            sitemaps=sitemaps,
            url_to_page=url_to_page,
            normalized_url_to_page=normalized_url_to_page,
            inlinks_map=inlinks_map,
            outlinks_map=outlinks_map,
            pages_evaluated=evaluated_count,
            pages_not_evaluated=not_evaluated_count,
        )
