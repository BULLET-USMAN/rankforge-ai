"""Deterministic recommendation prioritization service."""

from __future__ import annotations

from typing import Optional

from app.models.seo_audit_finding import SEOAuditFinding
from app.services.ai.types import RecommendationPriority, RecommendationType


class RecommendationPrioritizer:
    """
    Deterministic rule-based recommendation prioritization.
    Separates technical priority from speculative traffic claims.
    """

    @classmethod
    def calculate_priority(
        cls,
        rec_type: RecommendationType,
        finding: Optional[SEOAuditFinding] = None,
        current_value: Optional[str] = None,
    ) -> RecommendationPriority:
        # If tied directly to a finding, use the finding severity
        if finding:
            severity = (finding.severity or "").lower()
            if severity in ("critical", "high"):
                return RecommendationPriority.HIGH
            elif severity == "medium":
                return RecommendationPriority.MEDIUM
            else:
                return RecommendationPriority.LOW

        # If current value is empty for title or description, treat as high/medium
        if not current_value or not current_value.strip():
            if rec_type in (
                RecommendationType.TITLE_OPTIMIZATION,
                RecommendationType.HEADING_STRUCTURE,
            ):
                return RecommendationPriority.HIGH
            return RecommendationPriority.MEDIUM

        # By recommendation type heuristic default
        if rec_type == RecommendationType.TITLE_OPTIMIZATION:
            return RecommendationPriority.HIGH
        elif rec_type in (
            RecommendationType.META_DESCRIPTION,
            RecommendationType.HEADING_STRUCTURE,
        ):
            return RecommendationPriority.MEDIUM
        else:
            return RecommendationPriority.LOW
