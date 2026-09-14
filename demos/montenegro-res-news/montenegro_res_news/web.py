"""Thin classroom web app for Railway / local uvicorn.

Serves the evaluation-brief HTML. Live search runs only when an API key is set.
"""

from __future__ import annotations

import html as html_lib
import os

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse, Response

from montenegro_res_news.report import html_from_result
from montenegro_res_news.run import configured_search_backends, live_api_keys_present, run_sample, try_live

NO_KEYS_MESSAGE = (
    "No TAVILY_API_KEY, BRAVE_API_KEY, or NEWSAPI_KEY is set. "
    "This page stays on the classroom sample. No articles were invented."
)

app = FastAPI(
    title="Montenegro RES news demo",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)


def _toolbar(*, keys: bool, notice: str | None = None) -> str:
    backends = ", ".join(configured_search_backends()) or "none"
    if keys:
        live_block = (
            "<p>A search API key is configured "
            f"({html_lib.escape(backends)}). Live search still uses published news only "
            "and falls back to the sample rather than inventing rows.</p>"
            "<form method='post' action='/live'>"
            "<button type='submit'>Try live search</button>"
            "</form>"
            "<a class='quiet' href='/'>Classroom sample</a>"
        )
    else:
        live_block = (
            f"<p>{html_lib.escape(NO_KEYS_MESSAGE)}</p>"
            "<form method='post' action='/live'>"
            "<button type='submit'>Try live search</button>"
            "</form>"
            "<a class='quiet' href='/'>Classroom sample</a>"
        )
    extra = f"<p><strong>Note.</strong> {html_lib.escape(notice)}</p>" if notice else ""
    return (
        "<section class='toolbar'>"
        "<p>IPDET Impact London · hosted classroom handout (sample by default).</p>"
        f"{live_block}{extra}"
        "</section>"
    )


def _page(result: dict, *, notice: str | None = None) -> HTMLResponse:
    body = html_from_result(
        result,
        toolbar_html=_toolbar(keys=live_api_keys_present(), notice=notice),
    )
    return HTMLResponse(body)


@app.get("/", response_class=HTMLResponse)
def classroom_sample() -> HTMLResponse:
    return _page(run_sample())


@app.post("/live", response_class=HTMLResponse)
def live_or_sample() -> HTMLResponse:
    if not live_api_keys_present():
        result = run_sample()
        result["fallback"] = NO_KEYS_MESSAGE
        return _page(result, notice=NO_KEYS_MESSAGE)
    result = try_live(force_live=False)
    return _page(result)


@app.get("/health")
def health() -> JSONResponse:
    return JSONResponse(
        {
            "status": "ok",
            "demo": "montenegro-res-news",
            "live_backends": configured_search_backends(),
        }
    )


@app.get("/favicon.ico")
def favicon() -> Response:
    return Response(status_code=204)


def listen_port() -> int:
    return int(os.environ.get("PORT", "8000"))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=listen_port(), proxy_headers=True)
