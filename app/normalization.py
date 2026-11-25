from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from difflib import SequenceMatcher


def normalized_text(value: str | None) -> str:
    text = unicodedata.normalize("NFKD", value or "").encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", " ", text.casefold()).strip()


def canonical_event_key(event: dict) -> str:
    fields = [normalized_text(event.get(field)) for field in ("artist", "city", "venue", "date", "local_time")]
    if not all(fields):
        fields.extend([event.get("source"), event.get("slug")])
    return "event-" + hashlib.sha256(json.dumps(fields).encode()).hexdigest()[:32]


def _same_performance(left: dict, right: dict) -> bool:
    if left.get("source") == right.get("source"):
        return False
    for field in ("city", "venue", "date", "local_time"):
        if not normalized_text(left.get(field)) or normalized_text(left.get(field)) != normalized_text(right.get(field)):
            return False
    left_title = normalized_text(left.get("artist"))
    right_title = normalized_text(right.get("artist"))
    return bool(left_title and right_title and SequenceMatcher(None, left_title, right_title).ratio() >= 0.82)


def group_comparisons(events: list[dict]) -> list[dict]:
    groups: list[list[dict]] = []
    for event in events:
        matches = [other for other in events if _same_performance(event, other)]
        if len(matches) == 1 and sum(_same_performance(matches[0], other) for other in events) == 1:
            if any(matches[0] in group for group in groups):
                continue
            groups.append([event, matches[0]])
        else:
            groups.append([event])

    comparisons = []
    for group in groups:
        first = min(group, key=lambda event: (event.get("source") != "Ticketmaster", event.get("slug", "")))
        currencies = {event.get("currency") for event in group if event.get("currency")}
        priced = [event for event in group if event.get("low") is not None]
        same_currency = len(currencies) == 1 and all(event.get("currency") in currencies for event in priced)
        sources = [{
            "provider": event.get("source"),
            "provider_event_id": event.get("provider_event_id") or event.get("slug"),
            "url": event.get("url"),
            "price_type": event.get("price_type"),
            "published_minimum": event.get("low"),
            "currency": event.get("currency"),
            "fees_included": event.get("fees_included", "unknown"),
        } for event in sorted(group, key=lambda item: (item.get("low") is None, item.get("low") or 0))]
        comparisons.append({
            "event_key": canonical_event_key(first) if len(group) > 1 else first.get("slug"),
            "title": first.get("artist"),
            "city": first.get("city"),
            "venue": first.get("venue"),
            "date": first.get("date"),
            "category": first.get("category"),
            "sources": sources,
            "market": {
                "lowest_published": min((event["low"] for event in priced), default=None) if same_currency else None,
                "currency": next(iter(currencies), None) if same_currency else None,
                "comparison_basis": "published_minimum_fees_unknown" if priced and same_currency else "not_comparable",
                "fees_included": "unknown",
            },
        })
    return comparisons
