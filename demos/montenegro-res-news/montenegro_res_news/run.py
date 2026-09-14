"""Shared sample / live run used by the CLI and the web app."""

from __future__ import annotations

import os
from typing import Any

from montenegro_res_news.analyze import analyze_hit
from montenegro_res_news.mandate import QUALITY_MIN_ARTICLES, live_window_start
from montenegro_res_news.paths import load_sample
from montenegro_res_news.search import search_live

SAMPLE_FALLBACK = (
    "Using the checked-in pre-run compiled from published news and official pages "
    "(frozen 14 September 2026). No live web search was performed."
)

LIVE_KEY_VARS = ("TAVILY_API_KEY", "BRAVE_API_KEY", "NEWSAPI_KEY")


def sort_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        rows,
        key=lambda r: (str(r.get("date") or "not found") == "not found", str(r.get("date") or "")),
    )


def configured_search_backends() -> list[str]:
    mapping = {
        "TAVILY_API_KEY": "tavily",
        "BRAVE_API_KEY": "brave",
        "NEWSAPI_KEY": "newsapi",
    }
    return [name for env, name in mapping.items() if os.environ.get(env)]


def live_api_keys_present() -> bool:
    return bool(configured_search_backends())


def run_sample() -> dict[str, Any]:
    rows, log = load_sample()
    return {
        "rows": sort_rows(rows),
        "log": log,
        "backend": "sample",
        "mode": "sample",
        "fallback": SAMPLE_FALLBACK,
    }


def try_live(*, force_live: bool) -> dict[str, Any]:
    try:
        hits, log, backend = search_live()
    except Exception as exc:  # noqa: BLE001 — classroom: log and continue
        if force_live:
            raise
        rows, sample_log = load_sample()
        reason = f"Live search failed ({exc}). Falling back to the checked-in sample; no articles were invented."
        sample_log = list(sample_log) + [
            {
                "timestamp": "not found",
                "backend": "fallback",
                "query": "live search",
                "status": "error",
                "result_count": 0,
                "error": str(exc),
                "notes": reason,
            }
        ]
        return {
            "rows": sort_rows(rows),
            "log": sample_log,
            "backend": "sample",
            "mode": "sample",
            "fallback": reason,
        }

    rows = [analyze_hit(hit) for hit in hits]
    rows = [r for r in rows if r.get("quote") != "not found"]
    rows = _drop_outside_window(rows)

    if force_live:
        return {
            "rows": sort_rows(rows),
            "log": log,
            "backend": backend,
            "mode": "live",
            "fallback": None,
        }

    if len(rows) < QUALITY_MIN_ARTICLES:
        sample_rows, sample_log = load_sample()
        reason = (
            f"Live backend `{backend}` returned {len(rows)} usable news/official rows "
            f"(target ≥ {QUALITY_MIN_ARTICLES}). Using the checked-in sample instead of padding with invented coverage."
        )
        combined_log = list(log) + list(sample_log) + [
            {
                "timestamp": "not found",
                "backend": "fallback",
                "query": "quality threshold",
                "status": "ok",
                "result_count": len(sample_rows),
                "error": None,
                "notes": reason,
            }
        ]
        return {
            "rows": sort_rows(sample_rows),
            "log": combined_log,
            "backend": "sample",
            "mode": "sample",
            "fallback": reason,
        }

    return {
        "rows": sort_rows(rows),
        "log": log,
        "backend": backend,
        "mode": "live",
        "fallback": None,
    }


def _drop_outside_window(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    start = live_window_start().isoformat()
    kept: list[dict[str, Any]] = []
    for row in rows:
        value = str(row.get("date") or "not found")
        if value == "not found" or value >= start:
            kept.append(row)
    return kept
