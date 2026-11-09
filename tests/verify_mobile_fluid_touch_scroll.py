import sys
import unittest
import time
import urllib.request
from playwright.sync_api import sync_playwright

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

def is_server_running(url="http://127.0.0.1:8000/"):
    try:
        urllib.request.urlopen(url, timeout=0.8)
        return True
    except Exception:
        return False

class TestMobileFluidTouchScroll(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not is_server_running():
            raise unittest.SkipTest("Local dev server not running at 127.0.0.1:8000")
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()

    def test_mobile_iphone13_scrolling(self):
        ctx = self.browser.new_context(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True)
        page = ctx.new_page()
        page.goto("http://127.0.0.1:8000/", wait_until="networkidle")
        time.sleep(0.5)

        # 1. No horizontal overflow
        html_scroll_w = page.evaluate("document.documentElement.scrollWidth")
        body_scroll_w = page.evaluate("document.body.scrollWidth")
        self.assertLessEqual(html_scroll_w, 390, f"HTML scroll width ({html_scroll_w}) > 390")
        self.assertLessEqual(body_scroll_w, 390, f"Body scroll width ({body_scroll_w}) > 390")

        # 2. Arbitrary midway scroll stop (free scrolling, no forced snap)
        total_h = page.evaluate("document.documentElement.scrollHeight")
        client_h = page.evaluate("document.documentElement.clientHeight")
        target_y = round(0.42 * (total_h - client_h))
        page.evaluate(f"window.scrollTo(0, {target_y})")
        time.sleep(0.2)
        actual_y = page.evaluate("window.scrollY || document.documentElement.scrollTop")
        self.assertAlmostEqual(actual_y, target_y, delta=2, msg="Page snapped or jumped during free scroll")

        ctx.close()

    def test_mobile_android_scrolling(self):
        ctx = self.browser.new_context(viewport={'width': 360, 'height': 800}, is_mobile=True, has_touch=True)
        page = ctx.new_page()
        page.goto("http://127.0.0.1:8000/", wait_until="networkidle")
        time.sleep(0.5)

        html_scroll_w = page.evaluate("document.documentElement.scrollWidth")
        body_scroll_w = page.evaluate("document.body.scrollWidth")
        self.assertLessEqual(html_scroll_w, 360, f"HTML scroll width ({html_scroll_w}) > 360")
        self.assertLessEqual(body_scroll_w, 360, f"Body scroll width ({body_scroll_w}) > 360")

        ctx.close()

if __name__ == "__main__":
    unittest.main()
