"""Search backends and the search log.

Live mode never invents hits. Empty / error results are logged and returned as-is.
"""

from __future__ import annotations

import json
import os
from datetime import date, datetime, timezone
from typing import Any
from urllib.parse import urlparse

import requests

from montenegro_res_news.mandate import SEARCH_QUERIES, live_window_end, live_window_start
from montenegro_res_news.social import reject_social

USER_AGENT = "ebrd-ipdet-impact-demos/montenegro-res-news (teaching demo)"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def new_log() -> list[dict[str, Any]]:
    return []


def record(
    log: list[dict[str, Any]],
    *,
    backend: str,
    query: str,
    status: str,
    result_count: int = 0,
    date_from: str | None = None,
    date_to: str | None = None,
    error: str | None = None,
    notes: str | None = None,
) -> None:
    entry: dict[str, Any] = {
        "timestamp": utc_now_iso(),
        "backend": backend,
        "query": query,
        "date_from": date_from,
        "date_to": date_to,
        "status": status,
        "result_count": result_count,
        "error": error,
    }
    if notes:
        entry["notes"] = notes
    log.append(entry)


def choose_backend() -> str:
    if os.environ.get("TAVILY_API_KEY"):
        return "tavily"
    if os.environ.get("BRAVE_API_KEY"):
        return "brave"
    if os.environ.get("NEWSAPI_KEY"):
        return "newsapi"
    return "ddgs"


def search_live(
    queries: tuple[str, ...] | list[str] = SEARCH_QUERIES,
    *,
    today: date | None = None,
    log: list[dict[str, Any]] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], str]:
    """Run the mandated query set. Returns (hits, log, backend_name)."""
    if log is None:
        log = new_log()
    start = live_window_start(today)
    end = live_window_end(today)
    backend = choose_backend()
    hits: list[dict[str, Any]] = []

    if backend == "tavily":
        runner = _tavily
    elif backend == "brave":
        runner = _brave
    elif backend == "newsapi":
        runner = _newsapi
    else:
        runner = _ddgs

    for query in queries:
        try:
            batch = runner(query, start, end, log)
        except Exception as exc:  # noqa: BLE001 — classroom: log and continue
            record(
                log,
                backend=backend,
                query=query,
                status="error",
                date_from=start.isoformat(),
                date_to=end.isoformat(),
                error=str(exc),
            )
            continue
        hits.extend(batch)

    hits, dropped = reject_social(hits)
    if dropped:
        record(
            log,
            backend="filter",
            query="social-media host exclusion",
            status="ok",
            result_count=len(dropped),
            notes="Dropped social URLs; mandate allows news and official statements only.",
        )
    return _dedupe(hits), log, backend


