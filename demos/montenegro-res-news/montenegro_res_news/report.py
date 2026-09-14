"""Classroom report: markdown table, CSV, quiet HTML handout, tone-by-month strip."""

from __future__ import annotations

import csv
import html
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from montenegro_res_news.mandate import GOAL, QUALITY_MIN_ARTICLES, SCOPE

# Workshop palette: paper, ink, muted evaluation-report colours. No neon.
CSS = """
:root {
  --paper: #f7f5f1;
  --card: #ffffff;
  --ink: #2b2a27;
  --muted: #6d6860;
  --line: #e3ddd4;
  --accent: #3f5c4c;
  --positive: #3f5c4c;
  --negative: #8a5348;
  --neutral: #7a746c;
}
* { box-sizing: border-box; }
html, body {
  margin: 0;
  padding: 0;
  background: var(--paper);
  color: var(--ink);
  font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
  line-height: 1.5;
  font-size: 16px;
}
.wrap {
  max-width: 1080px;
  margin: 0 auto;
  padding: 2.25rem 1.5rem 3.5rem;
}
header h1 {
  font-family: Georgia, "Times New Roman", serif;
  font-weight: 400;
  font-size: 1.85rem;
  letter-spacing: -0.01em;
  margin: 0 0 0.35rem;
}
.kicker {
  color: var(--muted);
  font-size: 0.85rem;
  text-transform: none;
  letter-spacing: 0.02em;
  margin: 0 0 1.5rem;
}
.card {
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: 6px;
  padding: 1.15rem 1.25rem;
  margin-bottom: 1.25rem;
}
h2 {
  font-family: Georgia, "Times New Roman", serif;
  font-weight: 400;
  font-size: 1.2rem;
  margin: 0 0 0.7rem;
}
.summary p { margin: 0 0 0.5rem; }
.summary p:last-child { margin-bottom: 0; }
.mandate {
  color: var(--muted);
  font-size: 0.92rem;
}
table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.88rem;
}
th, td {
  text-align: left;
  vertical-align: top;
  padding: 0.55rem 0.5rem;
  border-bottom: 1px solid var(--line);
}
th {
  font-weight: 600;
  color: var(--muted);
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
td.quote { max-width: 28rem; }
a { color: var(--accent); }
.tone {
  white-space: nowrap;
  font-weight: 600;
  font-size: 0.82rem;
}
.tone.positive { color: var(--positive); }
.tone.negative { color: var(--negative); }
.tone.neutral { color: var(--neutral); }
.just { color: var(--muted); font-size: 0.8rem; display: block; margin-top: 0.2rem; }
.strip {
  display: flex;
  gap: 0.65rem;
  align-items: flex-end;
  overflow-x: auto;
  padding: 0.4rem 0 0.2rem;
}
.month {
  min-width: 3.4rem;
  text-align: center;
}
.bars {
  height: 88px;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  gap: 3px;
}
.bar {
  width: 9px;
  border-radius: 2px 2px 0 0;
}
.bar.positive { background: var(--positive); }
.bar.negative { background: var(--negative); }
.bar.neutral { background: var(--neutral); opacity: 0.75; }
.month label {
  display: block;
  margin-top: 0.35rem;
  font-size: 0.68rem;
  color: var(--muted);
}
.legend {
  font-size: 0.8rem;
  color: var(--muted);
  margin-top: 0.7rem;
}
.legend span { margin-right: 0.9rem; }
.swatch {
  display: inline-block;
  width: 9px;
  height: 9px;
  margin-right: 0.25rem;
  vertical-align: middle;
}
.note, footer {
  color: var(--muted);
  font-size: 0.82rem;
}
footer { margin-top: 1.5rem; }
.log {
  font-family: ui-monospace, "Cascadia Code", "Segoe UI Mono", monospace;
  font-size: 0.75rem;
  color: var(--muted);
  white-space: pre-wrap;
}
.toolbar {
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: 6px;
  padding: 0.95rem 1.15rem;
  margin-bottom: 1.25rem;
  color: var(--muted);
  font-size: 0.92rem;
}
.toolbar p { margin: 0 0 0.55rem; }
.toolbar p:last-child { margin-bottom: 0; }
.toolbar form { display: inline; }
.toolbar button,
.toolbar a.quiet {
  font: inherit;
  font-size: 0.88rem;
  background: var(--paper);
  color: var(--ink);
  border: 1px solid var(--line);
  border-radius: 4px;
  padding: 0.3rem 0.75rem;
  cursor: pointer;
  text-decoration: none;
  display: inline-block;
  margin-right: 0.4rem;
}
.toolbar button:hover,
.toolbar a.quiet:hover {
  border-color: #cfc8bc;
}
.log {
  font-family: ui-monospace, "Cascadia Code", "Segoe UI Mono", monospace;
  font-size: 0.75rem;
  color: var(--muted);
  white-space: pre-wrap;
}
"""


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


