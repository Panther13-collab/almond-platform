import unittest
import time
import os
import sqlite3
from core.config import Config
from core.auth_db import (
    init_db, get_db, DB_PATH, signup_user, login_user,
    login_or_signup_google_user, grant_vip_to_email,
    is_user_paid, get_user_profile, verify_session_token,
    record_contribution_payment, add_admin_reply_to_contribution,
    get_recent_contributions, get_all_users_admin,
    supabase_admin, supabase_client
)

class TestRenderRestartDurability(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()

    def test_01_user_and_vip_durability_across_ephemeral_db_wipe(self):
        """
        Simulate a full Render container cold start / restart:
        1. User creates account and is granted VIP.
        2. SQLite DB is completely removed.
        3. A new empty DB is initialized (simulating fresh container).
        4. Authentication, VIP status, and session token must persist seamlessly via Supabase.
        """
        if not Config.is_supabase_configured():
            self.skipTest("Supabase not configured in test environment")

        test_email = f"durable_cand_{int(time.time())}@example.com"
        test_pwd = "SecurePassword2026!"
        test_name = "Durable Candidate"

        # 1. Sign up user
        signup_res = signup_user(test_email, test_pwd, test_name, device_model="Poco M2 Pro")
        self.assertEqual(signup_res["status"], "success")
        user_id = signup_res["user_id"]
        token = signup_res["token"]

        # 2. Grant VIP Pass (30 days)
        grant_res = grant_vip_to_email(test_email, duration_days=30, granted_by="Founder")
        self.assertEqual(grant_res["status"], "success")
        self.assertTrue(is_user_paid(user_id))

        # 3. Simulate Render Container Restart: Delete local SQLite database
        time.sleep(0.5)
        with get_db() as conn:
            conn.cursor().execute("DELETE FROM users;")
            conn.cursor().execute("DELETE FROM vip_grants;")
            conn.cursor().execute("DELETE FROM payments;")
            conn.commit()

        # Confirm SQLite is empty
        with get_db() as conn:
            self.assertEqual(conn.cursor().execute("SELECT count(*) FROM users;").fetchone()[0], 0)
            self.assertEqual(conn.cursor().execute("SELECT count(*) FROM vip_grants;").fetchone()[0], 0)

        # 4. Verify Password Login rehydrates user from Supabase and restores VIP
        login_res = login_user(test_email, test_pwd, device_model="Poco M2 Pro")
        self.assertEqual(login_res["status"], "success", f"Password login failed after Render restart: {login_res}")
        self.assertTrue(login_res["is_paid"], "VIP status must survive container restart!")
        self.assertEqual(login_res["plan"], "vip_pass_30d")

        # 5. Verify token verification rehydrates user
        verified = verify_session_token(token, email=test_email)
        self.assertIsNotNone(verified, "Session token must remain valid after Render restart!")
        self.assertTrue(verified["is_paid"], "Session token profile must have VIP active!")

        # 6. Verify is_user_paid works
        self.assertTrue(is_user_paid(user_id), "is_user_paid must return True after container restart!")
        self.assertTrue(is_user_paid(test_email), "is_user_paid by email must return True after container restart!")

        # Clean up Supabase user to keep test environment tidy
        try:
            sp_user = supabase_admin.auth.admin.list_users(page=1, per_page=1000)
            for u in sp_user:
                if (u.email or "").lower() == test_email:
                    supabase_admin.auth.admin.delete_user(u.id)
                    break
        except Exception:
            pass

    def test_02_google_user_vip_durability_across_db_wipe(self):
        """Verify Google Sign-In user with VIP does not get downgraded to free when SQLite is wiped."""
        if not Config.is_supabase_configured():
            self.skipTest("Supabase not configured in test environment")

        google_email = f"google_vip_{int(time.time())}@gmail.com"
        g_res = login_or_signup_google_user(google_email, full_name="Google VIP Candidate", device_model="Pixel 8")
        self.assertEqual(g_res["status"], "success")
        u_id = g_res["user_id"]

        # Grant 90-day VIP pass
        grant_vip_to_email(google_email, duration_days=90, granted_by="Admin")
        self.assertTrue(is_user_paid(google_email))

        # WIPE SQLite
        with get_db() as conn:
            conn.cursor().execute("DELETE FROM users;")
            conn.cursor().execute("DELETE FROM vip_grants;")
            conn.commit()

        # Google Sign-in again after Render restart
        g_login = login_or_signup_google_user(google_email, full_name="Google VIP Candidate", device_model="Pixel 8")
        self.assertEqual(g_login["status"], "success")
        self.assertTrue(g_login["is_paid"], "Google VIP user must retain VIP status after Render restart!")
        self.assertEqual(g_login["plan"], "vip_pass_90d")

        # Clean up
        try:
            sp_user = supabase_admin.auth.admin.list_users(page=1, per_page=1000)
            for u in sp_user:
                if (u.email or "").lower() == google_email:
                    supabase_admin.auth.admin.delete_user(u.id)
                    break
        except Exception:
            pass

    def test_03_contributions_and_replies_survive_db_wipe(self):
        """Verify supporter contributions and founder replies survive SQLite wiping and rehydrate from cloud."""
        if not Config.is_supabase_configured():
            self.skipTest("Supabase not configured in test environment")

        pay_id = f"dur_contrib_{int(time.time())}"
        record_contribution_payment(
            user_id="durable_supporter",
            payment_id=pay_id,
            order_id="ord_dur_1",
            amount_inr=500,
            plan_name="Coffee Contribution",
            supporter_name="Arjun Sharma",
            supporter_message="Thanks for building Almond Jobs!"
        )
        add_admin_reply_to_contribution(payment_id=pay_id, reply_text="Thanks Arjun! Really appreciate your support!")

        # WIPE SQLite payments table
        with get_db() as conn:
            conn.cursor().execute("DELETE FROM payments WHERE status = 'contribution';")
            conn.commit()

        # Verify get_recent_contributions rehydrates from cloud system_store
        items = get_recent_contributions(limit=10)
        matched = [i for i in items if i["id"] == pay_id or i.get("payment_id") == pay_id]
        self.assertGreater(len(matched), 0, "Contribution must survive Render container restart!")
        self.assertEqual(matched[0]["admin_reply"], "Thanks Arjun! Really appreciate your support!")

    def test_04_founder_account_ssmsp12_durability(self):
        """Verify founder account ssmsp12@gmail.com has durable active VIP status across container restarts."""
        founder_email = "ssmsp12@gmail.com"
        self.assertTrue(is_user_paid(founder_email), f"Founder account {founder_email} must be an active VIP!")
        prof = get_user_profile(founder_email)
        self.assertIsNotNone(prof)
        self.assertTrue(prof["is_paid"])
        self.assertEqual(prof["plan_tier"], "1m")

if __name__ == "__main__":
    unittest.main()
