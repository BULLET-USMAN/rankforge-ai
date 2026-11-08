"""URL Normalizer and Scope Enforcement for RankForge Crawler.

Handles URL canonicalization, scope validation, trap detection,
and path sanitization.
"""

from __future__ import annotations

import re
from typing import Optional, Set
from urllib.parse import parse_qsl, urlencode, urljoin, urlparse, urlunparse

# File extensions that are clearly non-HTML web pages and should not be crawled as HTML
EXCLUDED_EXTENSIONS: Set[str] = {
    # Images
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".ico", ".bmp", ".tiff", ".avif",
    # Audio/Video
    ".mp3", ".mp4", ".wav", ".avi", ".mov", ".wmv", ".mkv", ".webm", ".flv",
    # Documents / Archives
    ".pdf", ".zip", ".tar", ".gz", ".7z", ".rar", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    # Code / Data assets
    ".css", ".js", ".mjs", ".json", ".xml", ".rss", ".atom", ".woff", ".woff2", ".ttf", ".eot",
}

# Tracking query parameters that pollute URL uniqueness without changing content
TRACKING_PARAMS: Set[str] = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "gclid", "fbclid", "mc_cid", "mc_eid", "_ga", "_gl", "msclkid",
}

# Patterns indicating crawl traps or infinite loops
CALENDAR_TRAP_PATTERN = re.compile(r"/(?:events|calendar|archive)/\d{4}/\d{1,2}(?:/\d{1,2})?", re.IGNORECASE)
REPEATED_SEGMENT_PATTERN = re.compile(r"/(?P<seg>[^/]{2,})/(?P=seg)(?:/(?P=seg))+", re.IGNORECASE)

# Sensitive paths to avoid crawling
SENSITIVE_PATHS: Set[str] = {
    "/login", "/logout", "/signin", "/signout", "/signup", "/register",
    "/cart", "/checkout", "/admin", "/wp-admin", "/user/login", "/auth",
    "/account", "/password/reset",
}


class UrlNormalizer:
    """Normalizes and validates URLs for the RankForge website crawler."""

    @classmethod
    def normalize_domain(cls, domain: str) -> str:
        """Strips scheme, port, trailing slashes, and lowercases domain."""
        domain = domain.strip().lower()
        if "://" in domain:
            domain = urlparse(domain).netloc
        domain = domain.split(":")[0]  # strip port if present
        return domain.rstrip("/")

    @classmethod
    def normalize_url(cls, raw_url: str, base_url: Optional[str] = None) -> Optional[str]:
        """Resolves, canonicalizes, and strips non-essential fragments/tracking params."""
        if not raw_url or not isinstance(raw_url, str):
            return None

        raw_url = raw_url.strip()
        if not raw_url or raw_url.startswith(("#", "javascript:", "mailto:", "tel:", "data:", "ftp:")):
            return None

        # Resolve relative URLs against base
        if base_url:
            raw_url = urljoin(base_url, raw_url)

        try:
            parsed = urlparse(raw_url)
        except Exception:
            return None

        # Only allow HTTP and HTTPS
        scheme = parsed.scheme.lower()
        if scheme not in ("http", "https"):
            return None

        # Netloc normalization
        netloc = parsed.netloc.lower()
        if not netloc:
            return None

        # Strip standard default ports
        if (scheme == "http" and netloc.endswith(":80")) or (scheme == "https" and netloc.endswith(":443")):
            netloc = netloc.split(":")[0]

        # Path normalization: collapse multiple slashes, strip fragment
        path = parsed.path
        if not path:
            path = "/"
        else:
            path = re.sub(r"/+", "/", path)

        # Normalize query: strip tracking parameters, sort parameters for deterministic deduplication
        query = ""
        if parsed.query:
            query_pairs = parse_qsl(parsed.query, keep_blank_values=False)
            filtered_pairs = [
                (k.lower(), v) for k, v in query_pairs
                if k.lower() not in TRACKING_PARAMS
            ]
            if filtered_pairs:
                filtered_pairs.sort(key=lambda x: (x[0], x[1]))
                query = urlencode(filtered_pairs)

        # Build clean URL without fragment
        clean_url = urlunparse((
            scheme,
            netloc,
            path,
            "",  # params
            query,
            ""   # fragment always stripped
        ))
        return clean_url

    @classmethod
    def is_in_scope(
        cls,
        url: str,
        target_domain: str,
        allow_subdomains: bool = False
    ) -> bool:
        """Determines if a URL belongs to the target website project scope."""
        clean_target = cls.normalize_domain(target_domain)
        try:
            parsed = urlparse(url)
            host = parsed.netloc.lower().split(":")[0]
        except Exception:
            return False

        if not host:
            return False

        if allow_subdomains:
            # Matches target.com or sub.target.com
            return host == clean_target or host.endswith(f".{clean_target}")

        # Exact match or standard www equivalence
        if host == clean_target:
            return True

        if clean_target.startswith("www.") and host == clean_target[4:]:
            return True
        if host.startswith("www.") and host[4:] == clean_target:
            return True

        return False

    @classmethod
    def is_crawlable_resource(cls, url: str) -> tuple[bool, Optional[str]]:
        """Checks if a URL is safe and valid to crawl as an HTML page.

        Returns (is_crawlable, reason_if_excluded).
        """
        try:
            parsed = urlparse(url)
        except Exception:
            return False, "invalid_url_syntax"

        path_lower = parsed.path.lower()

        # Check non-HTML file extensions
        for ext in EXCLUDED_EXTENSIONS:
            if path_lower.endswith(ext):
                return False, f"excluded_extension:{ext}"

        # Check sensitive paths
        for sensitive in SENSITIVE_PATHS:
            if path_lower == sensitive or path_lower.startswith(f"{sensitive}/"):
                return False, f"sensitive_path:{sensitive}"

        # Detect excessive depth
        segments = [s for s in parsed.path.split("/") if s]
        if len(segments) > 10:
            return False, "excessive_path_depth"

        # Detect repeated directory loop traps (e.g. /a/b/a/b/a/b)
        if REPEATED_SEGMENT_PATTERN.search(parsed.path):
            return False, "repeating_path_trap"

        # Detect calendar traps
        if CALENDAR_TRAP_PATTERN.search(parsed.path):
            return False, "calendar_trap"

        # Detect excessive query parameters
        if parsed.query:
            query_pairs = parse_qsl(parsed.query)
            if len(query_pairs) > 6:
                return False, "excessive_query_params"

        return True, None
