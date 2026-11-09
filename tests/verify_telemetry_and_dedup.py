import unittest
import os

class TestTelemetryAndDedup(unittest.TestCase):
    def setUp(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.html_path = os.path.join(self.base_dir, "templates", "index.html")
        self.js_path = os.path.join(self.base_dir, "static", "app.js")
        with open(self.html_path, "r", encoding="utf-8") as f:
            self.html = f.read()
        with open(self.js_path, "r", encoding="utf-8") as f:
            self.js = f.read()

    def test_01_telemetry_ticker_in_header(self):
        """Verify real-time live telemetry ticker elements in header."""
        self.assertIn('id="liveTelemetryTicker"', self.html, "liveTelemetryTicker element must exist in header")
        self.assertIn('id="tickerFeedItem"', self.html, "tickerFeedItem element must exist")

    def test_02_telemetry_ticker_logic_in_app_js(self):
        """Verify telemetry ticker rotation logic in app.js."""
        self.assertIn("initTelemetryTicker", self.js, "initTelemetryTicker function must exist in app.js")
        self.assertIn("tickerFeedItem", self.js, "tickerFeedItem referenced in app.js")

    def test_03_footer_directory_integrity(self):
        """Verify bottom footer contains complete 4-column directory and official email."""
        self.assertIn('id="bottomDirectoryFooter"', self.html)
        self.assertIn("almondjobs.official@gmail.com", self.html)
        self.assertIn("/it-jobs", self.html)
        self.assertIn("/non-it-jobs", self.html)
        self.assertIn("/core-jobs", self.html)
        self.assertIn("/naukri-alternative", self.html)
        self.assertIn("/terms", self.html)
        self.assertIn("/privacy", self.html)
        self.assertIn("/contact", self.html)

if __name__ == "__main__":
    unittest.main()
