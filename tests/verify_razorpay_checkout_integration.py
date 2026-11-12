import hashlib
import hmac
import os
import sys
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from core import payment
from core.config import Config


class TestRazorpayCheckoutIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_01_env_and_secret_hygiene(self):
        self.assertTrue(Config.is_razorpay_configured())
        self.assertTrue(Config.RAZORPAY_KEY_ID.startswith(("rzp_test_", "rzp_live_")))
        self.assertTrue(bool(Config.RAZORPAY_KEY_SECRET))

        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with open(os.path.join(base_dir, "templates", "index.html"), "r", encoding="utf-8") as f:
            html = f.read()
        with open(os.path.join(base_dir, "static", "app.js"), "r", encoding="utf-8") as f:
            js = f.read()

        self.assertIn("https://checkout.razorpay.com/v1/checkout.js", html)
        self.assertIn("https://checkout.razorpay.com/v1/checkout.js", js)
        self.assertIn("payment.failed", js)
        self.assertIn("ondismiss", js)
        self.assertNotIn(Config.RAZORPAY_KEY_SECRET, html)
        self.assertNotIn(Config.RAZORPAY_KEY_SECRET, js)
        self.assertNotIn("RAZORPAY_KEY_SECRET", html)
        self.assertNotIn("RAZORPAY_KEY_SECRET", js)

    def test_02_create_order_minimum_validation(self):
        for route in ("/api/payment/create-order", "/api/create-order"):
            res_low = self.client.post(route, json={"amount": 99, "currency": "INR"})
            self.assertEqual(res_low.status_code, 400)

            res_zero = self.client.post(route, json={"amount_inr": 0})
            self.assertEqual(res_zero.status_code, 400)

            res_bad = self.client.post(route, json={"amount": "not_a_number"})
            self.assertEqual(res_bad.status_code, 400)

    def test_03_create_order_live_and_error_mapping(self):
        # Successful order creation response contract (mocked when live key is active to avoid live test orders)
        class _SuccessOrder:
            @staticmethod
            def create(data=None):
                return {
                    "id": "order_MockVerified001",
                    "amount": data["amount"],
                    "currency": data["currency"],
                    "receipt": data["receipt"],
                }

        class _SuccessClient:
            order = _SuccessOrder()

        with patch.object(payment, "razorpay_client", _SuccessClient()):
            res = self.client.post("/api/create-order", json={"amount": 100, "currency": "INR", "receipt": "rcpt_unit_01"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "success")
        self.assertTrue(data["order_id"].startswith("order_"))
        self.assertEqual(data["amount"], 100)
        self.assertEqual(data["currency"], "INR")
        self.assertEqual(data["key_id"], Config.RAZORPAY_KEY_ID)
        self.assertNotIn("secret", str(data).lower())

        # Auth failure -> 401
        class _AuthFailOrder:
            @staticmethod
            def create(data=None):
                raise Exception("Authentication failed")

        class _AuthFailClient:
            order = _AuthFailOrder()

        with patch.object(payment, "razorpay_client", _AuthFailClient()):
            res_auth = self.client.post("/api/payment/create-order", json={"amount": 48500})
            self.assertEqual(res_auth.status_code, 401)

        # Generic Razorpay API failure -> 500
        class _ApiFailOrder:
            @staticmethod
            def create(data=None):
                raise Exception("Gateway timeout from Razorpay")

        class _ApiFailClient:
            order = _ApiFailOrder()

        with patch.object(payment, "razorpay_client", _ApiFailClient()):
            res_err = self.client.post("/api/payment/create-order", json={"amount": 48500})
            self.assertEqual(res_err.status_code, 500)

    def test_04_verify_payment_missing_fields_and_invalid_signature(self):
        for route in ("/api/payment/verify", "/api/verify-payment"):
            # Missing signature must fail with 400
            r_missing_sig = self.client.post(route, json={
                "order_id": "order_test_123",
                "payment_id": "pay_test_123",
            })
            self.assertEqual(r_missing_sig.status_code, 400)

            # Even order_sandbox_ prefix cannot bypass HMAC when Razorpay keys are configured
            r_bad_sig = self.client.post(route, json={
                "razorpay_order_id": "order_sandbox_forged",
                "razorpay_payment_id": "pay_test_123",
                "razorpay_signature": "forged_signature_hex",
            })
            self.assertEqual(r_bad_sig.status_code, 400)

    def test_05_verify_payment_valid_hmac_signature_both_payload_styles(self):
        order_id = "order_UnitTest001"
        payment_id = "pay_UnitTest001"
        msg = f"{order_id}|{payment_id}".encode("utf-8")
        valid_sig = hmac.new(
            Config.RAZORPAY_KEY_SECRET.encode("utf-8"),
            msg,
            hashlib.sha256,
        ).hexdigest()

        with patch("core.payment.record_successful_payment", return_value=True) as mock_rec:
            r1 = self.client.post("/api/payment/verify", json={
                "user_id": "usr_test_01",
                "order_id": order_id,
                "payment_id": payment_id,
                "signature": valid_sig,
                "amount_inr": 485,
                "plan_name": "Buy Almond Jobs 1 Coffee",
            })
            self.assertEqual(r1.status_code, 200)
            self.assertEqual(r1.json()["status"], "success")
            self.assertEqual(mock_rec.call_count, 1)

            r2 = self.client.post("/api/verify-payment", json={
                "razorpay_order_id": order_id,
                "razorpay_payment_id": payment_id,
                "razorpay_signature": valid_sig,
            })
            self.assertEqual(r2.status_code, 200)
            self.assertEqual(r2.json()["status"], "success")
            self.assertEqual(mock_rec.call_count, 2)


if __name__ == "__main__":
    unittest.main()
