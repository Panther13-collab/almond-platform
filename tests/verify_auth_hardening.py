import sys
import unittest
from core.auth_db import is_valid_candidate_email, send_signup_otp
from core.config import Config

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

class TestAuthHardening(unittest.TestCase):
    def test_dummy_and_disposable_emails_rejected(self):
        rejected_emails = [
            "aaaa@gmail.com",
            "bbbb@gmail.com",
            "1111@gmail.com",
            "test@gmail.com",
            "demo@gmail.com",
            "sample@gmail.com",
            "fake@gmail.com",
            "dummy@gmail.com",
            "temp@gmail.com",
            "asdf@gmail.com",
            "qwer@gmail.com",
            "user@mailinator.com",
            "user@tempmail.com",
            "user@10minutemail.com",
            "user@yopmail.com",
            "user@trashmail.com",
            "ab@gmail.com",
            "invalid_domain",
        ]
        for email in rejected_emails:
            valid, msg = is_valid_candidate_email(email)
            self.assertFalse(valid, f"Expected {email} to be rejected, but it passed!")

    def test_legitimate_emails_accepted(self):
        accepted_emails = [
            "almondjobs.official@gmail.com",
            "sridhar.engineer@gmail.com",
            "keerthana.sk@outlook.com",
            "developer@company.co",
            "contact@startup.ai",
        ]
        for email in accepted_emails:
            valid, msg = is_valid_candidate_email(email)
            self.assertTrue(valid, f"Expected {email} to be accepted, but got: {msg}")

    def test_send_signup_otp_rejects_dummy_without_leaking_code(self):
        res = send_signup_otp("aaaa@gmail.com")
        self.assertEqual(res["status"], "error")
        self.assertNotIn("dev_otp", res)
        self.assertNotIn("otp_code", res)

    def test_send_signup_otp_unconfigured_smtp_fails_safely(self):
        old_pass = Config.SMTP_PASS
        try:
            Config.SMTP_PASS = ""
            res = send_signup_otp("sridhar.engineer@gmail.com")
            self.assertEqual(res["status"], "error")
            self.assertNotIn("dev_otp", res)
            self.assertNotIn("otp_code", res)
        finally:
            Config.SMTP_PASS = old_pass

if __name__ == "__main__":
    unittest.main()
