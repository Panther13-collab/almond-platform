import os
import sys
import unittest
import re

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app import app
from core.config import Config

class TestCompleteTaxonomyAndEmail(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_01_single_official_email_enforcement(self):
        """Verify almondjobs.official@gmail.com is strictly used everywhere, with zero dummy emails."""
        endpoints = ["/privacy", "/refund-policy", "/contact", "/terms"]
        for ep in endpoints:
            res = self.client.get(ep)
            self.assertEqual(res.status_code, 200)
            self.assertIn("almondjobs.official@gmail.com", res.text)
            # Ensure no dummy emails exist
            self.assertNotIn("privacy@almondjobs.com", res.text)
            self.assertNotIn("support@almondjobs.com", res.text)
            self.assertNotIn("contact@almondjobs.com", res.text)
            self.assertNotIn("grievance@almondjobs.com", res.text)

    def test_02_new_high_intent_category_routes(self):
        """Verify each new category endpoint returns 200 with proper H1 and title."""
        categories = [
            ("it-jobs", "Direct IT & Information Technology Openings"),
            ("non-it-jobs", "Direct Non-IT & Corporate Management Openings"),
            ("core-jobs", "Direct Core Engineering Openings"),
            ("free-jobs", "100% Free Direct Application Job Portals"),
            ("high-paying-jobs", "Verified High-Paying & High CTC Career Openings"),
            ("no-mediator-jobs", "Direct Corporate Jobs Without Mediators or Agents"),
            ("no-consultancy-jobs", "Direct Company Hiring (Zero Consultancy Spread)"),
            ("naukri-alternative", "The Modern Alternative to Naukri for Direct Enterprise Careers"),
            ("smartrecruiters-direct-jobs", "Direct SmartRecruiters Corporate Career Feeds"),
            ("hot-jobs", "Urgent Hiring & Hot Corporate Job Openings"),
            ("temporary-jobs", "Temporary, Contract & Fast-Track Corporate Openings"),
            ("service-jobs", "Corporate Service & Technical Operations Openings"),
            ("career-jobs", "High-Growth Enterprise Career Openings"),
            ("linkedin-jobs-alternative", "The Direct Corporate Alternative to LinkedIn Jobs")
        ]

        for slug, expected_h1 in categories:
            res = self.client.get(f"/jobs/{slug}")
            self.assertEqual(res.status_code, 200, f"Failed for /jobs/{slug}")
            self.assertIn(expected_h1, res.text, f"H1 mismatch for /jobs/{slug}")
            self.assertIn("Almond Jobs", res.text)
            self.assertIn("0% Recruiter Spread", res.text)

    def test_03_convenience_root_aliases(self):
        """Verify convenience root aliases (e.g. /it-jobs, /no-mediator-jobs)."""
        aliases = [
            ("/it-jobs", "Direct IT & Information Technology Openings"),
            ("/non-it-jobs", "Direct Non-IT & Corporate Management Openings"),
            ("/core-jobs", "Direct Core Engineering Openings"),
            ("/free-jobs", "100% Free Direct Application Job Portals"),
            ("/high-paying-jobs", "Verified High-Paying & High CTC Career Openings"),
            ("/no-mediator-jobs", "Direct Corporate Jobs Without Mediators or Agents"),
            ("/naukri-alternative", "The Modern Alternative to Naukri"),
            ("/smartrecruiters-direct", "Direct SmartRecruiters Corporate Career Feeds")
        ]
        for path, expected_text in aliases:
            res = self.client.get(path)
            self.assertEqual(res.status_code, 200, f"Failed for alias {path}")
            self.assertIn(expected_text, res.text)

    def test_04_sitemap_categories_contain_all_new_hubs(self):
        """Verify sitemap-categories.xml includes all newly created hubs."""
        res = self.client.get("/sitemap-categories.xml")
        self.assertEqual(res.status_code, 200)
        xml = res.text
        for slug in ["it-jobs", "non-it-jobs", "core-jobs", "free-jobs", "high-paying-jobs", "no-mediator-jobs", "naukri-alternative", "smartrecruiters-direct-jobs"]:
            self.assertIn(f"https://almondjobs.com/jobs/{slug}", xml)

if __name__ == "__main__":
    unittest.main()
