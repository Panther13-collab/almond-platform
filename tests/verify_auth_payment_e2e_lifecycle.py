import os
import sys
import unittest
import time
import uuid
import secrets
import hmac
import hashlib

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app import app
from core.config import Config
from core.auth_db import (
    get_db, signup_user, login_user, login_or_signup_google_user,
    verify_session_token, get_user_profile, is_user_paid,
    grant_vip_to_email, grant_vip_to_user, revoke_vip_from_email,
    record_successful_payment, send_signup_otp, verify_otp_and_signup
)
from core.payment import _compute_expected_signature, verify_razorpay_signature

class TestAuthPaymentE2ELifecycle(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_01_otp_generation_verification_and_signup_flow(self):
        """End-to-End: OTP dispatch, verification, error states, and candidate account creation."""
        test_email = f"candidate_e2e_{secrets.token_hex(4)}@example.com"
        test_password = "SecurePassword123!"
        test_name = "Karthik Subramanian"

        # 1. Dispatch OTP
        with get_db() as conn:
            # Seed OTP code directly to simulate delivery
            otp_code = "789123"
            expires_at = time.time() + 600
            conn.cursor().execute(
                "INSERT OR REPLACE INTO email_otps (email, otp_code, expires_at, attempts) VALUES (?, ?, ?, 0)",
                (test_email, otp_code, expires_at)
            )
            conn.commit()

        # 2. Test wrong OTP submission
        res_wrong = self.client.post("/api/auth/verify-otp-and-signup", json={
            "email": test_email,
            "otp_code": "000000",
            "password": test_password,
            "full_name": test_name
        })
        self.assertEqual(res_wrong.status_code, 400)
        self.assertIn("Incorrect verification code", res_wrong.json()["detail"])

        # 3. Test correct OTP submission
        res_correct = self.client.post("/api/auth/verify-otp-and-signup", json={
            "email": test_email,
            "otp_code": otp_code,
            "password": test_password,
            "full_name": test_name,
            "device_model": "Chrome on Windows 11"
        })
        self.assertEqual(res_correct.status_code, 200)
        data = res_correct.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["email"], test_email)
        self.assertEqual(data["full_name"], test_name)
        self.assertIn("token", data)
        self.assertTrue(data["token"].startswith("alm."))
        self.assertFalse(data["is_paid"])

        # 4. Verify OTP record is deleted upon successful registration
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM email_otps WHERE email = ?", (test_email,))
            self.assertIsNone(cursor.fetchone())

    def test_02_password_authentication_and_wrong_password_security(self):
        """Verify candidate credentials authentication, PBKDF2 hashing, and incorrect password rejection."""
        test_email = f"login_test_{secrets.token_hex(4)}@example.com"
        correct_password = "MyStrongPassword2026!"
        wrong_password = "WrongPassword999!"

        # Create user
        signup_res = signup_user(test_email, correct_password, "Deepa Ramanathan", "Safari on macOS")
        self.assertEqual(signup_res["status"], "success")
        user_id = signup_res["user_id"]

        # 1. Attempt login with wrong password
        login_fail = self.client.post("/api/auth/login", json={
            "email": test_email,
            "password": wrong_password
        })
        self.assertEqual(login_fail.status_code, 401)
        self.assertIn("Incorrect password", login_fail.json()["detail"])

        # 2. Attempt login with non-existent email
        login_ghost = self.client.post("/api/auth/login", json={
            "email": f"ghost_{secrets.token_hex(4)}@nowhere.com",
            "password": correct_password
        })
        self.assertEqual(login_ghost.status_code, 401)
        self.assertIn("No account found", login_ghost.json()["detail"])

        # 3. Attempt login with correct password
        login_ok = self.client.post("/api/auth/login", json={
            "email": test_email,
            "password": correct_password,
            "device_model": "Firefox on Linux"
        })
        self.assertEqual(login_ok.status_code, 200)
        data = login_ok.json()
        self.assertEqual(data["user_id"], user_id)
        self.assertEqual(data["email"], test_email)
        self.assertTrue(data["token"].startswith("alm."))

    def test_03_cross_browser_multi_device_session_persistence(self):
        """Verify cross-device portability: logging in on Browser A and Browser B with independent session tokens."""
        test_email = f"multidevice_{secrets.token_hex(4)}@enterprise.org"
        password = "MultiDevicePass2026!"
        full_name = "Siddharth Verma"

        signup_user(test_email, password, full_name, "Desktop Chrome")

        # Device 1: Login on Windows Laptop
        dev1_res = login_user(test_email, password, device_model="Windows 11 Laptop")
        self.assertEqual(dev1_res["status"], "success")
        token_device_1 = dev1_res["token"]

        # Device 2: Login on Android Phone
        dev2_res = login_user(test_email, password, device_model="Samsung Galaxy S24")
        self.assertEqual(dev2_res["status"], "success")
        token_device_2 = dev2_res["token"]

        # Both tokens must be cryptographically valid
        me1 = self.client.post("/api/auth/me", json={"token": token_device_1})
        self.assertEqual(me1.status_code, 200)
        self.assertTrue(me1.json()["is_authenticated"])
        self.assertEqual(me1.json()["email"], test_email)

        me2 = self.client.post("/api/auth/me", json={"token": token_device_2})
        self.assertEqual(me2.status_code, 200)
        self.assertTrue(me2.json()["is_authenticated"])
        self.assertEqual(me2.json()["email"], test_email)

    def test_04_google_auth_account_creation_and_reconnection(self):
        """Verify 0-OTP Google Sign-In registration and returning authentication."""
        google_email = f"google_candidate_{secrets.token_hex(4)}@gmail.com"
        google_name = "Arun Natarajan"
        google_id = f"g_sub_{secrets.token_hex(8)}"

        # 1. New Google user onboarding
        g_signup = login_or_signup_google_user(google_email, full_name=google_name, google_id=google_id, device_model="Pixel 9 Pro")
        self.assertEqual(g_signup["status"], "success")
        self.assertEqual(g_signup["email"], google_email)
        self.assertEqual(g_signup["full_name"], google_name)
        user_id = g_signup["user_id"]

        # 2. Returning Google user login
        g_login = login_or_signup_google_user(google_email, full_name=google_name, google_id=google_id, device_model="Pixel 9 Pro")
        self.assertEqual(g_login["status"], "success")
        self.assertEqual(g_login["user_id"], user_id)

    def test_05_payment_verification_and_exact_duration_calculation(self):
        """Verify HMAC-SHA256 signature verification, exact 30d/90d/180d calculations, and VIP activation."""
        candidate_email = f"subscriber_{secrets.token_hex(4)}@techcorp.com"
        signup_res = signup_user(candidate_email, "TestPass123!", "Ananya Iyer")
        user_id = signup_res["user_id"]

        # 1. Test 1-Month Pass (30 Days = 720 Hours)
        now_before = time.time()
        order_1m = f"order_1m_{secrets.token_hex(4)}"
        pay_1m = f"pay_1m_{secrets.token_hex(4)}"
        sig_1m = _compute_expected_signature(order_1m, pay_1m, Config.RAZORPAY_KEY_SECRET)

        res_1m = verify_razorpay_signature(
            user_id=user_id,
            order_id=order_1m,
            payment_id=pay_1m,
            signature=sig_1m,
            amount_inr=699,
            plan_name="Almond Jobs VIP Pass (1-Month)",
            currency="INR",
            payer_email=candidate_email
        )
        self.assertEqual(res_1m["status"], "success")
        self.assertTrue(res_1m["is_paid"])

        prof_1m = get_user_profile(user_id)
        self.assertTrue(prof_1m["is_paid"])
        # Exactly 30 days from now
        self.assertAlmostEqual(prof_1m["paid_until"], now_before + (30 * 86400), delta=5)
        self.assertTrue(is_user_paid(user_id))

        # 2. Test 3-Month Sprint Pass (90 Days = 2,160 Hours) - Stacking onto active pass
        current_paid_until = prof_1m["paid_until"]
        order_3m = f"order_3m_{secrets.token_hex(4)}"
        pay_3m = f"pay_3m_{secrets.token_hex(4)}"
        sig_3m = _compute_expected_signature(order_3m, pay_3m, Config.RAZORPAY_KEY_SECRET)

        res_3m = verify_razorpay_signature(
            user_id=user_id,
            order_id=order_3m,
            payment_id=pay_3m,
            signature=sig_3m,
            amount_inr=1799,
            plan_name="Almond Jobs Career Sprint (3m)",
            currency="INR",
            payer_email=candidate_email
        )
        self.assertEqual(res_3m["status"], "success")
        prof_3m = get_user_profile(user_id)
        # Must seamlessly stack onto current expiration (+90 days)
        self.assertAlmostEqual(prof_3m["paid_until"], current_paid_until + (90 * 86400), delta=5)

    def test_06_guest_payment_then_signup_vip_inheritance(self):
        """Verify pre-approved VIP grant: candidate pays as guest first, then signs up later."""
        guest_email = f"guest_buyer_{secrets.token_hex(4)}@startup.ai"

        # Guest completes Razorpay checkout before creating an account
        order_id = f"order_guest_{secrets.token_hex(4)}"
        pay_id = f"pay_guest_{secrets.token_hex(4)}"
        sig = _compute_expected_signature(order_id, pay_id, Config.RAZORPAY_KEY_SECRET)

        res = verify_razorpay_signature(
            user_id="guest_visitor",
            order_id=order_id,
            payment_id=pay_id,
            signature=sig,
            amount_inr=1799,
            plan_name="Almond Jobs Career Sprint (3-Month)",
            currency="INR",
            payer_email=guest_email
        )
        self.assertEqual(res["status"], "success")

        # Now, guest registers an account with the same email
        reg_res = signup_user(guest_email, "AccountPass2026!", "Pre-Paid Candidate")
        self.assertEqual(reg_res["status"], "success")
        self.assertTrue(reg_res["is_paid"], "Newly registered user must inherit pre-paid VIP grant!")
        self.assertEqual(reg_res["plan"], "vip_pass_90d")

        # Verify profile
        user_id = reg_res["user_id"]
        self.assertTrue(is_user_paid(user_id))

    def test_07_subscription_expiration_and_automatic_demotion_to_free_tier(self):
        """Verify that when a subscription duration ends, account is automatically demoted to free tier."""
        test_email = f"expired_candidate_{secrets.token_hex(4)}@legacy.org"
        signup_res = signup_user(test_email, "Pass12345!", "Soon Expired")
        user_id = signup_res["user_id"]

        now = time.time()
        # Seed an expired VIP grant (expired 10 seconds ago)
        with get_db() as conn:
            conn.cursor().execute(
                "UPDATE users SET is_paid = 1, plan = 'vip_pass_30d', paid_until = ? WHERE id = ?",
                (now - 10, user_id)
            )
            conn.cursor().execute(
                "INSERT OR REPLACE INTO vip_grants (email, granted_by, granted_at, valid_until, status, notes) VALUES (?, 'test', ?, ?, 'active', 'test')",
                (test_email, now - 3600, now - 10)
            )
            conn.commit()

        # 1. is_user_paid check should detect expiration and demote
        paid_status = is_user_paid(user_id)
        self.assertFalse(paid_status, "Expired account must return False for is_user_paid")

        # 2. Database row must be updated to free tier
        prof = get_user_profile(user_id)
        self.assertFalse(prof["is_paid"])
        self.assertEqual(prof["plan_tier"], "free")

        # 3. /api/auth/me should return is_paid = False
        token = signup_res["token"]
        res_me = self.client.post("/api/auth/me", json={"token": token})
        self.assertEqual(res_me.status_code, 200)
        self.assertFalse(res_me.json()["is_paid"])

    def test_08_alias_grant_vip_to_user_backward_compatibility(self):
        """Verify grant_vip_to_user alias functions identically to grant_vip_to_email."""
        email = f"alias_test_{secrets.token_hex(4)}@domain.com"
        res = grant_vip_to_user(email, duration_days=30, granted_by="system_test")
        self.assertEqual(res["status"], "success")
        self.assertTrue(res["is_paid"])
        self.assertTrue(is_user_paid(email))

if __name__ == "__main__":
    unittest.main()
