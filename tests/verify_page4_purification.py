import unittest
import os
import re

class TestPage4Purification(unittest.TestCase):
    def setUp(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.html_path = os.path.join(self.base_dir, "templates", "index.html")
        with open(self.html_path, "r", encoding="utf-8") as f:
            self.html = f.read()

        # Extract Page 4 Results Stream HTML
        p4_start = self.html.find('id="results-stream"')
        self.assertTrue(p4_start != -1, "id='results-stream' not found")
        footer_start = self.html.find('<footer id="bottomDirectoryFooter"')
        self.assertTrue(footer_start != -1, "footer not found")
        self.p4 = self.html[p4_start:footer_start]

        # Extract results scroll container cleanly up to its closing tag
        scroll_start = self.p4.find('id="resultsScrollContainer"')
        self.assertTrue(scroll_start != -1, "resultsScrollContainer not found")
        scroll_end = self.p4.find('<!-- /#resultsScrollContainer -->', scroll_start)
        if scroll_end == -1:
            scroll_end = self.p4.find('</div>', scroll_start + 500)
        self.scroll_chunk = self.p4[scroll_start:scroll_end]

    def test_01_no_about_section_inside_scroll_container(self):
        """Verify that the 500-word #aboutAlmondJobsSection is NOT inside the scrollable job results flow."""
        self.assertNotIn('id="aboutAlmondJobsSection"', self.scroll_chunk,
                         "aboutAlmondJobsSection should not be inside resultsScrollContainer")

    def test_02_crawlable_disambiguation_drawer_exists(self):
        """Verify that a docked crawlable entity disambiguation drawer exists outside the job cards flow."""
        self.assertIn('id="enterpriseEntityDrawer"', self.html,
                      "enterpriseEntityDrawer should exist for Googlebot & LLM crawlability")
        self.assertIn("almond farming", self.html.lower(),
                      "Entity disambiguation against almond farming must be preserved for SEO")
        self.assertIn("almond house", self.html.lower(),
                      "Disambiguation against Almond House sweets must be preserved for SEO")

    def test_03_no_duplicate_category_links_in_drawer(self):
        """Verify duplicate category links are not rendered in the drawer (retained in footer)."""
        drawer_start = self.html.find('id="enterpriseEntityDrawer"')
        self.assertTrue(drawer_start != -1, "Drawer not found")
        drawer_end = self.html.find('</details>', drawer_start)
        self.assertTrue(drawer_end != -1, "Drawer closing tag not found")
        drawer_content = self.html[drawer_start:drawer_end]

        # In-drawer should not duplicate the 18+ category hrefs like /it-jobs, /non-it-jobs
        category_links = re.findall(r'href="/(it-jobs|non-it-jobs|core-jobs|free-jobs)"', drawer_content)
        self.assertEqual(len(category_links), 0,
                         "Category links should not be duplicated inside the drawer (only in footer)")

if __name__ == "__main__":
    unittest.main()
