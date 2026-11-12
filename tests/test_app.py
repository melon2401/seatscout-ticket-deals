import os
import tempfile
import unittest
from pathlib import Path

# Isolate tests before the app is imported: use a throwaway SQLite file and
# blank provider keys so tests never write to a real database or call live APIs.
# load_dotenv() does not override variables that are already set.
_TEST_DB = Path(tempfile.mkdtemp(prefix="seatscout-test-")) / "test.db"
os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_DB}"
os.environ["TICKETMASTER_API_KEY"] = ""
os.environ["SEATGEEK_CLIENT_ID"] = ""

from fastapi.testclient import TestClient

from app.main import app
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


if __name__ == "__main__":
    unittest.main()

