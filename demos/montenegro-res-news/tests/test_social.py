from montenegro_res_news.mandate import SOCIAL_HOST_MARKERS
from montenegro_res_news.social import is_social_url, reject_social


def test_blocks_twitter_and_linkedin():
    assert is_social_url("https://x.com/someone/status/1")
    assert is_social_url("https://www.linkedin.com/posts/abc")
    assert is_social_url("https://www.facebook.com/story")
    assert is_social_url("https://t.me/channel")
    assert not is_social_url("https://en.vijesti.me/news-b/economy-d/1")
    assert not is_social_url("https://www.ebrd.com/home/news-and-events/news/2025/x.html")
    assert not is_social_url("https://www.sluzbenilist.me/propisi/373190")


def test_reject_social_separates_hits():
    hits = [
        {"url": "https://balkangreenenergynews.com/story", "title": "ok"},
        {"url": "https://twitter.com/a/status/1", "title": "no"},
    ]
    kept, dropped = reject_social(hits)
    assert len(kept) == 1
    assert len(dropped) == 1
    assert any("twitter" in m for m in SOCIAL_HOST_MARKERS)
