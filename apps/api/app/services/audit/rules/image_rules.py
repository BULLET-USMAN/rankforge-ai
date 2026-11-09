"""Image SEO audit rules: missing alt attributes and generic alt text."""

from __future__ import annotations

from app.services.audit.base import BaseAuditRule
from app.services.audit.types import (
    AuditCategory,
    AuditEvaluationContext,
    FindingSeverity,
    RuleEvaluationResult,
)

GENERIC_ALT_WORDS = {
    "image",
    "photo",
    "picture",
    "pic",
    "logo",
    "icon",
    "placeholder",
    "graphic",
    "banner",
}


class MissingImageAltRule(BaseAuditRule):
    rule_id = "IMG-001"
    category = AuditCategory.IMAGES
    default_severity = FindingSeverity.MEDIUM
    title = "Images Missing Alt Attribute"
    description = (
        "Images on the page do not include an alt attribute for accessibility and search indexing."
    )

    def evaluate(self, context: AuditEvaluationContext) -> RuleEvaluationResult:
        findings = []
        checked = 0
        passed = 0

        # Check if the snapshot has image data available
        has_any_image_field = any(
            hasattr(p, "images_json") and p.images_json is not None for p in context.pages
        )
        if not has_any_image_field or len(context.pages) == 0:
            return RuleEvaluationResult(
                rule_id=self.rule_id,
                category=self.category,
                passed=True,
                status="not_evaluated",
                findings=[],
                pages_checked=0,
                pages_passed=0,
                reason="Image data was not captured in this crawl snapshot. A recrawl is required to evaluate image alt attributes.",
            )

        for page in context.pages:
            if page.status_code != 200:
                continue
            images = getattr(page, "images_json", None) or []
            if not images and getattr(page, "images_count", 0) == 0:
                continue

            checked += 1
            # Note: has_alt is False only when the alt attribute is completely omitted.
            # Empty alt="" (is_empty_alt=True) is valid for decorative images and should NOT be flagged as missing.
            missing_alt_images = [img for img in images if not img.get("has_alt", True)]

            if missing_alt_images:
                findings.append(
                    self.create_finding(
                        severity=FindingSeverity.MEDIUM,
                        title=f"{len(missing_alt_images)} Image(s) Missing Alt Attribute",
                        description=f"Page {page.url} contains {len(missing_alt_images)} image element(s) with no alt attribute.",
                        recommendation="Add descriptive alt attributes to informational images, or use alt='' if the image is purely decorative.",
                        evidence={
                            "url": page.url,
                            "missing_alt_count": len(missing_alt_images),
                            "images_sample": missing_alt_images[:5],
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
            status="evaluated",
            findings=findings,
            pages_checked=checked,
            pages_passed=passed,
        )


class GenericImageAltRule(BaseAuditRule):
    rule_id = "IMG-002"
    category = AuditCategory.IMAGES
    default_severity = FindingSeverity.LOW
    title = "Generic or Uninformative Alt Text"
    description = "Images use generic placeholder words (e.g. 'image', 'photo', 'logo') instead of descriptive context."

    def evaluate(self, context: AuditEvaluationContext) -> RuleEvaluationResult:
        findings = []
        checked = 0
        passed = 0

        has_any_image_field = any(
            hasattr(p, "images_json") and p.images_json is not None for p in context.pages
        )
        if not has_any_image_field or len(context.pages) == 0:
            return RuleEvaluationResult(
                rule_id=self.rule_id,
                category=self.category,
                passed=True,
                status="not_evaluated",
                findings=[],
                pages_checked=0,
                pages_passed=0,
                reason="Image data was not captured in this crawl snapshot. A recrawl is required to evaluate image alt attributes.",
            )

        for page in context.pages:
            if page.status_code != 200:
                continue
            images = getattr(page, "images_json", None) or []
            if not images:
                continue

            checked += 1
            generic_images = []
            for img in images:
                alt = (img.get("alt") or "").strip().lower()
                if alt in GENERIC_ALT_WORDS:
                    generic_images.append(img)

            if generic_images:
                findings.append(
                    self.create_finding(
                        severity=FindingSeverity.LOW,
                        title=f"{len(generic_images)} Image(s) with Generic Alt Text",
                        description=f"Page {page.url} has images with uninformative alt text like '{generic_images[0].get('alt')}'.",
                        recommendation="Replace generic placeholder terms with specific descriptions of what each image portrays.",
                        evidence={
                            "url": page.url,
                            "generic_alt_count": len(generic_images),
                            "images_sample": generic_images[:5],
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
            status="evaluated",
            findings=findings,
            pages_checked=checked,
            pages_passed=passed,
        )
