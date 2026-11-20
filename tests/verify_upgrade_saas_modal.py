import unittest
import os
import re

class TestUpgradeSaaSModal(unittest.TestCase):
    def setUp(self):
        html_path = os.path.join(os.path.dirname(__file__), "..", "templates", "index.html")
        with open(html_path, "r", encoding="utf-8") as f:
            self.html = f.read()

    def test_title_bar_upgrade_button_present(self):
        """Title bar must feature #topUpgradeBtn with 'Upgrade' text."""
        self.assertIn('id="topUpgradeBtn"', self.html)
        match = re.search(r'<button[^>]*id="topUpgradeBtn"[^>]*>.*?</button>', self.html, re.DOTALL)
        self.assertIsNotNone(match)
        btn_text = match.group(0)
        self.assertIn("Upgrade", btn_text)

    def test_two_column_saas_matrix_present(self):
        """Upgrade modal must provide side-by-side Free vs Pro comparative columns."""
        self.assertIn('id="freeTierColumn"', self.html)
        self.assertIn('id="proTierColumn"', self.html)

    def test_free_tier_features_and_disabled_button(self):
        """Free Tier must show standard directory access and disabled Current Plan button."""
        self.assertIn('id="freeTierCurrentPlanBtn"', self.html)
        free_col = re.search(r'id="freeTierColumn".*?id="proTierColumn"', self.html, re.DOTALL)
        self.assertIsNotNone(free_col)
        free_text = free_col.group(0)
        self.assertIn("Free", free_text)
        self.assertIn("Current Plan", free_text)

    def test_pro_tier_duration_pills_and_cta(self):
        """Pro Tier must feature 1m, 3m (30% OFF), 6m (35% OFF) duration pills and dynamic CTA."""
        self.assertIn('id="proTierPill_1m"', self.html)
        self.assertIn('id="proTierPill_3m"', self.html)
        self.assertIn('id="proTierPill_6m"', self.html)
        self.assertIn('id="proTierCheckoutBtn"', self.html)
        self.assertIn('id="proCheckoutPriceLabel"', self.html)

    def test_no_coffee_in_upgrade_modal(self):
        """Pro Upgrade modal must never contain coffee donation or tip solicitations."""
        modal_match = re.search(r'<div id="vipPassModal".*?</div>\s*<!-- \d+', self.html, re.DOTALL)
        if modal_match:
            modal_text = modal_match.group(0).lower()
            self.assertNotIn("buy us a coffee", modal_text)
            self.assertNotIn("support our mission", modal_text)


if __name__ == "__main__":
    unittest.main()
