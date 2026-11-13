from __future__ import annotations

from pathlib import Path
import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

from .data import EVENTS, OFFERS, PRICE_HISTORY, ZONES
from .providers import DemoProvider, SeatGeekProvider, TicketmasterProvider, provider_statuses
from .storage import get_price_history, init_db, save_event_snapshots

logger = logging.getLogger("seatscout.providers")

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

app = FastAPI(title="SeatScout", version="0.2.0")
allowed_origins = [origin.strip() for origin in os.getenv("ALLOWED_ORIGINS", "http://127.0.0.1:8000").split(",") if origin.strip()]
app.add_middleware(CORSMiddleware, allow_origins=allowed_origins, allow_methods=["GET"], allow_headers=["*"])
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")
templates = Jinja2Templates(directory=ROOT / "templates")
init_db()


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(request, "index.html", {
        "events": EVENTS,
        "offers": OFFERS,
        "history": PRICE_HISTORY,
        "zones": ZONES,
        "api_base": os.getenv("PUBLIC_API_BASE_URL", ""),
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
    sources: list[dict] = []
    for provider in (TicketmasterProvider(), SeatGeekProvider()):
        configured = bool(getattr(provider, "api_key", None) or getattr(provider, "client_id", None))
        if not configured:
            sources.append({"name": provider.name, "status": "not_configured", "count": 0})
            continue
        try:
            if isinstance(provider, TicketmasterProvider):
                provider_results = await provider.search(q, city)
            else:
                provider_results = await provider.search(q)
            live_results.extend(provider_results)
            sources.append({"name": provider.name, "status": "live" if provider_results else "no_match", "count": len(provider_results)})
        except Exception as exc:
            # httpx exceptions can include the request URL, whose query string contains
            # provider credentials. Record only the provider and exception class.
            logger.warning("%s search failed (%s)", provider.name, type(exc).__name__)
            sources.append({"name": provider.name, "status": "error", "count": 0})
    if live_results:
        save_event_snapshots(live_results)
        return {"events": live_results, "mode": "live", "sources": sources}
    estimated_results = [{**event, "source": "SeatScout estimate", "price_type": "estimated"} for event in results]
    if any(source["status"] == "error" for source in sources):
        fallback_reason = "provider_error"
    elif any(source["status"] == "no_match" for source in sources):
        fallback_reason = "no_live_match"
    else:
        fallback_reason = "providers_not_configured"
    return {"events": estimated_results, "mode": "estimated", "fallback_reason": fallback_reason, "sources": sources}


@app.get("/api/history/{event_key}")
async def price_history(event_key: str):
    snapshots = get_price_history(event_key)
    return {"event_key": event_key, "snapshots": snapshots, "count": len(snapshots)}


@app.get("/api/events/{event_slug}")
async def event_detail(event_slug: str):
    event = next((item for item in EVENTS if item["slug"] == event_slug), EVENTS[0])
    return {"event": event, "offers": OFFERS, "history": PRICE_HISTORY, "zones": ZONES}


@app.get("/api/providers")
async def providers():
    return {"providers": [status.__dict__ for status in provider_statuses()]}

