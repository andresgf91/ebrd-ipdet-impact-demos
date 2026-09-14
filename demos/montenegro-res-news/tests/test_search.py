from montenegro_res_news.search import _dedupe, choose_backend


def test_dedupe_by_url():
    hits = [
        {"url": "https://example.com/a/"},
        {"url": "https://example.com/a"},
        {"url": "https://example.com/b"},
    ]
    out = _dedupe(hits)
    assert len(out) == 2


def test_backend_prefers_tavily(monkeypatch):
    monkeypatch.delenv("BRAVE_API_KEY", raising=False)
    monkeypatch.delenv("NEWSAPI_KEY", raising=False)
    monkeypatch.setenv("TAVILY_API_KEY", "x")
    assert choose_backend() == "tavily"
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    assert choose_backend() == "ddgs"
