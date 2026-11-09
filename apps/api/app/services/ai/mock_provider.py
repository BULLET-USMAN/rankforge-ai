"""Deterministic Mock AI Provider for testing and local development."""

from __future__ import annotations

import re

from app.services.ai.provider_interface import AIProviderInterface
from app.services.ai.types import (
    AIProviderRequest,
    AIProviderResponse,
    RawAIOptimizationOutput,
)


class MockAIProvider(AIProviderInterface):
    """
    Mock AI Provider producing grounded, deterministic recommendations conforming
    strictly to RawAIOptimizationOutput. Used for automated tests and sandbox evaluation.
    """

    def __init__(self, model: str = "gemini-2.5-flash-mock"):
        self.model = model

    async def health_check(self) -> bool:
        return True

    async def generate(self, request: AIProviderRequest) -> AIProviderResponse:
        content = request.user_content
        template = request.prompt_template

        # Extract context fields from formatted prompt
        page_url_match = re.search(r"Page URL:\s*([^\r\n]+)", content)
        page_url = page_url_match.group(1).strip() if page_url_match else "https://example.com/page"

        current_title_match = re.search(r"Current Title:\s*([^\r\n]+)", content)
        current_title = current_title_match.group(1).strip() if current_title_match else ""

        h1_match = re.search(r"Primary H1:\s*([^\r\n]+)", content)
        h1 = h1_match.group(1).strip() if h1_match else ""

        guidance_match = re.search(r"User Guidance:\s*([^\r\n]+)", content)
        user_guidance = guidance_match.group(1).strip() if guidance_match else None

        # Build grounded response based on template type
        if "title" in template:
            base_topic = h1 or current_title or "Optimized Service Guide"
            suggested = f"{base_topic} | RankForge SEO"
            if user_guidance and "concise" in user_guidance.lower():
                suggested = base_topic[:45]

            output = RawAIOptimizationOutput(
                suggested_value=suggested,
                explanation=(
                    f"The proposed title aligns directly with the page's primary heading ('{h1}') "
                    "and adheres to standard display heuristics (under 60 characters) while incorporating brand identity."
                ),
                supporting_evidence=[
                    f"Primary H1 observed: '{h1}'",
                    f"Prior title was: '{current_title}'",
                    "Evidence-backed brand context identified.",
                ],
                limitations="Google search snippets may occasionally rewrite title tags depending on query intent.",
                alternative_suggestions=[
                    f"{base_topic} - Official Overview",
                    f"Guide to {base_topic}",
                ],
            )

        elif "description" in template:
            suggested = (
                f"Explore comprehensive technical SEO analysis and growth intelligence for {h1 or 'your website'}. "
                "Review verified crawl data, resolve high-priority issues, and improve visibility."
            )
            output = RawAIOptimizationOutput(
                suggested_value=suggested,
                explanation=(
                    "Summarizes the primary purpose of the page with clear value propositions, "
                    "staying within the recommended 120-160 character snippet window."
                ),
                supporting_evidence=[
                    f"Synthesized from page heading '{h1}' and topic focus.",
                    "Provides clear, factual user preview without clickbait claims.",
                ],
                limitations="Search engines may select snippets directly from page body text matching search queries.",
                alternative_suggestions=[
                    f"Discover verified technical SEO guidance for {h1 or 'your site'}. Inspect real crawl findings and action items."
                ],
            )

        elif "headings" in template:
            suggested = (
                f"# {h1 or 'Primary Topic'}\n"
                f"## Overview & Key Objectives\n"
                f"## Technical SEO Architecture\n"
                f"### Core Crawl Metrics\n"
                f"### Issue Remediation Workflow\n"
                f"## Summary & Verification Checklist"
            )
            output = RawAIOptimizationOutput(
                suggested_value=suggested,
                explanation=(
                    "Reorganizes heading structure into a logical H1 -> H2 -> H3 hierarchy, "
                    "improving readability and thematic scannability."
                ),
                supporting_evidence=[
                    "Resolved potential heading level skips and established clear topical boundaries.",
                ],
                limitations="Ensure headings accurately reflect actual section content before updating templates.",
            )

        elif "content_structure" in template:
            suggested = (
                "1. Introduce primary value proposition in the first paragraph.\n"
                "2. Break dense text blocks into bulleted lists of actionable insights.\n"
                "3. Add clear section subheadings separating diagnostic steps from remediation."
            )
            output = RawAIOptimizationOutput(
                suggested_value=suggested,
                explanation="Enhances user scannability and structural clarity without inventing unverified facts.",
                supporting_evidence=[
                    "Observed text density and section grouping in crawl extract."
                ],
                limitations="Recommendations are structural; domain experts should verify editorial voice.",
            )

        elif "internal_links" in template:
            # Extract eligible target urls if present
            targets = []
            target_matches = re.findall(r"-\s*(https?://[^\s\r\n]+)", content)
            if target_matches:
                targets = target_matches[:3]
            else:
                targets = ["https://example.com/blog", "https://example.com/features"]

            suggested_links = []
            for t in targets:
                suggested_links.append(
                    f"Target: {t} | Anchor: relevant guide | Placement: Related Resources section"
                )

            suggested = "\n".join(suggested_links)
            output = RawAIOptimizationOutput(
                suggested_value=suggested,
                explanation="Links closely related internal pages using descriptive anchor text, improving site navigation.",
                supporting_evidence=[
                    f"Selected strictly from {len(targets)} authorized internal crawled URLs."
                ],
                limitations="Verify that destination page context naturally supports the recommended link placement.",
            )

        elif "image_alt" in template:
            suggested = (
                "Action item: Perform manual visual inspection of flagged images. "
                "For informational images (diagrams, charts), provide brief descriptive text. "
                'For purely decorative styling elements, retain empty alt attribute (alt="").'
            )
            output = RawAIOptimizationOutput(
                suggested_value=suggested,
                explanation=(
                    "Because raw image pixels are not evaluated by the crawler, descriptive text cannot be safely inferred. "
                    "Decorative images must retain empty alt attributes for accessibility compliance."
                ),
                supporting_evidence=[
                    "Identified image tags without alt attributes in HTML source."
                ],
                limitations="Requires manual human visual inspection of image subject matter.",
            )

        else:
            output = RawAIOptimizationOutput(
                suggested_value="General SEO Recommendation",
                explanation="Evidence-based optimization proposal.",
                supporting_evidence=[f"Analyzed URL {page_url} against observed audit findings."],
            )

        raw_json = output.model_dump_json()
        input_tokens = len(content) // 4
        output_tokens = len(raw_json) // 4

        return AIProviderResponse(
            raw_text=raw_json,
            parsed_output=output,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            model=self.model,
            finish_reason="STOP",
        )
