from __future__ import annotations

from typing import Dict, Tuple

import requests


def fetch_http_url(source_ref: str) -> Tuple[str, Dict]:
    """Fetch text from an HTTP/HTTPS URL. If HTML, return raw HTML (normalizer will strip)."""
    resp = requests.get(source_ref, timeout=20)
    resp.raise_for_status()
    content_type = resp.headers.get("content-type", "").lower()
    text = resp.text
    meta = {
        "title": source_ref,
        "source_url": source_ref,
        "source_type": "http_url",
        "content_type": content_type,
        "is_html": "html" in content_type,
    }
    return text, meta
