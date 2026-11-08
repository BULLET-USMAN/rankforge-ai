"""Context builder for grounded AI recommendation generation."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.crawled_page import CrawledPage
from app.models.seo_audit_finding import SEOAuditFinding
from app.models.seo_audit_run import SEOAuditRun
from app.models.website_project import WebsiteProject
from app.services.ai.exceptions import AIInsufficientContextError
from app.services.ai.prompts.prompt_registry import PromptRegistry
from app.services.ai.security import PromptSecuritySanitizer
from app.services.ai.types import AIProviderRequest, RecommendationType


class OptimizationContextBuilder:
    """
    Assembles authorized, sanitized, evidence-grounded prompt payloads
    for the AI recommendation generator.
    """

    @classmethod
    def build_request(
        cls,
        db: Session,
        website: WebsiteProject,
        rec_type: RecommendationType,
        page_url: str,
        audit_run: Optional[SEOAuditRun] = None,
        finding: Optional[SEOAuditFinding] = None,
        user_guidance: Optional[str] = None,
    ) -> tuple[AIProviderRequest, Dict[str, Any]]:
        """
        Builds the AIProviderRequest and returns evidence metadata dictionary.
        """
        # Find CrawledPage record
        stmt = (
            select(CrawledPage)
            .where(
                CrawledPage.project_id == website.id,
                CrawledPage.url == page_url,
            )
            .order_by(CrawledPage.created_at.desc())
        )
        crawled_page: Optional[CrawledPage] = db.execute(stmt).scalars().first()

        current_title = ""
        current_description = ""
        h1 = ""
        headings_json = {}
        raw_body_text = ""
        images_summary = "No images recorded."
        missing_alt_count = 0
        word_count = 0
        internal_links_count = 0

        if crawled_page:
            current_title = crawled_page.title or ""
            current_description = crawled_page.meta_description or ""
            headings_json = crawled_page.headings_json or {}
            
            # Extract H1 safely whether headings_json is a list or dict
            h1_val = headings_json.get("h1")
            if isinstance(h1_val, list) and h1_val:
                first = h1_val[0]
                h1 = first if isinstance(first, str) else first.get("text", "")
            elif isinstance(h1_val, dict) and h1_val.get("items"):
                h1 = h1_val["items"][0].get("text", "")
            
            # Synthesize body text from metadata and headings if raw text sample not directly stored
            text_sample = getattr(crawled_page, "page_text_sample", None)
            if text_sample:
                raw_body_text = text_sample
            else:
                parts = []
                if current_title:
                    parts.append(f"Page Title: {current_title}")
                if current_description:
                    parts.append(f"Meta Description: {current_description}")
                for lvl in ["h1", "h2", "h3"]:
                    items = headings_json.get(lvl, [])
                    if isinstance(items, list):
                        parts.extend(f"{lvl.upper()}: {item}" if isinstance(item, str) else f"{lvl.upper()}: {item.get('text', '')}" for item in items[:5])
                raw_body_text = "\n".join(parts) or "No body text extracted."

            word_count = len(raw_body_text.split())
            missing_alt_count = crawled_page.images_missing_alt_count or 0
            if crawled_page.images_json:
                img_samples = [
                    f"src={img.get('src', '')[:60]}, alt='{img.get('alt', '')[:40]}'"
                    for img in crawled_page.images_json[:5]
                ]
                images_summary = "; ".join(img_samples)
            internal_links_count = crawled_page.internal_links_count or len(crawled_page.links_json or [])

        # Check for insufficient context
        if not crawled_page and not finding:
            raise AIInsufficientContextError(
                f"No crawl or audit data found for page: {page_url}. "
                "Insufficient content available for reliable optimization."
            )

        # Finding summary
        findings_str = "None specified."
        if finding:
            findings_str = (
                f"Rule: {finding.rule_id} (Severity: {finding.severity})\n"
                f"Title: {finding.title}\n"
                f"Description: {finding.description}\n"
                f"Evidence: {json.dumps(finding.evidence_json)}"
            )

        # For internal linking: fetch list of other eligible crawled pages on this website
        eligible_target_urls_str = "None available."
        eligible_urls_list: List[str] = []
        if rec_type == RecommendationType.INTERNAL_LINKING:
            target_stmt = (
                select(CrawledPage.url)
                .where(
                    CrawledPage.project_id == website.id,
                    CrawledPage.status_code == 200,
                    CrawledPage.url != page_url,
                )
                .limit(20)
            )
            eligible_urls_list = list(db.execute(target_stmt).scalars().all())
            if eligible_urls_list:
                eligible_target_urls_str = "\n".join(f"- {u}" for u in eligible_urls_list)
            else:
                eligible_target_urls_str = "- No other internal pages found in crawl dataset."

        # Delimiter security wrapping for untrusted page content
        wrapped_untrusted_content = PromptSecuritySanitizer.wrap_untrusted_content(raw_body_text)

        # User guidance block
        sanitized_guidance = PromptSecuritySanitizer.sanitize_user_guidance(user_guidance)
        user_guidance_block = ""
        if sanitized_guidance:
            user_guidance_block = (
                f"USER EDITING PREFERENCES (Heuristic guidance):\n"
                f"User Guidance: {sanitized_guidance}\n\n"
            )

        # Headings summary
        headings_summary_list = []
        for level in ["h1", "h2", "h3"]:
            items = headings_json.get(level, [])
            if isinstance(items, list) and items:
                text_items = [i if isinstance(i, str) else i.get("text", "") for i in items[:3]]
                headings_summary_list.append(f"{level.upper()}: {'; '.join(text_items)}")
        headings_summary = " | ".join(headings_summary_list) or "None recorded"

        # Resolve template
        template_name = PromptRegistry.get_template_for_type(rec_type)
        template_def = PromptRegistry.get_template(template_name)

        user_content = template_def["user_template"].format(
            page_url=page_url,
            domain=website.domain,
            current_title=current_title or "[Empty Title]",
            current_description=current_description or "[Empty Meta Description]",
            h1=h1 or "[No H1 Detected]",
            headings_summary=headings_summary,
            headings_json=json.dumps(headings_json),
            word_count=word_count,
            images_summary=images_summary,
            missing_alt_count=missing_alt_count,
            internal_links_count=internal_links_count,
            eligible_target_urls=eligible_target_urls_str,
            audit_findings=findings_str,
            untrusted_page_content=wrapped_untrusted_content,
            user_guidance_block=user_guidance_block,
        )

        evidence_meta = {
            "page_url": page_url,
            "crawled_page_id": crawled_page.id if crawled_page else None,
            "source_finding_id": finding.id if finding else None,
            "current_title": current_title,
            "current_description": current_description,
            "h1": h1,
            "word_count": word_count,
            "eligible_target_urls": eligible_urls_list,
        }

        request = AIProviderRequest(
            prompt_template=template_name,
            prompt_version=template_def.get("version", "1.0"),
            system_instruction=template_def["system_instruction"],
            user_content=user_content,
        )

        return request, evidence_meta
