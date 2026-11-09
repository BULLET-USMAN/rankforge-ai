"""Site structure and internal linking SEO audit rules."""

from __future__ import annotations

from app.services.audit.base import BaseAuditRule
from app.services.audit.types import (
    AuditCategory,
    AuditEvaluationContext,
    FindingSeverity,
    RuleEvaluationResult,
)


class DeepCrawlDepthRule(BaseAuditRule):
    rule_id = "LINK-001"
    category = AuditCategory.SITE_STRUCTURE
    default_severity = FindingSeverity.MEDIUM
    title = "Excessive Crawl Depth (Depth >= 4)"
    description = "Page is buried 4 or more clicks away from the homepage/seed URL."

    def evaluate(self, context: AuditEvaluationContext) -> RuleEvaluationResult:
        findings = []
        checked = 0
        passed = 0

        for page in context.pages:
            if page.status_code != 200:
                continue
            checked += 1
            if page.depth >= 4:
                findings.append(
                    self.create_finding(
                        severity=FindingSeverity.MEDIUM,
                        title=f"Excessive Crawl Depth (Level {page.depth})",
                        description=f"Page {page.url} is located at crawl depth {page.depth}, making it harder for search crawlers and users to reach.",
                        recommendation="Improve internal site architecture by adding contextual inlinks from category or hub pages to bring this content within 3 clicks of the root.",
                        evidence={"url": page.url, "depth": page.depth},
                        page_url=page.url,
                    )
                )
            else:
                passed += 1

        return RuleEvaluationResult(
            rule_id=self.rule_id,
            category=self.category,
            passed=len(findings) == 0,
            findings=findings,
            pages_checked=checked,
            pages_passed=passed,
        )


class OrphanPageRule(BaseAuditRule):
    rule_id = "LINK-002"
    category = AuditCategory.SITE_STRUCTURE
    default_severity = FindingSeverity.MEDIUM
    title = "Orphan Page (0 Internal Inlinks)"
    description = "Page was discovered (e.g., via sitemap or seed list) but has no incoming internal links from any crawled page on the website."

    def evaluate(self, context: AuditEvaluationContext) -> RuleEvaluationResult:
        findings = []
        checked = 0
        passed = 0

        # We evaluate pages that aren't the seed page (depth > 0 or sitemap discovery)
        for page in context.pages:
            if page.status_code != 200 or page.depth == 0:
                continue
            checked += 1

            inlinks = context.inlinks_map.get(page.normalized_url, set())
            if len(inlinks) == 0:
                findings.append(
                    self.create_finding(
                        severity=FindingSeverity.MEDIUM,
                        title="Orphan Page Detected",
                        description=f"Page {page.url} has 0 discovered incoming internal links from within the website structure.",
                        recommendation="Link to this page from relevant contextually related content or navigation menus to distribute link equity and assist discovery.",
                        evidence={
                            "url": page.url,
                            "discovery_method": page.discovery_method,
                            "inlinks_count": 0,
                        },
                        page_url=page.url,
                    )
                )
            else:
                passed += 1

        return RuleEvaluationResult(
            rule_id=self.rule_id,
            category=self.category,
            passed=len(findings) == 0,
            findings=findings,
            pages_checked=checked,
            pages_passed=passed,
        )


class EmptyAnchorTextRule(BaseAuditRule):
    rule_id = "LINK-003"
    category = AuditCategory.SITE_STRUCTURE
    default_severity = FindingSeverity.LOW
    title = "Empty Anchor Text on Internal Link"
    description = (
        "Internal hyperlinks lack anchor text or use empty whitespace, missing keyword signals."
    )

    def evaluate(self, context: AuditEvaluationContext) -> RuleEvaluationResult:
        findings = []
        checked = 0
        pages_with_empty = set()

        for page in context.pages:
            checked += 1
            links = page.links_json or []
            empty_links = [
                lnk
                for lnk in links
                if lnk.get("is_internal")
                and (not lnk.get("anchor_text") or not lnk.get("anchor_text").strip())
            ]
            if empty_links:
                pages_with_empty.add(page.url)
                findings.append(
                    self.create_finding(
                        severity=FindingSeverity.LOW,
                        title=f"Internal Links with Empty Anchor Text ({len(empty_links)} found)",
                        description=f"Page {page.url} contains {len(empty_links)} internal hyperlinks with blank or whitespace-only anchor text.",
                        recommendation="Provide concise, descriptive anchor text on every internal link to assist accessibility and search engine context.",
                        evidence={"url": page.url, "empty_links_sample": empty_links[:5]},
                        page_url=page.url,
                    )
                )

        return RuleEvaluationResult(
            rule_id=self.rule_id,
            category=self.category,
            passed=len(findings) == 0,
            findings=findings,
            pages_checked=checked,
            pages_passed=max(0, checked - len(pages_with_empty)),
        )
