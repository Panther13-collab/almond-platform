import unittest
import os
import re

class TestFooterAndAuthHardening(unittest.TestCase):
    def setUp(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.index_html_path = os.path.join(self.base_dir, "templates", "index.html")
        self.app_js_path = os.path.join(self.base_dir, "static", "app.js")
        
        with open(self.index_html_path, "r", encoding="utf-8") as f:
            self.html = f.read()
        with open(self.app_js_path, "r", encoding="utf-8") as f:
            self.js = f.read()

    def test_directory_footer_docked_and_outside_scroll(self):
        # Verify nav/footer is OUTSIDE resultsScrollContainer
        pos_scroll_close = self.html.find('</div> <!-- /#resultsScrollContainer -->')
        pos_footer = self.html.find('id="bottomDirectoryFooter"')
        self.assertNotEqual(pos_scroll_close, -1)
        self.assertNotEqual(pos_footer, -1)
        self.assertGreater(pos_footer, pos_scroll_close, "Directory footer must be placed outside / after #resultsScrollContainer")

    def test_no_ats_words_in_directory(self):
        # Extract the footer section
        start = self.html.find('id="bottomDirectoryFooter"')
        end = self.html.find('</footer>', start)
        footer_content = self.html[start:end]
        
        self.assertNotIn("Direct ATS Infrastructure", footer_content)
        self.assertNotIn("Direct ATS Portals Ingestion", footer_content)
        self.assertNotIn("Direct company ATS application pipelines", footer_content)
        self.assertNotIn("ATS", footer_content)

    def test_no_monopoly_word_in_guarantees(self):
        start = self.html.find('id="bottomDirectoryFooter"')
        end = self.html.find('</footer>', start)
        footer_content = self.html[start:end]
        self.assertNotIn("Almond Monopoly Guarantees", footer_content)

    def test_no_column_count_numbers(self):
        start = self.html.find('id="bottomDirectoryFooter"')
        end = self.html.find('</footer>', start)
        footer_content = self.html[start:end]
        # Check that 11, 8, 8, 6 badge counts are removed
        self.assertNotIn('<span class="text-violet-600 font-mono">11</span>', footer_content)
        self.assertNotIn('<span class="text-indigo-600 font-mono">8</span>', footer_content)
        self.assertNotIn('<span class="text-emerald-600 font-mono">8</span>', footer_content)
        self.assertNotIn('<span class="text-rose-600 font-mono">6</span>', footer_content)

    def test_integrated_copyright_in_footer(self):
        start = self.html.find('id="bottomDirectoryFooter"')
        end = self.html.find('</footer>', start)
        footer_content = self.html[start:end]
        self.assertIn("2026 Almond Job", footer_content)
        self.assertIn("Direct Corporate Career Feeds. All rights reserved.", footer_content)
        self.assertIn("Terms of Service", footer_content)
        self.assertIn("Privacy Policy", footer_content)
        self.assertIn("Refund Policy", footer_content)
        
        # Verify old floating watermark pill is removed
        self.assertNotIn('class="absolute bottom-3 inset-x-0 z-20 flex items-center justify-center pointer-events-none', self.html)

    def test_google_auth_and_confirm_password(self):
        # Primary Google Auth button at top of auth modal
        self.assertIn('id="googleAuthBtn"', self.html)
        self.assertIn('href="/api/auth/google/login"', self.html)
        self.assertIn('Continue with Google', self.html)
        self.assertNotIn('(0 OTP)', self.html)
        
        # Confirm password input present
        self.assertIn('id="authConfirmPasswordInput"', self.html)
        self.assertIn('id="signupConfirmPasswordField"', self.html)

        # JS validates confirm password on signup
        self.assertIn('window.activeAuthTab === "signup"', self.js)
        self.assertIn('Passwords do not match. Please re-enter.', self.js)

if __name__ == "__main__":
    unittest.main()
