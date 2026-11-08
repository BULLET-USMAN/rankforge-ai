"""Unit tests for SSRF-Hardened SafeHttpFetcher."""

import ipaddress

import pytest

from app.services.crawler.safe_fetcher import (
    SafeHttpFetcher,
    SSRFValidationError,
)


def test_ip_validation_blocks_loopback():
    with pytest.raises(SSRFValidationError, match="loopback"):
        SafeHttpFetcher.validate_destination_ip(ipaddress.ip_address("127.0.0.1"))

    with pytest.raises(SSRFValidationError, match="loopback"):
        SafeHttpFetcher.validate_destination_ip(ipaddress.ip_address("::1"))


def test_ip_validation_blocks_cloud_metadata():
    with pytest.raises(SSRFValidationError, match="169.254.169.254"):
        SafeHttpFetcher.validate_destination_ip(ipaddress.ip_address("169.254.169.254"))


def test_ip_validation_blocks_private_networks():
    # 10.0.0.0/8
    with pytest.raises(SSRFValidationError, match="private"):
        SafeHttpFetcher.validate_destination_ip(ipaddress.ip_address("10.0.0.5"))

    # 172.16.0.0/12
    with pytest.raises(SSRFValidationError, match="private"):
        SafeHttpFetcher.validate_destination_ip(ipaddress.ip_address("172.20.0.1"))

    # 192.168.0.0/16
    with pytest.raises(SSRFValidationError, match="private"):
        SafeHttpFetcher.validate_destination_ip(ipaddress.ip_address("192.168.1.100"))


def test_ip_validation_allows_public_ip():
    # Public DNS like 8.8.8.8, 1.1.1.1
    SafeHttpFetcher.validate_destination_ip(ipaddress.ip_address("8.8.8.8"))
    SafeHttpFetcher.validate_destination_ip(ipaddress.ip_address("1.1.1.1"))


def test_url_syntax_validation():
    # Valid HTTP/HTTPS
    scheme, host, port = SafeHttpFetcher.validate_url_syntax("https://example.com/path")
    assert scheme == "https"
    assert host == "example.com"
    assert port == 443

    scheme, host, port = SafeHttpFetcher.validate_url_syntax("http://example.com:8080/path")
    assert scheme == "http"
    assert host == "example.com"
    assert port == 8080

    # Invalid scheme
    with pytest.raises(SSRFValidationError, match="Scheme 'ftp' is prohibited"):
        SafeHttpFetcher.validate_url_syntax("ftp://example.com/file")

    with pytest.raises(SSRFValidationError, match="Scheme 'file' is prohibited"):
        SafeHttpFetcher.validate_url_syntax("file:///etc/passwd")

    # Embedded credentials
    with pytest.raises(SSRFValidationError, match="userinfo"):
        SafeHttpFetcher.validate_url_syntax("https://admin:pass@example.com")

    # Disallowed port
    with pytest.raises(SSRFValidationError, match="Port 22 is not allowed"):
        SafeHttpFetcher.validate_url_syntax("https://example.com:22/ssh")


def test_hostname_resolution_blocks_localhost():
    with pytest.raises(SSRFValidationError, match="localhost"):
        SafeHttpFetcher.resolve_and_validate_hostname("localhost")

    with pytest.raises(SSRFValidationError, match="metadata"):
        SafeHttpFetcher.resolve_and_validate_hostname("metadata.google.internal")


def test_fetch_sync_handles_ssrf_gracefully():
    # SafeHttpFetcher.fetch_sync returns SafeFetchResult with is_success=False instead of crashing
    result = SafeHttpFetcher.fetch_sync("http://127.0.0.1:8080/admin")
    assert not result.is_success
    assert "prohibited" in (result.error_details or "").lower() or "loopback" in (result.error_details or "").lower()
