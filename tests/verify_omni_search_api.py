import unittest
import sys
import os

# Add platform directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from core.curated_feeds import omni_search_all_feeds
from app import app


class TestOmniSearchAPI(unittest.TestCase):
    def test_omni_search_query_s(self):
        """Typing 's' or 'soft' should return software/systems openings across feeds."""
        res = omni_search_all_feeds(query="s", limit=15)
        self.assertIsInstance(res, dict)
        self.assertIn("items", res)
        self.assertIn("total", res)
        self.assertGreater(res["total"], 0)
        self.assertLessEqual(len(res["items"]), 15)

    def test_omni_search_package_filter(self):
        """Querying '7 LPA' or min_package_lpa=7.0 should filter matching compensation tiers."""
        res = omni_search_all_feeds(query="7 LPA", limit=15)
        self.assertIsInstance(res, dict)
        self.assertGreater(res["total"], 0)
        for item in res["items"][:5]:
            pkg = item.get("package_inr_lpa", 0.0)
            self.assertGreaterEqual(pkg, 6.0)

    def test_omni_search_empty_query_returns_high_freshness(self):
        """Empty query should return default high-freshness items without crashing."""
        res = omni_search_all_feeds(query="", limit=20)
        self.assertGreater(res["total"], 0)
        self.assertLessEqual(len(res["items"]), 20)

    def test_omni_search_api_endpoint(self):
        """FastAPI route /api/omni-search should return status: success with result."""
        client = TestClient(app)
        response = client.get("/api/omni-search?q=developer&limit=10")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("result", data)
        self.assertIn("items", data["result"])


if __name__ == "__main__":
    unittest.main()
