import unittest
import os
import re

class TestHeroOmniSearchMarkup(unittest.TestCase):
    def setUp(self):
        html_path = os.path.join(os.path.dirname(__file__), "..", "templates", "index.html")
        with open(html_path, "r", encoding="utf-8") as f:
            self.html = f.read()

    def test_omni_search_bar_elements_present(self):
        """Unified omni-search input and resume upload triggers must exist in hero fold."""
        self.assertIn('id="omniSearchBarContainer"', self.html, "Missing #omniSearchBarContainer")
        self.assertIn('id="omniSearchInput"', self.html, "Missing #omniSearchInput")
        self.assertIn('id="omniClearBtn"', self.html, "Missing #omniClearBtn")
        self.assertIn('id="omniResumeUploadBtn"', self.html, "Missing #omniResumeUploadBtn")
        self.assertIn('id="omniResumeFileInput"', self.html, "Missing #omniResumeFileInput")

    def test_omni_search_results_container_present(self):
        """Results stream container must exist directly below search bar."""
        self.assertIn('id="omniSearchResultsContainer"', self.html, "Missing #omniSearchResultsContainer")
        self.assertIn('id="omniResultsCardsGrid"', self.html, "Missing #omniResultsCardsGrid")

    def test_criteria_modal_present(self):
        """Intake modal for target role, expected package, and location must exist."""
        self.assertIn('id="omniCriteriaModal"', self.html, "Missing #omniCriteriaModal")
        self.assertIn('id="omniCriteriaTargetRole"', self.html, "Missing #omniCriteriaTargetRole")
        self.assertIn('id="omniCriteriaExpectedPackage"', self.html, "Missing #omniCriteriaExpectedPackage")
        self.assertIn('id="omniCriteriaLocation"', self.html, "Missing #omniCriteriaLocation")
        self.assertIn('id="omniCriteriaSubmitBtn"', self.html, "Missing #omniCriteriaSubmitBtn")

    def test_removed_cluttered_hero_badges(self):
        """Hero fold must not contain cluttered badges or anti-broker slogans."""
        hero_match = re.search(r'<section id="hero".*?</section>', self.html, re.DOTALL)
        self.assertIsNotNone(hero_match, "Hero section not found")
        hero_html = hero_match.group(0)
        self.assertNotIn("NO BROKERS", hero_html)
        self.assertNotIn("NO MIDDLEMEN", hero_html)
        self.assertNotIn("NO DEAD POSTS", hero_html)
        self.assertNotIn("Freshers &amp; Campus Notice", hero_html)


if __name__ == "__main__":
    unittest.main()
