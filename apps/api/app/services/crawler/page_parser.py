"""HTML Page Parser for Technical SEO Data Extraction.

Extracts:
- Document title and length
- Meta description
- Canonical link (resolved to absolute)
- Meta robots directives (e.g. noindex, nofollow)
- Heading metrics (H1 count, main H1 text)
- Discovered hyperlinks (classified into internal and external)
- Content SHA-256 fingerprint
"""

from __future__ import annotations

import hashlib
import logging
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from app.services.crawler.url_normalizer import UrlNormalizer

logger = logging.getLogger(__name__)

MAX_LINKS_STORED = 100


class ParsedPageData:
    """Structured SEO metadata extracted from an HTML page."""

    def __init__(self):
        self.title: Optional[str] = None
        self.meta_description: Optional[str] = None
        self.canonical_url: Optional[str] = None
        self.meta_robots: Optional[str] = None
        self.h1_count: int = 0
        self.primary_h1: Optional[str] = None
        self.internal_links_count: int = 0
        self.external_links_count: int = 0
        self.internal_links: List[str] = []
        self.external_links: List[str] = []
        self.links_detail: List[Dict[str, Any]] = []
        self.content_hash: Optional[str] = None


class PageParser:
    """Parses HTML content for SEO technical audit attributes."""

    @classmethod
    def parse_html(
        cls,
        html_content: str,
        current_url: str,
        target_domain: str
    ) -> ParsedPageData:
        """Parses HTML string into structured SEO attributes."""
        result = ParsedPageData()

        if not html_content:
            return result

        # Compute content fingerprint
        result.content_hash = hashlib.sha256(html_content.encode("utf-8")).hexdigest()

        try:
            # Prefer lxml parser, fall back to html.parser if lxml fails
            try:
                soup = BeautifulSoup(html_content, "lxml")
            except Exception:
                soup = BeautifulSoup(html_content, "html.parser")
        except Exception as exc:
            logger.warning("Failed to parse HTML for %s: %s", current_url, exc)
            return result

        # 1. Title
        title_tag = soup.find("title")
        if title_tag and title_tag.string:
            clean_title = title_tag.string.strip()
            result.title = clean_title[:500] if clean_title else None

        # 2. Meta description
        meta_desc = soup.find("meta", attrs={"name": lambda x: x and x.lower() == "description"})
        if meta_desc and meta_desc.get("content"):
            content = meta_desc["content"].strip()
            result.meta_description = content[:1000] if content else None

        # 3. Canonical Link
        canonical_tag = soup.find("link", attrs={"rel": lambda x: x and "canonical" in [v.lower() for v in (x if isinstance(x, list) else [x])]})
        if canonical_tag and canonical_tag.get("href"):
            raw_canonical = canonical_tag["href"].strip()
            resolved_canonical = urljoin(current_url, raw_canonical)
            result.canonical_url = UrlNormalizer.normalize_url(resolved_canonical)

        # 4. Meta Robots
        meta_robots = soup.find("meta", attrs={"name": lambda x: x and x.lower() == "robots"})
        if meta_robots and meta_robots.get("content"):
            result.meta_robots = meta_robots["content"].strip().lower()[:200]

        # 5. Headings (H1)
        h1_tags = soup.find_all("h1")
        result.h1_count = len(h1_tags)
        if h1_tags:
            first_h1_text = h1_tags[0].get_text(strip=True)
            result.primary_h1 = first_h1_text[:300] if first_h1_text else None

        # 6. Links discovery
        seen_internal = set()
        seen_external = set()

        for a_tag in soup.find_all("a", href=True):
            raw_href = a_tag["href"].strip()
            if not raw_href or raw_href.startswith(("#", "javascript:", "mailto:", "tel:", "data:", "ftp:")):
                continue

            normalized_link = UrlNormalizer.normalize_url(raw_href, base_url=current_url)
            if not normalized_link:
                continue

            anchor_text = a_tag.get_text(strip=True)[:100]
            rel_attr = a_tag.get("rel", "")
            rel_str = " ".join(rel_attr) if isinstance(rel_attr, list) else str(rel_attr)

            is_internal = UrlNormalizer.is_in_scope(normalized_link, target_domain)

            if is_internal:
                result.internal_links_count += 1
                if normalized_link not in seen_internal:
                    seen_internal.add(normalized_link)
                    result.internal_links.append(normalized_link)
                    if len(result.links_detail) < MAX_LINKS_STORED:
                        result.links_detail.append({
                            "url": normalized_link,
                            "type": "internal",
                            "text": anchor_text,
                            "rel": rel_str,
                        })
            else:
                result.external_links_count += 1
                if normalized_link not in seen_external:
                    seen_external.add(normalized_link)
                    result.external_links.append(normalized_link)
                    if len(result.links_detail) < MAX_LINKS_STORED:
                        result.links_detail.append({
                            "url": normalized_link,
                            "type": "external",
                            "text": anchor_text,
                            "rel": rel_str,
                        })

        return result
