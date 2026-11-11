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

Live results are normalized as `live_official` (Ticketmaster), `live_resale` (SeatGeek), or `estimated`. Searches with live prices are saved to the configured database. `GET /api/history/{event_key}` returns stored observations for price-history charts.

## Hourly price snapshots

Set `TRACKED_SEARCHES` to a comma-separated list, then run:

```bash
.venv/bin/python scripts/refresh_prices.py
```

The included `render.yaml` defines a free Python API service. Use a free Neon PostgreSQL database for durable history; unlike Render's free database, Neon does not expire after 30 days. The GitHub Actions workflow in `.github/workflows/refresh-prices.yml` runs the collector hourly at no cost for this public repository.

Add these encrypted secrets in **GitHub → Repository settings → Secrets and variables → Actions**:

- `DATABASE_URL`
- `TICKETMASTER_API_KEY`
- `SEATGEEK_CLIENT_ID`

Add the same three values in Render's Blueprint setup. Never put their values in source files or commits.

After the API is deployed, build the static frontend with its public URL:

```bash
PUBLIC_API_BASE_URL=https://your-api.example.com .venv/bin/python scripts/build_static.py
```

## Static hosted build

```bash
.venv/bin/python scripts/build_static.py
```

This writes the same interface to `dist/` for Sites hosting. Live Python API endpoints require a Python-capable host.
