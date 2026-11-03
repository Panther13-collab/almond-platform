import os
import sys
import unittest

# Ensure platform is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.auth_db import (
    signup_user,
    login_user,
    is_user_paid,
    record_successful_payment,
    get_user_profile,
    verify_session_token,
    init_db
)

class TestAuthPersistence(unittest.TestCase):
    def setUp(self):
        init_db()

    def test_signup_and_login(self):
        import time
        test_email = f"candidate_{int(time.time()*1000)}@almond.ai"
        test_pass = "SecurePass123!"
        test_name = "Alex Test Founder"

        # 1. Sign up
        res = signup_user(test_email, test_pass, test_name)
        self.assertEqual(res.get("status"), "success")
        user_id = res.get("user_id")
        self.assertEqual(len(user_id), 36)
        self.assertEqual(res.get("email"), test_email)
        self.assertFalse(res.get("is_paid"))

        # 2. Duplicate signup should fail
        dup = signup_user(test_email, "differentPass", "Imposter")
        self.assertEqual(dup.get("status"), "error")

        # 3. Login with wrong password should fail
        bad_login = login_user(test_email, "wrongPass")
        self.assertEqual(bad_login.get("status"), "error")

        # 4. Login with correct password
        login_res = login_user(test_email, test_pass)
        self.assertEqual(login_res.get("status"), "success")
        self.assertEqual(login_res.get("user_id"), user_id)
        token = login_res.get("token")
        self.assertTrue(token is not None and len(token) > 10)

        # 5. Verify session token
        valid_user = verify_session_token(token)
        self.assertIsNotNone(valid_user)
        self.assertEqual(valid_user.get("id"), user_id)
        self.assertEqual(valid_user.get("email"), test_email)

        # 6. Check free tier initially
        self.assertFalse(is_user_paid(user_id))

        # 7. Record payment / Upgrade to VIP
        pay_res = record_successful_payment(user_id, "pay_test_9999", "order_test_8888", 699.0)
        self.assertTrue(pay_res)
        self.assertTrue(is_user_paid(user_id))

        # 8. Profile reflection
        profile = get_user_profile(user_id)
        self.assertTrue(profile.get("is_paid"))
        self.assertEqual(profile.get("plan"), "pro_inr_699")

if __name__ == "__main__":
    unittest.main()
