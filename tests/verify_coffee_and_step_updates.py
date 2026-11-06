import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app import app

class TestCoffeeAndStepUpdates(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.html = res.text

    def test_01_no_example_or_name_in_placeholders(self):
        """Verify no 'example', 'e.g.', or user name in any input placeholders."""
        self.assertNotIn("E.g. Sridhar_S_Resume.pdf", self.html)
        self.assertNotIn("e.g. Sridhar S", self.html)
        self.assertNotIn("e.g. name@gmail.com", self.html)
        self.assertNotIn("e.g. Chennai", self.html)
        self.assertNotIn("e.g. Flutter", self.html)
        self.assertIn("Drop your resume here or", self.html)
        self.assertIn("browse files", self.html)

    def test_02_step1_and_step2_labels_and_colors(self):
        """Verify Step 1 and Step 2 labels and dark forest green container on both."""
        self.assertIn("Step 1", self.html)
        self.assertIn("Candidate Profile", self.html)
        self.assertIn("Step 2", self.html)
        self.assertIn("Target Compensation &amp; Geography", self.html)
        
        # Verify Step 2 criteria deck adapted the deep green gradient of Step 1
        self.assertIn('linear-gradient(160deg, #112215 0%, #0a160d 100%)', self.html)
        self.assertIn('id="criteria-deck"', self.html)

    def test_03_contribute_button_and_coffee_modal(self):
        """Verify Contribute button in navbar and Buy Almond Jobs a Coffee modal."""
        # Navbar Contribute button
        self.assertIn("Contribute", self.html)
        self.assertIn("openContributeModal()", self.html)

        # Modal elements
        self.assertIn("Buy Almond Jobs a coffee", self.html)
        self.assertIn("1,188+ Supporters", self.html)
        self.assertIn("Support ₹", self.html)
        self.assertIn("coffeeAmountDisplay", self.html)
        self.assertIn("485", self.html)
        self.assertIn("coffeeSupporterName", self.html)
        self.assertIn("coffeeSupporterMessage", self.html)
        self.assertIn("selectCoffeeCount(1, 485)", self.html)
        self.assertIn("selectCoffeeCount(3, 1455)", self.html)
        self.assertIn("selectCoffeeCount(5, 2425)", self.html)
        self.assertIn("selectCoffeeCount(10, 4850)", self.html)

    def test_04_recent_supporters_testimonials(self):
        """Verify recent supporters testimonials section matching screenshots."""
        self.assertIn("Recent supporters", self.html)
        self.assertIn("Stella", self.html)
        self.assertIn("📌 Pinned", self.html)
        self.assertIn("Arun Karthik", self.html)
        self.assertIn("Priya S.", self.html)
        self.assertIn("Alex Tischenko", self.html)
        self.assertIn("Venkatesh R.", self.html)
        self.assertIn("Sneha Reddy", self.html)
        self.assertIn("Rahul Sharma", self.html)
        self.assertIn("Thanks Almond Jobs, I got my job!", self.html)
        self.assertIn("escaped from broker", self.html)

if __name__ == "__main__":
    unittest.main()
