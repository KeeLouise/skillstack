import re
from urllib.parse import urljoin

try:
    import requests
except Exception:
    requests = None

_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0 Safari/537.36"
)

_OG_IMG_RE   = re.compile(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', re.I)
_TW_IMG_RE   = re.compile(r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)["\']', re.I)
_OG_TITLE_RE = re.compile(r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)["\']', re.I)
_TITLE_RE    = re.compile(r'<title[^>]*>(.*?)</title>', re.I | re.S)

def _get(url: str, timeout: float = 5.0):
    if not requests:
        return None, None
    try:
        r = requests.get(url, headers={"User-Agent": _UA}, timeout=timeout, allow_redirects=True)
        ct = r.headers.get("Content-Type", "")
        return r.text if "text/html" in ct or "text/" in ct or not ct else "", r.url
    except Exception:
        return None, None

def fetch_og_image(url: str) -> str | None:
    """
    Try to fetch a preview image (og:image or twitter:image).
    Returns an absolute URL or None.
    """
    html, final_url = _get(url)
    if not html or not final_url:
        return None

    m = _OG_IMG_RE.search(html)
    if m:
        return urljoin(final_url, m.group(1).strip())

    m = _TW_IMG_RE.search(html)
    if m:
        return urljoin(final_url, m.group(1).strip())

    return urljoin(final_url, "/favicon.ico")

def fetch_og_title(url: str) -> str | None:
    """
    Try to fetch a title (og:title or <title>).
    """
    html, _ = _get(url)
    if not html:
        return None
    m = _OG_TITLE_RE.search(html)
    if m:
        return m.group(1).strip()
    m = _TITLE_RE.search(html)
    if m:
        return re.sub(r"\s+", " ", m.group(1)).strip()
    return None