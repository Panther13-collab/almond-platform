import os
import sys
import unittest
import uuid
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import app
from core.config import Config
from core.auth_db import send_signup_otp, get_dynamic_pricing

class TestSignupEmailFallbackAndForeignPricing(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_01_smtp_unconfigured_returns_fallback_available(self):
        """When host SMTP credentials are empty, send_signup_otp gracefully offers fallback without blocking."""
        old_pass = Config.SMTP_PASS
        try:
            Config.SMTP_PASS = ""
            email = f"candidate_fallback_{uuid.uuid4().hex[:8]}@gmail.com"
            res = send_signup_otp(email)
            self.assertEqual(res["status"], "error")
            self.assertTrue(res.get("fallback_available"), "Expected fallback_available to be True when SMTP is unconfigured")
            self.assertEqual(res.get("error_code"), "EMAIL_DELIVERY_UNAVAILABLE")

            # Test API endpoint returns 200 with fallback signal so client never halts
            api_resp = self.client.post("/api/auth/send-otp", json={"email": email})
            self.assertEqual(api_resp.status_code, 200)
            data = api_resp.json()
            self.assertTrue(data.get("fallback_available"))
        finally:
            Config.SMTP_PASS = old_pass

    def test_02_direct_signup_endpoint_creates_candidate(self):
        """Direct signup endpoint /api/auth/signup works seamlessly without requiring OTP confirmation."""
        test_email = f"direct_cand_{uuid.uuid4().hex[:8]}@gmail.com"
        res = self.client.post("/api/auth/signup", json={
            "email": test_email,
            "password": "Password123!",
            "full_name": "Direct Tester",
            "device_model": "Test Browser"
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data.get("status"), "success")
        self.assertEqual(data.get("email"), test_email)
        self.assertTrue(bool(data.get("token")), "Expected session token in signup response")
        self.assertTrue(bool(data.get("user_id")), "Expected user_id in signup response")

    def test_03_foreign_pricing_matrix(self):
        """Verify optimized foreign pricing tiers reflect purchasing power parity."""
        self.assertEqual(Config.PRICE_USD, 19.99)
        self.assertEqual(Config.PRICE_EUR, 18.99)
        self.assertEqual(Config.PRICE_GBP, 15.99)

        tiers = Config.VIP_TIERS
        self.assertEqual(tiers["1m"]["USD"], 19.99)
        self.assertEqual(tiers["1m"]["EUR"], 18.99)
        self.assertEqual(tiers["1m"]["GBP"], 15.99)

        self.assertEqual(tiers["3m"]["USD"], 49.99)
        self.assertEqual(tiers["3m"]["EUR"], 46.99)
        self.assertEqual(tiers["3m"]["GBP"], 39.99)

        self.assertEqual(tiers["6m"]["USD"], 79.99)
        self.assertEqual(tiers["6m"]["EUR"], 74.99)
        self.assertEqual(tiers["6m"]["GBP"], 64.99)

        # Dynamic pricing table
        dyn_tiers = get_dynamic_pricing()
        self.assertGreaterEqual(dyn_tiers["1m"]["usd_price"], 19.99)
        self.assertGreaterEqual(dyn_tiers["3m"]["usd_price"], 49.99)
        self.assertGreaterEqual(dyn_tiers["6m"]["usd_price"], 79.99)

    def test_04_auth_context_notice_banner_removed(self):
        """Verify the 'Sign in to unlock your direct application pipeline' banner is completely removed from index.html."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        html = res.text
        self.assertNotIn('Sign in to Unlock Your Direct Application Pipeline', html)
        self.assertNotIn('Your parsed skills vector and compensation bounds are preserved', html)

if __name__ == "__main__":
    unittest.main()
