"""HTML Page Parser for Technical SEO Data Extraction.

Extracts:
- Document title and length
- Meta description
- Canonical link (resolved to absolute)
- Meta robots directives (e.g. noindex, nofollow)
- Heading metrics & structure (H1-H6 tags, counts, texts)
- Image metadata (src, alt attribute presence, decorative detection)
- Discovered hyperlinks (classified into internal and external)
- Structured data (JSON-LD blocks safely parsed with size bounds)
- Content SHA-256 fingerprint
"""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from app.services.crawler.url_normalizer import UrlNormalizer

logger = logging.getLogger(__name__)

MAX_LINKS_STORED = 100
MAX_IMAGES_STORED = 50
MAX_JSONLD_BLOCKS = 10
MAX_JSONLD_BYTES = 64 * 1024  # 64 KB


class ParsedPageData:
    """Structured SEO metadata extracted from an HTML page."""

    def __init__(self):
        self.title: Optional[str] = None
        self.meta_description: Optional[str] = None
        self.canonical_url: Optional[str] = None
        self.meta_robots: Optional[str] = None
        self.h1_count: int = 0
        self.primary_h1: Optional[str] = None
        self.headings_json: Dict[str, Any] = {
            "counts": {"h1": 0, "h2": 0, "h3": 0, "h4": 0, "h5": 0, "h6": 0},
            "h1": [],
            "h2": [],
            "h3": [],
            "h4": [],
            "h5": [],
            "h6": [],
        }
        self.images_count: int = 0
        self.images_missing_alt_count: int = 0
        self.images_json: List[Dict[str, Any]] = []
        self.structured_data_json: List[Dict[str, Any]] = []
        self.internal_links_count: int = 0
        self.external_links_count: int = 0
        self.internal_links: List[str] = []
        self.external_links: List[str] = []
        self.links_detail: List[Dict[str, Any]] = []
        self.content_hash: Optional[str] = None


class PageParser:
    """Parses HTML content for SEO technical audit attributes."""

    @classmethod
    def parse_html(cls, html_content: str, current_url: str, target_domain: str) -> ParsedPageData:
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
        canonical_tag = soup.find(
            "link",
            attrs={
                "rel": lambda x: (
                    x and "canonical" in [v.lower() for v in (x if isinstance(x, list) else [x])]
                )
            },
        )
        if canonical_tag and canonical_tag.get("href"):
            raw_canonical = canonical_tag["href"].strip()
            resolved_canonical = urljoin(current_url, raw_canonical)
            result.canonical_url = UrlNormalizer.normalize_url(resolved_canonical)

        # 4. Meta Robots
        meta_robots = soup.find("meta", attrs={"name": lambda x: x and x.lower() == "robots"})
        if meta_robots and meta_robots.get("content"):
            result.meta_robots = meta_robots["content"].strip().lower()[:200]

        # 5. Heading Structure (H1–H6)
        heading_counts = {"h1": 0, "h2": 0, "h3": 0, "h4": 0, "h5": 0, "h6": 0}
        heading_texts: Dict[str, List[str]] = {
            "h1": [],
            "h2": [],
            "h3": [],
            "h4": [],
            "h5": [],
            "h6": [],
        }

        for level in ("h1", "h2", "h3", "h4", "h5", "h6"):
            tags = soup.find_all(level)
            heading_counts[level] = len(tags)
            for tag in tags[:20]:
                text = tag.get_text(strip=True)[:200]
                if text:
                    heading_texts[level].append(text)

        result.headings_json = {
            "counts": heading_counts,
            **heading_texts,
        }
        result.h1_count = heading_counts["h1"]
        if heading_texts["h1"]:
            result.primary_h1 = heading_texts["h1"][0]

        # 6. Image SEO (src, alt attribute, decorative detection)
        img_tags = soup.find_all("img")
        result.images_count = len(img_tags)
        missing_alt = 0
        images_list = []

        for img in img_tags[:MAX_IMAGES_STORED]:
            raw_src = (img.get("src") or "").strip()
            resolved_src = urljoin(current_url, raw_src) if raw_src else ""
            has_alt = "alt" in img.attrs
            alt_val = img.get("alt")

            if not has_alt or alt_val is None:
                missing_alt += 1
                images_list.append(
                    {
                        "src": resolved_src[:500],
                        "alt": None,
                        "has_alt": False,
                        "is_empty_alt": False,
                    }
                )
            else:
                is_empty = str(alt_val).strip() == ""
                images_list.append(
                    {
                        "src": resolved_src[:500],
                        "alt": str(alt_val).strip()[:300],
                        "has_alt": True,
                        "is_empty_alt": is_empty,
                    }
                )

        result.images_missing_alt_count = missing_alt
        result.images_json = images_list

        # 7. Structured Data (JSON-LD)
        ld_scripts = soup.find_all(
            "script", attrs={"type": lambda x: x and "application/ld+json" in x.lower()}
        )
        structured_data = []

        for script in ld_scripts[:MAX_JSONLD_BLOCKS]:
            raw_content = script.string or script.get_text()
            if not raw_content:
                continue

            raw_trimmed = raw_content.strip()
            if len(raw_trimmed) > MAX_JSONLD_BYTES:
                structured_data.append(
                    {
                        "raw_type": None,
                        "is_valid_json": False,
                        "data": None,
                        "error": "JSON-LD block exceeds maximum 64KB limit",
                    }
                )
                continue

            try:
                parsed_json = json.loads(raw_trimmed)
                schema_type = None
                if isinstance(parsed_json, dict):
                    schema_type = parsed_json.get("@type")
                elif (
                    isinstance(parsed_json, list)
                    and parsed_json
                    and isinstance(parsed_json[0], dict)
                ):
                    schema_type = parsed_json[0].get("@type")

                structured_data.append(
                    {
                        "raw_type": str(schema_type) if schema_type else None,
                        "is_valid_json": True,
                        "data": parsed_json,
                        "error": None,
                    }
                )
            except Exception as exc:
                structured_data.append(
                    {
                        "raw_type": None,
                        "is_valid_json": False,
                        "data": None,
                        "error": f"Invalid JSON syntax: {str(exc)}",
                    }
                )

        result.structured_data_json = structured_data

        # 8. Links discovery
        seen_internal = set()
        seen_external = set()

        for a_tag in soup.find_all("a", href=True):
            raw_href = a_tag["href"].strip()
            if not raw_href or raw_href.startswith(
                ("#", "javascript:", "mailto:", "tel:", "data:", "ftp:")
            ):
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
                        result.links_detail.append(
                            {
                                "url": normalized_link,
                                "type": "internal",
                                "text": anchor_text,
                                "rel": rel_str,
                            }
                        )
            else:
                result.external_links_count += 1
                if normalized_link not in seen_external:
                    seen_external.add(normalized_link)
                    result.external_links.append(normalized_link)
                    if len(result.links_detail) < MAX_LINKS_STORED:
                        result.links_detail.append(
                            {
                                "url": normalized_link,
                                "type": "external",
                                "text": anchor_text,
                                "rel": rel_str,
                            }
                        )

        return result
