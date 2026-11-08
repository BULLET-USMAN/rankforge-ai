"""Structured data and XML sitemap SEO audit rules."""

from __future__ import annotations

from app.services.audit.base import BaseAuditRule
from app.services.audit.types import (
    AuditCategory,
    AuditEvaluationContext,
    FindingSeverity,
    RuleEvaluationResult,
)


class MalformedJsonLdRule(BaseAuditRule):
    rule_id = "SD-001"
    category = AuditCategory.STRUCTURED_DATA_SITEMAPS
    default_severity = FindingSeverity.HIGH
    title = "Malformed JSON-LD Syntax Error"
    description = "A JSON-LD structured data block contains invalid JSON syntax and cannot be parsed by search engines."

    def evaluate(self, context: AuditEvaluationContext) -> RuleEvaluationResult:
        findings = []
        checked = 0
        passed = 0

        has_sd_field = any(hasattr(p, "structured_data_json") and p.structured_data_json is not None for p in context.pages)
        if not has_sd_field or len(context.pages) == 0:
            return RuleEvaluationResult(
                rule_id=self.rule_id,
                category=self.category,
                passed=True,
                status="not_evaluated",
                findings=[],
                pages_checked=0,
                pages_passed=0,
                reason="Structured data was not captured in this crawl snapshot. A recrawl is required to evaluate JSON-LD schema.",
            )

        for page in context.pages:
            if page.status_code != 200:
                continue
            blocks = getattr(page, "structured_data_json", None) or []
            if not blocks:
                continue

            checked += 1
            syntax_errors = [b for b in blocks if not b.get("is_valid_json", True)]

            if syntax_errors:
                findings.append(
                    self.create_finding(
                        severity=FindingSeverity.HIGH,
                        title=f"{len(syntax_errors)} Malformed JSON-LD Block(s)",
                        description=f"Page {page.url} contains invalid JSON-LD syntax: {syntax_errors[0].get('error_message', 'JSON parse error')}.",
                        recommendation="Validate JSON-LD structured data syntax using Schema.org or Google Rich Results Test to fix syntax errors.",
                        evidence={"url": page.url, "error_details": syntax_errors[:3]},
                        page_url=page.url,
                    )
                )
            else:
                passed += 1

        return RuleEvaluationResult(
            rule_id=self.rule_id,
            category=self.category,
            passed=len(findings) == 0,
            status="evaluated",
            findings=findings,
            pages_checked=checked,
            pages_passed=passed,
        )


class MissingSchemaTypeRule(BaseAuditRule):
    rule_id = "SD-002"
    category = AuditCategory.STRUCTURED_DATA_SITEMAPS
    default_severity = FindingSeverity.MEDIUM
    title = "JSON-LD Missing @type or @context"
    description = "Structured data block does not define standard @type or @context attributes."

    def evaluate(self, context: AuditEvaluationContext) -> RuleEvaluationResult:
        findings = []
        checked = 0
        passed = 0

        has_sd_field = any(hasattr(p, "structured_data_json") and p.structured_data_json is not None for p in context.pages)
        if not has_sd_field or len(context.pages) == 0:
            return RuleEvaluationResult(
                rule_id=self.rule_id,
                category=self.category,
                passed=True,
                status="not_evaluated",
                findings=[],
                pages_checked=0,
                pages_passed=0,
                reason="Structured data was not captured in this crawl snapshot. A recrawl is required to evaluate JSON-LD schema.",
            )

        for page in context.pages:
            if page.status_code != 200:
                continue
            blocks = getattr(page, "structured_data_json", None) or []
            valid_blocks = [b for b in blocks if b.get("is_valid_json", True)]
            if not valid_blocks:
                continue

            checked += 1
            missing_types = [b for b in valid_blocks if not b.get("types")]

            if missing_types:
                findings.append(
                    self.create_finding(
                        severity=FindingSeverity.MEDIUM,
                        title="JSON-LD Block Missing @type Definition",
                        description=f"Page {page.url} contains a JSON-LD structured data block without a recognized @type declaration.",
                        recommendation="Define appropriate Schema.org @type (e.g., 'Article', 'Organization', 'Product') inside the JSON-LD snippet.",
                        evidence={"url": page.url, "invalid_blocks_count": len(missing_types)},
                        page_url=page.url,
                    )
                )
            else:
                passed += 1

        return RuleEvaluationResult(
            rule_id=self.rule_id,
            category=self.category,
            passed=len(findings) == 0,
            status="evaluated",
            findings=findings,
            pages_checked=checked,
            pages_passed=passed,
        )


class SitemapErrorRule(BaseAuditRule):
    rule_id = "SMAP-001"
    category = AuditCategory.STRUCTURED_DATA_SITEMAPS
    default_severity = FindingSeverity.HIGH
    title = "XML Sitemap Returned Error Status"
    description = "An XML sitemap discovered in robots.txt or standard paths failed to fetch or parse."

    def evaluate(self, context: AuditEvaluationContext) -> RuleEvaluationResult:
        findings = []
        checked = len(context.sitemaps)
        passed = 0

        for sm in context.sitemaps:
            status = getattr(sm, "status", "")
            code = getattr(sm, "status_code", 0)

            if status == "failed" or code >= 400:
                findings.append(
                    self.create_finding(
                        severity=FindingSeverity.HIGH,
                        title=f"XML Sitemap Error ({sm.url})",
                        description=f"Sitemap {sm.url} returned HTTP {code} or failed: {getattr(sm, 'error_details', 'Unreachable')}.",
                        recommendation="Ensure XML sitemaps are reachable, return HTTP 200, and are served with valid XML content-type.",
                        evidence={"sitemap_url": sm.url, "status_code": code, "error": getattr(sm, "error_details", None)},
                        page_url=sm.url,
                    )
                )
            else:
                passed += 1

        return RuleEvaluationResult(
            rule_id=self.rule_id,
            category=self.category,
            passed=len(findings) == 0,
            status="evaluated",
            findings=findings,
            pages_checked=checked,
            pages_passed=passed,
        )


class SitemapDuplicateUrlRule(BaseAuditRule):
    rule_id = "SMAP-002"
    category = AuditCategory.STRUCTURED_DATA_SITEMAPS
    default_severity = FindingSeverity.LOW
    title = "Duplicate URLs in XML Sitemap"
    description = "Sitemap contains multiple entries pointing to the identical target URL."

    def evaluate(self, context: AuditEvaluationContext) -> RuleEvaluationResult:
        findings = []
        checked = 0
        passed = 0

        # Gather pages discovered from sitemap
        sitemap_urls = [p.url for p in context.pages if p.discovery_method == "sitemap"]
        checked = len(sitemap_urls)

        seen: set[str] = set()
        duplicates: set[str] = set()
        for u in sitemap_urls:
            if u in seen:
                duplicates.add(u)
            seen.add(u)

        if duplicates:
            findings.append(
                self.create_finding(
                    severity=FindingSeverity.LOW,
                    title=f"{len(duplicates)} Duplicate URL(s) in XML Sitemap",
                    description=f"The sitemap files contain repeated entries for {len(duplicates)} URL(s).",
                    recommendation="Remove redundant URL elements from XML sitemap files to prevent unnecessary crawling and indexing bloat.",
                    evidence={"duplicate_urls": list(duplicates)[:10]},
                )
            )

        passed = checked - len(duplicates)
        return RuleEvaluationResult(
            rule_id=self.rule_id,
            category=self.category,
            passed=len(findings) == 0,
            status="evaluated",
            findings=findings,
            pages_checked=checked,
            pages_passed=max(0, passed),
        )
