import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

# Isolate tests before the app is imported: use a throwaway SQLite file and
# blank provider keys so tests never write to a real database or call live APIs.
# load_dotenv() does not override variables that are already set.
_TEST_DB = Path(tempfile.mkdtemp(prefix="seatscout-test-")) / "test.db"
os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_DB}"
os.environ["TICKETMASTER_API_KEY"] = ""
os.environ["SEATGEEK_CLIENT_ID"] = ""

from fastapi.testclient import TestClient

from app.main import app
from app.normalization import canonical_event_key, group_comparisons
from app.storage import get_price_history, save_event_snapshots


class SeatScoutTests(unittest.TestCase):
    client = TestClient(app)

    def test_home_renders_without_generic_tagline(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Find the best ticket", response.text)
        self.assertNotIn("Every seller. One honest total", response.text)

    def test_event_api_has_comparison_data(self):
        payload = self.client.get("/api/events/the-weeknd-toronto").json()
        self.assertTrue(payload["offers"])
        self.assertEqual(payload["history"]["low"][-1], 224)

    def test_provider_status_is_transparent(self):
        payload = self.client.get("/api/providers").json()
        names = {provider["name"] for provider in payload["providers"]}
        self.assertGreaterEqual(names, {"Ticketmaster", "SeatGeek"})

    def test_search_tolerates_artist_and_venue_typos(self):
        artist_results = self.client.get("/api/search", params={"q": "Talyor Swift"}).json()["events"]
        venue_results = self.client.get("/api/search", params={"q": "Rogers Centar"}).json()["events"]
        self.assertEqual(artist_results[0]["artist"], "Taylor Swift")
        self.assertTrue(any(event["venue"] == "Rogers Centre" for event in venue_results))

    def test_search_explains_when_live_providers_are_not_configured(self):
        payload = self.client.get("/api/search", params={"q": "The Weeknd", "city": "Toronto"}).json()
        self.assertEqual(payload["mode"], "estimated")
        self.assertEqual(payload["fallback_reason"], "providers_not_configured")
        self.assertTrue(all(source["status"] == "not_configured" for source in payload["sources"]))

    def test_search_reports_provider_failure_without_exposing_details(self):
        with patch.dict(os.environ, {"TICKETMASTER_API_KEY": "test-key"}), patch(
            "app.main.TicketmasterProvider.search", new=AsyncMock(side_effect=RuntimeError("secret upstream detail"))
        ):
            payload = self.client.get("/api/search", params={"q": "Concert", "city": "Toronto"}).json()
        self.assertEqual(payload["mode"], "estimated")
        self.assertEqual(payload["fallback_reason"], "provider_error")
        ticketmaster = next(source for source in payload["sources"] if source["name"] == "Ticketmaster")
        self.assertEqual(ticketmaster, {"name": "Ticketmaster", "status": "error", "count": 0})
        self.assertNotIn("secret upstream detail", str(payload))

    def test_live_price_snapshots_are_stored(self):
        key = "test-live-event"
        save_event_snapshots([{
            "slug": key,
            "artist": "Test Live Event",
            "source": "Test Provider",
            "price_type": "live_resale",
            "low": 123,
        }])
        history = get_price_history(key)
        self.assertEqual(history[-1]["price"], 123)
        self.assertEqual(history[-1]["price_type"], "live_resale")

    def test_same_performance_is_grouped_across_providers(self):
        records = [
            {"slug": "tm-1", "provider_event_id": "1", "artist": "Phoebe Bridgers", "city": "Toronto", "date": "2027-04-10", "venue": "Massey Hall", "category": "Concerts", "low": 120, "currency": "CAD", "source": "Ticketmaster", "price_type": "live_official", "url": "https://example.com/tm"},
            {"slug": "sg-2", "provider_event_id": "2", "artist": "Phoebe Bridgers Live", "city": "Toronto", "date": "2027-04-10", "venue": "Massey Hall", "category": "Concert", "low": 105, "currency": "CAD", "source": "SeatGeek", "price_type": "live_resale", "url": "https://example.com/sg"},
        ]
        for record in records:
            record["local_time"] = "20:00"
        comparisons = group_comparisons(records)
        self.assertEqual(len(comparisons), 1)
        self.assertEqual(len(comparisons[0]["sources"]), 2)
        self.assertEqual(comparisons[0]["market"]["lowest_published"], 105)
        self.assertEqual(comparisons[0]["market"]["comparison_basis"], "published_minimum_fees_unknown")
        records[1]["currency"] = None
        self.assertIsNone(group_comparisons(records)[0]["market"]["lowest_published"])
        records[1]["local_time"] = "17:00"
        self.assertEqual(len(group_comparisons(records)), 2)

    def test_canonical_key_separates_dates(self):
        first = canonical_event_key({"artist": "Oasis", "city": "Toronto", "date": "2027-08-24"})
        second = canonical_event_key({"artist": "Oasis", "city": "Toronto", "date": "2027-08-25"})
        self.assertNotEqual(first, second)


if __name__ == "__main__":
    unittest.main()

