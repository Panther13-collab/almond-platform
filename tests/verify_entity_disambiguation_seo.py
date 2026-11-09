import os
import sys
import unittest
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app import app, INDEXNOW_KEY

class TestEntityDisambiguationSEO(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_01_homepage_meta_and_entity_pill(self):
        """Verify homepage metadata and hero entity pill establishing Almond Jobs brand."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        html = res.text
        
        # Meta description contains explicit entity definition
        self.assertIn('Almond Jobs (almondjobs.com)', html)
        self.assertIn('official enterprise direct career portal', html)
        
        # Hero authority identity pill
        self.assertIn('Almond Jobs &bull; Find Every Direct Almond Job', html)
        
        # Semantic About & Disambiguation Section
        self.assertIn('id="aboutAlmondJobsSection"', html)
        self.assertTrue('About Almond Jobs &mdash; Active Enterprise Direct Career Platform' in html or 'About Almond Jobs &mdash; Active Enterprise Direct ATS Career Platform' in html)
        self.assertIn('Official Entity Disambiguation Notice', html)
        self.assertIn('Not Agricultural', html)
        self.assertIn('Completely unrelated to agricultural almond nut farming', html)

    def test_02_homepage_json_ld_schema(self):
        """Verify JSON-LD schema contains disambiguating descriptions and target FAQs."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        html = res.text

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        script = soup.find('script', type='application/ld+json')
        self.assertIsNotNone(script)
        
        data = json.loads(script.string)
        graph = data.get('@graph', [])
        types = [item.get('@type') for item in graph]
        self.assertIn('WebSite', types)
        self.assertIn('Organization', types)
        self.assertIn('WebApplication', types)
        self.assertIn('FAQPage', types)

        # Check disambiguatingDescription
        website = next(item for item in graph if item.get('@type') == 'WebSite')
        self.assertIn('completely unrelated to agricultural almond farming', website.get('disambiguatingDescription', ''))

        # Check FAQs
        faq = next(item for item in graph if item.get('@type') == 'FAQPage')
        questions = [q.get('name') for q in faq.get('mainEntity', [])]
        self.assertTrue(any('active and live job search portal' in q for q in questions))
        self.assertTrue(any('agricultural almond farming' in q for q in questions))

    def test_03_llms_txt_and_llms_full_disambiguation(self):
        """Verify llms.txt and llms-full.txt contain critical entity disambiguation notice."""
        res1 = self.client.get("/llms.txt")
        self.assertEqual(res1.status_code, 200)
        self.assertIn("CRITICAL ENTITY DISAMBIGUATION NOTICE", res1.text)
        self.assertIn("NOT AGRICULTURAL", res1.text)
        self.assertIn("NOT CYBERSECURITY AGENCY", res1.text)

        res2 = self.client.get("/llms-full.txt")
        self.assertEqual(res2.status_code, 200)
        self.assertIn("CRITICAL ENTITY DISAMBIGUATION NOTICE", res2.text)

    def test_04_programmatic_category_page_disambiguation(self):
        """Verify /jobs/{slug} renders structured data and anti-agricultural footer."""
        res = self.client.get("/jobs/software-engineer")
        self.assertEqual(res.status_code, 200)
        html = res.text
        self.assertIn("Almond Jobs (almondjobs.com)", html)
        self.assertIn("Not affiliated with agricultural farming", html)
        self.assertIn('"disambiguatingDescription"', html)

    def test_05_indexnow_key_endpoint(self):
        """Verify IndexNow endpoint serves the key for instant search engine verification."""
        res = self.client.get(f"/{INDEXNOW_KEY}.txt")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.text.strip(), INDEXNOW_KEY)

if __name__ == "__main__":
    unittest.main()
