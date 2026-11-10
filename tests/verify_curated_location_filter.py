import unittest
import os
import json
from bs4 import BeautifulSoup
from fastapi.testclient import TestClient
from app import app
from core.curated_feeds import query_curated_feed, matches_country_filter

class TestCuratedLocationFilter(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        html_path = os.path.join(os.path.dirname(__file__), "..", "templates", "index.html")
        with open(html_path, "r", encoding="utf-8") as f:
            cls.html = f.read()
        cls.soup = BeautifulSoup(cls.html, "html.parser")

        js_path = os.path.join(os.path.dirname(__file__), "..", "static", "app.js")
        with open(js_path, "r", encoding="utf-8") as f:
            cls.js = f.read()

    def test_curated_modal_location_filter_markup(self):
        """Verify the searchable location dropdown replaced the old recency/active dropdown."""
        # 1. Old curatedTimeSelect should no longer exist in the filters row
        old_time_select = self.soup.find("select", {"id": "curatedTimeSelect"})
        self.assertIsNone(old_time_select, "curatedTimeSelect must be replaced with location filter")

        # 2. Country dropdown container and trigger button must exist
        container = self.soup.find("div", {"id": "curatedLocationDropdownContainer"})
        self.assertIsNotNone(container, "#curatedLocationDropdownContainer must exist")

        trigger_btn = self.soup.find("button", {"id": "curatedLocationTriggerBtn"})
        self.assertIsNotNone(trigger_btn, "#curatedLocationTriggerBtn must exist")

        # 3. Hidden input for selected location value
        hidden_loc = self.soup.find("input", {"id": "curatedLocationSelect"})
        self.assertIsNotNone(hidden_loc, "#curatedLocationSelect must exist")
        self.assertEqual(hidden_loc.get("value"), "all")

        # 4. Search input on top of country list
        search_input = self.soup.find("input", {"id": "curatedLocationSearchInput"})
        self.assertIsNotNone(search_input, "#curatedLocationSearchInput must exist for searching countries")

        # 5. List container for scrollable countries
        country_list = self.soup.find("div", {"id": "curatedLocationList"})
        self.assertIsNotNone(country_list, "#curatedLocationList must exist")

    def test_js_country_combobox_logic(self):
        """Verify JavaScript implements country search, rendering, and selection."""
        self.assertIn("CURATED_WORLD_COUNTRIES", self.js)
        self.assertIn("toggleCuratedLocationDropdown", self.js)
        self.assertIn("renderCuratedLocationList", self.js)
        self.assertIn("filterCuratedLocationList", self.js)
        self.assertIn("selectCuratedLocation", self.js)
        self.assertIn("curatedLocationSelect", self.js)

    def test_matches_country_filter_logic(self):
        """Verify unit matching for India, US, and Remote."""
        sample_india = {"location": "Bengaluru, Karnataka, India", "locations_list": ["Bengaluru"]}
        sample_us = {"location": "Chicago, IL", "locations_list": ["Chicago, IL"]}
        sample_uk = {"location": "London, UK", "locations_list": ["London"]}
        sample_remote = {"location": "Worldwide / Remote", "locations_list": ["Remote"]}

        self.assertTrue(matches_country_filter(sample_india, "India"))
        self.assertFalse(matches_country_filter(sample_us, "India"))

        self.assertTrue(matches_country_filter(sample_us, "United States"))
        self.assertFalse(matches_country_filter(sample_india, "United States"))

        self.assertTrue(matches_country_filter(sample_uk, "United Kingdom"))
        self.assertTrue(matches_country_filter(sample_remote, "all"))

    def test_curated_feed_query_location_and_sort(self):
        """Verify query_curated_feed filters by location and sorts new-to-old and old-to-new."""
        # Query India latest
        res_latest = query_curated_feed(feed_type="internships", location="India", sort_by="latest")
        # Query India oldest
        res_oldest = query_curated_feed(feed_type="internships", location="India", sort_by="oldest")

        self.assertEqual(res_latest["total"], res_oldest["total"])
        if res_latest["items"] and len(res_latest["items"]) > 1:
            self.assertGreaterEqual(res_latest["items"][0]["date_posted_ts"], res_latest["items"][-1]["date_posted_ts"])
            self.assertLessEqual(res_oldest["items"][0]["date_posted_ts"], res_oldest["items"][-1]["date_posted_ts"])

    def test_api_curated_feeds_location_endpoint(self):
        """Verify /api/curated-feeds handles location and sort_by parameters over HTTP."""
        resp = self.client.get("/api/curated-feeds?feed_type=internships&location=India&sort_by=latest")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()["result"]
        self.assertIn("items", data)
        self.assertIn("total", data)

if __name__ == "__main__":
    unittest.main()
