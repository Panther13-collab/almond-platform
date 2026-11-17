import unittest
import io
from fastapi.testclient import TestClient

from app import app, _is_valid_admin_key
from core.config import Config
from core.security import rate_limiter, validate_uploaded_file
from core.doc_exporter import _sanitize_csv_cell, export_to_csv

class TestSecurityAuditAndHardening(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.admin_key = Config.ADMIN_SECRET_KEY

    def test_01_constant_time_admin_auth_and_timing_defense(self):
        """Verify admin key constant-time verification logic."""
        self.assertTrue(_is_valid_admin_key(self.admin_key))
        self.assertFalse(_is_valid_admin_key("wrong_secret_123"))
        self.assertFalse(_is_valid_admin_key(""))
        self.assertFalse(_is_valid_admin_key(None))
        # Unauthorized endpoint checks
        res = self.client.get("/api/admin/metrics?key=invalid_key")
        self.assertEqual(res.status_code, 401)
        res_fb = self.client.get("/api/admin/feedback?key=invalid_key")
        self.assertEqual(res_fb.status_code, 401)
        res_rev = self.client.get("/api/admin/revenue-analytics?key=invalid_key")
        self.assertEqual(res_rev.status_code, 401)

    def test_02_rate_limiter_endpoint_rules(self):
        """Verify that sensitive endpoints have strict sliding-window rate limits configured."""
        limits = rate_limiter.endpoint_limits
        self.assertIn("/api/auth/send-otp", limits)
        self.assertEqual(limits["/api/auth/send-otp"], (3, 60))
        self.assertIn("/api/feedback/submit", limits)
        self.assertEqual(limits["/api/feedback/submit"], (6, 60))
        self.assertIn("/api/find-jobs", limits)
        self.assertEqual(limits["/api/find-jobs"], (10, 60))

    def test_03_csv_formula_injection_defense(self):
        """Verify CWE-1236 spreadsheet formula sanitization."""
        dangerous_payloads = [
            "=cmd|' /C calc'!A0",
            "+12345",
            "-SUM(1,2)",
            "@HYPERLINK('http://attacker.com')",
            "\tTAB_INJECT",
            "\rCR_INJECT"
        ]
        for p in dangerous_payloads:
            sanitized = _sanitize_csv_cell(p)
            self.assertTrue(sanitized.startswith("'"), f"Failed to sanitize formula prefix for: {p}")

        safe_text = "Senior Staff Backend Engineer"
        self.assertEqual(_sanitize_csv_cell(safe_text), safe_text)

    def test_04_file_upload_security_and_traversal_guards(self):
        """Verify upload validation checks file size, extensions, magic bytes, and path traversal."""
        class MockFile:
            def __init__(self, filename):
                self.filename = filename

        # 1. Reject malicious extension
        with self.assertRaises(Exception):
            validate_uploaded_file(MockFile("malicious_script.exe"), b"MZ\x90\x00...")

        with self.assertRaises(Exception):
            validate_uploaded_file(MockFile("exploit.py"), b"import os; os.system('calc')")

        # 2. Reject fake PDF without PDF magic header
        with self.assertRaises(Exception):
            validate_uploaded_file(MockFile("fake.pdf"), b"This is not a pdf file")

        # 3. Path traversal filename sanitization
        safe_name = validate_uploaded_file(MockFile("../../../etc/passwd.pdf"), b"%PDF-1.4 valid test header")
        self.assertNotIn("..", safe_name)
        self.assertNotIn("/", safe_name)
        self.assertNotIn("\\", safe_name)

    def test_05_bot_shield_and_security_headers(self):
        """Verify malicious scanner blocking and OWASP response headers."""
        # Malicious UA blocking
        res_blocked = self.client.get("/api/find-jobs", headers={"user-agent": "sqlmap/1.5#stable"})
        self.assertEqual(res_blocked.status_code, 403)

        # Valid browser request -> verify enterprise security headers
        res = self.client.get("/", headers={"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        self.assertEqual(res.status_code, 200)
        headers = res.headers
        self.assertEqual(headers.get("X-Content-Type-Options"), "nosniff")
        self.assertEqual(headers.get("X-Frame-Options"), "SAMEORIGIN")
        self.assertEqual(headers.get("X-XSS-Protection"), "1; mode=block")
        self.assertEqual(headers.get("Referrer-Policy"), "strict-origin-when-cross-origin")
        self.assertIn("Strict-Transport-Security", headers)

if __name__ == "__main__":
    unittest.main()
