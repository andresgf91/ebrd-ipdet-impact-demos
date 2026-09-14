from fastapi.testclient import TestClient

from montenegro_res_news.web import NO_KEYS_MESSAGE, app


def test_home_serves_sample_handout(monkeypatch):
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    monkeypatch.delenv("BRAVE_API_KEY", raising=False)
    monkeypatch.delenv("NEWSAPI_KEY", raising=False)
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    html = response.text
    assert "Montenegro RES Law and the first solar auction" in html
    assert "#f7f5f1" in html
    assert "Official Gazette of Montenegro" in html
    assert "Tone by month" in html
    assert "Two-line summary" in html
    assert "neon" not in html.lower()
    assert "swagger" not in html.lower()


def test_live_without_keys_stays_on_sample(monkeypatch):
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    monkeypatch.delenv("BRAVE_API_KEY", raising=False)
    monkeypatch.delenv("NEWSAPI_KEY", raising=False)
    client = TestClient(app)
    response = client.post("/live")
    assert response.status_code == 200
    html = response.text
    assert "Official Gazette of Montenegro" in html
    assert "No TAVILY_API_KEY" in html or NO_KEYS_MESSAGE.split(".")[0] in html
    assert "invented" in html.lower() or "invent" in html.lower()


def test_listen_port_uses_env(monkeypatch):
    monkeypatch.setenv("PORT", "9876")
    from montenegro_res_news.web import listen_port

    assert listen_port() == 9876


def test_health():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["demo"] == "montenegro-res-news"


def test_live_with_key_does_not_invent(monkeypatch):
    monkeypatch.setenv("TAVILY_API_KEY", "test-key")

    def fake_try_live(*, force_live: bool):
        assert force_live is False
        return {
            "rows": [],
            "log": [{"backend": "tavily", "query": "q", "status": "ok", "result_count": 0}],
            "backend": "tavily",
            "mode": "live",
            "fallback": None,
        }

    monkeypatch.setattr("montenegro_res_news.web.try_live", fake_try_live)
    client = TestClient(app)
    response = client.post("/live")
    assert response.status_code == 200
    assert "Quality target is at least 20" in response.text
    assert "not invented" in response.text.lower() or "invented" in response.text.lower() or "not found" in response.text.lower()
