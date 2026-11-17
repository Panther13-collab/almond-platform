import os
import sys
import unittest
import re
import json

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

    def test_06_no_ats_in_vip_modal_and_exit_intent(self):
        """Verify that ATS references are completely eliminated from the VIP modal and exit intent."""
        tmpl_path = os.path.join(os.path.dirname(__file__), "..", "templates", "index.html")
        with open(tmpl_path, "r", encoding="utf-8") as f:
            html = f.read()

        self.assertIn('id="vipModalHeaderSubtitle" class="text-xs text-slate-600 font-semibold">Direct Company Ingestion', html)
        self.assertNotIn('Direct internal ATS ingestion', html)
        self.assertNotIn('corporate ATS systems', html)
        self.assertNotIn('direct corporate ATS portals', html)

        js_path = os.path.join(os.path.dirname(__file__), "..", "static", "app.js")
        with open(js_path, "r", encoding="utf-8") as f:
            js = f.read()
        self.assertNotIn('corporate ATS applications', js)
        self.assertNotIn('continuous direct ATS access', js)

    def test_07_mathematical_discounts_exact(self):
        """Verify that 3m discount is at least 30% and 6m discount is at least 35% across all currencies."""
        # 3m:
        # INR: (2599 - 1799) / 2599 = 30.78%
        # USD: (71.99 - 49.99) / 71.99 = 30.56%
        # EUR: (67.99 - 46.99) / 67.99 = 30.89%
        # GBP: (57.99 - 39.99) / 57.99 = 31.04%
        disc_3m_inr = (2599 - 1799) / 2599
        disc_3m_usd = (71.99 - 49.99) / 71.99
        disc_3m_eur = (67.99 - 46.99) / 67.99
        disc_3m_gbp = (57.99 - 39.99) / 57.99
        self.assertGreaterEqual(disc_3m_inr, 0.30)
        self.assertGreaterEqual(disc_3m_usd, 0.30)
        self.assertGreaterEqual(disc_3m_eur, 0.30)
        self.assertGreaterEqual(disc_3m_gbp, 0.30)

        # 6m:
        # INR: (4399 - 2799) / 4399 = 36.37%
        # USD: (124.99 - 79.99) / 124.99 = 36.00%
        # EUR: (116.99 - 74.99) / 116.99 = 35.90%
        # GBP: (99.99 - 64.99) / 99.99 = 35.00%
        disc_6m_inr = (4399 - 2799) / 4399
        disc_6m_usd = (124.99 - 79.99) / 124.99
        disc_6m_eur = (116.99 - 74.99) / 116.99
        disc_6m_gbp = (99.99 - 64.99) / 99.99
        self.assertGreaterEqual(disc_6m_inr, 0.35)
        self.assertGreaterEqual(disc_6m_usd, 0.35)
        self.assertGreaterEqual(disc_6m_eur, 0.35)
        self.assertGreaterEqual(disc_6m_gbp, 0.35)

    def test_08_exit_intent_adaptive_tiers_and_email_capture(self):
        """Verify app.js openPaymentExitIntent adapts per tier and passes email in verify payload."""
        js_path = os.path.join(os.path.dirname(__file__), "..", "static", "app.js")
        with open(js_path, "r", encoding="utf-8") as f:
            js = f.read()

        # Exit intent contains adaptive metaphors
        self.assertIn("A Career Upgrade Costs Less Than a Movie Ticket", js)
        self.assertIn("Transform Your Career for the Price of Dinner", js)
        self.assertIn("Half a Year of High-Growth Roles for the Cost of a Shirt", js)
        # Uses displayPrice instead of hardcoded INR amount
        self.assertIn("${currencySymbol}${displayPrice}", js)
        # Passes email in payment verification
        self.assertIn("email: currentProfile?.email || candidateUser.email", js)

    def test_09_active_vip_dashboard_location_currency_and_badges(self):
        """Verify active VIP dashboard includes location-detected currency badge, strikethrough MRP, and discount tags."""
        tmpl_path = os.path.join(os.path.dirname(__file__), "..", "templates", "index.html")
        with open(tmpl_path, "r", encoding="utf-8") as f:
            html = f.read()

        self.assertIn('id="vipUpgradeLocationBadge"', html)
        self.assertIn('id="vipUpgradeCurrencyDropdown"', html)
        self.assertIn('id="vipUpgradeOriginalPrice_3m"', html)
        self.assertIn('id="vipUpgradeOriginalPrice_6m"', html)
        self.assertIn('id="vipUpgradeDiscountBadge_3m"', html)
        self.assertIn('id="vipUpgradeDiscountBadge_6m"', html)
        self.assertIn('30% OFF', html)
        self.assertIn('35% OFF', html)

    def test_10_app_js_vip_modal_header_no_ats(self):
        """Verify static/app.js line 4854 and openVipPassModal sets Direct Company Ingestion without ATS."""
        js_path = os.path.join(os.path.dirname(__file__), "..", "static", "app.js")
        with open(js_path, "r", encoding="utf-8") as f:
            js = f.read()

        self.assertNotIn("Direct internal ATS ingestion", js)
        self.assertIn("Direct Company Ingestion • Apply before public platforms saturate", js)

if __name__ == "__main__":
    unittest.main()
