"""CLI: search → analyse → report, with a checked-in sample fallback."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from montenegro_res_news.paths import DEMO_ROOT
from montenegro_res_news.report import write_outputs
from montenegro_res_news.run import run_sample, try_live


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
        result = run_sample()
    else:
        result = try_live(force_live=args.live)

    paths = write_outputs(
        result["rows"],
        result["log"],
        args.outdir,
        mode=result["mode"],
        backend=result["backend"],
        fallback_reason=result["fallback"],
    )
    if args.write_sample:
        from montenegro_res_news.paths import SAMPLE_DIR

        write_outputs(
            result["rows"],
            result["log"],
            SAMPLE_DIR,
            mode=result["mode"],
            backend=result["backend"],
            fallback_reason=result["fallback"],
        )

    _print_console(result["rows"], paths, result["mode"], result["backend"], result["fallback"])
    return 0


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
