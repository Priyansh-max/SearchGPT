"""
URL detection + SSRF protection for link-input mode (Problem 6).

Two jobs:
1. Pull URLs out of a user's query (so we scrape those instead of running a web search),
   and recover the remaining text as the actual question.
2. Decide whether a URL is SAFE for the server to fetch. This is an SSRF guard: a public
   endpoint that fetches arbitrary user-supplied URLs must never be tricked into hitting
   internal/loopback/link-local addresses or cloud metadata endpoints.
"""
import ipaddress
import re
import socket
from typing import List, Tuple
from urllib.parse import urlparse

# Matches http/https URLs. Trailing sentence punctuation is trimmed separately.
_URL_RE = re.compile(r'https?://[^\s<>"\')]+', re.IGNORECASE)

# Hostnames we refuse outright regardless of DNS.
_BLOCKED_HOSTNAMES = {
    "localhost",
    "metadata.google.internal",       # GCP metadata
    "metadata",
}

# Trailing characters commonly glued to a URL inside prose.
_TRAILING_JUNK = ".,);]>'\""


def extract_urls(text: str) -> List[str]:
    """Return the list of http(s) URLs found in ``text`` (order-preserving, de-duped)."""
    if not text:
        return []
    seen = set()
    out = []
    for raw in _URL_RE.findall(text):
        url = raw.rstrip(_TRAILING_JUNK)
        if url and url not in seen:
            seen.add(url)
            out.append(url)
    return out


def strip_urls(text: str) -> str:
    """Remove any URLs from ``text`` and return the leftover question, whitespace-collapsed."""
    if not text:
        return ""
    without = _URL_RE.sub(" ", text)
    return re.sub(r"\s+", " ", without).strip()


def _ip_is_blocked(ip_str: str) -> bool:
    """True if an IP string is in a range the server must not fetch."""
    try:
        ip = ipaddress.ip_address(ip_str)
    except ValueError:
        return True  # unparseable → treat as unsafe
    return (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local      # 169.254.0.0/16 — includes cloud metadata 169.254.169.254
        or ip.is_reserved
        or ip.is_multicast
        or ip.is_unspecified
    )


def is_safe_url(url: str, *, resolve: bool = True) -> Tuple[bool, str]:
    """
    SSRF guard. Returns (ok, reason).

    Blocks: non-http(s) schemes, localhost/.local, IP literals in private/loopback/
    link-local/reserved ranges, and hostnames that *resolve* to such ranges.

    ``resolve=False`` skips the DNS lookup (useful in tests / offline contexts); the
    syntactic and IP-literal checks still apply.
    """
    if not url:
        return False, "empty url"

    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return False, f"scheme not allowed: {parsed.scheme or '(none)'}"

    host = parsed.hostname
    if not host:
        return False, "no host"

    host_l = host.lower()
    if host_l in _BLOCKED_HOSTNAMES or host_l.endswith(".local"):
        return False, f"blocked host: {host}"

    # If the host is an IP literal, validate it directly (no DNS needed).
    try:
        ipaddress.ip_address(host)
        if _ip_is_blocked(host):
            return False, f"blocked ip literal: {host}"
        return True, "ok"
    except ValueError:
        pass  # it's a hostname; fall through to DNS resolution

    if not resolve:
        return True, "ok (unresolved)"

    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror:
        return False, f"dns resolution failed: {host}"

    for info in infos:
        ip_str = info[4][0]
        if _ip_is_blocked(ip_str):
            return False, f"resolves to blocked ip: {ip_str}"

    return True, "ok"


def has_urls(text: str) -> bool:
    """Convenience: does the text contain at least one URL (i.e. should we use link mode)?"""
    return bool(_URL_RE.search(text or ""))
