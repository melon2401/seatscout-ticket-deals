from __future__ import annotations

import os
from dataclasses import dataclass
from difflib import SequenceMatcher

import httpx

from .data import EVENTS, OFFERS


@dataclass
class ProviderStatus:
    name: str
    mode: str
    ready: bool
    detail: str


class DemoProvider:
    name = "SeatScout demo feed"

    async def search(self, query: str) -> list[dict]:
        needle = query.casefold().strip()
        if not needle:
            return EVENTS
        indexed = [
            (event, " ".join([event["artist"], event["city"], event["venue"], event["category"]]).casefold())
            for event in EVENTS
        ]
        direct = [event for event, haystack in indexed if needle in haystack]
        if direct:
            return direct
        scored = [
            (max(SequenceMatcher(None, needle, term.casefold()).ratio() for term in [event["artist"], event["venue"], event["city"]]), event)
            for event, _ in indexed
        ]
        return [event for score, event in sorted(scored, key=lambda item: item[0], reverse=True) if score >= 0.62]

    async def offers(self, _event_slug: str) -> list[dict]:
        return OFFERS


class TicketmasterProvider:
    name = "Ticketmaster"
    base_url = "https://app.ticketmaster.com/discovery/v2"

    def __init__(self) -> None:
        self.api_key = os.getenv("TICKETMASTER_API_KEY")

    async def search(self, query: str, city: str | None = None) -> list[dict]:
        if not self.api_key:
            return []
        params = {"apikey": self.api_key, "keyword": query, "size": 20}
        if city:
            params["city"] = city
        async with httpx.AsyncClient(timeout=12) as client:
            response = await client.get(f"{self.base_url}/events.json", params=params)
            response.raise_for_status()
        events = response.json().get("_embedded", {}).get("events", [])
        return [{
            "slug": event["id"],
            "artist": event["name"],
            "city": event.get("_embedded", {}).get("venues", [{}])[0].get("city", {}).get("name", ""),
            "date": event.get("dates", {}).get("start", {}).get("localDate", ""),
            "venue": event.get("_embedded", {}).get("venues", [{}])[0].get("name", ""),
            "category": "Live event",
            "low": None,
            "change": None,
            "url": event.get("url"),
            "source": "Ticketmaster",
        } for event in events]


class SeatGeekProvider:
    name = "SeatGeek"

    def __init__(self) -> None:
        self.client_id = os.getenv("SEATGEEK_CLIENT_ID")

    async def search(self, query: str) -> list[dict]:
        if not self.client_id:
            return []
        async with httpx.AsyncClient(timeout=12) as client:
            response = await client.get("https://api.seatgeek.com/2/events", params={"client_id": self.client_id, "q": query, "per_page": 20})
            response.raise_for_status()
        return [{
            "slug": f"sg-{event['id']}",
            "artist": event["title"],
            "city": event.get("venue", {}).get("city", ""),
            "date": event.get("datetime_local", "")[:10],
            "venue": event.get("venue", {}).get("name", ""),
            "category": event.get("type", "Live event").replace("_", " ").title(),
            "low": event.get("stats", {}).get("lowest_price"),
            "change": None,
            "url": event.get("url"),
            "source": "SeatGeek",
        } for event in response.json().get("events", [])]


def provider_statuses() -> list[ProviderStatus]:
    return [
        ProviderStatus("Ticketmaster", "live" if os.getenv("TICKETMASTER_API_KEY") else "demo", bool(os.getenv("TICKETMASTER_API_KEY")), "Event discovery and official links"),
        ProviderStatus("SeatGeek", "live" if os.getenv("SEATGEEK_CLIENT_ID") else "demo", bool(os.getenv("SEATGEEK_CLIENT_ID")), "Event data and market statistics"),
        ProviderStatus("StubHub", "planned", False, "Partner approval required"),
        ProviderStatus("Ticket Evolution", "planned", False, "Commercial inventory feed"),
    ]

