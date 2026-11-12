from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import os
import sys
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from core.auth_db import is_user_paid, login_or_signup_google_user
from core.config import Config
from core.curated_feeds import query_curated_feed
from core.payment import apply_vip_latest_feed_lock


class TestVipPassAndLatestFeedGating(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.html = cls.client.get("/").text
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with open(os.path.join(base_dir, "static", "app.js"), "r", encoding="utf-8") as f:
            cls.js = f.read()

    def test_01_ui_separation_vip_pass_vs_contribute(self):
        # Dedicated VIP Pass modal & ₹1 launch promo + INR/USD planned parity
        self.assertIn('id="vipPassModal"', self.html)
        self.assertIn("Almond Jobs VIP Pass", self.html)
        self.assertIn("openVipPassModal()", self.html)
        self.assertIn("executeVipPassCheckout()", self.html)
        self.assertIn("VIP_PLANNED_PARITY", self.html)
        self.assertIn("₹699", self.html)
        self.assertIn("$8", self.html)

        # Contribute is cleanly separated: no "Upgrade to Direct Portal VIP Pass" inside #vipPricingModal
        vip_pricing_start = self.html.find('id="vipPricingModal"')
        vip_pass_start = self.html.find('id="vipPassModal"')
        contribute_html = self.html[vip_pricing_start:vip_pass_start]
        self.assertIn("Buy Almond Jobs a coffee", contribute_html)
        self.assertNotIn("Upgrade to Direct Portal VIP Pass", contribute_html)
        self.assertIn("independent of VIP Pass", contribute_html)

        # Side menu has Contribute as the LAST option in navigation items
        side_panel_start = self.html.find('id="sidePanel"')
        side_panel_footer = self.html.find('<!-- Drawer Footer -->', side_panel_start)
        side_panel_body = self.html[side_panel_start:side_panel_footer]
        pos_who = side_panel_body.rfind("navigateFromSidePanel('who')")
        pos_profile = side_panel_body.rfind("navigateFromSidePanel('profile')")
        pos_vip = side_panel_body.rfind("navigateFromSidePanel('vip')")
        pos_contribute = side_panel_body.rfind("navigateFromSidePanel('contribute')")
        self.assertGreater(pos_contribute, pos_who)
        self.assertGreater(pos_contribute, pos_profile)
        self.assertGreater(pos_contribute, pos_vip)

        # Profile modal has VIP Pass upgrade card AND Contribute placed at the bottom
        prof_start = self.html.find('id="profileModal"')
        prof_end = self.html.find('id="paymentExitIntentModal"', prof_start)
        profile_html = self.html[prof_start:prof_end]
        pos_prof_vip = profile_html.find("openVipPassModal()")
        pos_prof_logout = profile_html.find("handleLogout()")
        pos_prof_contrib = profile_html.rfind("openContributeModal()")
        self.assertNotEqual(pos_prof_vip, -1)
        self.assertGreater(pos_prof_contrib, pos_prof_vip)
        self.assertGreater(pos_prof_contrib, pos_prof_logout)

    def test_02_latest_feed_0_to_6_days_blur_logic(self):
        now = datetime.now(timezone.utc)
        sample_jobs = []
        for d in (0, 1, 2, 3, 4, 5, 6, 7, 10):
            sample_jobs.append({
                "title": f"Engineer {d}d",
                "company": f"Corp{d}",
                "url": f"https://boards.greenhouse.io/corp{d}/jobs/{d}",
                "posted_at": (now - timedelta(days=d, hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "cvmatch_score": 88,
            })

        locked_view = [dict(j) for j in sample_jobs]
        apply_vip_latest_feed_lock(locked_view, user_is_paid=False)

        for j in locked_view:
            days = j["days_ago"]
            if days <= 6:
                self.assertTrue(j["is_locked"], f"Job {days}d old should be locked for free users")
                self.assertEqual(j["url"], "#unlock-vip")
                self.assertNotIn(f"Corp{days}", j["company"])
            else:
                self.assertFalse(j["is_locked"], f"Job {days}d old should be unlocked for free users")
                self.assertTrue(j["url"].startswith("https://boards.greenhouse.io/"))

        vip_view = [dict(j) for j in sample_jobs]
        apply_vip_latest_feed_lock(vip_view, user_is_paid=True)
        for j in vip_view:
            self.assertFalse(j["is_locked"])
            self.assertTrue(j["url"].startswith("https://boards.greenhouse.io/"))

    def test_03_frontend_blur_and_unlock_cta(self):
        self.assertIn("isJobLatestFeedLocked", self.js)
        self.assertIn("blur-[5px]", self.js)
        self.assertIn("Unlock VIP for Latest Feed", self.js)
        self.assertIn("openVipPassModal()", self.js)

    def test_04_contribution_does_not_grant_vip_while_1rs_vip_does(self):
        email = f"vip_split_{int(datetime.now().timestamp() * 1000)}@example.com"
        user_res = login_or_signup_google_user(email, "VIP Tester", "google_vip_split_test")
        uid = user_res["user_id"]
        self.assertFalse(is_user_paid(uid))

        # 1. Verify voluntary coffee contribution does NOT unlock VIP
        order_c = "order_ContribTest001"
        pay_c = "pay_ContribTest001"
        sig_c = hmac.new(
            Config.RAZORPAY_KEY_SECRET.encode("utf-8"),
            f"{order_c}|{pay_c}".encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        r_contrib = self.client.post("/api/payment/verify", json={
            "user_id": uid,
            "order_id": order_c,
            "payment_id": pay_c,
            "signature": sig_c,
            "amount_inr": 485,
            "plan_name": "Buy Almond Jobs 1 Coffee",
            "purchase_type": "contribution",
        })
        self.assertEqual(r_contrib.status_code, 200)
        self.assertEqual(r_contrib.json()["purchase_type"], "contribution")
        self.assertFalse(r_contrib.json()["is_paid"])
        self.assertFalse(is_user_paid(uid), "Contribution must NEVER grant VIP Pass!")

        # 2. Verify Rs. 1 VIP Pass DOES unlock VIP
        order_v = "order_VipTest001"
        pay_v = "pay_VipTest001"
        sig_v = hmac.new(
            Config.RAZORPAY_KEY_SECRET.encode("utf-8"),
            f"{order_v}|{pay_v}".encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        r_vip = self.client.post("/api/payment/verify", json={
            "user_id": uid,
            "order_id": order_v,
            "payment_id": pay_v,
            "signature": sig_v,
            "amount_inr": 1,
            "plan_name": "Almond Jobs VIP Pass (30 Days)",
            "purchase_type": "vip_pass",
        })
        self.assertEqual(r_vip.status_code, 200)
        self.assertEqual(r_vip.json()["purchase_type"], "vip_pass")
        self.assertTrue(r_vip.json()["is_paid"])
        self.assertTrue(is_user_paid(uid), "VIP Pass checkout must activate VIP access!")

    def test_05_curated_feeds_respect_latest_feed_lock(self):
        now_ts = int(datetime.now(timezone.utc).timestamp())
        mock_items = [
            {
                "company": "FreshCorp",
                "role": "Fresh Intern",
                "location": "Remote",
                "url": "https://boards.greenhouse.io/freshcorp/1",
                "category": "Software",
                "date_posted_ts": now_ts - (2 * 86400),
                "date_posted_str": "2d ago",
            },
            {
                "company": "OlderCorp",
                "role": "Older Intern",
                "location": "Remote",
                "url": "https://boards.greenhouse.io/oldercorp/2",
                "category": "Software",
                "date_posted_ts": now_ts - (12 * 86400),
                "date_posted_str": "12d ago",
            },
        ]
        with patch("core.curated_feeds.get_feed_data", return_value=mock_items):
            free_res = query_curated_feed("internships", user_is_paid=False)
            self.assertTrue(free_res["items"][0]["is_locked"])
            self.assertEqual(free_res["items"][0]["date_posted_str"], "2d ago")
            self.assertFalse(free_res["items"][1]["is_locked"])

            vip_res = query_curated_feed("internships", user_is_paid=True)
            self.assertFalse(vip_res["items"][0]["is_locked"])
            self.assertEqual(vip_res["items"][0]["url"], "https://boards.greenhouse.io/freshcorp/1")


if __name__ == "__main__":
    unittest.main()