def _dedupe(hits: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for hit in hits:
        url = str(hit.get("url") or "").split("#")[0].rstrip("/")
        key = url.lower()
        if not key or key in seen:
            continue
        seen.add(key)
        hit["url"] = url
        out.append(hit)
    return out


def _tavily(query: str, start: date, end: date, log: list[dict[str, Any]]) -> list[dict[str, Any]]:
    key = os.environ["TAVILY_API_KEY"]
    payload = {
        "api_key": key,
        "query": query,
        "search_depth": "basic",
        "topic": "news",
        "max_results": 10,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "include_answer": False,
    }
    response = requests.post(
        "https://api.tavily.com/search",
        json=payload,
        timeout=30,
        headers={"User-Agent": USER_AGENT},
    )
    response.raise_for_status()
    data = response.json()
    results = data.get("results") or []
    record(
        log,
        backend="tavily",
        query=query,
        status="ok",
        result_count=len(results),
        date_from=start.isoformat(),
        date_to=end.isoformat(),
    )
    hits = []
    for item in results:
        hits.append(
            {
                "url": item.get("url") or "",
                "title": item.get("title") or "",
                "snippet": item.get("content") or "",
                "outlet": _outlet_from_url(item.get("url") or ""),
                "date": item.get("published_date") or "not found",
                "backend": "tavily",
            }
        )
    return hits


def _brave(query: str, start: date, end: date, log: list[dict[str, Any]]) -> list[dict[str, Any]]:
    key = os.environ["BRAVE_API_KEY"]
    params = {
        "q": query,
        "count": 10,
        "freshness": f"{start.isoformat()}to{end.isoformat()}",
        "text_decorations": 0,
    }
    response = requests.get(
        "https://api.search.brave.com/res/v1/web/search",
        params=params,
        timeout=30,
        headers={
            "Accept": "application/json",
            "X-Subscription-Token": key,
            "User-Agent": USER_AGENT,
        },
    )
    response.raise_for_status()
    data = response.json()
    results = ((data.get("web") or {}).get("results")) or []
    record(
        log,
        backend="brave",
        query=query,
        status="ok",
        result_count=len(results),
        date_from=start.isoformat(),
        date_to=end.isoformat(),
    )
    hits = []
    for item in results:
        hits.append(
            {
                "url": item.get("url") or "",
                "title": item.get("title") or "",
                "snippet": item.get("description") or "",
                "outlet": item.get("profile", {}).get("name")
                or _outlet_from_url(item.get("url") or ""),
                "date": (item.get("page_age") or "not found"),
                "backend": "brave",
            }
        )
    return hits


def _newsapi(query: str, start: date, end: date, log: list[dict[str, Any]]) -> list[dict[str, Any]]:
    key = os.environ["NEWSAPI_KEY"]
    params = {
        "q": query,
        "from": start.isoformat(),
        "to": end.isoformat(),
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": 20,
        "apiKey": key,
    }
    response = requests.get(
        "https://newsapi.org/v2/everything",
        params=params,
        timeout=30,
        headers={"User-Agent": USER_AGENT},
    )
    response.raise_for_status()
    data = response.json()
    if data.get("status") != "ok":
        raise RuntimeError(data.get("message") or json.dumps(data))
    results = data.get("articles") or []
    record(
        log,
        backend="newsapi",
        query=query,
        status="ok",
        result_count=len(results),
        date_from=start.isoformat(),
        date_to=end.isoformat(),
    )
    hits = []
    for item in results:
        source = item.get("source") or {}
        hits.append(
            {
                "url": item.get("url") or "",
                "title": item.get("title") or "",
                "snippet": item.get("description") or item.get("content") or "",
                "outlet": source.get("name") or _outlet_from_url(item.get("url") or ""),
                "date": (item.get("publishedAt") or "not found")[:10],
                "backend": "newsapi",
            }
        )
    return hits


def _ddgs(query: str, start: date, end: date, log: list[dict[str, Any]]) -> list[dict[str, Any]]:
    try:
        from ddgs import DDGS
    except ImportError:
        record(
            log,
            backend="ddgs",
            query=query,
            status="error",
            date_from=start.isoformat(),
            date_to=end.isoformat(),
            error="ddgs is not installed. pip install ddgs, or set TAVILY_API_KEY / BRAVE_API_KEY / NEWSAPI_KEY.",
        )
        return []

    results: list[dict[str, Any]] = []
    try:
        with DDGS() as client:
            news = list(
                client.news(query, timelimit="y", max_results=10)
                or []
            )
            if not news:
                news = list(client.text(query, timelimit="y", max_results=10) or [])
    except Exception as exc:  # noqa: BLE001
        record(
            log,
            backend="ddgs",
            query=query,
            status="error",
            date_from=start.isoformat(),
            date_to=end.isoformat(),
            error=str(exc),
        )
        return []

    record(
        log,
        backend="ddgs",
        query=query,
        status="ok",
        result_count=len(news),
        date_from=start.isoformat(),
        date_to=end.isoformat(),
        notes="DuckDuckGo has no guaranteed date filter; rows outside the 12-month window are dropped later.",
    )
    for item in news:
        url = item.get("url") or item.get("href") or ""
        results.append(
            {
                "url": url,
                "title": item.get("title") or "",
                "snippet": item.get("body") or item.get("excerpt") or "",
                "outlet": item.get("source") or _outlet_from_url(url),
                "date": item.get("date") or item.get("published") or "not found",
                "backend": "ddgs",
            }
        )
    return results


def _outlet_from_url(url: str) -> str:
    host = (urlparse(url).hostname or "").lower()
    if host.startswith("www."):
        host = host[4:]
    return host or "not found"
