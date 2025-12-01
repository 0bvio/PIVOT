from __future__ import annotations

import os
from typing import Dict, Tuple
from urllib.parse import urlparse

import requests


def _extract_channel_id(ref: str) -> str:
    # Accept raw channel ID or a URL like https://discord.com/channels/<guild>/<channel>
    if ref.isdigit():
        return ref
    try:
        parsed = urlparse(ref)
        if parsed.netloc.endswith("discord.com") and parsed.path.startswith("/channels/"):
            parts = parsed.path.split("/")
            if len(parts) >= 4:
                return parts[3]
    except Exception:
        pass
    raise ValueError("Invalid Discord channel reference")


def fetch_discord_channel(source_ref: str) -> Tuple[str, Dict]:
    token = os.environ.get("DISCORD_BOT_TOKEN")
    if not token:
        raise RuntimeError("DISCORD_BOT_TOKEN not set in environment")
    channel_id = _extract_channel_id(source_ref)
    headers = {
        "Authorization": f"Bot {token}",
        "User-Agent": "pivot-ingestor/0.1",
    }
    url = f"https://discord.com/api/v10/channels/{channel_id}/messages?limit=100"
    resp = requests.get(url, headers=headers, timeout=20)
    resp.raise_for_status()
    messages = resp.json()
    lines = []
    for m in reversed(messages):  # chronological
        author = (m.get("author") or {}).get("username") or ""
        content = m.get("content") or ""
        if content:
            lines.append(f"{author}: {content}")
    text = "\n".join(lines)
    meta = {
        "title": f"Discord Channel {channel_id}",
        "source_url": f"https://discord.com/channels/0/{channel_id}",
        "source_type": "discord",
        "is_html": False,
    }
    return text, meta
