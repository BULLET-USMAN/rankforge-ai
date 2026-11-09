"""Independent application-side validation for AI model outputs."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from app.services.ai.exceptions import AIValidationError
from app.services.ai.security import PromptSecuritySanitizer
from app.services.ai.types import (
    RawAIOptimizationOutput,
    RecommendationType,
)


class RecommendationValidator:
    """
    Validates and sanitizes model output before it can be stored
    as a reviewable recommendation proposal.
    """

    MAX_SUGGESTED_LENGTH = 5000
    MAX_EXPLANATION_LENGTH = 2000

    @classmethod
    def validate_and_clean(
        cls,
        output: RawAIOptimizationOutput,
        rec_type: RecommendationType,
        evidence_meta: Dict[str, Any],
    ) -> RawAIOptimizationOutput:
        """
        Validates output fields against constraints and sanitizes values.
        """
        if not output.suggested_value or not output.suggested_value.strip():
            raise AIValidationError("AI model returned an empty suggested value.")

        if len(output.suggested_value) > cls.MAX_SUGGESTED_LENGTH:
            raise AIValidationError(
                f"Suggested value exceeds max allowed length ({cls.MAX_SUGGESTED_LENGTH} chars)."
            )

        if not output.explanation or not output.explanation.strip():
            output.explanation = "Generated recommendation based on technical SEO audit evidence."

        if len(output.explanation) > cls.MAX_EXPLANATION_LENGTH:
            output.explanation = output.explanation[: cls.MAX_EXPLANATION_LENGTH]

        # Sanitize HTML script tags and inline handlers
        cleaned_suggested = PromptSecuritySanitizer.sanitize_output_value(output.suggested_value)
        cleaned_explanation = PromptSecuritySanitizer.sanitize_output_value(output.explanation)

        # For Internal Linking: verify that target URLs are from the authorized eligible list
        if rec_type == RecommendationType.INTERNAL_LINKING:
            eligible_urls = evidence_meta.get("eligible_target_urls", [])
            if eligible_urls:
                # Find all URLs mentioned in suggested_value
                found_urls = re.findall(r"https?://[^\s\r\n\"'>]+", cleaned_suggested)
                for u in found_urls:
                    # Strip punctuation
                    clean_u = u.rstrip(".,;:)")
                    if clean_u not in eligible_urls:
                        # Reject or sanitize hallucinated target URL
                        cleaned_suggested = cleaned_suggested.replace(
                            clean_u, "[Unverified link target removed]"
                        )

        # Clean alternative suggestions
        cleaned_alternatives: Optional[List[str]] = None
        if output.alternative_suggestions:
            cleaned_alternatives = [
                PromptSecuritySanitizer.sanitize_output_value(alt)
                for alt in output.alternative_suggestions[:3]
                if alt and alt.strip()
            ]

        return RawAIOptimizationOutput(
            suggested_value=cleaned_suggested,
            explanation=cleaned_explanation,
            supporting_evidence=output.supporting_evidence[:5],
            limitations=output.limitations,
            alternative_suggestions=cleaned_alternatives,
        )
