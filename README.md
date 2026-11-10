# SeatScout

Python/FastAPI ticket comparison prototype with a reusable vintage box-office design system. The frontend is server-rendered with Jinja and progressively enhanced in the browser. Saved deals are stored locally, so no login is required.

## Run locally

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000`.

## Data providers

Copy `.env.example` to `.env` and add supported keys. Without keys, the app transparently uses the built-in demonstration feed. Ticketmaster and SeatGeek adapters are implemented; StubHub and Ticket Evolution are represented as planned partner feeds.

## Static hosted build

```bash
.venv/bin/python scripts/build_static.py
```

This writes the same interface to `dist/` for Sites hosting. Live Python API endpoints require a Python-capable host.
