import ipaddress
import socket
from typing import Tuple
from urllib.parse import urlparse


class SSRFSecurityException(Exception):
    """Raised when a URL fails SSRF security validation."""
    pass


class SSRFGuard:
    """
    Production-grade SSRF (Server-Side Request Forgery) guard.
    Validates external URLs to prevent malicious targeting of internal networks,
    cloud metadata endpoints, and loopback services.
    """

    ALLOWED_SCHEMES = {"http", "https"}
    BLOCKED_HOSTNAMES = {
        "localhost",
        "127.0.0.1",
        "0.0.0.0",
        "::1",
        "metadata.google.internal",
        "instance-data",
    }

    @classmethod
    def validate_url(cls, raw_url: str) -> Tuple[bool, str]:
        """
        Validates URL syntax, protocol, and resolves IP to verify it is public and safe.
        Returns (is_safe, error_reason).
        """
        if not raw_url:
            return False, "URL cannot be empty"

        try:
            parsed = urlparse(raw_url.strip())
        except Exception:
            return False, "Invalid URL format"

        # Check scheme
        if parsed.scheme.lower() not in cls.ALLOWED_SCHEMES:
            return False, f"Scheme '{parsed.scheme}' is prohibited. Only HTTP and HTTPS are permitted."

        hostname = parsed.hostname
        if not hostname:
            return False, "Hostname could not be determined from URL."

        # Check blocked hostnames
        if hostname.lower() in cls.BLOCKED_HOSTNAMES:
            return False, f"Access to hostname '{hostname}' is blocked by security policy."

        # Check port if specified
        if parsed.port and parsed.port not in {80, 443, 8080, 8443}:
            return False, f"Port {parsed.port} is not in the allowed public HTTP/HTTPS ports."

        # Resolve DNS to IP and check for private / loopback / metadata ranges
        try:
            addr_info = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
        except socket.gaierror:
            return False, f"DNS resolution failed for hostname '{hostname}'."
        except Exception as e:
            return False, f"DNS check failed: {str(e)}"

        for family, _, _, _, sockaddr in addr_info:
            ip_str = sockaddr[0]
            try:
                ip = ipaddress.ip_address(ip_str)
            except ValueError:
                return False, f"Invalid resolved IP address: {ip_str}"

            # Specific cloud metadata and link-local protections first
            if str(ip) == "169.254.169.254":
                return False, "Targeting cloud metadata endpoint (169.254.169.254) is strictly forbidden."
            if ip.is_link_local:
                return False, f"Resolved IP {ip_str} is a link-local address (metadata service protection)."
            if ip.is_loopback:
                return False, f"Resolved IP {ip_str} is a loopback address."
            if ip.is_private:
                return False, f"Resolved IP {ip_str} is in a private network range (RFC 1918)."
            if ip.is_multicast:
                return False, f"Resolved IP {ip_str} is a multicast address."
            if ip.is_reserved:
                return False, f"Resolved IP {ip_str} is a reserved address."
            if ip.is_unspecified:
                return False, f"Resolved IP {ip_str} is an unspecified address."

        return True, "URL is safe"
