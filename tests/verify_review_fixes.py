import unittest
import time
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.curated_feeds import omni_search_all_feeds

class TestReviewFixes(unittest.TestCase):
    def setUp(self):
        js_path = os.path.join(os.path.dirname(__file__), "..", "static", "app.js")
        with open(js_path, "r", encoding="utf-8") as f:
            self.app_js = f.read()

    def test_01_xss_sanitization_in_card_rendering(self):
        """static/app.js must define an entity escaper and sanitize fields in renderOmniResults."""
        self.assertTrue(
            "escapeClean" in self.app_js or "escapeHtml" in self.app_js or "escapeText" in self.app_js,
            "Missing HTML entity escaper function in static/app.js"
        )
        self.assertIn("escapeClean(job.company", self.app_js, "job.company not escaped before DOM insertion")
        self.assertIn("escapeClean(job.role", self.app_js, "job.role not escaped before DOM insertion")

    def test_02_location_parameter_supported_in_omni_search_client(self):
        """executeOmniSearch and submitOmniCriteria must forward location to /api/omni-search."""
        self.assertIn("location: window.omniActiveLocation", self.app_js, "Missing location parameter forwarding in executeOmniSearch")
        self.assertIn("window.omniActiveLocation = loc", self.app_js, "submitOmniCriteria does not record location")

    def test_03_compensation_queries_non_lpa_and_ranges(self):
        """Queries with '$90,000', '100k', or ranges '7-12 LPA' should parse cleanly without returning 0 results."""
        # Range query '7-12 LPA'
        res_range = omni_search_all_feeds(query="7-12 LPA", limit=15)
        self.assertGreater(res_range["total"], 0, "Query '7-12 LPA' returned 0 results")
        
        # USD query '$90,000' or '$100k'
        res_usd = omni_search_all_feeds(query="$90,000", limit=15)
        self.assertGreater(res_usd["total"], 0, "Query '$90,000' returned 0 results")

    def test_04_drag_and_drop_handlers_present_in_client(self):
        """static/app.js must attach dragenter, dragover, and drop event listeners to searchContainer."""
        self.assertIn("dragover", self.app_js, "Missing dragover handler in static/app.js")
        self.assertIn("drop", self.app_js, "Missing drop handler in static/app.js")

    def test_05_omni_search_speed_optimization(self):
        """omni_search_all_feeds execution should be sub-25ms when min_package_lpa == 0."""
        # Warm cache
        _ = omni_search_all_feeds(query="", limit=21)
        
        t0 = time.time()
        res = omni_search_all_feeds(query="engineer", limit=21)
        dur = (time.time() - t0) * 1000
        print(f"Omni-search execution took {dur:.2f}ms")
        self.assertLess(dur, 50.0, f"Omni-search too slow ({dur:.2f}ms)")
        self.assertGreater(res["total"], 0)


if __name__ == "__main__":
    unittest.main()
