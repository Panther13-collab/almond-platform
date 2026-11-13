import unittest
import os
import re

class TestExitIntentDismissal(unittest.TestCase):
    def setUp(self):
        self.app_js_path = os.path.join(os.path.dirname(__file__), "..", "static", "app.js")
        self.index_path = os.path.join(os.path.dirname(__file__), "..", "templates", "index.html")
        with open(self.app_js_path, "r", encoding="utf-8") as f:
            self.app_js = f.read()
        with open(self.index_path, "r", encoding="utf-8") as f:
            self.index_html = f.read()

    def test_01_razorpay_modal_ondismiss_calls_exit_intent(self):
        """Verify triggerRazorpayCheckout options.modal.ondismiss calls openPaymentExitIntent."""
        # Find triggerRazorpayCheckout in app.js
        self.assertIn("modal:", self.app_js)
        self.assertIn("ondismiss:", self.app_js)
        # Verify openPaymentExitIntent is called inside ondismiss
        ondismiss_match = re.search(r'ondismiss:\s*function\(\)\s*\{([\s\S]*?)\}', self.app_js)
        self.assertTrue(ondismiss_match, "modal.ondismiss function not found in app.js")
        body = ondismiss_match.group(1)
        self.assertIn("openPaymentExitIntent", body, "modal.ondismiss must call openPaymentExitIntent!")

    def test_02_exit_intent_copy_movie_ticket_and_dinner(self):
        """User explicitly commanded: 'movie ticket' for 1-month, 'dinner' for 3-month / 6-month, across all currencies."""
        self.assertIn("A Career Upgrade Costs Less Than a Movie Ticket", self.app_js)
        self.assertIn("Transform Your Career for the Price of Dinner", self.app_js)
        self.assertIn("price of a movie ticket", self.app_js)
        self.assertIn("price of a nice weekend dinner", self.app_js)

    def test_03_exit_intent_modal_elements_exist_in_html(self):
        """Ensure paymentExitIntentModal has all target elements in index.html."""
        modal_match = re.search(r'id=["\']paymentExitIntentModal["\'][\s\S]*?</div>\s*</div>\s*</div>', self.index_html)
        self.assertTrue(modal_match, "paymentExitIntentModal not found in index.html")
        modal = modal_match.group(0)
        self.assertIn('id="exitIntentTitle"', modal)
        self.assertIn('id="exitIntentMessage"', modal)
        self.assertIn('id="exitIntentPrice"', modal)
        self.assertIn('resumePaymentFromExitIntent', modal)

if __name__ == "__main__":
    unittest.main()
