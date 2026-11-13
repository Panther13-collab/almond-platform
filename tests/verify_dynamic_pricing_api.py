import unittest
import json
import time
from fastapi.testclient import TestClient
from app import app
from core.config import Config
from core.auth_db import get_db, init_db, get_dynamic_pricing, update_tier_pricing, record_successful_payment

class TestDynamicPricingApi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        cls.client = TestClient(app)
        cls.admin_key = Config.ADMIN_SECRET_KEY

    def test_01_public_pricing_endpoint_defaults(self):
        """Verify GET /api/pricing returns 1m, 3m, 6m with strike-through original prices and zero 'MRP' mentions."""
        resp = self.client.get("/api/pricing")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data.get("success", False))
        tiers = data.get("tiers", {})

        # Ensure all 3 tiers exist
        self.assertIn("1m", tiers)
        self.assertIn("3m", tiers)
        self.assertIn("6m", tiers)

        # Verify 1m tier
        t1m = tiers["1m"]
        self.assertEqual(t1m["inr_price"], 699)
        self.assertEqual(t1m["usd_price"], 9.99)
        self.assertEqual(t1m["duration_days"], 30)

        # Verify 3m tier: 30% discount
        t3m = tiers["3m"]
        self.assertEqual(t3m["inr_price"], 1799)
        self.assertEqual(t3m["inr_original"], 2599)
        self.assertEqual(t3m["discount_pct"], 30)
        self.assertIn("30%", t3m["discount_label"])

        # Verify 6m tier: 35% discount on 4299
        t6m = tiers["6m"]
        self.assertEqual(t6m["inr_price"], 2799)
        self.assertEqual(t6m["inr_original"], 4299)
        self.assertEqual(t6m["discount_pct"], 35)
        self.assertIn("35%", t6m["discount_label"])

        # Strict check: "MRP" must NOT be in JSON payload keys or labels
        raw_text = json.dumps(data)
        self.assertNotIn("MRP", raw_text)

    def test_02_admin_pricing_update_and_protection(self):
        """Verify POST /api/admin/pricing updates prices and does NOT alter existing VIP accounts' paid_until."""
        # 1. Setup a test VIP user with specific paid_until
        test_uid = "test_vip_pricing_safe_user"
        initial_paid_until = time.time() + (45 * 86400)
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users WHERE id = ?", (test_uid,))
            cursor.execute("""
                INSERT INTO users (id, email, password_hash, salt, is_paid, plan, paid_until, created_at, updated_at)
                VALUES (?, ?, 'hash', 'salt', 1, 'vip_pass_30d', ?, ?, ?)
            """, (test_uid, "pricing_safe@example.com", initial_paid_until, time.time(), time.time()))
            conn.commit()

        # 2. Update 3m festival price via admin API
        update_payload = {
            "tier_id": "3m",
            "inr_price": 1599,
            "inr_original": 2599,
            "usd_price": 21.99,
            "usd_original": 34.99,
            "eur_price": 21.99,
            "eur_original": 34.99,
            "gbp_price": 21.99,
            "gbp_original": 34.99,
            "discount_pct": 38,
            "discount_label": "38% OFF Festival Special",
            "badge_text": "Diwali Offer"
        }

        # Call with admin key header
        resp = self.client.post("/api/admin/pricing", json=update_payload, headers={"X-Admin-Key": self.admin_key})
        self.assertEqual(resp.status_code, 200)
        up_data = resp.json()
        self.assertTrue(up_data.get("success", False))

        # 3. Verify public GET /api/pricing reflects the update
        get_resp = self.client.get("/api/pricing")
        self.assertEqual(get_resp.status_code, 200)
        updated_tiers = get_resp.json().get("tiers", {})
        self.assertEqual(updated_tiers["3m"]["inr_price"], 1599)
        self.assertEqual(updated_tiers["3m"]["badge_text"], "Diwali Offer")

        # 4. CRITICAL: Verify existing user's paid_until remains completely untouched!
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT paid_until FROM users WHERE id = ?", (test_uid,))
            user_row = cursor.fetchone()
            self.assertIsNotNone(user_row)
            self.assertAlmostEqual(user_row["paid_until"], initial_paid_until, places=1)

        # 5. Restore default 3m price
        restore_payload = {
            "tier_id": "3m",
            "inr_price": 1799,
            "inr_original": 2599,
            "usd_price": 24.99,
            "usd_original": 34.99,
            "eur_price": 24.99,
            "eur_original": 34.99,
            "gbp_price": 24.99,
            "gbp_original": 34.99,
            "discount_pct": 30,
            "discount_label": "30% OFF Limited Offer",
            "badge_text": "Career Sprint"
        }
        self.client.post("/api/admin/pricing", json=restore_payload, headers={"X-Admin-Key": self.admin_key})

if __name__ == "__main__":
    unittest.main()
