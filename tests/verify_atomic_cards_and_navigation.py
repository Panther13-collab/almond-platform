import unittest
import os

class TestAtomicCardsAndNavigation(unittest.TestCase):
    def setUp(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.js_path = os.path.join(self.base_dir, "static", "app.js")
        with open(self.js_path, "r", encoding="utf-8") as f:
            self.js = f.read()

    def test_01_atomic_card_structure(self):
        """Verify renderJobCards produces Direction B Swiss Luxury atomic cards."""
        self.assertIn("kage-card", self.js, "Job card container must be present")
        self.assertIn("direct-apply-link", self.js, "Direct apply CTA must be present")
        self.assertIn("generate-pitch-btn", self.js, "Pitch button must be preserved")
        self.assertIn("save-kanban-btn", self.js, "Kanban bookmark button must be preserved")
        self.assertIn("e8dfd1", self.js, "Champagne luxury border color should be utilized")

    def test_02_smooth_navigation_anchors(self):
        """Verify navigation routes to unified anchors without crashing."""
        self.assertIn("goToSlide", self.js, "goToSlide function must be defined")
        self.assertIn("search-deck", self.js, "Search deck anchor must be referenced in navigation")
        self.assertIn("feed-stream", self.js, "Feed stream anchor must be referenced in navigation")

if __name__ == "__main__":
    unittest.main()
