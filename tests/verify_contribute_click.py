import os
import sys
import time
import subprocess
from playwright.sync_api import sync_playwright

def verify():
    # Start app server on port 8009
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app:app", "--port", "8009", "--host", "127.0.0.1"],
        cwd=os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    time.sleep(3)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            page.goto("http://127.0.0.1:8009/", wait_until="networkidle")

            # Check that Contribute button exists
            contribute_btn = page.locator('button:has-text("Contribute")').first
            assert contribute_btn.is_visible(), "Contribute button is not visible"

            # Click Contribute button
            contribute_btn.click()
            page.wait_for_timeout(500)

            # Check modal is visible
            modal = page.locator("#vipPricingModal")
            assert modal.is_visible(), "Modal did not open after clicking Contribute"

            # Check heading text
            heading = page.locator('h3:has-text("Buy Almond Jobs a coffee")')
            assert heading.is_visible(), "Modal heading not found"

            # Select 3 coffees (data-count="3")
            pill_3 = page.locator('button.coffee-pill[data-count="3"]')
            pill_3.click()
            page.wait_for_timeout(300)

            amount_span = page.locator("#coffeeAmountDisplay")
            val = amount_span.text_content().strip()
            assert val == "1455", f"Expected amount 1455, got {val}"

            # Select 5 coffees (data-count="5")
            pill_5 = page.locator('button.coffee-pill[data-count="5"]')
            pill_5.click()
            page.wait_for_timeout(300)

            val5 = amount_span.text_content().strip()
            assert val5 == "2425", f"Expected amount 2425, got {val5}"

            # Take screenshot of open modal
            page.screenshot(path="tests/contribute_modal_verified.png")
            print("VERIFICATION_SUCCESS: Contribute button clicked, modal displayed, coffee multipliers dynamically updated to 1455 and 2425!")
            browser.close()
    finally:
        proc.terminate()
        proc.wait()

if __name__ == "__main__":
    verify()
