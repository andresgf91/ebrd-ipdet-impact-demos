from montenegro_res_news.mandate import QUALITY_MIN_ARTICLES
from montenegro_res_news.run import try_live


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

    monkeypatch.setattr("montenegro_res_news.run.search_live", fake_search_live)
    result = try_live(force_live=False)
    assert result["mode"] == "sample"
    assert result["backend"] == "sample"
    assert len(result["rows"]) >= QUALITY_MIN_ARTICLES
    reason = result["fallback"] or ""
    assert "invent" in reason.lower()
    assert any(e.get("backend") == "tavily" for e in result["log"])


def test_force_live_keeps_empty_results(monkeypatch):
    def fake_search_live(*_args, **_kwargs):
        return [], [{"backend": "tavily", "query": "q", "status": "ok", "result_count": 0}], "tavily"

    monkeypatch.setattr("montenegro_res_news.run.search_live", fake_search_live)
    result = try_live(force_live=True)
    assert result["mode"] == "live"
    assert result["backend"] == "tavily"
    assert result["rows"] == []
    assert result["fallback"] is None
