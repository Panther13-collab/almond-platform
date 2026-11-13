import unittest
import os
import re

class TestVip3TierModal(unittest.TestCase):
    def setUp(self):
        self.index_path = os.path.join(os.path.dirname(__file__), "..", "templates", "index.html")
        self.app_js_path = os.path.join(os.path.dirname(__file__), "..", "static", "app.js")
        with open(self.index_path, "r", encoding="utf-8") as f:
            self.index_html = f.read()
        with open(self.app_js_path, "r", encoding="utf-8") as f:
            self.app_js = f.read()

    def test_01_no_mrp_in_modal_or_app(self):
        """User explicitly commanded: 'No need to mention it as MRP anywhere, that was the actual price. Look at how ChatGPT, Gemini, or Anthropic portray their cost'."""
        # Check inside vipPassModal section of index.html
        modal_match = re.search(r'id=["\']vipPassModal["\'][\s\S]*?id=["\']paymentExitIntentModal["\']', self.index_html)
        self.assertTrue(modal_match, "vipPassModal not found in index.html")
        modal_content = modal_match.group(0)
        self.assertNotIn("MRP", modal_content, "The acronym 'MRP' must NOT appear anywhere in the VIP modal!")

    def test_02_three_tier_purchase_cards_exist_for_unpaid(self):
        """Guests and unpaid candidates must see 1m, 3m (30% off), and 6m (35% off on 4299) in purchase view."""
        purchase_view_match = re.search(r'id=["\']vipModalPurchaseView["\'][\s\S]*?id=["\']vipModalActiveMemberView["\']', self.index_html)
        self.assertTrue(purchase_view_match, "vipModalPurchaseView not found")
        pv = purchase_view_match.group(0)

        # Check for card elements or identifiers for all 3 tiers
        self.assertIn("vipPurchaseCard_1m", pv)
        self.assertIn("vipPurchaseCard_3m", pv)
        self.assertIn("vipPurchaseCard_6m", pv)

        # Strikethrough classes for discounted tiers
        self.assertIn("line-through", pv, "Strikethrough base prices must be present for 3m and 6m!")
        self.assertIn("30%", pv, "30% off discount badge must be present for 3-month tier")
        self.assertIn("35%", pv, "35% off discount badge must be present for 6-month tier")

    def test_03_js_tier_selection_and_pricing_sync(self):
        """static/app.js must define selectVipPurchaseTier and sync dynamic pricing."""
        self.assertIn("selectVipPurchaseTier", self.app_js)
        self.assertIn("/api/pricing", self.app_js)

if __name__ == "__main__":
    unittest.main()
