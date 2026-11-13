import unittest
import time
from starlette.testclient import TestClient
from app import app
from core.config import Config
from core.auth_db import (
    init_db, get_db, grant_vip_to_email, is_user_paid,
    record_successful_payment, add_admin_reply_to_contribution,
    get_recent_contributions, record_contribution_payment
)
from core.security import acquire_search_slot, release_search_slot, MAX_CONCURRENT_SEARCHES

class TestVipPersistenceAndReplies(unittest.TestCase):
    def setUp(self):
        init_db()
        self.client = TestClient(app)
        self.admin_key = Config.ADMIN_SECRET_KEY

    def test_01_one_rupee_test_payment_gives_full_month(self):
        """Verify that testing with 1 INR for a VIP pass does NOT give only 24 hours, but full 30 days."""
        uid = f"test_cand_1inr_{int(time.time())}"
        with get_db() as conn:
            conn.cursor().execute(
                "INSERT INTO users (id, email, password_hash, salt, full_name, created_at, updated_at) VALUES (?, ?, 'h', 's', 'Tester', ?, ?)",
                (uid, f"{uid}@example.com", time.time(), time.time())
            )
            conn.commit()

        # User pays 1 INR for Almond Jobs VIP Pass
        res = record_successful_payment(
            user_id=uid,
            payment_id=f"pay_1inr_{uid}",
            order_id=f"ord_1inr_{uid}",
            amount_inr=1.0,
            plan_name="Almond Jobs 1-Month VIP Pass"
        )
        self.assertTrue(res)

        # Check paid_until in users table: must be ~30 days (2592000s) from now, not 24 hours!
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT plan, paid_until FROM users WHERE id = ?", (uid,))
            row = cursor.fetchone()
            self.assertEqual(row["plan"], "vip_pass_30d")
            diff = row["paid_until"] - time.time()
            self.assertGreater(diff, 25 * 86400, "1 INR payment for VIP pass must grant 30 days, not 24h!")

        self.assertTrue(is_user_paid(uid))

    def test_02_vip_grant_persistence_across_multiple_checks(self):
        """Verify that granting VIP to an email persists and does not disappear."""
        test_email = f"director_{int(time.time())}@enterprise.org"
        res = grant_vip_to_email(test_email, duration_days=90, granted_by="Founder", notes="Executive Board")
        self.assertEqual(res["status"], "success")

        # Check by email directly
        self.assertTrue(is_user_paid(test_email))

        # Check 10 times consecutively (simulating page refreshes)
        for _ in range(10):
            self.assertTrue(is_user_paid(test_email), "VIP access must not disappear on refresh!")

    def test_03_admin_reply_to_supporter_contribution(self):
        """Verify founder can reply to a community contribution and see it reflected."""
        pay_id = f"pay_contrib_{int(time.time())}"
        record_contribution_payment(
            user_id="supporter_user_1",
            payment_id=pay_id,
            order_id="ord_contrib_1",
            amount_inr=485,
            plan_name="Buy Almond Jobs a coffee",
            supporter_name="Karthik R",
            supporter_message="Direct enterprise links saved me 40 hours of recruiter ghosting!"
        )

        # Post founder reply
        reply_res = add_admin_reply_to_contribution(
            payment_id=pay_id,
            reply_text="Thank you Karthik! So glad to hear you connected directly with engineering leadership!"
        )
        self.assertEqual(reply_res["status"], "success")

        # Fetch recent contributions and check reply
        items = get_recent_contributions(limit=5)
        matched = [i for i in items if i["id"] == pay_id or i.get("supporter_name") == "Karthik R"]
        self.assertGreater(len(matched), 0)
        self.assertEqual(matched[0]["admin_reply"], "Thank you Karthik! So glad to hear you connected directly with engineering leadership!")

    def test_04_concurrency_slots_increased(self):
        """Verify MAX_CONCURRENT_SEARCHES is expanded to comfortably handle high concurrent traffic."""
        self.assertGreaterEqual(MAX_CONCURRENT_SEARCHES, 20)

    def test_05_admin_reply_api_endpoint(self):
        """Verify POST /api/admin/reply-contribution requires key and saves reply."""
        pay_id = f"pay_api_{int(time.time())}"
        record_contribution_payment(
            user_id="supporter_api_user",
            payment_id=pay_id,
            order_id="ord_api_1",
            amount_inr=485,
            plan_name="Coffee Contribution",
            supporter_name="Sneha Patil",
            supporter_message="Best job platform ever!"
        )

        # Unauthorized attempt
        bad_res = self.client.post("/api/admin/reply-contribution", json={
            "payment_id": pay_id,
            "reply": "Thank you!",
            "key": "wrong_key"
        })
        self.assertEqual(bad_res.status_code, 401)

        # Authorized attempt
        good_res = self.client.post("/api/admin/reply-contribution", json={
            "payment_id": pay_id,
            "reply": "Thank you Sneha, wishing you all the best!",
            "key": self.admin_key
        })
        self.assertEqual(good_res.status_code, 200)
        data = good_res.json()
        self.assertEqual(data["status"], "success")

        # Verify in public feed API
        feed_res = self.client.get("/api/contributions/recent")
        self.assertEqual(feed_res.status_code, 200)
        items = feed_res.json().get("contributions", [])
        matched = [i for i in items if i.get("supporter_name") == "Sneha Patil"]
        self.assertGreater(len(matched), 0)
        self.assertEqual(matched[0]["admin_reply"], "Thank you Sneha, wishing you all the best!")

if __name__ == "__main__":
    unittest.main()
