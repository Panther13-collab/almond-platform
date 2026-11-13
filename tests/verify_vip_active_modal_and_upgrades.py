import os
import sys
import unittest
import time
from unittest.mock import patch
from fastapi.testclient import TestClient

# Ensure platform root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import app
from core.auth_db import (
    get_db,
    init_db,
    signup_user,
    get_user_profile,
    record_successful_payment,
    is_user_paid
)
from core.config import Config
from core.payment import create_razorpay_order, verify_razorpay_signature


class TestVipActiveModalAndUpgrades(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        cls.client = TestClient(app)

    def setUp(self):
        self.test_email = f"vip_test_{int(time.time()*1000)}@example.com"
        reg = signup_user(self.test_email, "SecurePass123!", "VIP Test Candidate")
        self.user_id = reg["user_id"]
        self.token = reg["token"]

    def test_01_initial_state_is_unpaid(self):
        """Candidate starts with free plan and unpaid status."""
        self.assertFalse(is_user_paid(self.user_id))
        prof = get_user_profile(self.user_id)
        self.assertFalse(prof["is_paid"])
        self.assertEqual(prof.get("plan_tier"), "free")

    def test_02_activate_1month_vip_pass(self):
        """Activating 1-Month VIP pass grants 30 days and sets plan_tier to 1m."""
        now = time.time()
        ok = record_successful_payment(
            self.user_id,
            "pay_1m_test_123",
            "order_1m_test_123",
            699,
            "Almond Jobs 1-Month VIP Pass"
        )
        self.assertTrue(ok)
        self.assertTrue(is_user_paid(self.user_id))
        prof = get_user_profile(self.user_id)
        self.assertTrue(prof["is_paid"])
        self.assertEqual(prof.get("plan_tier"), "1m")
        self.assertGreaterEqual(prof["paid_until"], now + 29 * 86400)
        self.assertLessEqual(prof["paid_until"], now + 31 * 86400)

    def test_03_duration_stacking_on_upgrade_to_3month(self):
        """Upgrading to 3-Month Sprint stacks 90 days onto existing remaining validity."""
        now = time.time()
        # First buy 1 month
        record_successful_payment(self.user_id, "pay_1m", "ord_1m", 699, "Almond Jobs 1-Month VIP Pass")
        prof1 = get_user_profile(self.user_id)
        initial_paid_until = prof1["paid_until"]

        # Now upgrade to 3 months (90 days)
        record_successful_payment(self.user_id, "pay_3m", "ord_3m", 1799, "Almond Jobs 3-Month VIP Pass (Career Sprint)")
        prof2 = get_user_profile(self.user_id)
        self.assertTrue(prof2["is_paid"])
        self.assertEqual(prof2.get("plan_tier"), "3m")
        # Should stack 90 days on top of initial_paid_until
        expected_stacked = initial_paid_until + (90 * 86400)
        self.assertAlmostEqual(prof2["paid_until"], expected_stacked, delta=10)

    def test_04_upgrade_to_6month_dominance(self):
        """Upgrading to 6-Month Dominance sets plan_tier to 6m and stacks 180 days."""
        record_successful_payment(self.user_id, "pay_6m", "ord_6m", 2999, "Almond Jobs 6-Month VIP Pass (Career Dominance)")
        prof = get_user_profile(self.user_id)
        self.assertTrue(prof["is_paid"])
        self.assertEqual(prof.get("plan_tier"), "6m")
        self.assertGreaterEqual(prof["paid_until"], time.time() + 179 * 86400)

    def test_05_config_pricing_tiers(self):
        """Config has defined VIP tiers with currency parity and zero equivalent labels."""
        self.assertTrue(hasattr(Config, "VIP_TIERS"))
        tiers = Config.VIP_TIERS
        self.assertIn("1m", tiers)
        self.assertIn("3m", tiers)
        self.assertIn("6m", tiers)
        self.assertEqual(tiers["1m"]["INR"], 699)
        self.assertEqual(tiers["3m"]["INR"], 1799)
        self.assertEqual(tiers["6m"]["INR"], 2999)
        self.assertEqual(tiers["1m"]["USD"], 9.99)
        self.assertEqual(tiers["3m"]["USD"], 24.99)
        self.assertEqual(tiers["6m"]["USD"], 39.99)

    def test_06_api_me_returns_vip_tiers_and_plan_tier(self):
        """Endpoint /api/auth/me returns plan_tier, formatted date, and VIP tier map."""
        record_successful_payment(self.user_id, "pay_me_1m", "ord_me_1m", 699, "Almond Jobs 1-Month VIP Pass")
        resp = self.client.post("/api/auth/me", json={"token": self.token, "user_id": self.user_id, "email": self.test_email})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["is_paid"])
        self.assertEqual(data["plan_tier"], "1m")
        self.assertIn("vip_tiers", data)
        self.assertIn("3m", data["vip_tiers"])
        self.assertIn("6m", data["vip_tiers"])

    def test_07_index_html_has_dual_vip_views_and_upgrade_ui(self):
        """index.html contains both unpaid purchase view and active member view with upgrades and contribute CTA."""
        index_path = os.path.join(os.path.dirname(__file__), "..", "templates", "index.html")
        with open(index_path, "r", encoding="utf-8") as f:
            html = f.read()

        # Dual modal views
        self.assertIn('id="vipModalPurchaseView"', html)
        self.assertIn('id="vipModalActiveMemberView"', html)

        # Active member details
        self.assertIn('id="vipActiveMemberPlanBadge"', html)
        self.assertIn('id="vipActiveMemberPlanTitle"', html)
        self.assertIn('id="vipUpgradeSection"', html)
        self.assertIn('id="vipUpgradeCard_3m"', html)
        self.assertIn('id="vipUpgradeCard_6m"', html)
        self.assertIn('id="vipUpgradeCheckoutBtn"', html)

        # Active member contribute CTA
        self.assertIn('openContributeModal()', html)

        # Candidate profile active VIP section & contribute section
        self.assertIn('id="profileActiveVipSection"', html)
        self.assertIn('id="profileContributeSection"', html)


if __name__ == "__main__":
    unittest.main()
