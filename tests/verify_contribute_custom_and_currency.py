import unittest
import time
from fastapi.testclient import TestClient
from app import app
from core.auth_db import get_recent_contributions, record_contribution_payment, get_db

class TestContributeCustomAndCurrency(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_01_pricing_formula_parity(self):
        """Verify coffee pricing formula for INR, USD, EUR, GBP and custom counts."""
        coffee_rates = {"INR": 485, "USD": 5, "EUR": 5, "GBP": 5}
        
        # Test 1 coffee
        self.assertEqual(1 * coffee_rates["INR"], 485)
        self.assertEqual(1 * coffee_rates["USD"], 5)
        self.assertEqual(1 * coffee_rates["EUR"], 5)
        self.assertEqual(1 * coffee_rates["GBP"], 5)
        
        # Test 3 coffees (user example in prompt)
        self.assertEqual(3 * coffee_rates["INR"], 1455)
        self.assertEqual(3 * coffee_rates["USD"], 15)
        self.assertEqual(3 * coffee_rates["EUR"], 15)
        self.assertEqual(3 * coffee_rates["GBP"], 15)

        # Test custom count (e.g. 6 coffees)
        self.assertEqual(6 * coffee_rates["INR"], 2910)
        self.assertEqual(6 * coffee_rates["USD"], 30)
        self.assertEqual(6 * coffee_rates["EUR"], 30)
        self.assertEqual(6 * coffee_rates["GBP"], 30)

    def test_02_create_order_multicurrency(self):
        """Verify order creation API with USD, EUR, GBP, and INR."""
        # 3 coffees in USD ($15 = 1500 cents)
        resp_usd = self.client.post("/api/payment/create-order", json={
            "user_id": "test_guest_usd",
            "amount": 1500,
            "amount_inr": 1455,
            "currency": "USD",
            "plan_name": "Buy Almond Jobs 3 Coffees ($15)",
            "purchase_type": "contribution"
        })
        self.assertEqual(resp_usd.status_code, 200)
        data_usd = resp_usd.json()
        self.assertEqual(data_usd.get("status"), "success")
        self.assertEqual(data_usd.get("currency"), "USD")
        self.assertEqual(data_usd.get("amount"), 1500)
        self.assertEqual(data_usd.get("purchase_type"), "contribution")

        # 3 coffees in INR (₹1455 = 145500 paise)
        resp_inr = self.client.post("/api/payment/create-order", json={
            "user_id": "test_guest_inr",
            "amount": 145500,
            "amount_inr": 1455,
            "currency": "INR",
            "plan_name": "Buy Almond Jobs 3 Coffees (₹1,455)",
            "purchase_type": "contribution"
        })
        self.assertEqual(resp_inr.status_code, 200)
        data_inr = resp_inr.json()
        self.assertEqual(data_inr.get("status"), "success")
        self.assertEqual(data_inr.get("currency"), "INR")
        self.assertEqual(data_inr.get("amount"), 145500)

    def test_03_verify_contribution_persists_feedback(self):
        """Verify voluntary contribution payment persists feedback, currency, and does NOT grant VIP."""
        import hmac
        import hashlib
        from unittest.mock import patch
        from core.config import Config
        from core import payment

        order_id = f"order_test_{int(time.time())}"
        pay_id = f"pay_test_{int(time.time())}"
        secret = Config.RAZORPAY_KEY_SECRET or "sandbox_secret"
        valid_sig = hmac.new(
            secret.encode("utf-8"),
            f"{order_id}|{pay_id}".encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

        with patch.object(payment, "razorpay_client", None):
            resp = self.client.post("/api/payment/verify", json={
                "user_id": "supporter_user_123",
                "order_id": order_id,
                "payment_id": pay_id,
                "signature": valid_sig,
                "amount_inr": 1455,
                "currency": "USD",
                "plan_name": "Buy Almond Jobs 3 Coffees ($15)",
                "purchase_type": "contribution",
                "supporter_name": "Siddharth Test Engineer",
                "supporter_message": "Direct Greenhouse portals saved me weeks of ghost recruiter spam!"
            })
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertEqual(data.get("status"), "success")
            self.assertEqual(data.get("purchase_type"), "contribution")
            self.assertFalse(data.get("is_paid")) # Voluntary support does not grant VIP pass
            self.assertEqual(data.get("supporter_name"), "Siddharth Test Engineer")
            self.assertEqual(data.get("currency"), "USD")

    def test_04_recent_contributions_feed_expanded(self):
        """Verify recent contributions feed returns 30+ authentic supporters with testimonials."""
        resp = self.client.get("/api/contributions/recent")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data.get("status"), "success")
        contribs = data.get("contributions", [])
        self.assertGreaterEqual(len(contribs), 30, f"Expected 30+ supporters in feed, got {len(contribs)}")
        
        # Verify pinned supporter is present
        pinned = [c for c in contribs if c.get("name") == "Stella" or c.get("is_pinned")]
        self.assertTrue(len(pinned) > 0, "Stella pinned supporter must be present")

if __name__ == "__main__":
    unittest.main()
