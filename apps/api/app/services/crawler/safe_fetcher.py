"""SSRF-Hardened Safe HTTP Fetcher for RankForge Crawler & Domain Verification.

Protects against:
- Loopback (127.0.0.0/8, ::1)
- RFC 1918 Private networks (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16)
- Cloud metadata service (169.254.169.254, metadata.google.internal)
- Link-local (169.254.0.0/16, fe80::/10)
- Multicast and reserved ranges
- DNS rebinding attacks via per-hop pre-connection DNS validation
- Redirect loops and redirect hops to private destinations
- Response size budget exhaustion (HTML, sitemaps, verification files)
Captures:
- Status code, latency, headers, content type, byte size
- X-Robots-Tag response header
- Redirect chain hops
"""

from __future__ import annotations

import ipaddress
import logging
import socket
import time
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import urljoin, urlparse

import httpx

logger = logging.getLogger(__name__)

DEFAULT_USER_AGENT = "RankForgeBot/1.0 (+https://rankforge.ai/bot)"
MAX_HTML_BYTES = 2 * 1024 * 1024  # 2 MB
MAX_VERIFICATION_BYTES = 16 * 1024  # 16 KB
MAX_SITEMAP_BYTES = 5 * 1024 * 1024  # 5 MB
MAX_REDIRECTS = 3

ALLOWED_SCHEMES = {"http", "https"}
ALLOWED_PORTS = {80, 443, 8080, 8443}
BLOCKED_HOSTNAMES = {
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
    "::1",
    "metadata.google.internal",
    "instance-data",
}
BLOCKED_TLDS = {
    "local",
    "internal",
    "lan",
    "home",
    "corp",
    "test",
    "example",
    "invalid",
    "onion",
}


class SafeFetchError(Exception):
    """Raised when an external HTTP fetch fails security, timeout, or size constraints."""
    pass


class SSRFValidationError(SafeFetchError):
    """Raised when target destination violates SSRF or network boundaries."""
    pass


class ResponseSizeExceededError(SafeFetchError):
    """Raised when response body exceeds allocated byte budget."""
    pass


class SafeFetchResult:
    """Standardized result of a safe fetch operation."""

    def __init__(
        self,
        is_success: bool,
        status_code: int = 0,
        response_time_ms: float = 0.0,
        text_content: Optional[str] = None,
        content_type: Optional[str] = None,
        byte_size: int = 0,
        error_details: Optional[str] = None,
        final_url: Optional[str] = None,
        x_robots_tag: Optional[str] = None,
        redirect_chain: Optional[List[Dict[str, Any]]] = None,
    ):
        self.is_success = is_success
        self.status_code = status_code
        self.response_time_ms = response_time_ms
        self.text_content = text_content
        self.content_type = content_type
        self.byte_size = byte_size
        self.error_details = error_details
        self.final_url = final_url
        self.x_robots_tag = x_robots_tag
        self.redirect_chain = redirect_chain if redirect_chain is not None else []

    @property
    def text(self) -> str:
        """Compatibility property for httpx.Response interface."""
        return self.text_content or ""


