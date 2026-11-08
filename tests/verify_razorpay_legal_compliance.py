import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app import app

class TestRazorpayLegalCompliance(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_01_terms_page(self):
        res = self.client.get("/terms")
        self.assertEqual(res.status_code, 200)
        self.assertIn("Terms of Service", res.text)
        self.assertIn("Razorpay", res.text)
        self.assertIn("Acceptance of Terms", res.text)

    def test_02_privacy_page(self):
        res = self.client.get("/privacy")
        self.assertEqual(res.status_code, 200)
        self.assertIn("Privacy Policy", res.text)
        self.assertIn("Zero Recruiter Selling", res.text)
        self.assertIn("Razorpay", res.text)

    def test_03_refund_policy_page(self):
        res = self.client.get("/refund-policy")
        self.assertEqual(res.status_code, 200)
        self.assertIn("Cancellation & Refund Policy", res.text)
        self.assertIn("7-Day Refund Policy", res.text)
        self.assertIn("support@almondjobs.com", res.text)

    def test_04_contact_page(self):
        res = self.client.get("/contact")
        self.assertEqual(res.status_code, 200)
        self.assertIn("Contact Us", res.text)
        self.assertIn("support@almondjobs.com", res.text)
        self.assertIn("Operating Entity", res.text)

    def test_05_footer_contains_all_links(self):
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        html = res.text
        self.assertIn('href="/terms"', html)
        self.assertIn('href="/privacy"', html)
        self.assertIn('href="/refund-policy"', html)
        self.assertIn('href="/contact"', html)

if __name__ == "__main__":
    unittest.main()
