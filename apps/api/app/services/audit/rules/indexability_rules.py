"""Indexability SEO audit rules: meta robots and X-Robots-Tag directives."""

from __future__ import annotations

from app.services.audit.base import BaseAuditRule
from app.services.audit.types import (
    AuditCategory,
    AuditEvaluationContext,
    FindingSeverity,
    RuleEvaluationResult,
)


class MetaRobotsNoindexRule(BaseAuditRule):
    rule_id = "INDX-001"
    category = AuditCategory.INDEXABILITY
    default_severity = FindingSeverity.HIGH
    title = "Page Disallowed via Meta Robots Noindex"
    description = "The page contains a <meta name='robots' content='noindex'> directive instructing search engines not to index it."

    def evaluate(self, context: AuditEvaluationContext) -> RuleEvaluationResult:
        findings = []
        checked = 0
        passed = 0

        for page in context.pages:
            if page.status_code != 200:
                continue
            checked += 1
            meta_robots = (page.meta_robots or "").lower()
            if "noindex" in meta_robots or "none" in meta_robots:
                findings.append(
                    self.create_finding(
                        severity=FindingSeverity.HIGH,
                        title="Meta Robots Noindex Directive",
                        description=f"Page at {page.url} specifies '{page.meta_robots}', preventing search engines from indexing the page.",
                        recommendation="If this page is intended to be found in search engines, remove the 'noindex' directive from the meta robots tag.",
                        evidence={"meta_robots": page.meta_robots, "url": page.url},
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


class XRobotsTagNoindexRule(BaseAuditRule):
    rule_id = "INDX-002"
    category = AuditCategory.INDEXABILITY
    default_severity = FindingSeverity.HIGH
    title = "Page Blocked via X-Robots-Tag HTTP Header"
    description = "The HTTP response header includes an X-Robots-Tag directive instructing search bots not to index the page."

    def evaluate(self, context: AuditEvaluationContext) -> RuleEvaluationResult:
        findings = []
        checked = 0
        passed = 0

        for page in context.pages:
            if page.status_code != 200:
                continue
            checked += 1
            x_robots = (page.x_robots_tag or "").lower()
            if "noindex" in x_robots or "none" in x_robots:
                findings.append(
                    self.create_finding(
                        severity=FindingSeverity.HIGH,
                        title="X-Robots-Tag Noindex Header",
                        description=f"HTTP response for {page.url} includes 'X-Robots-Tag: {page.x_robots_tag}', preventing indexing.",
                        recommendation="If this page should be indexed, adjust web server or application header configuration to remove 'noindex'.",
                        evidence={"x_robots_tag": page.x_robots_tag, "url": page.url},
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


class MetaRobotsNofollowRule(BaseAuditRule):
    rule_id = "INDX-003"
    category = AuditCategory.INDEXABILITY
    default_severity = FindingSeverity.MEDIUM
    title = "Page Contains Nofollow Directive"
    description = "Page signals search engines not to follow any hyperlinks found on the page."

    def evaluate(self, context: AuditEvaluationContext) -> RuleEvaluationResult:
        findings = []
        checked = 0
        passed = 0

        for page in context.pages:
            if page.status_code != 200:
                continue
            checked += 1
            meta_robots = (page.meta_robots or "").lower()
            x_robots = (page.x_robots_tag or "").lower()

            if "nofollow" in meta_robots or "nofollow" in x_robots or "none" in meta_robots:
                findings.append(
                    self.create_finding(
                        severity=FindingSeverity.MEDIUM,
                        title="Nofollow Directive on Page",
                        description=f"Page at {page.url} specifies 'nofollow', preventing search engines from discovering or passing signals to outlinks.",
                        recommendation="Remove 'nofollow' from page-level directives unless this page explicitly contains untrusted user-submitted links.",
                        evidence={"meta_robots": page.meta_robots, "x_robots_tag": page.x_robots_tag},
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


class SitemapUrlNoindexRule(BaseAuditRule):
    rule_id = "INDX-004"
    category = AuditCategory.INDEXABILITY
    default_severity = FindingSeverity.CRITICAL
    title = "Sitemap Contains Noindex URL"
    description = "A URL submitted in an XML sitemap is marked as noindex, creating conflicting indexing signals."

    def evaluate(self, context: AuditEvaluationContext) -> RuleEvaluationResult:
        findings = []
        checked = 0
        passed = 0

        # Collect URLs found via sitemap
        sitemap_pages = [p for p in context.pages if p.discovery_method == "sitemap"]
        checked = len(sitemap_pages)

        for page in sitemap_pages:
            meta_robots = (page.meta_robots or "").lower()
            x_robots = (page.x_robots_tag or "").lower()
            is_noindex = ("noindex" in meta_robots) or ("noindex" in x_robots) or ("none" in meta_robots)

            if is_noindex:
                findings.append(
                    self.create_finding(
                        severity=FindingSeverity.CRITICAL,
                        title="Sitemap URL Has Noindex Directive",
                        description=f"URL {page.url} is listed in an XML sitemap but returns a noindex directive.",
                        recommendation="Either remove the URL from the XML sitemap or remove the noindex directive so search engines receive consistent instructions.",
                        evidence={"url": page.url, "meta_robots": page.meta_robots, "x_robots_tag": page.x_robots_tag},
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
