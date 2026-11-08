from app.services.ssrf_guard import SSRFGuard


def test_ssrf_blocks_private_ips():
    """SSRF guard must reject RFC 1918 private IPv4 addresses."""
    blocked_urls = [
        "http://10.0.0.1/admin",
        "http://172.16.0.1:8080/metrics",
        "http://192.168.1.1/",
    ]
    for url in blocked_urls:
        is_safe, reason = SSRFGuard.validate_url(url)
        assert not is_safe
        assert "private network" in reason.lower() or "blocked" in reason.lower()


def test_ssrf_blocks_loopback_and_localhost():
    """SSRF guard must reject loopback addresses and localhost."""
    loopback_urls = [
        "http://127.0.0.1/",
        "http://localhost:8000/api",
        "http://0.0.0.0/",
    ]
    for url in loopback_urls:
        is_safe, reason = SSRFGuard.validate_url(url)
        assert not is_safe
        assert "blocked" in reason.lower() or "loopback" in reason.lower()


def test_ssrf_blocks_cloud_metadata():
    """SSRF guard must strictly block cloud instance metadata IP 169.254.169.254."""
    url = "http://169.254.169.254/latest/meta-data/"
    is_safe, reason = SSRFGuard.validate_url(url)
    assert not is_safe
    assert "metadata" in reason.lower() or "link-local" in reason.lower()


def test_ssrf_blocks_invalid_schemes():
    """SSRF guard must reject non-HTTP/HTTPS schemes."""
    schemes = [
        "file:///etc/passwd",
        "gopher://example.com/",
        "ftp://example.com/file.txt",
    ]
    for url in schemes:
        is_safe, reason = SSRFGuard.validate_url(url)
        assert not is_safe
        assert "prohibited" in reason.lower()


def test_ssrf_allows_valid_public_domain():
    """SSRF guard should approve standard public websites."""
    is_safe, reason = SSRFGuard.validate_url("https://example.com")
    assert is_safe
    assert reason == "URL is safe"
