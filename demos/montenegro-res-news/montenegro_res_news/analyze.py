"""Extract a quoted claim, tone, and topic from a search hit.

Live mode uses only the title + snippet the search backend returned.
Missing facts are `not found` — never inferred from world knowledge.

An optional OpenAI call can refine labels when OPENAI_API_KEY is set.
The default is a transparent keyword heuristic so the classroom can audit it.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any

from montenegro_res_news.mandate import CANONICAL_TOPICS, TONES
from montenegro_res_news.models import not_found

REFORM_MARKERS = (
    "res law",
    "renewable energy sources law",
    "renewable energy law",
    "renewables act",
    "law on the use of energy from renewable",
    "zakon o korišćenju energije iz obnovljivih",
    "zakon o koriscenju energije iz obnovljivih",
    "solar auction",
    "renewable energy auction",
    "market premium",
    "tržišna premija",
    "trzisna premija",
    "aukcija",
    "contract for difference",
    "contracts for difference",
    "cfd",
    "250 mw",
)

POSITIVE_MARKERS = (
    "milestone",
    "landmark",
    "pivotal",
    "major step",
    "strategic leap",
    "new wave of investment",
    "open the door",
    "growing",
    "attract",
    "transparent",
    "solid foundation",
    "accelerate",
    "opportunity",
    "success",
    "confidence",
    "better conditions",
    "investor interest exists",
    "delighted",
)

NEGATIVE_MARKERS = (
    "cancel",
    "cancelled",
    "canceled",
    "annul",
    "scrap",
    "reject",
    "disqualif",
    "fail",
    "failed",
    "shortcoming",
    "mismatch",
    "did not meet",
    "none of the bids",
    "no bids",
    "delay",
    "bottleneck",
    "not set a",
    "have not set",
    "awaits changed",
    "no such auctions have taken place",
)

TOPIC_MARKERS: dict[str, tuple[str, ...]] = {
    "investor interest": (
        "investor",
        "investment",
        "private sector",
        "bankable",
        "financing",
        "interest exists",
        "attract",
        "hundreds of millions",
    ),
    "grid": (
        "grid",
        "connection",
        "transmission",
        "cges",
        "network-connection",
        "curtailment",
        "dispatch",
    ),
    "coal phase-out": (
        "coal",
        "pljevlja",
        "just transition",
        "decarbon",
        "lignite",
    ),
    "permitting": (
        "permit",
        "spatial",
        "urban planning",
        "documentation",
        "qualification",
        "by-law",
        "bylaw",
        "secondary legislation",
        "legal framework",
        "tender documentation",
        "eligibility",
    ),
}


def analyze_hit(hit: dict[str, Any]) -> dict[str, Any]:
    title = str(hit.get("title") or "").strip()
    snippet = str(hit.get("snippet") or "").strip()
    blob = f"{title}. {snippet}".strip()

    quote = _extract_quote(blob)
    claim = quote if quote != not_found() else not_found()

    if os.environ.get("OPENAI_API_KEY") and blob:
        llm = _llm_labels(title, snippet, quote)
        if llm:
            tone, tone_why, topic, topic_why = llm
            return _row(hit, quote, claim, tone, tone_why, topic, topic_why)

    tone, tone_why = _tone(blob, quote)
    topic, topic_why = _topic(blob)
    return _row(hit, quote, claim, tone, tone_why, topic, topic_why)


def _row(
    hit: dict[str, Any],
    quote: str,
    claim: str,
    tone: str,
    tone_why: str,
    topic: str,
    topic_why: str,
) -> dict[str, Any]:
    date_value = _normalise_date(hit.get("date"))
    outlet = str(hit.get("outlet") or "").strip() or not_found()
    url = str(hit.get("url") or "").strip() or not_found()
    title = str(hit.get("title") or "").strip() or not_found()
    return {
        "outlet": outlet,
        "date": date_value,
        "url": url,
        "title": title,
        "quote": quote,
        "claim": claim,
        "tone": tone,
        "tone_justification": tone_why,
        "topic": topic,
        "topic_justification": topic_why,
        "source_type": "news_or_official",
    }


def _extract_quote(blob: str) -> str:
    if not blob or blob in {".", ""}:
        return not_found()
    lower = blob.lower()
    if not any(marker in lower for marker in REFORM_MARKERS):
        return not_found()
    sentences = _sentences(blob)
    scored: list[tuple[int, int, str]] = []
    for sentence in sentences:
        hits = [marker for marker in REFORM_MARKERS if marker in sentence.lower()]
        if hits:
            scored.append((len(hits), len(sentence), sentence))
    if not scored:
        return _clip(sentences[0] if sentences else blob)
    scored.sort(reverse=True)
    return _clip(scored[0][2])


def _sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text.replace("\n", " ").strip())
    return [p.strip() for p in parts if p.strip()]


def _clip(text: str, limit: int = 280) -> str:
    text = re.sub(r"\s+", " ", text).strip().strip('"')
    if len(text) <= limit:
        return text
    return text[: limit - 1].rsplit(" ", 1)[0] + "…"


def _tone(blob: str, quote: str) -> tuple[str, str]:
    if quote == not_found():
        return "neutral", "not found: no quoted reform claim to label."
    text = blob.lower()
    pos = [m for m in POSITIVE_MARKERS if m in text]
    neg = [m for m in NEGATIVE_MARKERS if m in text]
    if pos and not neg:
        return "positive", f"Quoted text uses constructive language ({', '.join(pos[:3])})."
    if neg and not pos:
        return "negative", f"Quoted text reports a setback ({', '.join(neg[:3])})."
    if pos and neg:
        return (
            "neutral",
            f"Mixed cues in the snippet (positive: {pos[0]}; negative: {neg[0]}); labelled neutral rather than inferred.",
        )
    return "neutral", "Factual wording without a clear evaluative cue in the quoted text."


def _topic(blob: str) -> tuple[str, str]:
    text = blob.lower()
    scores: list[tuple[int, str, str]] = []
    for topic, markers in TOPIC_MARKERS.items():
        hits = [m for m in markers if m in text]
        if hits:
            scores.append((len(hits), topic, hits[0]))
    if not scores:
        return (
            "legal framework",
            "Snippet discusses the RES reform without a clearer canonical topic; related topic used.",
        )
    scores.sort(reverse=True)
    _, topic, marker = scores[0]
    kind = "canonical" if topic in CANONICAL_TOPICS else "related"
    return topic, f"{kind} topic from quoted cue '{marker}'."


def _normalise_date(value: Any) -> str:
    if value is None:
        return not_found()
    text = str(value).strip()
    if not text or text.lower() == "not found":
        return not_found()
    match = re.search(r"(20\d{2}-\d{2}-\d{2})", text)
    if match:
        return match.group(1)
    match = re.search(r"(20\d{2}/\d{2}/\d{2})", text)
    if match:
        return match.group(1).replace("/", "-")
    return not_found()


def _llm_labels(title: str, snippet: str, quote: str) -> tuple[str, str, str, str] | None:
    """Optional. Must still ground labels in the provided snippet — not training knowledge."""
    try:
        import requests
    except ImportError:
        return None
    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    prompt = {
        "model": model,
        "temperature": 0,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You label news snippets about Montenegro's RES Law and solar auctions. "
                    "Use only the given title, snippet, and quote. "
                    "If evidence is missing, use not found. Never invent facts. "
                    "Return JSON with keys tone, tone_justification, topic, topic_justification. "
                    f"tone must be one of {list(TONES)}. "
                    "topic should be one of investor interest, grid, coal phase-out, permitting "
                    "or a short related topic if clearly justified."
                ),
            },
            {
                "role": "user",
                "content": json.dumps(
                    {"title": title, "snippet": snippet, "quote": quote},
                    ensure_ascii=False,
                ),
            },
        ],
    }
    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}",
                "Content-Type": "application/json",
            },
            json=prompt,
            timeout=30,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        data = json.loads(content)
        tone = str(data.get("tone") or "neutral").lower()
        if tone not in TONES:
            tone = "neutral"
        topic = str(data.get("topic") or "legal framework").strip() or "legal framework"
        tone_why = str(data.get("tone_justification") or not_found()).strip() or not_found()
        topic_why = str(data.get("topic_justification") or not_found()).strip() or not_found()
        return tone, tone_why, topic, topic_why
    except Exception:  # noqa: BLE001
        return None
