"""HTTP status, internal links health, and redirect SEO audit rules."""

from __future__ import annotations

from app.services.audit.base import BaseAuditRule
from app.services.audit.types import (
    AuditCategory,
    AuditEvaluationContext,
    FindingSeverity,
    RuleEvaluationResult,
)


class InternalDeadLinkRule(BaseAuditRule):
    rule_id = "HTTP-001"
    category = AuditCategory.LINKS_HTTP
    default_severity = FindingSeverity.CRITICAL
    title = "Internal Link to Broken Page (4xx)"
    description = (
        "An internal link points to a page that returns a 4xx client error (e.g., 404 Not Found)."
    )

    def evaluate(self, context: AuditEvaluationContext) -> RuleEvaluationResult:
        findings = []
        checked = 0
        broken_targets: set[str] = set()

        for page in context.pages:
            checked += 1
            links = page.links_json or []
            for link in links:
                if not link.get("is_internal"):
                    continue
                target_url = link.get("target_url") or link.get("url")
                if not target_url:
                    continue
                target_page = context.url_to_page.get(
                    target_url
                ) or context.normalized_url_to_page.get(target_url)
                if target_page and 400 <= target_page.status_code < 500:
                    broken_targets.add(target_url)
                    findings.append(
                        self.create_finding(
                            severity=FindingSeverity.CRITICAL,
                            title=f"Internal Link to Broken {target_page.status_code} Page",
                            description=f"Page {page.url} links to broken URL {target_url} (HTTP {target_page.status_code}).",
                            recommendation="Update or remove the hyperlink so users and search bots do not land on dead pages.",
                            evidence={
                                "source_url": page.url,
                                "target_url": target_url,
                                "status_code": target_page.status_code,
                                "anchor_text": link.get("anchor_text", ""),
                            },
                            page_url=page.url,
                            fingerprint_key=f"{page.url}->{target_url}",
                        )
                    )

        return RuleEvaluationResult(
            rule_id=self.rule_id,
            category=self.category,
            passed=len(findings) == 0,
            findings=findings,
            pages_checked=checked,
            pages_passed=max(0, checked - len(broken_targets)),
        )


class InternalServerErrorLinkRule(BaseAuditRule):
    rule_id = "HTTP-002"
    category = AuditCategory.LINKS_HTTP
    default_severity = FindingSeverity.CRITICAL
    title = "Internal Link to Server Error Page (5xx)"
    description = "An internal link points to a page returning a 5xx server error."

    def evaluate(self, context: AuditEvaluationContext) -> RuleEvaluationResult:
        findings = []
        checked = 0

        for page in context.pages:
            checked += 1
            links = page.links_json or []
            for link in links:
                if not link.get("is_internal"):
                    continue
                target_url = link.get("target_url") or link.get("url")
                if not target_url:
                    continue
                target_page = context.url_to_page.get(
                    target_url
                ) or context.normalized_url_to_page.get(target_url)
                if target_page and target_page.status_code >= 500:
                    findings.append(
                        self.create_finding(
                            severity=FindingSeverity.CRITICAL,
                            title=f"Internal Link to Server Error (HTTP {target_page.status_code})",
                            description=f"Page {page.url} links to internal URL {target_url} which crashed with HTTP {target_page.status_code}.",
                            recommendation="Investigate the backend crash on the target route and fix the application failure.",
                            evidence={
                                "source_url": page.url,
                                "target_url": target_url,
                                "status_code": target_page.status_code,
                            },
                            page_url=page.url,
                            fingerprint_key=f"{page.url}->{target_url}",
                        )
                    )

        return RuleEvaluationResult(
            rule_id=self.rule_id,
            category=self.category,
            passed=len(findings) == 0,
            findings=findings,
            pages_checked=checked,
            pages_passed=max(0, checked - len(findings)),
        )


class InternalRedirectLinkRule(BaseAuditRule):
    rule_id = "HTTP-003"
    category = AuditCategory.LINKS_HTTP
    default_severity = FindingSeverity.MEDIUM
    title = "Internal Link to Redirect (3xx)"
    description = "An internal link points to a URL that returns an HTTP redirect instead of linking directly to final destination."

    def evaluate(self, context: AuditEvaluationContext) -> RuleEvaluationResult:
        findings = []
        checked = 0

        for page in context.pages:
            checked += 1
            links = page.links_json or []
            for link in links:
                if not link.get("is_internal"):
                    continue
                target_url = link.get("target_url") or link.get("url")
                if not target_url:
                    continue
                target_page = context.url_to_page.get(
                    target_url
                ) or context.normalized_url_to_page.get(target_url)
                if target_page and 300 <= target_page.status_code < 400:
                    findings.append(
                        self.create_finding(
                            severity=FindingSeverity.MEDIUM,
                            title="Internal Link Points to Redirect",
                            description=f"Page {page.url} links to redirecting URL {target_url} (HTTP {target_page.status_code}).",
                            recommendation="Update internal hyperlinks to point directly to the destination URL, saving crawl budget and latency.",
                            evidence={
                                "source_url": page.url,
                                "target_url": target_url,
                                "redirect_code": target_page.status_code,
                            },
                            page_url=page.url,
                            fingerprint_key=f"{page.url}->{target_url}",
                        )
                    )

        return RuleEvaluationResult(
            rule_id=self.rule_id,
            category=self.category,
            passed=len(findings) == 0,
            findings=findings,
            pages_checked=checked,
            pages_passed=max(0, checked - len(findings)),
        )


class RedirectChainRule(BaseAuditRule):
    rule_id = "HTTP-004"
    category = AuditCategory.LINKS_HTTP
    default_severity = FindingSeverity.HIGH
    title = "Redirect Chain Detected (> 1 hop)"
    description = "A crawled URL underwent multiple redirect hops before resolving."

    def evaluate(self, context: AuditEvaluationContext) -> RuleEvaluationResult:
        findings = []
        checked = 0
        passed = 0

        for page in context.pages:
            chain = page.redirect_chain_json or []
            checked += 1
            if len(chain) > 1:
                findings.append(
                    self.create_finding(
                        severity=FindingSeverity.HIGH,
                        title=f"Redirect Chain Detected ({len(chain)} hops)",
                        description=f"URL {page.url} resolved through {len(chain)} redirect hops: {' -> '.join(h.get('to_url', '') for h in chain)}.",
                        recommendation="Eliminate intermediate hops and redirect directly to the final canonical destination in a single 301 response.",
                        evidence={"url": page.url, "hop_count": len(chain), "chain": chain},
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


class SlowPageLatencyRule(BaseAuditRule):
    rule_id = "HTTP-005"
    category = AuditCategory.LINKS_HTTP
    default_severity = FindingSeverity.MEDIUM
    title = "Slow Server Response Time (> 2000 ms)"
    description = "Page response latency exceeded 2000 ms during crawling."

    def evaluate(self, context: AuditEvaluationContext) -> RuleEvaluationResult:
        findings = []
        checked = 0
        passed = 0

        for page in context.pages:
            if page.status_code != 200:
                continue
            checked += 1
            if page.response_time_ms > 2000.0:
                findings.append(
                    self.create_finding(
                        severity=FindingSeverity.MEDIUM,
                        title=f"Slow Response Latency ({round(page.response_time_ms)} ms)",
                        description=f"Page {page.url} took {round(page.response_time_ms)} ms to respond to the crawler fetch.",
                        recommendation="Optimize server-side response times, enable caching, and evaluate database queries to achieve < 800 ms TTFB.",
                        evidence={"url": page.url, "response_time_ms": page.response_time_ms},
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
