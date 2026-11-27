import os
import sys
import unittest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import app
from core.auth_db import is_bot_or_scanner, get_analytics_summary


class TestConversionAndTickBoxFixes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with open(os.path.join(base_dir, "templates", "index.html"), "r", encoding="utf-8") as f:
            cls.html = f.read()
        with open(os.path.join(base_dir, "static", "app.js"), "r", encoding="utf-8") as f:
            cls.js = f.read()

    def test_01_simple_tickbox_bot_check_and_api(self):
        """Hold-until-green check is replaced by simple single-click tick-box CAPTCHA."""
        self.assertIn('id="humanTickCheckbox"', self.html)
        self.assertIn('I am not a robot', self.html)
        self.assertNotIn('Hold for a few seconds and release before loading completes', self.html)
        self.assertIn('check_method: "checkbox"', self.js)
        self.assertNotIn('MIN_HOLD_TIME', self.js)

        resp = self.client.post("/api/security/verify-human", json={"check_method": "checkbox"})
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json().get("verified"))
        self.assertEqual(resp.cookies.get("almond_human_verified"), "1")

    def test_02_homepage_speed_headers_and_inline_india_feed(self):
        """GET / omits no-store for bfcache, caches versioned JS, and inlines geo-matched initial feed."""
        resp = self.client.get("/", headers={"cf-ipcountry": "IN"})
        self.assertEqual(resp.status_code, 200)
        cc = resp.headers.get("cache-control", "").lower()
        self.assertNotIn("no-store", cc)
        self.assertIn("window.__ALMOND_INITIAL_FEED__", resp.text)
        self.assertIn('id="omniQuickFilterChips"', resp.text)

        js_resp = self.client.get("/static/app.js?v=20261127_v23_conv_fix")
        self.assertEqual(js_resp.status_code, 200)
        self.assertIn("max-age=604800", js_resp.headers.get("cache-control", ""))

    def test_03_guest_india_geo_prioritization_and_two_free_samples(self):
        """Guest Indian visitor receives India-prioritized feed with 2 unlocked direct sample links."""
        resp = self.client.get("/api/omni-search?geo_country=India&limit=15&offset=0")
        self.assertEqual(resp.status_code, 200)
        items = resp.json()["result"]["items"]
        self.assertEqual(len(items), 15)

        unlocked_samples = [
            it for it in items
            if not it.get("is_auth_locked") and not it.get("is_locked") and str(it.get("url", "")).startswith("http")
        ]
        self.assertEqual(len(unlocked_samples), 2)

        top5_locs = " ".join(str(it.get("location", "")).lower() for it in items[:5])
        self.assertTrue(
            any(tok in top5_locs for tok in ("india", "bengaluru", "bangalore", "hyderabad", "pune", "chennai", "mumbai")),
            f"Expected Indian locations in top 5 guest results, got: {top5_locs}"
        )

    def test_04_mobile_webview_auth_and_instant_signup_js(self):
        """Instagram WebView protects against Google 403 error and email signup activates directly without OTP block."""
        self.assertIn("toggleAuthPasswordVisibility", self.html)
        self.assertIn("toggleAuthPasswordVisibility", self.js)
        self.assertIn("Instagram blocks Google Sign-In popups", self.js)
        self.assertIn("window.executeDirectSignupFallback(email, password, derivedName)", self.js)
        self.assertIn("almond_google_new_signup", self.js)

    def test_05_meta_crawler_filtered_and_head_ignored(self):
        """Meta link preview bots are flagged as bots and HEAD requests do not inflate visitor counts."""
        self.assertTrue(is_bot_or_scanner("/", "facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)"))
        self.assertTrue(is_bot_or_scanner("/", "meta-externalagent/1.1"))
        self.assertFalse(is_bot_or_scanner("/", "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) Instagram 350.0.0.0"))

        before_views = get_analytics_summary().get("today_views", 0)
        head_resp = self.client.head("/")
        self.assertEqual(head_resp.status_code, 200)
        after_views = get_analytics_summary().get("today_views", 0)
        self.assertEqual(before_views, after_views)


if __name__ == "__main__":
    unittest.main()
