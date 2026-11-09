"""Unit tests for context building, output validation, and prioritizer."""

from __future__ import annotations

import pytest

from app.models.seo_audit_finding import SEOAuditFinding
from app.services.ai.exceptions import AIValidationError
from app.services.ai.prioritizer import RecommendationPrioritizer
from app.services.ai.types import (
    RawAIOptimizationOutput,
    RecommendationPriority,
    RecommendationType,
)
from app.services.ai.validator import RecommendationValidator


def test_validator_rejects_empty_suggestion():
    output = RawAIOptimizationOutput(
        suggested_value="   ",
        explanation="Test",
    )
    with pytest.raises(AIValidationError) as exc:
        RecommendationValidator.validate_and_clean(
            output=output,
            rec_type=RecommendationType.TITLE_OPTIMIZATION,
            evidence_meta={},
        )
    assert "empty suggested value" in str(exc.value)


def test_validator_filters_unauthorized_internal_link_targets():
    output = RawAIOptimizationOutput(
        suggested_value=(
            "Add link to https://example.com/authorized-page and "
            "also link to https://malicious-external-site.com/spam"
        ),
        explanation="Internal linking proposal",
    )
    evidence_meta = {"eligible_target_urls": ["https://example.com/authorized-page"]}
    validated = RecommendationValidator.validate_and_clean(
        output=output,
        rec_type=RecommendationType.INTERNAL_LINKING,
        evidence_meta=evidence_meta,
    )
    assert "https://example.com/authorized-page" in validated.suggested_value
    assert "https://malicious-external-site.com/spam" not in validated.suggested_value
    assert "[Unverified link target removed" in validated.suggested_value


def test_prioritizer_severity_mapping():
    # Critical finding -> HIGH priority
    critical_finding = SEOAuditFinding(
        audit_run_id="run-1",
        organization_id="org-1",
        website_project_id="web-1",
        rule_id="RULE_001",
        severity="critical",
        category="metadata",
        title="Missing Title",
        description="Page has no title tag",
        recommendation="Add title",
        finding_fingerprint="fp1",
    )
    assert (
        RecommendationPrioritizer.calculate_priority(
            rec_type=RecommendationType.TITLE_OPTIMIZATION,
            finding=critical_finding,
        )
        == RecommendationPriority.HIGH
    )

    # Low finding -> LOW priority
    low_finding = SEOAuditFinding(
        audit_run_id="run-1",
        organization_id="org-1",
        website_project_id="web-1",
        rule_id="RULE_002",
        severity="low",
        category="headings",
        title="Suboptimal Heading",
        description="Minor formatting",
        recommendation="Fix",
        finding_fingerprint="fp2",
    )
    assert (
        RecommendationPrioritizer.calculate_priority(
            rec_type=RecommendationType.HEADING_STRUCTURE,
            finding=low_finding,
        )
        == RecommendationPriority.LOW
    )

    # Empty current value -> HIGH for title
    assert (
        RecommendationPrioritizer.calculate_priority(
            rec_type=RecommendationType.TITLE_OPTIMIZATION,
            finding=None,
            current_value="",
        )
        == RecommendationPriority.HIGH
    )
