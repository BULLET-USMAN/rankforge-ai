"""Safe XML Sitemap Parser and Discovery Service for RankForge Crawler.

Uses defusedxml to guard against XML entity expansion / billion laughs attacks.
Handles standard <urlset> and nested <sitemapindex> hierarchies with recursion and budget limits.
"""

from __future__ import annotations

import logging
from typing import List, Optional, Set
from urllib.parse import urlparse

import defusedxml.ElementTree as ET

from app.services.crawler.safe_fetcher import SafeHttpFetcher
from app.services.crawler.url_normalizer import UrlNormalizer

logger = logging.getLogger(__name__)

# XML Namespaces commonly used in sitemaps
NAMESPACES = {
    "sm": "http://www.sitemaps.org/schemas/sitemap/0.9",
}

MAX_SITEMAP_DOCS = 5
MAX_SITEMAP_URLS = 500
MAX_SITEMAP_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB


class SitemapParseResult:
    """Outcome of parsing sitemaps for a website."""

    def __init__(self):
        self.discovered_urls: List[str] = []
        self.sitemap_documents: List[dict] = []
        self.errors: List[str] = []


class SitemapService:
    """Discovers and parses XML sitemaps for a website project."""

    @classmethod
    def _extract_tag_local(cls, element: ET.Element) -> str:
        """Strips XML namespace prefix from tag."""
        tag = element.tag
        if "}" in tag:
            return tag.split("}", 1)[1]
        return tag

    @classmethod
    def parse_sitemap_xml(
        cls,
        xml_content: str,
        target_domain: str,
        sitemap_url: str
    ) -> tuple[List[str], List[str], Optional[str]]:
        """Parses sitemap XML content safely.

        Returns (discovered_page_urls, nested_sitemap_urls, error_message).
        """
        page_urls: List[str] = []
        nested_sitemaps: List[str] = []

        if not xml_content or not xml_content.strip():
            return page_urls, nested_sitemaps, "Empty sitemap content"

        try:
            root = ET.fromstring(xml_content.encode("utf-8"))
        except Exception as exc:
            return page_urls, nested_sitemaps, f"Invalid XML: {str(exc)}"

        root_tag = cls._extract_tag_local(root).lower()

        if root_tag == "sitemapindex":
            # Nested sitemap index: <sitemap><loc>...</loc></sitemap>
            for child in root:
                if cls._extract_tag_local(child).lower() == "sitemap":
                    for sub in child:
                        if cls._extract_tag_local(sub).lower() == "loc" and sub.text:
                            loc = sub.text.strip()
                            norm = UrlNormalizer.normalize_url(loc, base_url=sitemap_url)
                            if norm and UrlNormalizer.is_in_scope(norm, target_domain):
                                nested_sitemaps.append(norm)

        elif root_tag == "urlset":
            # Direct URL set: <url><loc>...</loc></url>
            for child in root:
                if cls._extract_tag_local(child).lower() == "url":
                    for sub in child:
                        if cls._extract_tag_local(sub).lower() == "loc" and sub.text:
                            loc = sub.text.strip()
                            norm = UrlNormalizer.normalize_url(loc, base_url=sitemap_url)
                            if norm and UrlNormalizer.is_in_scope(norm, target_domain):
                                is_crawlable, _ = UrlNormalizer.is_crawlable_resource(norm)
                                if is_crawlable:
                                    page_urls.append(norm)
        else:
            return page_urls, nested_sitemaps, f"Unrecognized root element: <{root_tag}>"

        return page_urls, nested_sitemaps, None

    @classmethod
    def discover_and_parse_sync(
        cls,
        base_url: str,
        target_domain: str,
        seed_sitemaps: Optional[List[str]] = None,
        job_id: Optional[str] = None,
        project_id: Optional[str] = None
    ) -> SitemapParseResult:
        """Discovers, fetches, and parses sitemaps synchronously."""
        result = SitemapParseResult()
        fetcher = SafeHttpFetcher()

        parsed_base = urlparse(base_url)
        origin = f"{parsed_base.scheme}://{parsed_base.netloc}"

        # Build candidate list: seed sitemaps from robots.txt, plus standard endpoints
        candidates: List[str] = []
        if seed_sitemaps:
            for s in seed_sitemaps:
                norm = UrlNormalizer.normalize_url(s, base_url=origin)
                if norm and norm not in candidates:
                    candidates.append(norm)

        # Add standard fallbacks if not already in list
        standard_fallbacks = [
            f"{origin}/sitemap.xml",
            f"{origin}/sitemap_index.xml",
        ]
        for fb in standard_fallbacks:
            if fb not in candidates:
                candidates.append(fb)

        visited_sitemaps: Set[str] = set()
        queue: List[str] = list(candidates)
        all_discovered_urls: Set[str] = set()

        while queue and len(visited_sitemaps) < MAX_SITEMAP_DOCS and len(all_discovered_urls) < MAX_SITEMAP_URLS:
            sitemap_url = queue.pop(0)
            if sitemap_url in visited_sitemaps:
                continue

            visited_sitemaps.add(sitemap_url)

            # Enforce scope check on sitemap URL itself
            if not UrlNormalizer.is_in_scope(sitemap_url, target_domain):
                continue

            fetch_res = fetcher.fetch_sync(sitemap_url, max_size_bytes=MAX_SITEMAP_SIZE_BYTES)
            doc_record = {
                "url": sitemap_url,
                "status_code": fetch_res.status_code,
                "discovered_urls_count": 0,
                "error_details": None,
                "is_valid": False,
            }

            if not fetch_res.is_success or not fetch_res.text_content:
                doc_record["error_details"] = fetch_res.error_details or f"HTTP {fetch_res.status_code}"
                result.sitemap_documents.append(doc_record)
                continue

            page_urls, nested, parse_err = cls.parse_sitemap_xml(
                fetch_res.text_content,
                target_domain,
                sitemap_url=sitemap_url
            )

            if parse_err:
                doc_record["error_details"] = parse_err
                result.sitemap_documents.append(doc_record)
                continue

            doc_record["is_valid"] = True
            doc_record["discovered_urls_count"] = len(page_urls)
            result.sitemap_documents.append(doc_record)

            for u in page_urls:
                if len(all_discovered_urls) < MAX_SITEMAP_URLS:
                    all_discovered_urls.add(u)

            # Enqueue nested sitemaps if within depth/budget
            for nest in nested:
                if nest not in visited_sitemaps and nest not in queue:
                    queue.append(nest)

        result.discovered_urls = list(all_discovered_urls)
        return result
