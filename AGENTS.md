# SeatScout: project brief

Read this before working on SeatScout. Keep it short and current. Full history lives in git and in the archived Codex chats, not here.

## What it is

A ticket price comparison site (Toronto edition) with a vintage box-office design. FastAPI serves one Jinja template plus plain JS and CSS. SQLAlchemy stores price snapshots. There are no accounts: saved deals live in the browser's localStorage under `seatscout-saved`.

## Where things run

- API: Render free web service, defined in `render.yaml`. Health check is `/api/health`. The API keys are set in Render.
- Database: Neon Postgres in production, chosen because Render's free Postgres expires after 30 days. Locally it is SQLite (`seatscout.db`).
- Hourly price collector: GitHub Actions, `.github/workflows/refresh-prices.yml`, at 17 minutes past each hour. It needs the repo secrets `DATABASE_URL`, `TICKETMASTER_API_KEY` and `SEATGEEK_CLIENT_ID`.
- Static site: `dist/`, hosted on ChatGPT Sites (`.openai/hosting.json`) at seatscout-ticket-deals.jest-asking.chatgpt.site.
- Repo: github.com/melon2401/seatscout-ticket-deals, branch `main`.

## Commands

```bash
.venv/bin/uvicorn app.main:app --reload          # run at http://127.0.0.1:8000
.venv/bin/python -m unittest -v tests.test_app   # tests; name the module, plain discovery finds nothing
PUBLIC_API_BASE_URL=https://<render-url> .venv/bin/python scripts/build_static.py   # rebuild dist/
.venv/bin/python scripts/refresh_prices.py       # one snapshot run; needs TRACKED_SEARCHES
```

## Decisions and constraints

- Never commit secrets. `.env` is gitignored. Production values live in Render and GitHub secrets.
- `dist/` is committed. Rebuild it after any change to `templates/` or `static/` and commit both together.
- Every price has a `price_type`: `live_official` (Ticketmaster), `live_resale` (SeatGeek) or `estimated`. Never present an estimate as a live price.
- Without API keys the app falls back to the demo data in `app/data.py`.
- Stay on free tiers. Ticketmaster's free quota is 5,000 requests a day.
- `app/storage.py` loads `.env` itself, and real environment variables take precedence. `postgresql://` URLs are rewritten to the psycopg driver.
- Tests use a throwaway SQLite file and blank API keys, set at the top of `tests/test_app.py`.
- Python is 3.14 locally (`.venv`) and 3.13 on Render and in Actions.
- Keep commits small, in conventional style (`feat:`, `fix:`, `test:`, `ci:`).
- Ask the owner before deleting files or making large changes.

## Open work (as of 2026-11-11)

1. Run the tests on the Mac, then commit the uncommitted `.env` loading fix and test isolation.
2. Confirm the GitHub Actions secrets exist and the hourly job is passing.
3. Get the Render URL and rebuild `dist/` with it. The hosted site does not call the API yet.
4. Listings, zones, seller strip and chart are hardcoded demo data. The chart should read `/api/history` for live events.
5. `/api/events/{slug}` returns The Weeknd for unknown slugs instead of a 404.
6. Provider calls are not cached, SeatGeek search ignores the city, and "Watch price" does nothing.
7. StubHub and Ticket Evolution are placeholders only.

## Not known yet

Anything decided only in the Codex chats. Add it here once the archive has been reviewed.
