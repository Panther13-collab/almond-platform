import unittest
import os
import re

class TestWorkspaceStreamlining(unittest.TestCase):
    def setUp(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.html_path = os.path.join(self.base_dir, "templates", "index.html")
        with open(self.html_path, "r", encoding="utf-8") as f:
            self.html = f.read()

        # Extract Page 3 Workspace HTML
        start = self.html.find('id="workspace"')
        end = self.html.find('id="results-stream"')
        self.assertTrue(start != -1, "id='workspace' not found")
        self.assertTrue(end != -1, "id='results-stream' not found")
        self.p3 = self.html[start:end]

    def test_01_adaptive_cv_hub_structure(self):
        """Verify adaptive CV dropzone and vector container exist on Page 3."""
        self.assertIn('id="dropZone"', self.p3, "Drop zone container must exist")
        self.assertIn('id="resumeFileInput"', self.p3, "File input must exist")
        self.assertIn('id="parsedProfileSection"', self.p3, "Parsed profile vector section must exist")
        self.assertIn('id="profileSkillsBadges"', self.p3, "Skills badges container must exist")

    def test_02_no_misplaced_whoweare_in_skills(self):
        """Verify the misplaced 'Who We Are' button is removed from Page 3 skills card."""
        skills_idx = self.p3.find('id="parsedProfileSection"')
        self.assertTrue(skills_idx != -1)
        skills_chunk = self.p3[skills_idx:skills_idx+2000]
        self.assertNotIn("Who We Are", skills_chunk, "Misplaced Who We Are button must be removed from skills card")

    def test_03_salary_presets_and_no_redundant_slider(self):
        """Verify salary input has quick presets and no redundant slider."""
        self.assertIn('id="packageNumberInput"', self.p3, "Package number input must exist")
        self.assertIn('currency-tab', self.p3, "Currency selector tabs must exist")
        self.assertIn('salary-preset-btn', self.p3, "Salary quick preset buttons must exist")
        self.assertNotIn('id="packageRangeSlider"', self.p3, "Redundant range slider should be removed")

    def test_04_compact_layout_and_primary_action(self):
        """Verify search button and compact responsive container exist."""
        self.assertIn('id="searchJobsBtn"', self.p3, "Primary search button must exist")
        self.assertIn('id="locationSearchInput"', self.p3, "Location search input must exist")

if __name__ == "__main__":
    unittest.main()
