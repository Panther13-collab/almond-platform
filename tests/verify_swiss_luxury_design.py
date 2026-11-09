import unittest
import os

class TestSwissLuxuryDesign(unittest.TestCase):
    def setUp(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.html_path = os.path.join(self.base_dir, "templates", "index.html")
        with open(self.html_path, "r", encoding="utf-8") as f:
            self.html = f.read()

    def test_01_swiss_luxury_palette_and_background(self):
        """Verify unified warm almond cream background (#faf8f5) and no dark green split SVG."""
        self.assertIn("#faf8f5", self.html.lower(), "Warm almond cream background #faf8f5 must be present")
        self.assertNotIn("rightGreenClip", self.html, "Old split green background SVG clip should be removed")
        self.assertNotIn("greenGlowTop", self.html, "Old green glow gradients should be removed")

    def test_02_fluid_modern_containers(self):
        """Verify unified modern sections: search deck, feed stream, drawer, and footer."""
        self.assertIn('id="hero"', self.html, "Hero section must exist")
        self.assertIn('id="search-deck"', self.html, "Unified search & CV deck must exist")
        self.assertIn('id="feed-stream"', self.html, "Live feed stream container must exist")
        self.assertIn('id="enterpriseEntityDrawer"', self.html, "Docked entity drawer must exist")
        self.assertIn('id="bottomDirectoryFooter"', self.html, "Footer directory must exist")

    def test_03_telemetry_ticker_and_proof_pills(self):
        """Verify real-time live telemetry ticker and core proof badges."""
        self.assertIn('id="liveTelemetryTicker"', self.html, "Live telemetry ticker must exist")
        self.assertIn('id="tickerFeedItem"', self.html, "Ticker feed item must exist")
        self.assertIn("3,315,258", self.html, "Live feed counter must be present")
        self.assertIn("0% Recruiter Spread", self.html, "Core guarantee must be present")

if __name__ == "__main__":
    unittest.main()
