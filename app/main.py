from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .data import EVENTS, OFFERS, PRICE_HISTORY, ZONES
from .providers import DemoProvider, SeatGeekProvider, TicketmasterProvider, provider_statuses

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

app = FastAPI(title="SeatScout", version="0.2.0")
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")
templates = Jinja2Templates(directory=ROOT / "templates")


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(request, "index.html", {
        "events": EVENTS,
        "offers": OFFERS,
        "history": PRICE_HISTORY,
        "zones": ZONES,
    })


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "seatscout", "version": app.version}


@app.get("/api/events")
async def events(category: str | None = None):
    rows = EVENTS if not category or category == "All" else [event for event in EVENTS if event["category"] == category]
    return {"events": rows, "count": len(rows)}


@app.get("/api/search")
async def search(q: str = Query("", max_length=120), city: str | None = None):
    demo = DemoProvider()
    results = await demo.search(q)
    live_results: list[dict] = []
    for provider in (TicketmasterProvider(), SeatGeekProvider()):
        try:
            if isinstance(provider, TicketmasterProvider):
                live_results.extend(await provider.search(q, city))
            else:
                live_results.extend(await provider.search(q))
        except Exception:
            continue
    return {"events": live_results or results, "mode": "live" if live_results else "demo"}


@app.get("/api/events/{event_slug}")
async def event_detail(event_slug: str):
    event = next((item for item in EVENTS if item["slug"] == event_slug), EVENTS[0])
    return {"event": event, "offers": OFFERS, "history": PRICE_HISTORY, "zones": ZONES}


@app.get("/api/providers")
async def providers():
    return {"providers": [status.__dict__ for status in provider_statuses()]}

