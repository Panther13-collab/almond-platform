import os
import unittest
from fastapi.testclient import TestClient

from app import app


class TestBotHoldValidation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_api_verify_human_valid_timing(self):
        """Test that a legitimate human hold duration succeeds and issues session verification cookie."""
        resp = self.client.post("/api/security/verify-human", json={"hold_duration_ms": 1950})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data.get("status"), "success")
        self.assertTrue(data.get("verified"))
        # Verify session cookie was set
        self.assertIn("almond_human_verified", resp.cookies)
        self.assertEqual(resp.cookies["almond_human_verified"], "1")

    def test_api_verify_human_empty_payload(self):
        """Test that a default validation beacon succeeds and issues session cookie."""
        resp = self.client.post("/api/security/verify-human", json={})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data.get("status"), "success")
        self.assertTrue(data.get("verified"))

    def test_api_verify_human_rejects_too_fast_bot(self):
        """Test that automated bots clicking instantly (< 800ms) are rejected."""
        resp = self.client.post("/api/security/verify-human", json={"hold_duration_ms": 250})
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Invalid verification telemetry duration", resp.json().get("detail", ""))

    def test_api_verify_human_rejects_held_too_long_bot(self):
        """Test that sticky bots holding indefinitely (> 5000ms) are rejected."""
        resp = self.client.post("/api/security/verify-human", json={"hold_duration_ms": 8500})
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Invalid verification telemetry duration", resp.json().get("detail", ""))

    def test_api_verify_human_rejects_malformed_input(self):
        """Test that non-numeric telemetry values are safely rejected with 400."""
        resp = self.client.post("/api/security/verify-human", json={"hold_duration_ms": "not-a-number"})
        self.assertEqual(resp.status_code, 400)

    def test_api_verify_human_checkbox(self):
        """Test that simple one-click checkbox verification succeeds and sets verification cookie."""
        resp = self.client.post("/api/security/verify-human", json={"check_method": "checkbox"})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data.get("status"), "success")
        self.assertTrue(data.get("verified"))
        self.assertEqual(resp.cookies.get("almond_human_verified"), "1")

    def test_html_modal_and_session_bootstrap(self):
        """Test that index.html contains the simple tick-box human check and session bootstrap script."""
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        html_path = os.path.join(base_dir, "templates", "index.html")
        with open(html_path, "r", encoding="utf-8") as f:
            html = f.read()

        self.assertIn('id="humanVerifyModal"', html)
        self.assertIn('id="humanTickCheckbox"', html)
        self.assertIn('id="holdVerifyBtn"', html)
        self.assertIn('id="holdVerifySuccessIcon"', html)
        self.assertIn('id="holdVerifyBtnText"', html)
        self.assertIn('id="holdVerifyHint"', html)
        self.assertIn('z-[99999]', html)
        self.assertIn('sessionStorage.getItem("almond_human_verified")', html)

    def test_js_checkbox_logic_and_session_persistence(self):
        """Test that static/app.js contains simple checkbox verification, session check, and verify-human call."""
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        js_path = os.path.join(base_dir, "static", "app.js")
        with open(js_path, "r", encoding="utf-8") as f:
            js = f.read()

        self.assertIn('function isHumanVerified()', js)
        self.assertIn('sessionStorage.getItem("almond_human_verified") === "true"', js)
        self.assertIn('humanTickCheckbox', js)
        self.assertIn('check_method: "checkbox"', js)
        self.assertIn('sessionStorage.setItem("almond_human_verified", "true")', js)
        self.assertIn('/api/security/verify-human', js)
        self.assertIn('Human Verified', js)


if __name__ == "__main__":
    unittest.main()
