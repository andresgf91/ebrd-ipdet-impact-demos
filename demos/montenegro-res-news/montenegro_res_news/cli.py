"""CLI: search → analyse → report, with a checked-in sample fallback."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from montenegro_res_news.analyze import analyze_hit
from montenegro_res_news.mandate import QUALITY_MIN_ARTICLES, live_window_start
from montenegro_res_news.paths import DEMO_ROOT, load_sample
from montenegro_res_news.report import write_outputs
from montenegro_res_news.search import search_live


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Search published coverage of Montenegro’s RES Law and first solar auction, "
            "label tone/topic from quotes, and write a classroom report."
        )
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--sample",
        action="store_true",
        help="Skip live search and write the checked-in pre-run (classroom fallback).",
    )
    mode.add_argument(
        "--live",
        action="store_true",
        help="Live search only. Do not fall back to the sample; may return fewer than 20 rows.",
    )
    parser.add_argument(
        "--outdir",
        type=Path,
        default=DEMO_ROOT / "output",
        help="Directory for table.csv, report.html, report.md, search_log.json (default: ./output).",
    )
    parser.add_argument(
        "--write-sample",
        action="store_true",
        help="Also refresh demos/.../sample/ with this run (used when regenerating the fallback).",
    )
    args = parser.parse_args(argv)

    if args.sample:
        rows, log = load_sample()
        backend = "sample"
        fallback = (
            "Using the checked-in pre-run compiled from published news and official pages "
            "(frozen 14 September 2026). No live web search was performed."
        )
        mode_name = "sample"
    else:
        rows, log, backend, fallback, mode_name = _try_live(force_live=args.live)

    rows = sorted(
        rows,
        key=lambda r: (str(r.get("date") or "not found") == "not found", str(r.get("date") or "")),
    )

    paths = write_outputs(
        rows,
        log,
        args.outdir,
        mode=mode_name,
        backend=backend,
        fallback_reason=fallback,
    )
    if args.write_sample:
        from montenegro_res_news.paths import SAMPLE_DIR

        write_outputs(
            rows,
            log,
            SAMPLE_DIR,
            mode=mode_name,
            backend=backend,
            fallback_reason=fallback,
        )

    _print_console(rows, paths, mode_name, backend, fallback)
    return 0


def _try_live(*, force_live: bool) -> tuple[list[dict[str, Any]], list[dict[str, Any]], str, str | None, str]:
    try:
        hits, log, backend = search_live()
    except Exception as exc:  # noqa: BLE001
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
        return rows, sample_log, "sample", reason, "sample"

    rows = [analyze_hit(hit) for hit in hits]
    # Unrelated hits have quote = not found; do not keep them as fake coverage.
    rows = [r for r in rows if r.get("quote") != "not found"]
    rows = _drop_outside_window(rows)

    if force_live:
        return rows, log, backend, None, "live"

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
        return sample_rows, combined_log, "sample", reason, "sample"

    return rows, log, backend, None, "live"


def _drop_outside_window(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    start = live_window_start().isoformat()
    kept: list[dict[str, Any]] = []
    for row in rows:
        value = str(row.get("date") or "not found")
        if value == "not found" or value >= start:
            kept.append(row)
    return kept


def _print_console(
    rows: list[dict[str, Any]],
    paths: dict[str, Path],
    mode: str,
    backend: str,
    fallback: str | None,
) -> None:
    print(f"mode={mode}  backend={backend}  rows={len(rows)}")
    if fallback:
        print(fallback)
    print()
    print(f"{'outlet':<28} {'date':<12} {'tone':<9} topic")
    print("-" * 88)
    for row in rows:
        outlet = (row.get("outlet") or "not found")[:27]
        print(
            f"{outlet:<28} {str(row.get('date') or 'not found'):<12} "
            f"{str(row.get('tone') or 'not found'):<9} {row.get('topic') or 'not found'}"
        )
    print()
    print("Wrote:")
    for name, path in paths.items():
        print(f"  {name}: {path}")


if __name__ == "__main__":
    sys.exit(main())
