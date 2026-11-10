import unittest
import os
import sys
import json
import csv
import io
from fastapi.testclient import TestClient

# Ensure platform root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import app
from core.config import Config
from core.auth_db import (
    is_bot_or_scanner, parse_device_hardware, record_page_visit,
    get_analytics_summary, get_all_users_admin, get_db
)

class TestTelemetryDeviceAndBotFilter(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_01_bot_and_vulnerability_scanner_detection(self):
        """Verify is_bot_or_scanner filters malicious exploit targets and bot crawlers."""
        # Malicious / scanner paths from screenshot
        self.assertTrue(is_bot_or_scanner("/wp-admin/install.php", "Mozilla/5.0"))
        self.assertTrue(is_bot_or_scanner("/wp-login.php", "Mozilla/5.0"))
        self.assertTrue(is_bot_or_scanner("//xmlrpc.php", "Mozilla/5.0"))
        self.assertTrue(is_bot_or_scanner("/phpmyadmin/index.php", "Mozilla/5.0"))
        self.assertTrue(is_bot_or_scanner("/.env", "Mozilla/5.0"))
        self.assertTrue(is_bot_or_scanner("/.git/config", "Mozilla/5.0"))

        # Automated bot user agents
        self.assertTrue(is_bot_or_scanner("/", "curl/7.88.1"))
        self.assertTrue(is_bot_or_scanner("/", "python-requests/2.31.0"))
        self.assertTrue(is_bot_or_scanner("/", "zgrab/0.x"))
        self.assertTrue(is_bot_or_scanner("/", "CensysInspect/1.1"))
        self.assertTrue(is_bot_or_scanner("/", ""))  # Empty UA

        # Legitimate candidate routes and browsers
        chrome_ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        self.assertFalse(is_bot_or_scanner("/", chrome_ua))
        self.assertFalse(is_bot_or_scanner("/jobs/software-engineer", chrome_ua))
        self.assertFalse(is_bot_or_scanner("/privacy", chrome_ua))
        self.assertFalse(is_bot_or_scanner("/contact", chrome_ua))
        self.assertFalse(is_bot_or_scanner("/terms", chrome_ua))
        self.assertFalse(is_bot_or_scanner("/admin", chrome_ua))

    def test_02_device_hardware_model_parser(self):
        """Verify parse_device_hardware accurately detects Poco M2 Pro, Samsung A-Series, iPhone, Windows 11."""
        # 1. Poco M2 Pro (Xiaomi M2003J6CI)
        poco_ua = "Mozilla/5.0 (Linux; Android 10; M2003J6CI) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
        res_poco = parse_device_hardware(poco_ua)
        self.assertEqual(res_poco["category"], "Mobile Phone")
        self.assertIn("Poco M2 Pro", res_poco["model"])

        # 2. Samsung Galaxy A34 5G (SM-A346E)
        samsung_ua = "Mozilla/5.0 (Linux; Android 13; SM-A346E) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Mobile Safari/537.36"
        res_samsung = parse_device_hardware(samsung_ua)
        self.assertEqual(res_samsung["category"], "Mobile Phone")
        self.assertEqual(res_samsung["brand"], "Samsung")
        self.assertIn("Galaxy A34", res_samsung["model"])

        # 3. Google Pixel 8 Pro
        pixel_ua = "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Mobile Safari/537.36"
        res_pixel = parse_device_hardware(pixel_ua)
        self.assertEqual(res_pixel["brand"], "Google")
        self.assertIn("Pixel 8", res_pixel["model"])

        # 4. Apple iPhone
        iphone_ua = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Mobile/15E148 Safari/604.1"
        res_iphone = parse_device_hardware(iphone_ua)
        self.assertEqual(res_iphone["brand"], "Apple")
        self.assertIn("iPhone", res_iphone["model"])

        # 5. Windows 11 Desktop (with Client Hints platform version)
        win_ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        res_win11 = parse_device_hardware(win_ua, client_hints={"platform": "Windows", "platform_version": "15.0.0"})
        self.assertEqual(res_win11["category"], "Desktop")
        self.assertIn("Windows 11", res_win11["model"])

        # 6. Apple MacBook (macOS)
        mac_ua = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1"
        res_mac = parse_device_hardware(mac_ua)
        self.assertEqual(res_mac["brand"], "Apple")
        self.assertIn("MacBook", res_mac["model"])

    def test_03_telemetry_recording_and_analytics_summary(self):
        """Verify record_page_visit segregates bots and captures hardware devices in analytics summary."""
        # Record bot hit
        record_page_visit("/wp-admin/install.php", "198.51.100.99", "curl/7.88.1")
        # Record candidate hit
        record_page_visit(
            "/jobs/", "203.0.113.88",
            "Mozilla/5.0 (Linux; Android 10; M2003J6CI) AppleWebKit/537.36 Chrome/120.0 Mobile Safari/537.36"
        )

        analytics = get_analytics_summary()
        self.assertGreater(analytics["bot_probes_total"], 0)
        self.assertGreater(analytics["total_pageviews"], 0)
        self.assertIn("hardware_devices", analytics)
        # Verify blocked probes list contains wp-admin
        blocked_paths = [p["path"] for p in analytics["top_blocked_probes"]]
        self.assertTrue(any("wp-admin" in p for p in blocked_paths))

    def test_04_candidate_directory_supabase_sync_and_persistence(self):
        """Verify get_all_users_admin synchronizes from Supabase and lists real candidate emails."""
        candidates = get_all_users_admin()
        self.assertGreater(len(candidates), 0, "Candidate directory should never be empty when Supabase is configured!")
        
        emails = [c["email"].lower() for c in candidates]
        # Verify real registered candidate emails exist
        self.assertTrue(any("sridhar" in e for e in emails), "Expected real registered candidate email in directory")
        self.assertTrue(any("anandhan" in e or "santhosh" in e or "ssmsp" in e for e in emails))

        for cand in candidates[:5]:
            self.assertIn("email", cand)
            self.assertIn("auth_provider", cand)
            self.assertIn("device_display", cand)
            self.assertIn("created_at_str", cand)

    def test_05_admin_html_dashboard_and_export_endpoints(self):
        """Verify /admin portal renders with candidate directory and CSV export includes device models."""
        admin_key = Config.ADMIN_SECRET_KEY
        
        # 1. Test /admin HTML dashboard
        resp = self.client.get(f"/admin?key={admin_key}")
        self.assertEqual(resp.status_code, 200)
        html = resp.text
        self.assertIn("Almond Jobs Telemetry", html)
        self.assertIn("Registered Candidates Directory", html)
        self.assertIn("Device & Hardware Breakdown", html)
        self.assertIn("Security Probes Blocked", html)
        self.assertIn("Verified Candidate Routes", html)

        # 2. Test /api/admin/metrics API
        resp_api = self.client.get(f"/api/admin/metrics?key={admin_key}")
        self.assertEqual(resp_api.status_code, 200)
        data = resp_api.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("analytics", data)
        self.assertIn("candidates", data)
        self.assertGreater(len(data["candidates"]), 0)

        # 3. Test /api/admin/export-users CSV endpoint
        resp_csv = self.client.get(f"/api/admin/export-users?key={admin_key}")
        self.assertEqual(resp_csv.status_code, 200)
        self.assertEqual(resp_csv.headers["content-type"], "text/csv; charset=utf-8")
        csv_text = resp_csv.text
        self.assertIn("Device / Hardware Model", csv_text)
        self.assertIn("Email", csv_text)

if __name__ == '__main__':
    unittest.main()
