"""Metadata SEO audit rules: titles and meta descriptions."""

from __future__ import annotations

from typing import List

from app.services.audit.base import BaseAuditRule
from app.services.audit.types import (
    AuditCategory,
    AuditEvaluationContext,
    FindingSeverity,
    RuleEvaluationResult,
)


class MissingTitleRule(BaseAuditRule):
    rule_id = "META-001"
    category = AuditCategory.METADATA
    default_severity = FindingSeverity.CRITICAL
    title = "Missing Page Title Tag"
    description = "The page does not contain an HTML <title> tag."

    def evaluate(self, context: AuditEvaluationContext) -> RuleEvaluationResult:
        findings = []
        checked = 0
        passed = 0

        for page in context.pages:
            if page.status_code != 200:
                continue
            checked += 1
            if page.title is None:
                findings.append(
                    self.create_finding(
                        severity=FindingSeverity.CRITICAL,
                        title="Missing Page Title Tag",
                        description=f"Page at {page.url} is missing an HTML <title> tag in the document head.",
                        recommendation="Add a descriptive <title> tag inside the <head> element to communicate page topic to search engines and users.",
                        evidence={"url": page.url, "status_code": page.status_code},
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


class EmptyTitleRule(BaseAuditRule):
    rule_id = "META-002"
    category = AuditCategory.METADATA
    default_severity = FindingSeverity.HIGH
    title = "Empty Page Title Tag"
    description = "The page <title> tag is empty or contains only whitespace."

    def evaluate(self, context: AuditEvaluationContext) -> RuleEvaluationResult:
        findings = []
        checked = 0
        passed = 0

        for page in context.pages:
            if page.status_code != 200:
                continue
            checked += 1
            if page.title is not None and len(page.title.strip()) == 0:
                findings.append(
                    self.create_finding(
                        severity=FindingSeverity.HIGH,
                        title="Empty Page Title Tag",
                        description=f"Page at {page.url} has an empty <title> tag containing only whitespace.",
                        recommendation="Populate the <title> tag with a unique, descriptive page title reflecting the primary content.",
                        evidence={"url": page.url, "raw_title": page.title},
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


class DuplicateTitleRule(BaseAuditRule):
    rule_id = "META-003"
    category = AuditCategory.METADATA
    default_severity = FindingSeverity.MEDIUM
    title = "Duplicate Page Title"
    description = "Multiple indexable pages share identical <title> text."

    def evaluate(self, context: AuditEvaluationContext) -> RuleEvaluationResult:
        findings = []
        # Group titles across 200 OK pages
        title_map: dict[str, List[str]] = {}
        checked = 0

        for page in context.pages:
            if page.status_code != 200 or not page.title or not page.title.strip():
                continue
            checked += 1
            clean_title = page.title.strip()
            title_map.setdefault(clean_title, []).append(page.url)

        duplicates = {t: urls for t, urls in title_map.items() if len(urls) > 1}

        for title_text, urls in duplicates.items():
            for url in urls:
                findings.append(
                    self.create_finding(
                        severity=FindingSeverity.MEDIUM,
                        title="Duplicate Page Title",
                        description=f"Page at {url} shares its title '{title_text}' with {len(urls) - 1} other page(s).",
                        recommendation="Craft a distinctive title tag for each page so users and search engines can differentiate pages.",
                        evidence={
                            "title": title_text,
                            "shared_with": [u for u in urls if u != url],
                        },
                        page_url=url,
                        fingerprint_key=title_text,
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


class TitleLengthRule(BaseAuditRule):
    rule_id = "META-004"
    category = AuditCategory.METADATA
    default_severity = FindingSeverity.LOW
    title = "Suboptimal Title Tag Length"
    description = "Page title tag is too short (< 30 characters) or too long (> 65 characters)."

    def evaluate(self, context: AuditEvaluationContext) -> RuleEvaluationResult:
        findings = []
        checked = 0
        passed = 0

        for page in context.pages:
            if page.status_code != 200 or not page.title or not page.title.strip():
                continue
            checked += 1
            length = len(page.title.strip())
            if length < 30:
                findings.append(
                    self.create_finding(
                        severity=FindingSeverity.LOW,
                        title="Title Tag Too Short",
                        description=f"Page title is {length} characters long, which may not provide sufficient context for search engines.",
                        recommendation="Expand the title tag to between 30 and 65 characters to clearly communicate the topic and include primary keywords.",
                        evidence={"length": length, "title": page.title.strip()},
                        page_url=page.url,
                    )
                )
            elif length > 65:
                findings.append(
                    self.create_finding(
                        severity=FindingSeverity.INFORMATIONAL,
                        title="Title Tag May Truncate in SERPs",
                        description=f"Page title is {length} characters long and may be truncated on search engine results pages.",
                        recommendation="Keep primary keywords in the first 60 characters to ensure visibility in standard search result snippets.",
                        evidence={"length": length, "title": page.title.strip()},
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


class MissingMetaDescriptionRule(BaseAuditRule):
    rule_id = "META-005"
    category = AuditCategory.METADATA
    default_severity = FindingSeverity.MEDIUM
    title = "Missing Meta Description"
    description = "The page does not have a meta description tag."

    def evaluate(self, context: AuditEvaluationContext) -> RuleEvaluationResult:
        findings = []
        checked = 0
        passed = 0

        for page in context.pages:
            if page.status_code != 200:
                continue
            checked += 1
            if page.meta_description is None:
                findings.append(
                    self.create_finding(
                        severity=FindingSeverity.MEDIUM,
                        title="Missing Meta Description",
                        description=f"Page at {page.url} is missing a <meta name='description'> tag.",
                        recommendation="Add a concise meta description summarizing page value to encourage search snippet click-through.",
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


class EmptyMetaDescriptionRule(BaseAuditRule):
    rule_id = "META-006"
    category = AuditCategory.METADATA
    default_severity = FindingSeverity.LOW
    title = "Empty Meta Description"
    description = "The meta description tag is empty or contains only whitespace."

    def evaluate(self, context: AuditEvaluationContext) -> RuleEvaluationResult:
        findings = []
        checked = 0
        passed = 0

        for page in context.pages:
            if page.status_code != 200:
                continue
            checked += 1
            if page.meta_description is not None and len(page.meta_description.strip()) == 0:
                findings.append(
                    self.create_finding(
                        severity=FindingSeverity.LOW,
                        title="Empty Meta Description",
                        description=f"Page at {page.url} has an empty meta description attribute.",
                        recommendation="Supply a concise summary of the page content within the meta description attribute.",
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


class DuplicateMetaDescriptionRule(BaseAuditRule):
    rule_id = "META-007"
    category = AuditCategory.METADATA
    default_severity = FindingSeverity.LOW
    title = "Duplicate Meta Description"
    description = "Multiple pages share the exact same meta description text."

    def evaluate(self, context: AuditEvaluationContext) -> RuleEvaluationResult:
        findings = []
        desc_map: dict[str, List[str]] = {}
        checked = 0

        for page in context.pages:
            if (
                page.status_code != 200
                or not page.meta_description
                or not page.meta_description.strip()
            ):
                continue
            checked += 1
            clean_desc = page.meta_description.strip()
            desc_map.setdefault(clean_desc, []).append(page.url)

        duplicates = {d: urls for d, urls in desc_map.items() if len(urls) > 1}

        for desc_text, urls in duplicates.items():
            for url in urls:
                findings.append(
                    self.create_finding(
                        severity=FindingSeverity.LOW,
                        title="Duplicate Meta Description",
                        description=f"Page at {url} shares its meta description with {len(urls) - 1} other page(s).",
                        recommendation="Provide distinct meta descriptions for each page reflecting each URL's specific purpose.",
                        evidence={
                            "description_sample": desc_text[:80] + "...",
                            "shared_with": [u for u in urls if u != url],
                        },
                        page_url=url,
                        fingerprint_key=desc_text[:64],
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


class MetaDescriptionLengthRule(BaseAuditRule):
    rule_id = "META-008"
    category = AuditCategory.METADATA
    default_severity = FindingSeverity.LOW
    title = "Suboptimal Meta Description Length"
    description = "Meta description is too short (< 70 characters) or too long (> 160 characters)."

    def evaluate(self, context: AuditEvaluationContext) -> RuleEvaluationResult:
        findings = []
        checked = 0
        passed = 0

        for page in context.pages:
            if (
                page.status_code != 200
                or not page.meta_description
                or not page.meta_description.strip()
            ):
                continue
            checked += 1
            length = len(page.meta_description.strip())
            if length < 70:
                findings.append(
                    self.create_finding(
                        severity=FindingSeverity.INFORMATIONAL,
                        title="Meta Description Too Short",
                        description=f"Meta description is only {length} characters long, missing opportunity for click-driving context.",
                        recommendation="Aim for 120-160 characters with clear benefits and a gentle call to action.",
                        evidence={
                            "length": length,
                            "meta_description": page.meta_description.strip(),
                        },
                        page_url=page.url,
                    )
                )
            elif length > 160:
                findings.append(
                    self.create_finding(
                        severity=FindingSeverity.INFORMATIONAL,
                        title="Meta Description May Truncate",
                        description=f"Meta description is {length} characters long and will likely truncate in search snippet displays.",
                        recommendation="Keep core message within 155-160 characters so Google does not cut it off in search results.",
                        evidence={
                            "length": length,
                            "meta_description": page.meta_description.strip(),
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
