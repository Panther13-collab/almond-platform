import os
import sys
import time
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import app as app_module
from core.auth_db import (
    get_db,
    init_db,
    login_or_signup_google_user,
    record_successful_payment,
    signup_user,
)

STATIC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "static"))


class TestLoggedInMatchAndSessionPersistence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        cls.client = TestClient(app_module.app)
        with open(os.path.join(STATIC_DIR, "app.js"), "r", encoding="utf-8") as f:
            cls.js = f.read()

    def test_01_ephemeral_sqlite_reset_preserves_logged_in_session(self):
        email = f"persist_{int(time.time() * 1000)}@gmail.com"
        res = login_or_signup_google_user(email, "Sridhar Candidate", "g_123", device_model="Windows 11 Chrome")
        self.assertEqual(res.get("status"), "success")
        user_id = res["user_id"]
        token = res["token"]

        # Record a 30-day Rs 1 VIP Pass payment in SQLite payments (and suppose container restarted & wiped users table)
        record_successful_payment(user_id, "pay_rehydrate_01", "order_rehydrate_01", 1.0, "VIP Pass — 30 Days Latest Feed")
        with get_db() as conn:
            conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
            conn.commit()

        # Simulate browser reload calling /api/auth/me with cached token + email
        me_resp = self.client.post("/api/auth/me", json={
            "token": token,
            "user_id": user_id,
            "email": email,
            "full_name": "Sridhar Candidate",
        })
        self.assertEqual(me_resp.status_code, 200)
        body = me_resp.json()
        self.assertTrue(body.get("is_authenticated"), "Valid HMAC session must rehydrate after ephemeral DB reset")
        self.assertEqual(body.get("email"), email)
        self.assertEqual(body.get("user_id"), user_id)
        self.assertTrue(body.get("is_paid"), "VIP status from payments must survive rehydration")
        self.assertTrue(body.get("token"))

        # Forged token must still be rejected cleanly with invalid_token=True
        bad_resp = self.client.post("/api/auth/me", json={
            "token": f"alm.{user_id}.{int(time.time())}.deadbeef",
            "user_id": user_id,
            "email": email,
        })
        self.assertEqual(bad_resp.status_code, 200)
        bad_body = bad_resp.json()
        self.assertFalse(bad_body.get("is_authenticated"))
        self.assertTrue(bad_body.get("invalid_token"))

    def test_02_frontend_session_keys_and_pending_search_slide(self):
        # 1. isUserLoggedIn checks both almond_session_token and almond_auth_token
        self.assertIn('localStorage.getItem("almond_session_token") || localStorage.getItem("almond_auth_token")', self.js)
        # 2. completeGoogleAuth stores both keys
        google_fn_idx = self.js.find("async function completeGoogleAuth")
        self.assertNotEqual(google_fn_idx, -1)
        google_block = self.js[google_fn_idx:google_fn_idx + 1400]
        self.assertIn('localStorage.setItem("almond_session_token", data.token)', google_block)
        self.assertIn('localStorage.setItem("almond_auth_token", data.token)', google_block)
        # 3. initAuthSession only deletes tokens on explicit invalid_token === true
        init_idx = self.js.find("window.initAuthSession = async function()")
        self.assertNotEqual(init_idx, -1)
        init_block = self.js[init_idx:init_idx + 3500]
        self.assertIn("data.invalid_token === true", init_block)
        self.assertIn("email, full_name: fullName", init_block)
        # 4. Email login pending search goes to Slide 3 (Results), never Slide 2
        self.assertNotIn("executeSearch();\n                window.goToSlide(2);", self.js.replace("\r\n", "\n"))

    def test_03_match_my_resume_logged_in_shows_all_with_only_0_to_6d_blurred(self):
        email = f"matcher_{int(time.time() * 1000)}@gmail.com"
        user = signup_user(email, "Pass12345!", "Matcher User")
        user_id = user["user_id"]

        now_utc = datetime.now(timezone.utc)
        iso_days = lambda d: (now_utc - timedelta(days=d, hours=2)).isoformat()

        mock_ats = [
            {"id": "j0", "public_slug": "j0", "title": "Staff ML Eng", "company": "TodayCorp", "url": "https://jobs.lever.co/today", "posted_at": iso_days(0), "cvmatch_score": 94},
            {"id": "j3", "public_slug": "j3", "title": "Backend Lead", "company": "MidWeekCo", "url": "https://boards.greenhouse.io/midweek", "posted_at": iso_days(3), "cvmatch_score": 90},
            {"id": "j6", "public_slug": "j6", "title": "Platform Eng", "company": "SixDayCo", "url": "https://jobs.ashbyhq.com/sixday", "posted_at": iso_days(6), "cvmatch_score": 88},
            {"id": "j7", "public_slug": "j7", "title": "Senior Python Eng", "company": "SevenDayCo", "url": "https://jobs.lever.co/sevenday", "posted_at": iso_days(7), "cvmatch_score": 86},
            {"id": "j14", "public_slug": "j14", "title": "Cloud Architect", "company": "TwoWeekCo", "url": "https://boards.greenhouse.io/twoweek", "posted_at": iso_days(14), "cvmatch_score": 82},
        ]
        mock_fnd = [
            {"id": "f2", "title": "Founding Eng", "company": "LatestYC", "url": "https://ycombinator.com/latest", "posted_at": iso_days(2), "cvmatch_score": 91},
            {"id": "f10", "title": "Systems Eng", "company": "OpenYC", "url": "https://ycombinator.com/open10", "posted_at": iso_days(10), "cvmatch_score": 85},
        ]

        payload = {
            "profile": {"name": "Matcher User", "role": "Software Engineer", "skills": ["Python", "SQL"], "yoe": 3},
            "user_id": user_id,
            "preferences": {"currency": "INR", "min_package": 0, "locations": [f"TestLoc_{time.time()}"], "work_mode": "all", "employment_type": "all"},
        }

        with patch("app.search_matching_jobs", return_value={"ats_jobs": mock_ats, "linkedin_jobs": []}), \
             patch("app.fetch_hn_founder_jobs", return_value=mock_fnd):
            resp = self.client.post("/api/find-jobs", json=payload)

        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertFalse(data.get("is_paid"))
        jobs = data.get("jobs", [])
        fnd = data.get("founder_jobs", [])
        self.assertEqual(len(jobs), 5, "All jobs must be returned (no 3-job truncation)")
        self.assertEqual(len(fnd), 2)

        by_id = {j["id"]: j for j in jobs}
        for locked_id in ("j0", "j3", "j6"):
            self.assertTrue(by_id[locked_id]["is_locked"], f"{locked_id} (0-6d) must be blurred/locked")
            self.assertEqual(by_id[locked_id]["url"], "#unlock-vip")
            self.assertIsNotNone(by_id[locked_id].get("days_ago"))

        for open_id, expected_url in (("j7", "https://jobs.lever.co/sevenday"), ("j14", "https://boards.greenhouse.io/twoweek")):
            self.assertFalse(by_id[open_id]["is_locked"], f"{open_id} (7d+) must be visible and unlocked")
            self.assertEqual(by_id[open_id]["url"], expected_url)

        f_by_id = {j["id"]: j for j in fnd}
        self.assertTrue(f_by_id["f2"]["is_locked"])
        self.assertFalse(f_by_id["f10"]["is_locked"])
        self.assertEqual(f_by_id["f10"]["url"], "https://ycombinator.com/open10")

        # Now activate Rs 1 VIP Pass and confirm all 0-6d jobs unlock cleanly
        record_successful_payment(user_id, f"pay_vip_{int(time.time()*1000)}", "order_vip_1", 1.0, "VIP Pass — 30 Days Latest Feed")
        with patch("app.search_matching_jobs", return_value={"ats_jobs": [dict(x) for x in mock_ats], "linkedin_jobs": []}), \
             patch("app.fetch_hn_founder_jobs", return_value=[dict(x) for x in mock_fnd]):
            vip_resp = self.client.post("/api/find-jobs", json=payload)

        self.assertEqual(vip_resp.status_code, 200)
        vip_data = vip_resp.json()
        self.assertTrue(vip_data.get("is_paid"))
        for j in vip_data.get("jobs", []):
            self.assertFalse(j["is_locked"], f"VIP user should see unlocked job {j['id']}")


if __name__ == "__main__":
    unittest.main()
