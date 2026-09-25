"""Mandate constants from the IPDET Impact London brief (slide ~30)."""

from __future__ import annotations

from datetime import date, timedelta

GOAL = (
    "Evidence on how Montenegro’s Renewable Energy Sources (RES) Law "
    "and auctions are being received."
)

SCOPE = "Published news and official statements only. No social media."

CONSTRAINTS = (
    "Quote the source for every claim. Say 'not found' rather than infer. "
    "Keep a log of every search."
)

QUALITY_MIN_ARTICLES = 20

TONES = ("positive", "negative", "neutral")

CANONICAL_TOPICS = (
    "investor interest",
    "grid",
    "coal phase-out",
    "permitting",
)

# Related topics are allowed when clearly justified from the quoted text.
RELATED_TOPICS = (
    "legal framework",
    "auction design",
    "just transition",
)

SOCIAL_HOST_MARKERS = (
    "twitter.com",
    "x.com",
    "t.co",
    "facebook.com",
    "fb.com",
    "instagram.com",
    "tiktok.com",
    "reddit.com",
    "t.me",
    "telegram.org",
    "youtube.com",
    "youtu.be",
    "linkedin.com",
    "threads.net",
    "truthsocial.com",
    "mastodon",
    "bsky.app",
    "vk.com",
    "weibo.com",
)

# Live classroom search: last 12 months (the slide). Sample coverage starts
# at law passage (Aug 2024) so the two-line summary can show what shifted.
SEARCH_QUERIES = (
    'Montenegro "Renewable Energy Sources" Law OR "RES Law" auction',
    'Montenegro "Law on the Use of Energy from Renewable Sources"',
    'Montenegro "solar auction" OR "solar power auction" 250 MW',
    'Montenegro "market premium" solar auction',
    "Montenegro first renewable energy auction EBRD",
    'Crna Gora "zakon o korišćenju energije iz obnovljivih izvora"',
    'Crna Gora aukcija solarna "tržišna premija"',
    "Montenegro solar auction cancelled OR annulled bids",
    "Montenegro three-year incentive plan solar wind auction",
    "Montenegro Ministry of Energy renewable energy auction Šahmanović",
)


def live_window_end(today: date | None = None) -> date:
    return today or date.today()


def live_window_start(today: date | None = None) -> date:
    return live_window_end(today) - timedelta(days=365)


# Sample freeze: compiled 14 Sep 2026 from published pages (not social).
SAMPLE_FREEZE_DATE = date(2026, 9, 14)
SAMPLE_WINDOW_START = date(2024, 8, 1)
