import unittest

from fastapi.testclient import TestClient

from app.main import app


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


if __name__ == "__main__":
    unittest.main()

