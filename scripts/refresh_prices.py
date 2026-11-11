from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.providers import SeatGeekProvider, TicketmasterProvider
from app.storage import init_db, save_event_snapshots


async def refresh() -> int:
    load_dotenv()
    searches = [item.strip() for item in os.getenv("TRACKED_SEARCHES", "").split(",") if item.strip()]
    city = os.getenv("TRACKED_CITY", "Toronto")
    providers = (TicketmasterProvider(), SeatGeekProvider())
    captured = 0
    for query in searches:
        for provider in providers:
            try:
                events = await provider.search(query, city) if isinstance(provider, TicketmasterProvider) else await provider.search(query)
                captured += save_event_snapshots(events)
            except Exception as error:
                print(f"{provider.name}: {query}: {error}")
    return captured


if __name__ == "__main__":
    init_db()
    count = asyncio.run(refresh())
    print(f"Stored {count} live price snapshots")
