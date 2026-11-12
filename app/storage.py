from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import DateTime, Float, Integer, MetaData, String, Table, Column, create_engine, select


# Load .env before reading DATABASE_URL. Real environment variables still take precedence.
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./seatscout.db")
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)
metadata = MetaData()
price_snapshots = Table(
    "price_snapshots",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("event_key", String(180), nullable=False, index=True),
    Column("event_name", String(240), nullable=False),
    Column("provider", String(80), nullable=False),
    Column("price_type", String(40), nullable=False),
    Column("price", Float, nullable=False),
    Column("recorded_at", DateTime(timezone=True), nullable=False, index=True),
)


def init_db() -> None:
    metadata.create_all(engine)


def save_event_snapshots(events: list[dict]) -> int:
    now = datetime.now(timezone.utc)
    rows = []
    for event in events:
        price = event.get("low")
        if price is None:
            continue
        rows.append({
            "event_key": str(event.get("slug") or event.get("artist", "unknown")).lower(),
            "event_name": event.get("artist", "Unknown event"),
            "provider": event.get("source", "SeatScout"),
            "price_type": event.get("price_type", "estimated"),
            "price": float(price),
            "recorded_at": now,
        })
    if rows:
        with engine.begin() as connection:
            connection.execute(price_snapshots.insert(), rows)
    return len(rows)


def get_price_history(event_key: str, limit: int = 720) -> list[dict]:
    query = (
        select(price_snapshots)
        .where(price_snapshots.c.event_key == event_key.lower())
        .order_by(price_snapshots.c.recorded_at.desc())
        .limit(limit)
    )
    with engine.connect() as connection:
        rows = connection.execute(query).mappings().all()
    return [
        {
            "provider": row["provider"],
            "price_type": row["price_type"],
            "price": row["price"],
            "recorded_at": row["recorded_at"].isoformat(),
        }
        for row in reversed(rows)
    ]