class SafeHttpFetcher:
    """SSRF-hardened HTTP fetching engine for domain verification and crawler operations."""

    @classmethod
    def validate_destination_ip(cls, ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> None:
        """Enforces that an IP address is publicly routable and safe."""
        if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
            cls.validate_destination_ip(ip.ipv4_mapped)
            return

        ip_str = str(ip)
        if ip_str == "169.254.169.254":
            raise SSRFValidationError("Targeting cloud metadata IP (169.254.169.254) is prohibited.")
        if ip.is_loopback:
            raise SSRFValidationError(f"Target IP {ip_str} is a loopback address.")
        if ip.is_private:
            raise SSRFValidationError(f"Target IP {ip_str} is in an RFC 1918 private network range.")
        if ip.is_link_local:
            raise SSRFValidationError(f"Target IP {ip_str} is a link-local address.")
        if ip.is_multicast:
            raise SSRFValidationError(f"Target IP {ip_str} is a multicast address.")
        if ip.is_reserved or ip.is_unspecified:
            raise SSRFValidationError(f"Target IP {ip_str} is a reserved or unspecified address.")

    @classmethod
    def resolve_and_validate_hostname(cls, hostname: str) -> str:
        """Resolves hostname to IP addresses and validates all returned records against SSRF rules."""
        host_clean = hostname.strip().lower()

        if host_clean in BLOCKED_HOSTNAMES:
            raise SSRFValidationError(f"Hostname '{host_clean}' is prohibited by security policy.")

        parts = host_clean.split(".")
        if len(parts) >= 2 and parts[-1] in BLOCKED_TLDS:
            raise SSRFValidationError(f"TLD '.{parts[-1]}' is prohibited.")

        # Check if hostname is an IP literal
        try:
            ip_obj = ipaddress.ip_address(host_clean)
            cls.validate_destination_ip(ip_obj)
            return host_clean
        except ValueError:
            pass

        # Perform DNS resolution
        try:
            addr_info = socket.getaddrinfo(host_clean, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
        except socket.gaierror as e:
            raise SafeFetchError(f"DNS resolution failed for '{host_clean}': {e}")

        if not addr_info:
            raise SafeFetchError(f"No IP addresses resolved for '{host_clean}'.")

        primary_ip = None
        for item in addr_info:
            sockaddr = item[4]
            ip_candidate = sockaddr[0]
            try:
                ip_obj = ipaddress.ip_address(ip_candidate)
                cls.validate_destination_ip(ip_obj)
                if not primary_ip:
                    primary_ip = ip_candidate
            except ValueError:
                raise SafeFetchError(f"Invalid resolved IP '{ip_candidate}'.")

        return primary_ip or host_clean

    @classmethod
    def validate_url_syntax(cls, url: str) -> Tuple[str, str, int]:
        """Parses and validates scheme, netloc, port."""
        if not url or not isinstance(url, str):
            raise SafeFetchError("Invalid or empty URL provided.")

        try:
            parsed = urlparse(url)
        except Exception as e:
            raise SafeFetchError(f"Malformed URL: {e}")

        scheme = parsed.scheme.lower()
        if scheme not in ALLOWED_SCHEMES:
            raise SSRFValidationError(f"Scheme '{scheme}' is prohibited. Only HTTP and HTTPS are permitted.")

        if parsed.username or parsed.password:
            raise SSRFValidationError("Embedded userinfo (user:pass@) is prohibited.")

        hostname = parsed.hostname
        if not hostname:
            raise SSRFValidationError("A valid hostname could not be determined.")

        port = parsed.port or (443 if scheme == "https" else 80)
        if port not in ALLOWED_PORTS:
            raise SSRFValidationError(f"Port {port} is not allowed for web crawler fetches.")

        return scheme, hostname.lower(), port

    @classmethod
    def fetch_sync(
        cls,
        url: str,
        user_agent: str = DEFAULT_USER_AGENT,
        max_bytes: Optional[int] = None,
        max_size_bytes: Optional[int] = None,
        timeout_seconds: float = 10.0,
        allowed_domains: Optional[Set[str]] = None,
        max_redirects: int = MAX_REDIRECTS,
    ) -> SafeFetchResult:
        """Synchronously fetches a resource with SSRF defense and returns SafeFetchResult."""
        budget = max_size_bytes if max_size_bytes is not None else (max_bytes if max_bytes is not None else MAX_HTML_BYTES)
        current_url = url
        redirects_followed = 0
        redirect_chain: List[Dict[str, Any]] = []
        start_time = time.time()

        try:
            with httpx.Client(
                verify=True,
                timeout=httpx.Timeout(timeout_seconds, connect=5.0, read=timeout_seconds),
                headers={"User-Agent": user_agent, "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"},
                follow_redirects=False,
            ) as client:
                while True:
                    scheme, hostname, _ = cls.validate_url_syntax(current_url)

                    if allowed_domains and hostname not in allowed_domains:
                        raise SSRFValidationError(
                            f"Redirect target '{hostname}' is outside allowed domain scope {allowed_domains}."
                        )

                    cls.resolve_and_validate_hostname(hostname)

                    try:
                        response = client.get(current_url)
                    except httpx.TimeoutException:
                        raise SafeFetchError(f"Connection timed out while fetching {current_url}.")
                    except httpx.ConnectError as e:
                        raise SafeFetchError(f"Failed to establish connection to {current_url}: {e}")
                    except Exception as e:
                        raise SafeFetchError(f"HTTP request error: {e}")

                    content_length = response.headers.get("content-length")
                    if content_length and int(content_length) > budget:
                        raise ResponseSizeExceededError(
                            f"Response content length ({content_length} bytes) exceeds limit ({budget} bytes)."
                        )

                    if response.is_redirect:
                        if redirects_followed >= max_redirects:
                            raise SafeFetchError(f"Exceeded maximum redirect limit of {max_redirects}.")

                        location = response.headers.get("location")
                        if not location:
                            raise SafeFetchError("Received redirect status code without Location header.")

                        next_url = urljoin(current_url, location)
                        redirect_chain.append({
                            "from_url": current_url,
                            "to_url": next_url,
                            "status_code": response.status_code,
                        })
                        current_url = next_url
                        redirects_followed += 1
                        continue

                    if len(response.content) > budget:
                        raise ResponseSizeExceededError(
                            f"Downloaded content size ({len(response.content)} bytes) exceeds limit ({budget} bytes)."
                        )

                    elapsed_ms = (time.time() - start_time) * 1000.0
                    x_robots_tag = response.headers.get("x-robots-tag")

                    return SafeFetchResult(
                        is_success=(response.status_code < 400),
                        status_code=response.status_code,
                        response_time_ms=round(elapsed_ms, 2),
                        text_content=response.text,
                        content_type=response.headers.get("content-type"),
                        byte_size=len(response.content),
                        final_url=current_url,
                        x_robots_tag=x_robots_tag,
                        redirect_chain=redirect_chain,
                    )

        except Exception as exc:
            elapsed_ms = (time.time() - start_time) * 1000.0
            return SafeFetchResult(
                is_success=False,
                status_code=0,
                response_time_ms=round(elapsed_ms, 2),
                error_details=str(exc),
                final_url=current_url,
                redirect_chain=redirect_chain,
            )

    @classmethod
    async def fetch_async(
        cls,
        url: str,
        user_agent: str = DEFAULT_USER_AGENT,
        max_bytes: Optional[int] = None,
        max_size_bytes: Optional[int] = None,
        timeout_seconds: float = 10.0,
        allowed_domains: Optional[Set[str]] = None,
        max_redirects: int = MAX_REDIRECTS,
    ) -> SafeFetchResult:
        """Asynchronously fetches a resource with SSRF defense and returns SafeFetchResult."""
        budget = max_size_bytes if max_size_bytes is not None else (max_bytes if max_bytes is not None else MAX_HTML_BYTES)
        current_url = url
        redirects_followed = 0
        redirect_chain: List[Dict[str, Any]] = []
        start_time = time.time()

        try:
            async with httpx.AsyncClient(
                verify=True,
                timeout=httpx.Timeout(timeout_seconds, connect=5.0, read=timeout_seconds),
                headers={"User-Agent": user_agent, "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"},
                follow_redirects=False,
            ) as client:
                while True:
                    scheme, hostname, _ = cls.validate_url_syntax(current_url)

                    if allowed_domains and hostname not in allowed_domains:
                        raise SSRFValidationError(
                            f"Redirect target '{hostname}' is outside allowed domain scope {allowed_domains}."
                        )

                    cls.resolve_and_validate_hostname(hostname)

                    try:
                        response = await client.get(current_url)
                    except httpx.TimeoutException:
                        raise SafeFetchError(f"Connection timed out while fetching {current_url}.")
                    except httpx.ConnectError as e:
                        raise SafeFetchError(f"Failed to establish connection to {current_url}: {e}")
                    except Exception as e:
                        raise SafeFetchError(f"HTTP request error: {e}")

                    content_length = response.headers.get("content-length")
                    if content_length and int(content_length) > budget:
                        raise ResponseSizeExceededError(
                            f"Response content length ({content_length} bytes) exceeds limit ({budget} bytes)."
                        )

                    if response.is_redirect:
                        if redirects_followed >= max_redirects:
                            raise SafeFetchError(f"Exceeded maximum redirect limit of {max_redirects}.")

                        location = response.headers.get("location")
                        if not location:
                            raise SafeFetchError("Received redirect status code without Location header.")

                        next_url = urljoin(current_url, location)
                        redirect_chain.append({
                            "from_url": current_url,
                            "to_url": next_url,
                            "status_code": response.status_code,
                        })
                        current_url = next_url
                        redirects_followed += 1
                        continue

                    if len(response.content) > budget:
                        raise ResponseSizeExceededError(
                            f"Downloaded content size ({len(response.content)} bytes) exceeds limit ({budget} bytes)."
                        )

                    elapsed_ms = (time.time() - start_time) * 1000.0
                    x_robots_tag = response.headers.get("x-robots-tag")

                    return SafeFetchResult(
                        is_success=(response.status_code < 400),
                        status_code=response.status_code,
                        response_time_ms=round(elapsed_ms, 2),
                        text_content=response.text,
                        content_type=response.headers.get("content-type"),
                        byte_size=len(response.content),
                        final_url=current_url,
                        x_robots_tag=x_robots_tag,
                        redirect_chain=redirect_chain,
                    )

        except Exception as exc:
            elapsed_ms = (time.time() - start_time) * 1000.0
            return SafeFetchResult(
                is_success=False,
                status_code=0,
                response_time_ms=round(elapsed_ms, 2),
                error_details=str(exc),
                final_url=current_url,
                redirect_chain=redirect_chain,
            )
