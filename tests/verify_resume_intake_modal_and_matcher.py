import unittest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.curated_feeds import matches_country_filter, omni_search_all_feeds

class TestResumeIntakeModalAndMatcher(unittest.TestCase):
    def setUp(self):
        index_path = os.path.join(os.path.dirname(__file__), "..", "templates", "index.html")
        with open(index_path, "r", encoding="utf-8") as f:
            self.index_html = f.read()

        js_path = os.path.join(os.path.dirname(__file__), "..", "static", "app.js")
        with open(js_path, "r", encoding="utf-8") as f:
            self.app_js = f.read()

    def test_01_composite_location_filtering(self):
        """matches_country_filter must correctly split composite locations like 'Remote / Bangalore'."""
        sample_item_blr = {"location": "Bengaluru, Karnataka, India", "locations_list": ["India"]}
        sample_item_remote = {"location": "Worldwide / Remote", "locations_list": ["Remote"]}
        sample_item_us = {"location": "Austin, TX, USA", "locations_list": ["United States"]}

        # "Remote / Bangalore" should match Bangalore job AND Remote job
        self.assertTrue(matches_country_filter(sample_item_blr, "Remote / Bangalore"))
        self.assertTrue(matches_country_filter(sample_item_remote, "Remote / Bangalore"))
        # But not purely US job if not remote
        self.assertFalse(matches_country_filter(sample_item_us, "Remote / Bangalore"))

        # India, Remote
        self.assertTrue(matches_country_filter(sample_item_blr, "India, Remote"))
        self.assertTrue(matches_country_filter(sample_item_remote, "India, Remote"))

    def test_02_multi_word_role_and_package_search_does_not_return_zero(self):
        """Searching multi-word roles like 'Senior Design Engineer' with 7 LPA must return matching jobs."""
        res = omni_search_all_feeds(query="Senior Design Engineer", min_package_lpa=7.0, limit=15)
        self.assertGreater(res["total"], 0, "Multi-word role search returned 0 results!")
        self.assertGreater(len(res["items"]), 0, "No items returned in page_slice!")

    def test_03_modal_html_contains_all_required_candidate_and_filter_fields(self):
        """index.html must contain Identified Candidate, Verified Experience, Derived Skills, Package Dropdown, Work Arrangement, and Contract Type."""
        # Identified Candidate & Experience
        self.assertIn("omniProfileName", self.index_html, "Missing omniProfileName in index.html")
        self.assertIn("omniProfileYoe", self.index_html, "Missing omniProfileYoe in index.html")

        # Derived Skills
        self.assertIn("omniSkillsBadgesContainer", self.index_html, "Missing omniSkillsBadgesContainer in index.html")
        self.assertIn("omniSkillsCountBadge", self.index_html, "Missing omniSkillsCountBadge in index.html")
        self.assertIn("omniAddSkillInput", self.index_html, "Missing omniAddSkillInput in index.html")

        # Minimum Expected Package Dropdown
        self.assertIn("omniCriteriaPackageSelect", self.index_html, "Missing omniCriteriaPackageSelect dropdown in index.html")
        self.assertIn('value="7"', self.index_html, "Dropdown missing 7 LPA option")
        self.assertIn('value="15"', self.index_html, "Dropdown missing 15 LPA option")
        self.assertIn('value="35"', self.index_html, "Dropdown missing 35 LPA option")

        # Location Typeahead & Preset Pills
        self.assertIn("omniCriteriaLocationInput", self.index_html, "Missing omniCriteriaLocationInput in index.html")
        self.assertIn("omniCriteriaLocationDropdown", self.index_html, "Missing omniCriteriaLocationDropdown in index.html")

        # Work Arrangement & Contract Type
        self.assertIn("omni_work_mode", self.index_html, "Missing omni_work_mode in index.html")
        self.assertIn("omni_contract_type", self.index_html, "Missing omni_contract_type in index.html")

    def test_04_app_js_populates_rich_profile_and_handles_skills(self):
        """app.js must define skill tag manipulation and populate candidate details on resume upload."""
        self.assertIn("renderOmniSkillBadges", self.app_js, "Missing renderOmniSkillBadges in static/app.js")
        self.assertIn("addOmniSkill", self.app_js, "Missing addOmniSkill in static/app.js")
        self.assertIn("removeOmniSkill", self.app_js, "Missing removeOmniSkill in static/app.js")
        self.assertIn("omniCriteriaPackageSelect", self.app_js, "app.js does not read omniCriteriaPackageSelect")

    def test_05_fallback_pipeline_prevents_zero_results_on_resume_intake(self):
        """Even with very strict filters, omni_search_all_feeds or fallback pipeline should never return 0 total jobs when feeds are populated."""
        res = omni_search_all_feeds(query="NonexistentSpecialtyRole9999", location="Mars", min_package_lpa=80.0, limit=15)
        # Fallback should kick in to provide recommended corporate jobs
        self.assertGreater(res["total"], 0, "Fallback failed to return corporate postings!")

    def test_06_work_mode_and_contract_type_filtering(self):
        """omni_search_all_feeds correctly processes work_mode and contract_type parameters."""
        res_remote = omni_search_all_feeds(query="Engineer", work_mode="remote", limit=10)
        self.assertGreater(res_remote["total"], 0)

        res_intern = omni_search_all_feeds(contract_type="internship", limit=10)
        self.assertGreater(res_intern["total"], 0)


if __name__ == "__main__":
    unittest.main()
