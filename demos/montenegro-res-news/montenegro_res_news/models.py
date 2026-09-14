"""Lightweight data objects — kept as dicts plus helpers so the classroom can inspect JSON easily."""

from __future__ import annotations

from typing import Any, TypedDict


class ArticleRow(TypedDict, total=False):
    outlet: str
    date: str
    url: str
    title: str
    quote: str
    claim: str
    tone: str
    tone_justification: str
    topic: str
    topic_justification: str
    source_type: str


REQUIRED_TABLE_FIELDS = (
    "outlet",
    "date",
    "url",
    "quote",
    "tone",
    "topic",
)


def not_found() -> str:
    return "not found"


def is_missing(value: Any) -> bool:
    if value is None:
        return True
    text = str(value).strip()
    return text == "" or text.lower() == "not found"
