from montenegro_res_news.cli import _try_live
from montenegro_res_news.mandate import QUALITY_MIN_ARTICLES


def test_thin_live_falls_back_without_inventing(monkeypatch):
    def fake_search_live(*_args, **_kwargs):
        log = [
            {
                "timestamp": "2026-09-14T00:00:00+00:00",
                "backend": "tavily",
                "query": "Montenegro solar auction",
                "status": "ok",
                "result_count": 0,
                "error": None,
            }
        ]
        return [], log, "tavily"

    monkeypatch.setattr("montenegro_res_news.cli.search_live", fake_search_live)
    rows, log, backend, reason, mode = _try_live(force_live=False)
    assert mode == "sample"
    assert backend == "sample"
    assert len(rows) >= QUALITY_MIN_ARTICLES
    assert reason and "invented" in reason.lower() or "invent" in (reason or "").lower()
    assert any(e.get("backend") == "tavily" for e in log)


def test_force_live_keeps_empty_results(monkeypatch):
    def fake_search_live(*_args, **_kwargs):
        return [], [{"backend": "tavily", "query": "q", "status": "ok", "result_count": 0}], "tavily"

    monkeypatch.setattr("montenegro_res_news.cli.search_live", fake_search_live)
    rows, _log, backend, reason, mode = _try_live(force_live=True)
    assert mode == "live"
    assert backend == "tavily"
    assert rows == []
    assert reason is None
