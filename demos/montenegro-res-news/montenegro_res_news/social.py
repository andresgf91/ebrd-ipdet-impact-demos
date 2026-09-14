"""Drop social-media hosts. Mandate: published news and official statements only."""

from __future__ import annotations

from urllib.parse import urlparse

from montenegro_res_news.mandate import SOCIAL_HOST_MARKERS


def host_of(url: str) -> str:
    try:
        return (urlparse(url).hostname or "").lower()
    except ValueError:
        return ""


def is_social_url(url: str) -> bool:
    host = host_of(url)
    if not host:
        return False
    labels = host.split(".")
    for marker in SOCIAL_HOST_MARKERS:
        marker = marker.lower().lstrip(".")
        if "." in marker:
            if host == marker or host.endswith("." + marker):
                return True
        elif marker in labels:
            return True
    return False


def reject_social(hits: list[dict]) -> tuple[list[dict], list[dict]]:
    kept: list[dict] = []
    dropped: list[dict] = []
    for hit in hits:
        url = str(hit.get("url") or "")
        if is_social_url(url):
            dropped.append(hit)
        else:
            kept.append(hit)
    return kept, dropped
