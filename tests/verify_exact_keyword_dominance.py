import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app import app

class TestExactKeywordDominance(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_01_homepage_meta_keywords(self):
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        html = res.text
        self.assertIn("almond jobs, Almond Jobs, almond job, Almond job", html)
        self.assertIn("Almond Jobs &bull; Find Every Direct Almond Job", html)
        self.assertIn("Official Almond Jobs Directory &amp; Almond Job Search", html)

    def test_02_almond_jobs_direct_page(self):
        res = self.client.get("/almond-jobs")
        self.assertEqual(res.status_code, 200)
        html = res.text
        self.assertIn("Almond Jobs — 3,315,000+ Verified Direct Enterprise Job Openings", html)
        self.assertIn("Almond Jobs Official Enterprise Career Directory", html)
        self.assertIn("0% Recruiter Spread", html)

    def test_03_almond_job_singular_page(self):
        res = self.client.get("/almond-job")
        self.assertEqual(res.status_code, 200)
        html = res.text
        self.assertIn("Almond Job Search — Find Every Direct Corporate Opening", html)
        self.assertIn("Find Your Next Almond Job Direct from Employer Infrastructure", html)

    def test_04_sitemap_categories_inclusion(self):
        res = self.client.get("/sitemap-categories.xml")
        self.assertEqual(res.status_code, 200)
        xml = res.text
        self.assertIn("https://almondjobs.com/jobs/almond-jobs", xml)
        self.assertIn("https://almondjobs.com/jobs/almond-job", xml)

if __name__ == "__main__":
    unittest.main()
