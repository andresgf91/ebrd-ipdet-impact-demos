import json
from pathlib import Path

from montenegro_res_news.mandate import QUALITY_MIN_ARTICLES
from montenegro_res_news.paths import SAMPLE_DIR, load_sample
from montenegro_res_news.social import is_social_url

TONES = {"positive", "negative", "neutral"}


def test_sample_meets_quality_and_mandate():
    rows, log = load_sample()
    assert len(rows) >= QUALITY_MIN_ARTICLES
    assert log, "search log must record the pre-run queries"

    for row in rows:
        assert row["outlet"]
        assert row["url"] and row["url"] != "not found"
        assert not is_social_url(row["url"])
        assert row["quote"] and row["quote"] != ""
        assert row["tone"] in TONES
        assert row["tone_justification"]
        assert row["topic"]
        assert row["topic_justification"]
        for field in ("quote", "tone_justification"):
            assert "TODO" not in row[field]

    dates = {row["date"] for row in rows}
    assert "not found" in dates, "at least one missing date should stay 'not found' rather than guessed"


def test_sample_files_exist():
    for name in ("articles.json", "search_log.json"):
        assert (SAMPLE_DIR / name).is_file()
    data = json.loads(Path(SAMPLE_DIR / "articles.json").read_text(encoding="utf-8"))
    assert isinstance(data, list)