def build_html(
    rows: list[dict[str, Any]],
    strip: list[dict[str, Any]],
    summary: str,
    search_log: list[dict[str, Any]],
    mode: str,
    backend: str,
    fallback_reason: str | None,
    generated: str,
    *,
    toolbar_html: str = "",
) -> str:
    max_count = 1
    for bucket in strip:
        max_count = max(max_count, bucket.get("positive", 0), bucket.get("negative", 0), bucket.get("neutral", 0))

    month_html = []
    for bucket in strip:
        month_html.append("<div class='month'>")
        month_html.append("<div class='bars'>")
        for tone in ("positive", "negative", "neutral"):
            count = int(bucket.get(tone, 0))
            if count == 0:
                height = 2
            else:
                height = max(12, int(80 * (count / max_count)))
            month_html.append(f"<div class='bar {tone}' style='height:{height}px' title='{tone}: {count}'></div>")
        month_html.append("</div>")
        month_html.append(f"<label>{html.escape(str(bucket['month']))}</label>")
        month_html.append("</div>")

    table_rows = []
    for row in rows:
        url = row.get("url") or "not found"
        if url != "not found":
            link = f"<a href='{html.escape(url)}'>open</a>"
        else:
            link = "not found"
        tone = html.escape(str(row.get("tone") or "neutral"))
        table_rows.append(
            "<tr>"
            f"<td>{html.escape(str(row.get('outlet') or 'not found'))}</td>"
            f"<td>{html.escape(str(row.get('date') or 'not found'))}</td>"
            f"<td>{link}</td>"
            f"<td class='quote'>{html.escape(str(row.get('quote') or 'not found'))}"
            f"<span class='just'>{html.escape(str(row.get('title') or ''))}</span></td>"
            f"<td><span class='tone {tone}'>{tone}</span>"
            f"<span class='just'>{html.escape(str(row.get('tone_justification') or 'not found'))}</span></td>"
            f"<td>{html.escape(str(row.get('topic') or 'not found'))}"
            f"<span class='just'>{html.escape(str(row.get('topic_justification') or 'not found'))}</span></td>"
            "</tr>"
        )

    summary_paras = "".join(f"<p>{html.escape(p.strip())}</p>" for p in _split_summary(summary))
    fallback = (
        f"<p class='note'><strong>Fallback.</strong> {html.escape(fallback_reason)}</p>"
        if fallback_reason
        else ""
    )
    quality_note = ""
    if len(rows) < QUALITY_MIN_ARTICLES:
        quality_note = (
            f"<p class='note'>Quality target is at least {QUALITY_MIN_ARTICLES} articles; "
            f"this run has {len(rows)}. Missing coverage is left empty rather than invented.</p>"
        )

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Montenegro RES Law and first solar auction — media reception</title>
  <style>{CSS}</style>
</head>
<body>
  <div class="wrap">
    {toolbar_html}
    <header>
      <p class="kicker">IPDET Impact London · EBRD teaching demo · {html.escape(generated)} · {html.escape(mode)} / {html.escape(backend)}</p>
      <h1>Montenegro RES Law and the first solar auction</h1>
      <p class="kicker">How published news and official statements received the reform</p>
    </header>
    <section class="card mandate">
      <h2>Mandate</h2>
      <p>{html.escape(GOAL)}</p>
      <p>{html.escape(SCOPE)} Quote the source for every claim. Write <em>not found</em> rather than infer. Log every search.</p>
      {fallback}
    </section>
    <section class="card summary">
      <h2>Two-line summary</h2>
      {summary_paras}
    </section>
    <section class="card">
      <h2>Tone by month</h2>
      <div class="strip">
        {''.join(month_html)}
      </div>
      <p class="legend">
        <span><i class="swatch" style="background:var(--positive)"></i>positive</span>
        <span><i class="swatch" style="background:var(--negative)"></i>negative</span>
        <span><i class="swatch" style="background:var(--neutral)"></i>neutral</span>
      </p>
      {quality_note}
    </section>
    <section class="card">
      <h2>Agent table</h2>
      <table>
        <thead>
          <tr>
            <th>Outlet</th>
            <th>Date</th>
            <th>Link</th>
            <th>Quote</th>
            <th>Tone</th>
            <th>Topic</th>
          </tr>
        </thead>
        <tbody>
          {''.join(table_rows)}
        </tbody>
      </table>
    </section>
    <section class="card">
      <h2>Search log</h2>
      <div class="log">{html.escape(json.dumps(search_log, indent=2, ensure_ascii=False))}</div>
    </section>
    <footer>
      Teaching material for IPDET Impact London (28–29 September 2026). Filo Analytics / Andrés González Flores.
      Visuals are a classroom handout, not a product UI.
    </footer>
  </div>
</body>
</html>
"""
    return page


def html_from_result(
    result: dict[str, Any],
    *,
    toolbar_html: str = "",
) -> str:
    rows = result["rows"]
    summary = two_line_summary(rows, mode=result["mode"])
    strip = tone_by_month(rows)
    generated = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    return build_html(
        rows,
        strip,
        summary,
        result["log"],
        result["mode"],
        result["backend"],
        result.get("fallback"),
        generated,
        toolbar_html=toolbar_html,
    )


def _split_summary(summary: str) -> list[str]:
    # Prefer two sentences for the mandated two-line summary.
    parts = [p.strip() for p in summary.replace("  ", " ").split(". ") if p.strip()]
    if len(parts) <= 2:
        return [p if p.endswith(".") else p + "." for p in parts] or [summary]
    first = ". ".join(parts[: max(1, len(parts) // 2)]).rstrip(".") + "."
    second = ". ".join(parts[max(1, len(parts) // 2) :]).rstrip(".") + "."
    return [first, second]
