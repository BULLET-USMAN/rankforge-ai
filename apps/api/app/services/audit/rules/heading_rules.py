"""Heading structure SEO audit rules."""

from __future__ import annotations

from typing import List

from app.services.audit.base import BaseAuditRule
from app.services.audit.types import (
    AuditCategory,
    AuditEvaluationContext,
    FindingSeverity,
    RuleEvaluationResult,
)


class MissingH1Rule(BaseAuditRule):
    rule_id = "HEAD-001"
    category = AuditCategory.HEADINGS
    default_severity = FindingSeverity.HIGH
    title = "Missing H1 Heading"
    description = "The page does not contain any primary <h1> heading tag."

    def evaluate(self, context: AuditEvaluationContext) -> RuleEvaluationResult:
        findings = []
        checked = 0
        passed = 0

        for page in context.pages:
            if page.status_code != 200:
                continue
            checked += 1
            if page.h1_count == 0:
                findings.append(
                    self.create_finding(
                        severity=FindingSeverity.HIGH,
                        title="Missing H1 Heading",
                        description=f"Page at {page.url} lacks a primary <h1> heading tag.",
                        recommendation="Add an <h1> heading tag that clearly introduces the main topic of the page.",
                        evidence={"url": page.url, "h1_count": 0},
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


class MultipleH1Rule(BaseAuditRule):
    rule_id = "HEAD-002"
    category = AuditCategory.HEADINGS
    default_severity = FindingSeverity.INFORMATIONAL
    title = "Multiple H1 Headings Detected"
    description = "The page contains more than one <h1> heading."

    def evaluate(self, context: AuditEvaluationContext) -> RuleEvaluationResult:
        findings = []
        checked = 0
        passed = 0

        for page in context.pages:
            if page.status_code != 200:
                continue
            checked += 1
            if page.h1_count > 1:
                findings.append(
                    self.create_finding(
                        severity=FindingSeverity.INFORMATIONAL,
                        title="Multiple H1 Headings Detected",
                        description=f"Page at {page.url} has {page.h1_count} <h1> headings. While HTML5 permits multiple H1s, best practice favors a single top-level heading per page.",
                        recommendation="Consider keeping only one primary <h1> representing the main page topic and converting secondary headings to <h2>.",
                        evidence={"url": page.url, "h1_count": page.h1_count},
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


class EmptyH1Rule(BaseAuditRule):
    rule_id = "HEAD-003"
    category = AuditCategory.HEADINGS
    default_severity = FindingSeverity.MEDIUM
    title = "Empty H1 Heading"
    description = "An <h1> heading on the page contains empty text or only whitespace."

    def evaluate(self, context: AuditEvaluationContext) -> RuleEvaluationResult:
        findings = []
        checked = 0
        passed = 0

        for page in context.pages:
            if page.status_code != 200 or page.h1_count == 0:
                continue
            checked += 1

            headings = page.headings_json or {}
            h1_items = headings.get("h1", {}).get("items", [])
            has_empty = any(len(item.get("text", "").strip()) == 0 for item in h1_items)

            if has_empty:
                findings.append(
                    self.create_finding(
                        severity=FindingSeverity.MEDIUM,
                        title="Empty H1 Heading",
                        description=f"Page at {page.url} contains an empty <h1> element with no descriptive text.",
                        recommendation="Ensure all <h1> tags contain meaningful text describing the primary subject.",
                        evidence={"url": page.url, "h1_items": h1_items},
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


class HeadingHierarchySkipRule(BaseAuditRule):
    rule_id = "HEAD-004"
    category = AuditCategory.HEADINGS
    default_severity = FindingSeverity.LOW
    title = "Heading Level Skipped"
    description = "Page jumps heading levels (e.g., from H1 directly to H3 without an intermediate H2)."

    def evaluate(self, context: AuditEvaluationContext) -> RuleEvaluationResult:
        findings = []
        checked = 0
        passed = 0

        for page in context.pages:
            if page.status_code != 200 or page.h1_count == 0:
                continue
            checked += 1

            headings = page.headings_json or {}
            h1_count = headings.get("h1", {}).get("count", 0)
            h2_count = headings.get("h2", {}).get("count", 0)
            h3_count = headings.get("h3", {}).get("count", 0)

            # If there are H3 tags but 0 H2 tags, hierarchy is skipped
            if h1_count > 0 and h2_count == 0 and h3_count > 0:
                findings.append(
                    self.create_finding(
                        severity=FindingSeverity.LOW,
                        title="Heading Level Skipped (H1 to H3)",
                        description=f"Page at {page.url} has H1 and H3 headings but lacks any H2 subheadings.",
                        recommendation="Organize page content hierarchically: introduce section topics with <h2> tags before using <h3> subheadings.",
                        evidence={"h1_count": h1_count, "h2_count": h2_count, "h3_count": h3_count},
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


class DuplicateH1Rule(BaseAuditRule):
    rule_id = "HEAD-005"
    category = AuditCategory.HEADINGS
    default_severity = FindingSeverity.LOW
    title = "Duplicate H1 Tag Across Pages"
    description = "Multiple distinct URLs share the identical primary <h1> heading text."

    def evaluate(self, context: AuditEvaluationContext) -> RuleEvaluationResult:
        findings = []
        checked = 0
        h1_map: dict[str, List[str]] = {}

        for page in context.pages:
            if page.status_code != 200 or page.h1_count == 0:
                continue
            checked += 1

            headings = page.headings_json or {}
            h1_items = headings.get("h1", {}).get("items", [])
            if h1_items:
                first_h1_text = h1_items[0].get("text", "").strip()
                if first_h1_text:
                    h1_map.setdefault(first_h1_text, []).append(page.url)

        duplicates = {txt: urls for txt, urls in h1_map.items() if len(urls) > 1}

        for h1_text, urls in duplicates.items():
            for url in urls:
                findings.append(
                    self.create_finding(
                        severity=FindingSeverity.LOW,
                        title="Duplicate H1 Tag Across Pages",
                        description=f"Page at {url} shares its H1 heading '{h1_text}' with {len(urls) - 1} other page(s).",
                        recommendation="Assign distinct H1 headings to each page so users and search engines can immediately grasp each page's distinct purpose.",
                        evidence={"h1_text": h1_text, "shared_with": [u for u in urls if u != url]},
                        page_url=url,
                        fingerprint_key=h1_text,
                    )
                )

        passed = checked - len(findings)
        return RuleEvaluationResult(
            rule_id=self.rule_id,
            category=self.category,
            passed=len(findings) == 0,
            findings=findings,
            pages_checked=checked,
            pages_passed=max(0, passed),
        )
