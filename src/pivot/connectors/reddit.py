from __future__ import annotations

from typing import Dict, Tuple
from urllib.parse import urlparse

import requests


def _to_json_url(url: str) -> str:
    # Accept thread URL or short link; append .json with raw_json=1
    parsed = urlparse(url)
    if not parsed.netloc:
        raise ValueError("Invalid Reddit URL")
    if not url.endswith(".json"):
        if not url.endswith("/"):
            url = url + "/"
        url = url + ".json"
    if "raw_json=1" not in url:
        sep = "&" if "?" in url else "?"
        url = f"{url}{sep}raw_json=1"
    return url


def fetch_reddit_thread(source_ref: str) -> Tuple[str, Dict]:
    url = _to_json_url(source_ref)
    headers = {"User-Agent": "pivot-ingestor/0.1"}
    resp = requests.get(url, headers=headers, timeout=20)
    resp.raise_for_status()
    data = resp.json()
    texts: list[str] = []
    title = None
    try:
        post = data[0]["data"]["children"][0]["data"]
        title = post.get("title")
        selftext = post.get("selftext", "")
        if title:
            texts.append(title)
        if selftext:
            texts.append(selftext)
        # comments tree
        def walk(node):
            if isinstance(node, dict) and node.get("kind") == "t1":
                body = node.get("data", {}).get("body")
                if body:
                    texts.append(body)
            if isinstance(node, dict):
                kids = node.get("data", {}).get("replies")
                if isinstance(kids, dict):
                    for ch in kids.get("data", {}).get("children", []):
                        walk(ch)
        if len(data) > 1:
            for ch in data[1].get("data", {}).get("children", []):
                walk(ch)
    except Exception:
        # Fallback: flatten as string
        texts.append(resp.text)
    text = "\n\n".join(t for t in texts if t)
    meta = {
        "title": title or source_ref,
        "source_url": source_ref,
        "source_type": "reddit",
        "is_html": False,
    }
    return text, meta
