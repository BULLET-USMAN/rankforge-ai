import ipaddress
import re
from typing import Tuple
from urllib.parse import urlparse

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


class DomainValidationError(Exception):
    """Raised when a user-submitted domain or URL fails validation."""

    pass


class DomainNormalizer:
    """
    Robust normalizer and security validator for user-submitted domain strings and URLs.
    Handles raw domains (example.com), full URLs (https://www.example.com/path),
    extracts the normalized domain and canonical URL, and rejects private/loopback/unsafe addresses.
    """

    @classmethod
    def normalize_and_validate(cls, raw_input: str) -> Tuple[str, str]:
        """
        Takes raw user input, normalizes it, validates safety, and returns:
          (normalized_domain, canonical_url)
        Raises DomainValidationError on failure.
        """
        if not raw_input or not raw_input.strip():
            raise DomainValidationError("Domain or URL cannot be empty.")

        text = raw_input.strip()

        # Reject control characters
        if any(ord(c) < 32 or ord(c) == 127 for c in text):
            raise DomainValidationError("Input contains invalid or unsafe control characters.")

        # If no scheme is present, default to https:// for parsing
        has_scheme = bool(re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", text))
        parse_target = text if has_scheme else f"https://{text}"

        try:
            parsed = urlparse(parse_target)
        except Exception:
            raise DomainValidationError("Malformed URL or domain format.")

        # Check scheme
        scheme = parsed.scheme.lower()
        if scheme not in {"http", "https"}:
            raise DomainValidationError(
                f"Unsupported scheme '{scheme}'. Only HTTP and HTTPS are permitted."
            )

        # Reject embedded credentials (user:pass@host)
        if parsed.username or parsed.password:
            raise DomainValidationError(
                "Embedded credentials (user:pass@) are strictly prohibited."
            )

        # Reject non-standard ports
        if parsed.port and parsed.port not in {80, 443, 8080, 8443}:
            raise DomainValidationError(
                f"Port {parsed.port} is not permitted for monitored websites."
            )

        hostname = parsed.hostname
        if not hostname:
            raise DomainValidationError("A valid hostname could not be determined.")

        hostname = hostname.lower().strip()

        # Check blocked hostnames
        if hostname in BLOCKED_HOSTNAMES:
            raise DomainValidationError(f"Host '{hostname}' is prohibited.")

        # Check for IP address input (must not be private, loopback, link-local, multicast, etc.)
        try:
            ip = ipaddress.ip_address(hostname)
            if ip.is_private:
                raise DomainValidationError(
                    "Private network IP addresses (RFC 1918) cannot be added as websites."
                )
            if ip.is_loopback:
                raise DomainValidationError("Loopback addresses cannot be added as websites.")
            if ip.is_link_local:
                raise DomainValidationError(
                    "Link-local addresses (cloud metadata) cannot be added as websites."
                )
            if ip.is_multicast or ip.is_reserved or ip.is_unspecified:
                raise DomainValidationError(
                    "Reserved or multicast addresses cannot be added as websites."
                )
            if str(ip) == "169.254.169.254":
                raise DomainValidationError(
                    "Cloud metadata IP (169.254.169.254) is strictly prohibited."
                )
        except ValueError:
            # Not an IP literal, it is a domain name. Proceed with domain checks.
            pass

        # Check domain syntax: must have at least one dot and valid TLD
        parts = hostname.split(".")
        if len(parts) < 2 or not all(parts):
            raise DomainValidationError(
                "Domain must include a valid second-level name and top-level domain (e.g., example.com)."
            )

        tld = parts[-1]
        if tld in BLOCKED_TLDS:
            raise DomainValidationError(
                f"Top-level domain '.{tld}' is reserved for private or internal networks."
            )

        # Validate label characters (letters, numbers, hyphens)
        domain_regex = r"^([a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}$"
        if not re.match(domain_regex, hostname):
            raise DomainValidationError("Domain contains invalid characters or formatting.")

        normalized_domain = hostname

        # Construct canonical URL
        # Default to HTTPS unless HTTP was explicitly specified
        port_suffix = f":{parsed.port}" if parsed.port and parsed.port not in {80, 443} else ""
        canonical_url = f"{scheme}://{normalized_domain}{port_suffix}/"

        return normalized_domain, canonical_url
