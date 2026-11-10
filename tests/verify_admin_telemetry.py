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
        self.assertIn("Candidate ID,Full Name,Email,Sign-in Provider", res_auth.text)
        self.assertIn("Device / Hardware Model", res_auth.text)

if __name__ == "__main__":
    unittest.main()
