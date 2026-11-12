import os
import sys
import unittest

# Ensure platform root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app import app
from core.config import Config
from core.auth_db import (
    record_page_visit,
    get_analytics_summary,
    get_all_users_admin,
    login_or_signup_google_user
)

class TestAdminTelemetryAndTraffic(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.admin_key = Config.ADMIN_SECRET_KEY

    def test_01_record_page_visit_filtering(self):
        """Verify tracking records HTML/job visits and filters static assets."""
        # Non-tracked assets
        self.assertFalse(record_page_visit("/static/app.js", "1.2.3.4", "Mozilla/5.0"))
        self.assertFalse(record_page_visit("/static/warrior_clean.webp", "1.2.3.4", "Mozilla/5.0"))
        self.assertFalse(record_page_visit("/robots.txt", "1.2.3.4", "Mozilla/5.0"))
        self.assertFalse(record_page_visit("/health", "1.2.3.4", "Mozilla/5.0"))

        # Tracked career routes
        self.assertTrue(record_page_visit("/", "1.2.3.4", "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"))
        self.assertTrue(record_page_visit("/jobs/software-engineer", "1.2.3.4", "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X)"))

    def test_02_get_analytics_summary(self):
        """Verify analytics metrics aggregation."""
        summary = get_analytics_summary()
        self.assertIn("total_pageviews", summary)
        self.assertIn("today_pageviews", summary)
        self.assertIn("unique_visitors_total", summary)
        self.assertIn("today_unique_visitors", summary)
        self.assertIn("desktop_views", summary)
        self.assertIn("mobile_views", summary)
        self.assertIn("top_pages", summary)
        self.assertIn("daily_trend", summary)
        self.assertIn("total_users", summary)
        self.assertGreaterEqual(summary["total_pageviews"], 1)
        self.assertGreaterEqual(summary["total_users"], 1)

    def test_03_get_all_users_admin(self):
        """Verify candidate directory returns records with expected schema."""
        users = get_all_users_admin()
        self.assertIsInstance(users, list)
        self.assertGreater(len(users), 0)
        sample = users[0]
        self.assertIn("id", sample)
        self.assertIn("email", sample)
        self.assertIn("full_name", sample)
        self.assertIn("plan", sample)
        self.assertIn("is_paid", sample)
        self.assertIn("auth_provider", sample)
        self.assertIn("created_at_str", sample)

    def test_04_admin_route_security_and_rendering(self):
        """Verify /admin protects access with secret key and renders lock screen without key."""
        # Unauthenticated: should return 200 with lock view
        res = self.client.get("/admin")
        self.assertEqual(res.status_code, 200)
        self.assertIn("Almond Jobs Telemetry", res.text)
        self.assertIn("Admin Secret Access Key", res.text)
        self.assertNotIn("Registered Candidates Directory", res.text)

        # Authenticated with valid key: renders full dashboard
        res_auth = self.client.get(f"/admin?key={self.admin_key}")
        self.assertEqual(res_auth.status_code, 200)
        self.assertIn("Registered Candidates Directory", res_auth.text)
        self.assertIn("Core Telemetry & Engagements", res_auth.text)
        self.assertIn("Download CSV Export", res_auth.text)
        self.assertIn("almond_admin_key", res_auth.headers.get("set-cookie", ""))

    def test_05_admin_metrics_api(self):
        """Verify /api/admin/metrics returns JSON data when authorized."""
        # Unauthorized
        res_unauth = self.client.get("/api/admin/metrics?key=invalid_secret_key")
        self.assertEqual(res_unauth.status_code, 401)

        # Authorized
        res_auth = self.client.get(f"/api/admin/metrics?key={self.admin_key}")
        self.assertEqual(res_auth.status_code, 200)
        data = res_auth.json()
        self.assertEqual(data.get("status"), "success")
        self.assertIn("analytics", data)
        self.assertIn("candidates", data)

    def test_06_admin_export_users_csv(self):
        """Verify /api/admin/export-users returns downloadable CSV spreadsheet."""
        # Unauthorized
        res_unauth = self.client.get("/api/admin/export-users?key=wrong")
        self.assertEqual(res_unauth.status_code, 401)

        # Authorized
        res_auth = self.client.get(f"/api/admin/export-users?key={self.admin_key}")
        self.assertEqual(res_auth.status_code, 200)
        self.assertEqual(res_auth.headers.get("content-type"), "text/csv; charset=utf-8")
        self.assertIn("attachment; filename=\"almond_candidates_export.csv\"", res_auth.headers.get("content-disposition", ""))
        self.assertIn("Candidate ID,Full Name,Email,Account Classification,Sign-in Provider", res_auth.text)
        self.assertIn("Device / Hardware Model", res_auth.text)

    def test_07_admin_grant_and_revoke_vip_api(self):
        """Verify admin can grant 1-month VIP to an email, pre-approving access on future login, and revoking it."""
        # 1. Unauthorized check
        r_unauth = self.client.post("/api/admin/grant-vip", json={"email": "vip_future@startup.io", "key": "bad_key"})
        self.assertEqual(r_unauth.status_code, 401)

        # 2. Grant VIP to email
        test_email = "vip_future_director@startup.io"
        r_grant = self.client.post("/api/admin/grant-vip", json={
            "email": test_email,
            "duration_days": 30,
            "key": self.admin_key
        })
        self.assertEqual(r_grant.status_code, 200)
        grant_data = r_grant.json()
        self.assertEqual(grant_data["status"], "success")
        self.assertTrue(grant_data["is_paid"])
        self.assertEqual(grant_data["days_remaining"], 30)

        # 3. Future candidate signs in for the first time via Google
        login_res = login_or_signup_google_user(test_email, "Future VIP Director", "goog_future_123")
        self.assertEqual(login_res["status"], "success")
        self.assertTrue(login_res["is_paid"], "Candidate pre-approved for VIP must have VIP active on first sign-in!")
        self.assertEqual(login_res["plan"], "vip_pass_30d")

        # 4. Check is_user_paid
        uid = login_res["user_id"]
        from core.auth_db import is_user_paid
        self.assertTrue(is_user_paid(uid))

        # 5. Revoke VIP
        r_revoke = self.client.post("/api/admin/grant-vip", json={
            "email": test_email,
            "action": "revoke",
            "key": self.admin_key
        })
        self.assertEqual(r_revoke.status_code, 200)
        self.assertFalse(r_revoke.json()["is_paid"])
        self.assertFalse(is_user_paid(uid), "Candidate must be reverted to free tier after revoke!")

    def test_08_vip_1month_expiration_auto_revert(self):
        """Verify that after 1 month (expiration date passed), candidate is automatically removed from VIP."""
        import time
        from core.auth_db import get_db, is_user_paid
        test_email = "expired_vip_user@company.com"
        u = login_or_signup_google_user(test_email, "Expired Candidate", "goog_exp_123")
        uid = u["user_id"]

        now = time.time()
        # Set paid_until in the past (e.g. 1 hour ago, expired 1-month VIP pass)
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET is_paid = 1, plan = 'vip_pass_30d', paid_until = ? WHERE id = ?", (now - 3600, uid))
            conn.commit()

        # is_user_paid must detect expiration, auto-revert to free, and return False
        self.assertFalse(is_user_paid(uid), "Expired VIP pass must return False and remove account from VIP!")

        # Verify users table in DB was updated to is_paid = 0 and plan = 'free'
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT is_paid, plan FROM users WHERE id = ?", (uid,))
            row = cursor.fetchone()
            self.assertEqual(row["is_paid"], 0)
            self.assertEqual(row["plan"], "free")

    def test_09_admin_page_filters_and_dummy_classification(self):
        """Verify admin UI contains multi-filters, quick filter pills, and dummy email classification."""
        from core.auth_db import is_dummy_email
        self.assertTrue(is_dummy_email("dummy_candidate@example.com"))
        self.assertTrue(is_dummy_email("test_user_4492@test.com"))
        self.assertTrue(is_dummy_email("vip_split_17949382@fake.com"))
        self.assertFalse(is_dummy_email("sarah.connor@cyberdyne.ai"))
        self.assertFalse(is_dummy_email("sridhar.engineer@gmail.com"))

        res_auth = self.client.get(f"/admin?key={self.admin_key}")
        self.assertEqual(res_auth.status_code, 200)
        self.assertIn("Grant 1-Month VIP Access to Email", res_auth.text)
        self.assertIn("admin-grant-email", res_auth.text)
        self.assertIn("Quick Filters:", res_auth.text)
        self.assertIn("✨ Genuine Real", res_auth.text)
        self.assertIn("⚡ Newly Added (24h)", res_auth.text)
        self.assertIn("🧪 Test / Dummy", res_auth.text)
        self.assertIn("filter-type", res_auth.text)
        self.assertIn("filter-recency", res_auth.text)
        self.assertIn("filter-vip", res_auth.text)
        self.assertIn("filter-provider", res_auth.text)

if __name__ == "__main__":
    unittest.main()
