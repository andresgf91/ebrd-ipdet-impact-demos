from montenegro_res_news.analyze import analyze_hit
from montenegro_res_news.report import two_line_summary


def test_unrelated_snippet_is_not_found_not_inferred():
    row = analyze_hit(
        {
            "title": "Sports roundup",
            "snippet": "A football club signed a new striker.",
            "url": "https://example.com/sports",
            "outlet": "Example",
            "date": "yesterday afternoon",
        }
    )
    assert row["quote"] == "not found"
    assert row["date"] == "not found"
    assert row["tone_justification"].startswith("not found")


def test_reform_snippet_keeps_a_quote():
    row = analyze_hit(
        {
            "title": "Montenegro launches solar auction",
            "snippet": "The first solar auction will award a market premium for 250 MW.",
            "url": "https://example.com/res",
            "outlet": "Example News",
            "date": "2025-07-11",
        }
    )
    assert row["quote"] != "not found"
    assert "250 MW" in row["quote"] or "market premium" in row["quote"].lower()
    assert row["date"] == "2025-07-11"


def test_empty_live_summary_says_not_found():
    text = two_line_summary([], mode="live")
    assert text.lower().startswith("not found")
