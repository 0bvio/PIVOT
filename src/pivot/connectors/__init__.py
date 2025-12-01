from __future__ import annotations

from typing import Any, Dict, Tuple


def run_connector(source_type: str, source_ref: str, extra: Dict[str, Any] | None = None) -> Tuple[str, Dict[str, Any]]:
    extra = extra or {}
    if source_type == "local_file":
        from .local_file import load_local_file

        return load_local_file(source_ref)
    if source_type == "http_url":
        from .http_url import fetch_http_url

        return fetch_http_url(source_ref)
    if source_type == "reddit":
        from .reddit import fetch_reddit_thread

        return fetch_reddit_thread(source_ref)
    if source_type == "discord":
        from .discord import fetch_discord_channel

        return fetch_discord_channel(source_ref)
    if source_type == "google_drive":
        # google drive connector may not be present in tests
        try:
            from .google_drive import fetch_google_drive

            return fetch_google_drive(source_ref)
        except Exception as e:
            raise RuntimeError("google_drive connector not available") from e
    raise ValueError(f"Unsupported source_type: {source_type}")
