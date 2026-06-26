"""
Tests for URL detection + SSRF guard (Problem 6).

All offline/deterministic: SSRF cases use IP literals or reserved hostnames so no real
DNS/network is required.
"""
import sys
from pathlib import Path

# Make the backend package importable when running pytest from anywhere.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from utils.url_utils import (  # noqa: E402
    extract_urls,
    strip_urls,
    is_safe_url,
    has_urls,
)


# ---------- extraction ----------

def test_extract_single_url():
    assert extract_urls("summarize https://example.com/page for me") == [
        "https://example.com/page"
    ]


def test_extract_trims_trailing_punctuation():
    assert extract_urls("see https://example.com/path).") == ["https://example.com/path"]


def test_extract_multiple_and_dedupes():
    text = "compare https://a.com and https://b.com and https://a.com again"
    assert extract_urls(text) == ["https://a.com", "https://b.com"]


def test_extract_none():
    assert extract_urls("just a normal query") == []
    assert extract_urls("") == []


def test_has_urls():
    assert has_urls("go to http://x.com")
    assert not has_urls("no links here")


# ---------- stripping (recover the question) ----------

def test_strip_urls_leaves_question():
    assert strip_urls("summarize https://example.com/page in 3 points") == (
        "summarize in 3 points"
    )


def test_strip_urls_only_url():
    assert strip_urls("https://example.com") == ""


# ---------- SSRF guard: must BLOCK ----------

def test_block_localhost():
    ok, reason = is_safe_url("http://localhost:8000/admin")
    assert not ok and "localhost" in reason


def test_block_loopback_literal():
    ok, _ = is_safe_url("http://127.0.0.1/")
    assert not ok


def test_block_ipv6_loopback():
    ok, _ = is_safe_url("http://[::1]/")
    assert not ok


def test_block_private_ranges():
    for url in ("http://10.0.0.5/", "http://192.168.1.1/", "http://172.16.0.1/"):
        ok, _ = is_safe_url(url)
        assert not ok, url


def test_block_cloud_metadata():
    # 169.254.169.254 = AWS/GCP/Azure metadata endpoint (link-local)
    ok, _ = is_safe_url("http://169.254.169.254/latest/meta-data/")
    assert not ok


def test_block_non_http_schemes():
    for url in ("file:///etc/passwd", "ftp://host/x", "gopher://host"):
        ok, _ = is_safe_url(url)
        assert not ok, url


def test_block_dotlocal():
    ok, _ = is_safe_url("http://printer.local/")
    assert not ok


# ---------- SSRF guard: must ALLOW ----------

def test_allow_public_ip_literal():
    ok, reason = is_safe_url("https://1.1.1.1/")
    assert ok, reason


def test_allow_public_hostname_without_resolution():
    # resolve=False keeps it offline; syntactic + non-private checks still run.
    ok, reason = is_safe_url("https://example.com/article", resolve=False)
    assert ok, reason
