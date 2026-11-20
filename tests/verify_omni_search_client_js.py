import unittest
import subprocess
import os

class TestOmniSearchClientJS(unittest.TestCase):
    def setUp(self):
        self.js_path = os.path.join(os.path.dirname(__file__), "..", "static", "app.js")
        with open(self.js_path, "r", encoding="utf-8") as f:
            self.js_content = f.read()

    def test_js_syntax_clean(self):
        """static/app.js must pass node syntax check without any errors."""
        res = subprocess.run(["node", "-c", self.js_path], capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"JS Syntax Error: {res.stderr}")

    def test_omni_search_functions_declared(self):
        """All omni-search controller functions must be defined in app.js."""
        expected_functions = [
            "handleOmniSearchInput",
            "clearOmniSearch",
            "triggerOmniResumeUpload",
            "handleOmniResumeSelected",
            "openOmniCriteriaModal",
            "closeOmniCriteriaModal",
            "submitOmniCriteria",
            "setOmniCategoryFilter",
            "loadMoreOmniResults"
        ]
        for fn in expected_functions:
            self.assertIn(fn, self.js_content, f"Function {fn} missing from static/app.js")

    def test_omni_search_abort_controller_present(self):
        """app.js must implement AbortController to cancel stale in-flight search requests."""
        self.assertIn("omniSearchAbortController", self.js_content, "Missing omniSearchAbortController in app.js")


if __name__ == "__main__":
    unittest.main()
