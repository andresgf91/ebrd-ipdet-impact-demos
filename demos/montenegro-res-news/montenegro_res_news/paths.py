"""Load the checked-in classroom fallback. Never mix invented live rows into it."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DEMO_ROOT = Path(__file__).resolve().parent.parent
SAMPLE_DIR = DEMO_ROOT / "sample"


def sample_articles_path() -> Path:
    return SAMPLE_DIR / "articles.json"


def sample_search_log_path() -> Path:
    return SAMPLE_DIR / "search_log.json"


def load_sample() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    articles = json.loads(sample_articles_path().read_text(encoding="utf-8"))
    log_path = sample_search_log_path()
    log = json.loads(log_path.read_text(encoding="utf-8")) if log_path.exists() else []
    return articles, log
