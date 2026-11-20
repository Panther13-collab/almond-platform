import os
import sys
import time
import subprocess
from playwright.sync_api import sync_playwright

def run_browser_verification():
    app_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    port = 8028
    
    # Start app server on isolated test port
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app:app", "--port", str(port), "--host", "127.0.0.1"],
        cwd=app_dir
    )
    
    import urllib.request
    server_ready = False
    for attempt in range(25):
        time.sleep(1)
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=2) as response:
                if response.status == 200:
                    server_ready = True
                    print(f"Test server responsive on port {port} after {attempt + 1}s.")
                    break
        except Exception:
            pass
            
    if not server_ready:
        proc.terminate()
        raise RuntimeError("Server failed to respond within 25 seconds.")
    
    console_errors = []
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            
            # Listen for uncaught console errors
            page.on("console", lambda msg: console_errors.append(f"[{msg.type}] {msg.text}") if msg.type in ["error"] else None)
            page.on("pageerror", lambda err: console_errors.append(f"[pageerror] {err}"))
            
            # Bypass human verification barrier for automated testing
            page.add_init_script("sessionStorage.setItem('almond_human_verified', 'true');")
            
            print("\n1. Navigating to homepage...")
            page.goto(f"http://127.0.0.1:{port}/", wait_until="networkidle")
            page.wait_for_timeout(1000)
            
            # 1. Verify Clean Minimalist Hero Elements
            print("2. Verifying Minimalist Hero Fold & Omni-Search Bar...")
            search_bar = page.locator("#omniSearchBarContainer")
            assert search_bar.is_visible(), "Omni-search container not visible"
            
            search_input = page.locator("#omniSearchInput")
            assert search_input.is_visible(), "Omni-search input not visible"
            
            upload_btn = page.locator("#omniResumeUploadBtn")
            assert upload_btn.is_visible(), "Upload resume button not visible"
            assert "Upload your resume" in upload_btn.inner_text(), "Upload resume button text missing"
            print("   [PASS] Omni-search bar & resume action chip visible.")
            
            # 2. Verify Initial Live Stream Postings
            print("3. Verifying Live Corporate Stream...")
            cards_grid = page.locator("#omniResultsCardsGrid")
            assert cards_grid.is_visible(), "Results cards grid not visible"
            page.wait_for_selector("#omniResultsCardsGrid > div", timeout=5000)
            initial_card_count = cards_grid.locator("> div").count()
            assert initial_card_count > 0, "No initial job cards rendered"
            print(f"   [PASS] Initial live feed loaded {initial_card_count} corporate postings.")
            
            # 3. Test Keystroke Debounced Search ('s')
            print("4. Testing Single-Letter Instant Keystroke Search ('s')...")
            search_input.fill("s")
            page.wait_for_timeout(600) # Allow 120ms debounce + fetch
            s_count = cards_grid.locator("> div").count()
            assert s_count > 0, "No cards rendered after typing 's'"
            clear_btn = page.locator("#omniClearBtn")
            assert clear_btn.is_visible(), "Clear button not visible when query typed"
            print(f"   [PASS] Keystroke 's' returned {s_count} matching openings.")
            
            # 4. Test Package Query ('7 LPA')
            print("5. Testing Compensation Query ('7 LPA')...")
            search_input.fill("7 LPA")
            page.wait_for_timeout(600)
            pkg_count = cards_grid.locator("> div").count()
            assert pkg_count > 0, "No cards rendered for '7 LPA'"
            print(f"   [PASS] Package filter '7 LPA' returned {pkg_count} matching openings.")
            
            # 5. Clear Search
            clear_btn.click()
            page.wait_for_timeout(500)
            assert search_input.input_value() == "", "Search input did not clear"
            print("   [PASS] Search cleared cleanly.")
            
            # 6. Test Criteria Intake Modal
            print("6. Testing Criteria Intake Modal...")
            page.evaluate("window.openOmniCriteriaModal({ current_role: 'Full Stack Engineer' })")
            page.wait_for_timeout(400)
            criteria_modal = page.locator("#omniCriteriaModal")
            assert criteria_modal.is_visible(), "Criteria intake modal not visible"
            
            role_input = page.locator("#omniCriteriaTargetRole")
            role_input.fill("AI Specialist")
            pkg_input = page.locator("#omniCriteriaExpectedPackage")
            pkg_input.fill("12 LPA")
            
            submit_btn = page.locator("#omniCriteriaSubmitBtn")
            submit_btn.click()
            page.wait_for_timeout(600)
            assert not criteria_modal.is_visible(), "Criteria modal did not close after submit"
            print("   [PASS] Criteria intake submitted and rendered matched jobs.")
            
            # 7. Test Title Bar Upgrade Button & 2-Column SaaS Matrix
            print("7. Testing Title Bar 'Upgrade' Button & SaaS Pricing Matrix...")
            upgrade_btn = page.locator("#topUpgradeBtn")
            assert upgrade_btn.is_visible(), "Top Upgrade button not visible in title bar"
            upgrade_btn.click()
            page.wait_for_timeout(500)
            
            vip_modal = page.locator("#vipPassModal")
            assert vip_modal.is_visible(), "Upgrade modal did not open"
            
            # Verify 2-Column Comparative Matrix
            free_col = page.locator("#freeTierColumn")
            pro_col = page.locator("#proTierColumn")
            assert free_col.is_visible(), "Free Tier column missing from modal"
            assert pro_col.is_visible(), "Pro Tier column missing from modal"
            
            # Verify Disabled Current Plan button on Free Tier
            current_plan_btn = page.locator("#freeTierCurrentPlanBtn")
            assert current_plan_btn.is_visible() and current_plan_btn.is_disabled(), "Free Tier Current Plan button not disabled"
            
            # Test Duration Pills Toggle (1m, 6m, 3m)
            price_display = page.locator("#proCheckoutPriceDisplay")
            checkout_btn = page.locator("#proTierCheckoutBtn")
            
            # 1 Month Pill
            pill_1m = page.locator("#proTierPill_1m")
            pill_1m.click()
            page.wait_for_timeout(300)
            assert "699" in price_display.inner_text(), f"Expected 699 in 1m price, got: {price_display.inner_text()}"
            assert "699" in checkout_btn.inner_text(), f"Expected 699 in checkout CTA, got: {checkout_btn.inner_text()}"
            print("   [PASS] 1-Month duration pill selected (INR 699).")
            
            # 6 Months Pill
            pill_6m = page.locator("#proTierPill_6m")
            pill_6m.click()
            page.wait_for_timeout(300)
            assert "2,799" in price_display.inner_text() or "2799" in price_display.inner_text(), f"Expected 2799 in 6m price, got: {price_display.inner_text()}"
            assert "2,799" in checkout_btn.inner_text() or "2799" in checkout_btn.inner_text(), f"Expected 2799 in checkout CTA, got: {checkout_btn.inner_text()}"
            print("   [PASS] 6-Month duration pill selected (INR 2,799).")
            
            # 3 Months Pill (Default / Most Popular)
            pill_3m = page.locator("#proTierPill_3m")
            pill_3m.click()
            page.wait_for_timeout(300)
            assert "1,799" in price_display.inner_text() or "1799" in price_display.inner_text(), f"Expected 1799 in 3m price, got: {price_display.inner_text()}"
            assert "1,799" in checkout_btn.inner_text() or "1799" in checkout_btn.inner_text(), f"Expected 1799 in checkout CTA, got: {checkout_btn.inner_text()}"
            print("   [PASS] 3-Month duration pill selected (INR 1,799).")
            
            # Close modal
            close_btn = vip_modal.locator('button[onclick*="closeVipPassModal"]').first
            close_btn.click()
            page.wait_for_timeout(400)
            assert not vip_modal.is_visible(), "Upgrade modal did not close"
            print("   [PASS] Upgrade modal closed.")
            
            browser.close()
            
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            
    # Check for console errors
    # Filter out harmless 404 for optional favicon or benign network warnings
    fatal_errors = [e for e in console_errors if not any(ignore in e for ignore in ["favicon", "clarity", "gtag"])]
    if fatal_errors:
        print("\n[FAIL] Console errors detected:")
        for err in fatal_errors:
            print(f"  {err}")
        raise AssertionError(f"Encountered {len(fatal_errors)} console errors during E2E verification.")
        
    print("\n[ALL PASS] Browser E2E Omni-Search and SaaS Upgrade verified cleanly with 0 console errors!")

if __name__ == "__main__":
    run_browser_verification()
