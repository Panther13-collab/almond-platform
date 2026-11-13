import unittest
import os
import re

class TestAdminDashboardV2(unittest.TestCase):
    def setUp(self):
        self.admin_path = os.path.join(os.path.dirname(__file__), "..", "templates", "admin.html")
        with open(self.admin_path, "r", encoding="utf-8") as f:
            self.admin_html = f.read()

    def test_01_tabbed_navigation_structure(self):
        """Admin dashboard must feature 5 clear executive tabs."""
        self.assertIn("tab-btn-overview", self.admin_html)
        self.assertIn("tab-btn-pricing", self.admin_html)
        self.assertIn("tab-btn-candidates", self.admin_html)
        self.assertIn("tab-btn-grants", self.admin_html)
        self.assertIn("tab-btn-security", self.admin_html)

        self.assertIn('id="panel-overview"', self.admin_html)
        self.assertIn('id="panel-pricing"', self.admin_html)
        self.assertIn('id="panel-candidates"', self.admin_html)
        self.assertIn('id="panel-grants"', self.admin_html)
        self.assertIn('id="panel-security"', self.admin_html)

    def test_02_pricing_manager_individual_currency_inputs(self):
        """Pricing tab must have individual editable inputs for INR, USD, EUR, GBP for 1m, 3m, 6m."""
        self.assertIn('id="price_1m_inr"', self.admin_html)
        self.assertIn('id="price_1m_usd"', self.admin_html)
        self.assertIn('id="price_3m_inr"', self.admin_html)
        self.assertIn('id="orig_3m_inr"', self.admin_html)
        self.assertIn('id="price_6m_inr"', self.admin_html)
        self.assertIn('id="orig_6m_inr"', self.admin_html)

    def test_03_zero_mrp_in_admin_pricing(self):
        """No mention of 'MRP' in the pricing manager; use Original Price / Offer Price."""
        pricing_panel_match = re.search(r'id=["\']panel-pricing["\'][\s\S]*?id=["\']panel-candidates["\']', self.admin_html)
        self.assertTrue(pricing_panel_match, "panel-pricing not found")
        content = pricing_panel_match.group(0)
        self.assertNotIn("MRP", content, "The acronym 'MRP' must NOT appear in the admin pricing manager!")

    def test_04_js_tab_switching_function(self):
        """Must define switchAdminTab to seamlessly toggle panels."""
        self.assertIn("switchAdminTab", self.admin_html)

if __name__ == "__main__":
    unittest.main()
