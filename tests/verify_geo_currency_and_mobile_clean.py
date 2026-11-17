import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app import app

class TestGeoCurrencyAndMobileClean(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_01_legal_pages_no_support_button(self):
        """Verify that legal subpages do NOT have the confusing 'Support Almond' button."""
        endpoints = ["/terms", "/privacy", "/refund-policy", "/contact"]
        for ep in endpoints:
            res = self.client.get(ep)
            self.assertEqual(res.status_code, 200)
            self.assertNotIn("Support Almond", res.text, f"Support Almond found in {ep}")
            self.assertNotIn("/#contribute", res.text, f"/#contribute found in {ep}")
            self.assertIn("Back to Platform", res.text, f"Back to Platform missing in {ep}")

    def test_02_razorpay_prefill_no_dummy_candidate_email(self):
        """Verify that static/app.js does not contain dummy candidate@almondjobs.com prefill."""
        js_path = os.path.join(os.path.dirname(__file__), "..", "static", "app.js")
        with open(js_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertNotIn("candidate@almondjobs.com", content, "Found candidate@almondjobs.com dummy email in static/app.js")

    def test_03_geo_currency_api_endpoint(self):
        """Verify that /api/geo-currency accurately maps Cloudflare CF-IPCountry headers."""
        # 1. Netherlands (EUR)
        res_nl = self.client.get("/api/geo-currency", headers={"cf-ipcountry": "NL"})
        self.assertEqual(res_nl.status_code, 200)
        data_nl = res_nl.json()
        self.assertEqual(data_nl.get("country"), "NL")
        self.assertEqual(data_nl.get("currency"), "EUR")

        # 2. United Kingdom (GBP)
        res_gb = self.client.get("/api/geo-currency", headers={"cf-ipcountry": "GB"})
        self.assertEqual(res_gb.status_code, 200)
        data_gb = res_gb.json()
        self.assertEqual(data_gb.get("country"), "GB")
        self.assertEqual(data_gb.get("currency"), "GBP")

        # 3. United States (USD)
        res_us = self.client.get("/api/geo-currency", headers={"cf-ipcountry": "US"})
        self.assertEqual(res_us.status_code, 200)
        data_us = res_us.json()
        self.assertEqual(data_us.get("country"), "US")
        self.assertEqual(data_us.get("currency"), "USD")

        # 4. India (INR)
        res_in = self.client.get("/api/geo-currency", headers={"cf-ipcountry": "IN"})
        self.assertEqual(res_in.status_code, 200)
        data_in = res_in.json()
        self.assertEqual(data_in.get("country"), "IN")
        self.assertEqual(data_in.get("currency"), "INR")

    def test_04_index_server_geo_meta_injection(self):
        """Verify that server injects geo meta tags based on client's network IP header."""
        res = self.client.get("/", headers={"cf-ipcountry": "NL"})
        self.assertEqual(res.status_code, 200)
        self.assertIn('<meta name="server-geo-country" content="NL">', res.text)
        self.assertIn('<meta name="server-geo-currency" content="EUR">', res.text)

    def test_05_mobile_navbar_and_feedback_layout(self):
        """Verify index.html has decongested mobile layout and elevated feedback button."""
        tmpl_path = os.path.join(os.path.dirname(__file__), "..", "templates", "index.html")
        with open(tmpl_path, "r", encoding="utf-8") as f:
            html = f.read()

        # Top contribute button is hidden on mobile screens
        self.assertIn('id="topContributeBtn" onclick="openContributeModal()" class="hidden sm:flex', html)
        # Mobile live pill removed from center navbar
        self.assertNotIn('3.3M+</span>\n                    <span class="text-emerald-700 font-bold">Live</span>', html)
        # Feedback button elevated above bottom ticker
        self.assertIn('bottom-16 sm:bottom-6 right-3 sm:right-6', html)

if __name__ == "__main__":
    unittest.main()
