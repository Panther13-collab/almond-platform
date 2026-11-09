import unittest
from bs4 import BeautifulSoup

class TestStep2AndMatchingLoader(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open("templates/index.html", "r", encoding="utf-8") as f:
            cls.html = f.read()
        cls.soup = BeautifulSoup(cls.html, "html.parser")

        with open("static/app.js", "r", encoding="utf-8") as f:
            cls.js = f.read()

    def test_quick_location_pills_markup(self):
        """Verify location suggestion pills in Step 2 have data-loc attributes and loc-preset-pill class"""
        pills_container = self.soup.find("div", {"id": "quickLocationPills"})
        self.assertIsNotNone(pills_container, "quickLocationPills container must exist")
        buttons = pills_container.find_all("button")
        self.assertGreaterEqual(len(buttons), 5, "At least 5 location pills must be present")

        expected_locs = ["Worldwide Remote", "All India", "Bengaluru", "Chennai", "United States", "Europe"]
        found_locs = [b.get("data-loc") for b in buttons if b.get("data-loc")]
        for loc in expected_locs:
            self.assertIn(loc, found_locs, f"Location pill '{loc}' must have data-loc attribute")
            self.assertTrue(any(f"addLocationPreset('{loc}')" in b.get("onclick", "") for b in buttons),
                            f"Location pill '{loc}' must call addLocationPreset('{loc}') on click")

    def test_work_arrangement_controls_markup(self):
        """Verify Work Arrangement options include All, Remote, Hybrid, Onsite"""
        work_mode_inputs = self.soup.find_all("input", {"name": "work_mode"})
        work_modes = [inp.get("value") for inp in work_mode_inputs]
        self.assertIn("all", work_modes)
        self.assertIn("remote", work_modes, "Work arrangement must include 'remote' option")
        self.assertIn("hybrid", work_modes)
        self.assertIn("onsite", work_modes)

    def test_contract_type_controls_markup(self):
        """Verify Contract Type options include all, full-time, contract"""
        emp_inputs = self.soup.find_all("input", {"name": "employment_type"})
        emp_types = [inp.get("value") for inp in emp_inputs]
        self.assertIn("all", emp_types)
        self.assertIn("full-time", emp_types)
        self.assertIn("contract", emp_types)

    def test_slide3_animated_loader_markup(self):
        """Verify Slide 3 jobsLoading includes founder reassurance and progress bar"""
        loader = self.soup.find("div", {"id": "jobsLoading"})
        self.assertIsNotNone(loader, "#jobsLoading must exist")
        
        # Must have progress bar elements
        progress_bar = self.soup.find("div", {"id": "loaderProgressBar"})
        self.assertIsNotNone(progress_bar, "#loaderProgressBar must exist")
        
        # Must have rotating quote element
        quote_el = self.soup.find("p", {"id": "loaderRotatingQuote"})
        self.assertIsNotNone(quote_el, "#loaderRotatingQuote must exist")
        
        # Verify inspiring founder copy keywords
        loader_text = loader.get_text()
        self.assertIn("best matching jobs", loader_text.lower())
        self.assertIn("wait for the best result", loader_text.lower())
        self.assertIn("broker", loader_text.lower())
        self.assertIn("hiring team", loader_text.lower())

    def test_js_add_location_preset_defined(self):
        """Verify window.addLocationPreset and window.updateQuickLocationPillsUI are implemented in app.js"""
        self.assertIn("window.addLocationPreset = function", self.js)
        self.assertIn("window.updateQuickLocationPillsUI = function", self.js)
        self.assertIn("window.renderActiveLocationTags", self.js)

    def test_js_salary_preset_and_work_controls(self):
        """Verify setSalaryPreset and work arrangement controls in app.js"""
        self.assertIn("window.setSalaryPreset = function", self.js)
        self.assertIn("initWorkArrangementControls", self.js)

    def test_js_animated_search_loader(self):
        """Verify startSearchLoader and stopSearchLoader cycle founder messages in app.js"""
        self.assertIn("function startSearchLoader()", self.js)
        self.assertIn("function stopSearchLoader()", self.js)
        self.assertIn("Bypassing 100% of brokers and middlemen", self.js)
        self.assertIn("landing you directly with internal hiring teams & HR", self.js)
        self.assertIn("window.goToSlide(3)", self.js)

if __name__ == "__main__":
    unittest.main()
