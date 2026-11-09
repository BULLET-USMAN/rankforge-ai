"""Canonical URL SEO audit rules."""

from __future__ import annotations

from urllib.parse import urlparse

from app.services.audit.base import BaseAuditRule
from app.services.audit.types import (
    AuditCategory,
    AuditEvaluationContext,
    FindingSeverity,
    RuleEvaluationResult,
)


class MissingCanonicalRule(BaseAuditRule):
    rule_id = "CANON-001"
    category = AuditCategory.CANONICAL
    default_severity = FindingSeverity.LOW
    title = "Missing Canonical Tag"
    description = "The page does not specify a rel='canonical' link element."

    def evaluate(self, context: AuditEvaluationContext) -> RuleEvaluationResult:
        findings = []
        checked = 0
        passed = 0

        for page in context.pages:
            if page.status_code != 200:
                continue
            checked += 1
            if not page.canonical_url or not page.canonical_url.strip():
                findings.append(
                    self.create_finding(
                        severity=FindingSeverity.LOW,
                        title="Missing Canonical Tag",
                        description=f"Page at {page.url} lacks a rel='canonical' link tag.",
                        recommendation="Add a self-referencing or target rel='canonical' tag to prevent duplicate content ambiguities.",
                        evidence={"url": page.url},
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


class InvalidCanonicalFragmentRule(BaseAuditRule):
    rule_id = "CANON-002"
    category = AuditCategory.CANONICAL
    default_severity = FindingSeverity.HIGH
    title = "Canonical URL Contains Fragment Identifier"
    description = "The canonical URL includes an anchor fragment (#) which search engines ignore for indexing purposes."

    def evaluate(self, context: AuditEvaluationContext) -> RuleEvaluationResult:
        findings = []
        checked = 0
        passed = 0

        for page in context.pages:
            if page.status_code != 200 or not page.canonical_url:
                continue
            checked += 1
            parsed = urlparse(page.canonical_url)
            if parsed.fragment:
                findings.append(
                    self.create_finding(
                        severity=FindingSeverity.HIGH,
                        title="Canonical URL Contains Fragment Identifier",
                        description=f"Page at {page.url} specifies canonical URL '{page.canonical_url}' with a '#' hash fragment.",
                        recommendation="Remove the fragment identifier from the canonical URL; canonical targets must be bare document URLs.",
                        evidence={"canonical_url": page.canonical_url, "fragment": parsed.fragment},
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


class BrokenCanonicalRule(BaseAuditRule):
    rule_id = "CANON-003"
    category = AuditCategory.CANONICAL
    default_severity = FindingSeverity.CRITICAL
    title = "Canonical Points to Broken Page (4xx/5xx)"
    description = "The canonical tag points to a URL that returns an error status code."

    def evaluate(self, context: AuditEvaluationContext) -> RuleEvaluationResult:
        findings = []
        checked = 0
        passed = 0

        for page in context.pages:
            if page.status_code != 200 or not page.canonical_url:
                continue
            checked += 1
            target = context.url_to_page.get(
                page.canonical_url
            ) or context.normalized_url_to_page.get(page.canonical_url)
            if target and target.status_code >= 400:
                findings.append(
                    self.create_finding(
                        severity=FindingSeverity.CRITICAL,
                        title=f"Canonical Points to HTTP {target.status_code} Error",
                        description=f"Page at {page.url} sets canonical target to {page.canonical_url}, which returns status {target.status_code}.",
                        recommendation="Update the canonical URL to point to a valid, live 200 OK document.",
                        evidence={
                            "canonical_url": page.canonical_url,
                            "target_status": target.status_code,
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


class RedirectCanonicalRule(BaseAuditRule):
    rule_id = "CANON-004"
    category = AuditCategory.CANONICAL
    default_severity = FindingSeverity.HIGH
    title = "Canonical Points to Redirecting URL"
    description = "The canonical tag points to a URL that returns an HTTP 3xx redirect."

    def evaluate(self, context: AuditEvaluationContext) -> RuleEvaluationResult:
        findings = []
        checked = 0
        passed = 0

        for page in context.pages:
            if page.status_code != 200 or not page.canonical_url:
                continue
            checked += 1
            target = context.url_to_page.get(
                page.canonical_url
            ) or context.normalized_url_to_page.get(page.canonical_url)
            if target and 300 <= target.status_code < 400:
                findings.append(
                    self.create_finding(
                        severity=FindingSeverity.HIGH,
                        title="Canonical Points to Redirecting URL",
                        description=f"Page at {page.url} sets canonical target to {page.canonical_url}, which redirects with HTTP {target.status_code}.",
                        recommendation="Point the canonical URL directly to the final 200 OK destination rather than intermediate redirect hops.",
                        evidence={
                            "canonical_url": page.canonical_url,
                            "target_status": target.status_code,
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


class CanonicalLoopRule(BaseAuditRule):
    rule_id = "CANON-005"
    category = AuditCategory.CANONICAL
    default_severity = FindingSeverity.CRITICAL
    title = "Circular Canonical Loop Detected"
    description = "Two or more pages point canonical tags to each other in a loop."

    def evaluate(self, context: AuditEvaluationContext) -> RuleEvaluationResult:
        findings = []
        checked = 0
        passed = 0

        for page in context.pages:
            if page.status_code != 200 or not page.canonical_url:
                continue
            checked += 1

            # Check if canonical target points back to this page
            target = context.url_to_page.get(
                page.canonical_url
            ) or context.normalized_url_to_page.get(page.canonical_url)
            if target and target.canonical_url:
                if (
                    target.canonical_url in (page.url, page.normalized_url)
                    and page.url != target.url
                ):
                    findings.append(
                        self.create_finding(
                            severity=FindingSeverity.CRITICAL,
                            title="Circular Canonical Loop",
                            description=f"Page {page.url} specifies canonical {target.url}, while {target.url} specifies canonical {page.url}.",
                            recommendation="Break the circular canonical loop by choosing one single definitive URL as the canonical version.",
                            evidence={"page_url": page.url, "target_url": target.url},
                            page_url=page.url,
                            fingerprint_key=f"{page.url}->{target.url}",
                        )
                    )
                    continue

            passed += 1

        return RuleEvaluationResult(
            rule_id=self.rule_id,
            category=self.category,
            passed=len(findings) == 0,
            findings=findings,
            pages_checked=checked,
            pages_passed=passed,
        )


class ExternalCanonicalRule(BaseAuditRule):
    rule_id = "CANON-006"
    category = AuditCategory.CANONICAL
    default_severity = FindingSeverity.INFORMATIONAL
    title = "Cross-Domain Canonical URL"
    description = "The canonical tag points to an external third-party domain."

    def evaluate(self, context: AuditEvaluationContext) -> RuleEvaluationResult:
        findings = []
        checked = 0
        passed = 0

        for page in context.pages:
            if page.status_code != 200 or not page.canonical_url:
                continue
            checked += 1
            parsed = urlparse(page.canonical_url)
            if parsed.netloc and parsed.netloc.lower() != context.primary_domain.lower():
                findings.append(
                    self.create_finding(
                        severity=FindingSeverity.INFORMATIONAL,
                        title="Cross-Domain Canonical URL",
                        description=f"Page at {page.url} sets canonical target to external domain '{parsed.netloc}'.",
                        recommendation="Confirm that this cross-domain canonicalization is intentional (e.g. syndicated content) and not a configuration mistake.",
                        evidence={
                            "canonical_url": page.canonical_url,
                            "target_domain": parsed.netloc,
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
