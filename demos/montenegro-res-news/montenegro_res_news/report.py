"""Classroom report: markdown table, CSV, and the web handout.

The HTML walks an agentic loop — goal, tools, plan/reason, action,
observation, memory, stop — then leaves the evidence on the page.
"""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from montenegro_res_news.classroom_page import CSS as CSS  # re-exported for tests
from montenegro_res_news.classroom_page import build_html, html_from_result
from montenegro_res_news.mandate import GOAL, QUALITY_MIN_ARTICLES, SCOPE

def two_line_summary(rows: list[dict[str, Any]], *, mode: str) -> str:
    """Evidence-based two-liner. Sample uses the curated record; live stays conservative."""
    if mode == "sample":
        return (
            "After the August 2024 RES Law, published coverage was mostly legal briefing: "
            "Energy Community, law firms and the EBRD treated auctions and market premiums as the new investment framework. "
            "Reception shifted after the first 250 MW solar auction — July 2025 launch pieces were optimistic, "
            "but from January 2026 outlets reported all four bids disqualified on permitting, grid and documentation grounds, "
            "and by July–August 2026 official statements said a relaunch awaits revised rules with no date fixed."
        )
    if not rows:
        return (
            "not found: live search returned no usable news or official statements in the last 12 months. "
            "Do not infer reception of the RES Law or the first solar auction from an empty result set."
        )
    counts = Counter(r.get("tone") for r in rows)
    first = min((r.get("date") or "9999") for r in rows)
    last = max((r.get("date") or "") for r in rows)
    return (
        f"Live run labelled {len(rows)} published items ({counts.get('positive', 0)} positive, "
        f"{counts.get('negative', 0)} negative, {counts.get('neutral', 0)} neutral) dated {first} to {last}. "
        "See the quoted cells for what each outlet actually said; empty or weak snippets are marked not found rather than inferred."
    )


def tone_by_month(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    buckets: dict[str, Counter[str]] = defaultdict(Counter)
    undated = Counter()
    for row in rows:
        date = str(row.get("date") or "")
        tone = str(row.get("tone") or "neutral")
        if len(date) >= 7 and date[0:4].isdigit():
            buckets[date[:7]][tone] += 1
        else:
            undated[tone] += 1
    months = sorted(buckets)
    out = [{"month": m, **{t: int(buckets[m][t]) for t in ("positive", "negative", "neutral")}} for m in months]
    if undated:
        out.append(
            {
                "month": "date not found",
                "positive": int(undated["positive"]),
                "negative": int(undated["negative"]),
                "neutral": int(undated["neutral"]),
            }
        )
    return out


def write_outputs(
    rows: list[dict[str, Any]],
    search_log: list[dict[str, Any]],
    outdir: Path,
    *,
    mode: str,
    backend: str,
    fallback_reason: str | None = None,
) -> dict[str, Path]:
    outdir.mkdir(parents=True, exist_ok=True)
    rows = sorted(
        rows,
        key=lambda r: (str(r.get("date") or "not found") == "not found", str(r.get("date") or "")),
    )
    summary = two_line_summary(rows, mode=mode)
    strip = tone_by_month(rows)
    generated = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    csv_path = outdir / "table.csv"
    md_path = outdir / "report.md"
    html_path = outdir / "report.html"
    log_path = outdir / "search_log.json"
    summary_path = outdir / "summary.txt"
    json_path = outdir / "articles.json"

    _write_csv(csv_path, rows)
    _write_markdown(md_path, rows, strip, summary, search_log, mode, backend, fallback_reason, generated)
    html_path.write_text(
        build_html(
            rows,
            strip,
            summary,
            search_log,
            mode,
            backend,
            fallback_reason,
            generated,
        ),
        encoding="utf-8",
    )
    log_path.write_text(json.dumps(search_log, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    summary_path.write_text(summary + "\n", encoding="utf-8")
    json_path.write_text(json.dumps(rows, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    return {
        "csv": csv_path,
        "markdown": md_path,
        "html": html_path,
        "search_log": log_path,
        "summary": summary_path,
        "articles": json_path,
    }


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = [
        "outlet",
        "date",
        "url",
        "quote",
        "tone",
        "tone_justification",
        "topic",
        "topic_justification",
        "title",
        "claim",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "not found") for k in fields})


def _write_markdown(
    path: Path,
    rows: list[dict[str, Any]],
    strip: list[dict[str, Any]],
    summary: str,
    search_log: list[dict[str, Any]],
    mode: str,
    backend: str,
    fallback_reason: str | None,
    generated: str,
) -> None:
    lines = [
        "# Montenegro RES Law and first solar auction — media reception",
        "",
        f"_IPDET Impact London teaching demo · generated {generated} · mode `{mode}` · backend `{backend}`_",
        "",
        f"**Goal.** {GOAL}",
        "",
        f"**Scope.** {SCOPE}",
        "",
    ]
    if fallback_reason:
        lines += [f"**Fallback.** {fallback_reason}", ""]
    lines += [
        "## Two-line summary",
        "",
        summary,
        "",
        "## Tone by month",
        "",
        "| Month | Positive | Negative | Neutral |",
        "| --- | ---: | ---: | ---: |",
    ]
    for bucket in strip:
        lines.append(
            f"| {bucket['month']} | {bucket.get('positive', 0)} | {bucket.get('negative', 0)} | {bucket.get('neutral', 0)} |"
        )
    lines += [
        "",
        f"Rows: **{len(rows)}** (quality target ≥ {QUALITY_MIN_ARTICLES}).",
        "",
        "## Agent table",
        "",
        "| Outlet | Date | Link | Quote | Tone | Topic |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        url = row.get("url") or "not found"
        link = f"[link]({url})" if url != "not found" else "not found"
        quote = _md_cell(row.get("quote"))
        tone = f"{row.get('tone')} — {_md_cell(row.get('tone_justification'))}"
        topic = f"{row.get('topic')} — {_md_cell(row.get('topic_justification'))}"
        lines.append(
            f"| {_md_cell(row.get('outlet'))} | {_md_cell(row.get('date'))} | {link} | {quote} | {tone} | {topic} |"
        )
    lines += ["", "## Search log", "", "```json", json.dumps(search_log, indent=2, ensure_ascii=False), "```", ""]
    path.write_text("\n".join(lines), encoding="utf-8")


def _md_cell(value: Any) -> str:
    text = str(value or "not found").replace("|", "\\|").replace("\n", " ")
    return text
