import hmac
import hashlib
import os
import sys
import unittest
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import app as app_module
from core.config import Config
from core.auth_db import (
    init_db,
    is_user_paid,
    login_or_signup_google_user,
    record_successful_payment,
    record_contribution_payment,
)
from core.payment import apply_vip_latest_feed_lock
from core.curated_feeds import query_curated_feed
from core.doc_exporter import export_to_docx, export_to_csv, is_export_job_locked, _export_pdf_pure_python


class TestVipPassAndLatestFeedGating(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        cls.client = TestClient(app_module.app)
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with open(os.path.join(base_dir, "templates", "index.html"), "r", encoding="utf-8") as f:
            cls.html = f.read()
        with open(os.path.join(base_dir, "static", "app.js"), "r", encoding="utf-8") as f:
            cls.js = f.read()

    def test_01_ui_separation_vip_pass_vs_contribute(self):
        # Dedicated VIP Pass modal & ₹699 planned price + INR/USD/EUR/GBP planned parity
        self.assertIn('id="vipPassModal"', self.html)
        self.assertIn("Almond Jobs VIP Pass", self.html)
        self.assertIn("openVipPassModal()", self.html)
        self.assertIn("executeVipPassCheckout()", self.html)
        self.assertIn("VIP_PLANNED_PARITY", self.html)
        self.assertIn("₹699", self.html)
        self.assertIn("$9.99", self.html)
        self.assertIn("€9.99", self.html)
        self.assertIn("£9.99", self.html)

        # No prices on navbar or outer surfaces
        self.assertIn('<span id="topVipPassLabel">VIP Pass</span>', self.html)
        self.assertNotIn('<span id="topVipPassLabel">VIP Pass &bull; ₹699</span>', self.html)
        self.assertIn('👑 Unlock VIP Pass', self.html)
        self.assertNotIn('👑 Unlock VIP Pass &mdash; ₹1', self.html)

        # 1-Month VIP Pass duration & no "equivalent to" wording
        self.assertIn("Standard 1-Month VIP Pass", self.html)
        self.assertIn("1 Month Access", self.html)
        self.assertNotIn("USD eq.", self.html)
        self.assertNotIn("INR eq.", self.html)
        self.assertNotIn("EUR eq.", self.html)
        self.assertNotIn("GBP eq.", self.html)
        self.assertNotIn("&approx; $9.99 USD", self.html)

        # Rotating live reviews & dynamic supporters
        self.assertIn('id="miniLiveReviewCard"', self.html)
        self.assertIn('id="liveReviewEmotion"', self.html)
        self.assertIn("startLiveReviewTicker", self.js)
        self.assertIn("fetchRecentContributions", self.js)
        self.assertIn("addSupporterToFeed", self.js)

        # Founder voice: no 0-6 days robotic text in VIP modal
        vip_pass_start = self.html.find('id="vipPassModal"')
        prof_start = self.html.find('id="profileModal"')
        vip_pass_html = self.html[vip_pass_start:prof_start]
        self.assertNotIn("0&ndash;6", vip_pass_html)
        self.assertNotIn("0-6", vip_pass_html)

        # Contribute button near profile with coffee logo
        self.assertIn('id="topContributeBtn"', self.html)
        self.assertIn("openContributeModal()", self.html)
        self.assertIn("☕", self.html)

        # Profile dial VIP indicators
        self.assertIn('id="topProfileVipCrown"', self.html)
        self.assertIn('id="topProfileVipBadge"', self.html)

        # Contribute is cleanly separated: no "Upgrade to Direct Portal VIP Pass" inside #vipPricingModal
        vip_pricing_start = self.html.find('id="vipPricingModal"')
        contribute_html = self.html[vip_pricing_start:vip_pass_start]
        self.assertIn("Buy Almond Jobs a coffee", contribute_html)
        self.assertNotIn("Upgrade to Direct Portal VIP Pass", contribute_html)
        self.assertIn("independent", contribute_html)
        self.assertNotIn("0&ndash;6 day", contribute_html)

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

    def test_02_latest_feed_company_visible_and_designation_blurred(self):
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
                # COMPANY NAME IS PRESERVED so users are tempted!
                self.assertEqual(j["company"], f"Corp{days}")
                # Designation is masked
                self.assertEqual(j["title"], "Confidential Role (VIP Pass)")
            else:
                self.assertFalse(j["is_locked"], f"Job {days}d old should be unlocked for free users")
                self.assertEqual(j["company"], f"Corp{days}")
                self.assertEqual(j["title"], f"Engineer {days}d")
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
        self.assertIn("VIP Active ✓", self.js)
        self.assertIn("topProfileVipCrown", self.js)
        self.assertIn("topProfileVipBadge", self.js)

    def test_04_contribution_does_not_grant_vip_while_vip_order_does(self):
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

        # 2. Verify planned VIP Pass DOES unlock VIP
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
            "amount_inr": 699,
            "plan_name": "Almond Jobs VIP Pass (30 Days)",
            "purchase_type": "vip_pass",
        })
        self.assertEqual(r_vip.status_code, 200)
        self.assertEqual(r_vip.json()["purchase_type"], "vip_pass")
        self.assertTrue(r_vip.json()["is_paid"])
        self.assertTrue(is_user_paid(uid), "VIP Pass must grant active VIP status!")

    def test_05_curated_feeds_respect_latest_feed_lock(self):
        res_free = query_curated_feed("internships", limit=20, offset=0, user_is_paid=False)
        items_free = res_free["items"]
        for item in items_free:
            days = item.get("days_ago")
            if days is not None and days <= 6:
                self.assertTrue(item.get("is_locked"))
                self.assertEqual(item.get("url"), "#unlock-vip")
                # Company remains visible
                self.assertTrue(bool(item.get("company")))

        res_vip = query_curated_feed("internships", limit=20, offset=0, user_is_paid=True)
        items_vip = res_vip["items"]
        for item in items_vip:
            self.assertFalse(item.get("is_locked"))
            self.assertNotEqual(item.get("url"), "#unlock-vip")

    def test_06_dossier_exports_gate_latest_links_for_free_and_unlock_for_vip(self):
        now = datetime.now(timezone.utc)
        sample_jobs = [
            {
                "title": "Software Engineer (Today)",
                "company": "Google",
                "url": "https://www.google.com/careers/job1",
                "posted_at": (now - timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "days_ago": 0,
                "cvmatch_score": 95,
                "comp_display": "₹35,00,000",
                "source": "Direct Feed"
            },
            {
                "title": "Senior Backend Engineer (10d)",
                "company": "Stripe",
                "url": "https://stripe.com/jobs/job2",
                "posted_at": (now - timedelta(days=10)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "days_ago": 10,
                "cvmatch_score": 90,
                "comp_display": "₹45,00,000",
                "source": "Direct Feed"
            }
        ]

        # 1. Lock check helper
        self.assertTrue(is_export_job_locked(sample_jobs[0], is_paid=False))
        self.assertFalse(is_export_job_locked(sample_jobs[1], is_paid=False))
        self.assertFalse(is_export_job_locked(sample_jobs[0], is_paid=True))
        self.assertFalse(is_export_job_locked(sample_jobs[1], is_paid=True))

        # 2. Test CSV export for free user
        csv_free_path = os.path.join(os.path.dirname(__file__), "test_free_export.csv")
        export_to_csv(sample_jobs, csv_free_path, is_paid=False)
        with open(csv_free_path, "r", encoding="utf-8") as f:
            csv_free_content = f.read()
        if os.path.exists(csv_free_path):
            os.remove(csv_free_path)

        self.assertNotIn("https://www.google.com/careers/job1", csv_free_content, "Free user CSV must NOT contain 0-day link!")
        self.assertIn("LOCKED (VIP Required", csv_free_content)
        self.assertIn("Google", csv_free_content, "Company name must remain visible in CSV!")
        self.assertIn("https://stripe.com/jobs/job2", csv_free_content, "Older (10d) link must remain visible!")

        # 3. Test CSV export for VIP user
        csv_vip_path = os.path.join(os.path.dirname(__file__), "test_vip_export.csv")
        export_to_csv(sample_jobs, csv_vip_path, is_paid=True)
        with open(csv_vip_path, "r", encoding="utf-8") as f:
            csv_vip_content = f.read()
        if os.path.exists(csv_vip_path):
            os.remove(csv_vip_path)

        self.assertIn("https://www.google.com/careers/job1", csv_vip_content, "VIP CSV must contain latest 0-day link!")
        self.assertIn("https://stripe.com/jobs/job2", csv_vip_content, "VIP CSV must contain older link!")
        self.assertNotIn("LOCKED", csv_vip_content)

        # 4. Test PDF export for free user
        pdf_free_path = os.path.join(os.path.dirname(__file__), "test_free_export.pdf")
        _export_pdf_pure_python({"name": "Test User"}, sample_jobs, pdf_free_path, is_paid=False)
        self.assertTrue(os.path.exists(pdf_free_path))
        if os.path.exists(pdf_free_path):
            os.remove(pdf_free_path)

        # 5. Test DOCX export for free user
        docx_free_path = os.path.join(os.path.dirname(__file__), "test_free_export.docx")
        export_to_docx({"name": "Test User"}, sample_jobs, docx_free_path, is_paid=False)
        self.assertTrue(os.path.exists(docx_free_path))
        if os.path.exists(docx_free_path):
            os.remove(docx_free_path)

    def test_07_contributions_recent_feed_and_persisted_comments(self):
        email = f"supporter_feed_{int(datetime.now().timestamp() * 1000)}@example.com"
        user_res = login_or_signup_google_user(email, "Supporter Test", "google_supporter_feed_test")
        uid = user_res["user_id"]

        order_id = f"order_feed_{int(datetime.now().timestamp() * 1000)}"
        payment_id = f"pay_feed_{int(datetime.now().timestamp() * 1000)}"
        sig = hmac.new(
            Config.RAZORPAY_KEY_SECRET.encode("utf-8"),
            f"{order_id}|{payment_id}".encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        test_msg = "Super clean experience, direct links saved me hours!"
        test_name = "Karthik Raja"

        r = self.client.post("/api/payment/verify", json={
            "user_id": uid,
            "order_id": order_id,
            "payment_id": payment_id,
            "signature": sig,
            "amount_inr": 485,
            "plan_name": "Buy Almond Jobs 1 Coffee",
            "purchase_type": "contribution",
            "supporter_name": test_name,
            "supporter_message": test_msg
        })
        self.assertEqual(r.status_code, 200)

        # Verify /api/contributions/recent returns this supporter
        r_feed = self.client.get("/api/contributions/recent")
        self.assertEqual(r_feed.status_code, 200)
        feed_data = r_feed.json()
        self.assertIn("contributions", feed_data)
        matches = [c for c in feed_data["contributions"] if c.get("supporter_name") == test_name]
        self.assertTrue(len(matches) > 0, "Submitted supporter comment must be returned in recent contributions feed")
        self.assertEqual(matches[0]["supporter_message"], test_msg)


if __name__ == "__main__":
    unittest.main()
