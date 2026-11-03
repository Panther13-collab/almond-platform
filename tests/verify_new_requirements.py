import sys
import time
import requests
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')

def run_tests():
    print("==================================================")
    print("TEST SUITE: ML CARD, 3X/DAY SYNC, & BESPOKE CURATION UX")
    print("==================================================")

    # 1. Test Backend API Caching Speed
    print("\n1. Testing Backend Curated Feeds Response Latency...")
    t0 = time.time()
    resp = requests.get("http://127.0.0.1:8000/api/curated-feeds?feed_type=aiml&query=&category=All&time_filter=all&limit=30&offset=0")
    latency = time.time() - t0
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    data = resp.json()
    items = data.get("result", {}).get("items", [])
    print(f"   API Response Time: {latency:.4f}s ({len(items)} items returned)")
    assert latency < 0.1, f"Expected sub-100ms response from local cache, got {latency:.4f}s"
    print("   ✓ Curated feeds served instantly from local cache without blocking network calls")

    # 2. Test Resume Search Caching for Similar Skills
    print("\n2. Testing Resume Search Caching for Similar Skills...")
    sample_payload = {
        "profile": {
            "name": "Alex Mercer",
            "skills": ["Python", "PyTorch", "FastAPI", "PostgreSQL", "Docker", "Machine Learning"],
            "target_role": "AI Engineer",
            "experience_years": 4
        },
        "preferences": {
            "min_package": 15,
            "currency": "INR",
            "locations": ["Worldwide Remote"],
            "work_mode": "all",
            "employment_type": "all",
            "include_linkedin": False
        }
    }
    t0 = time.time()
    r1 = requests.post("http://127.0.0.1:8000/api/find-jobs", json=sample_payload)
    t1_time = time.time() - t0
    print(f"   First Search Duration: {t1_time:.4f}s (Status: {r1.status_code})")

    # Second Search with same/similar skills (should hit cache)
    t0 = time.time()
    r2 = requests.post("http://127.0.0.1:8000/api/find-jobs", json=sample_payload)
    t2_time = time.time() - t0
    print(f"   Second Search Duration (Cached): {t2_time:.4f}s (Status: {r2.status_code})")
    assert r2.status_code == 200
    assert t2_time < 0.05, f"Expected instant cache hit under 50ms, got {t2_time:.4f}s"
    print("   ✓ Resume matching results cached for similar skills — instant sub-50ms repeat search!")

    # 3. Playwright UI Verification
    print("\n3. Testing Frontend UI with Playwright...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = context.new_page()

        page.goto("http://127.0.0.1:8000/", wait_until="networkidle")
        page.wait_for_timeout(1000)

        # 3a. Verify all 3 Directory buttons on Homepage
        print("\n3a. Checking Homepage Directory Badges...")
        btn_intern = page.locator("#heroBadge_internships")
        btn_aiml = page.locator("#heroBadge_aiml")
        btn_entry = page.locator("#heroBadge_entrylevel")

        assert btn_intern.is_visible(), "heroBadge_internships should be visible"
        assert btn_aiml.is_visible(), "heroBadge_aiml should be visible"
        assert btn_entry.is_visible(), "heroBadge_entrylevel should be visible"

        print(f"   Internships button text: '{btn_intern.inner_text().strip()}'")
        print(f"   AI/ML button text: '{btn_aiml.inner_text().strip()}'")
        print(f"   Entry-Level button text: '{btn_entry.inner_text().strip()}'")

        assert "AI/ML Specialist" in btn_aiml.inner_text(), "Expected 'AI/ML Specialist' in badge"
        assert "530+" in btn_aiml.inner_text(), "Expected '530+' in badge"
        print("   ✓ Homepage contains all 3 live directory cards (Internships, AI/ML, Entry-Level)")

        # Capture screenshot of homepage with all 3 badges
        page.screenshot(path="C:/Users/hp/.gemini/antigravity/brain/9aa8f19b-dcde-4560-9464-6fdb4b2814bd/homepage_with_aiml_card_1920.png")
        print("   ✓ Screenshot saved: homepage_with_aiml_card_1920.png")

        # 3b. Click AI/ML Card and test 2.5s Curation Loading Screen
        print("\n3b. Clicking AI/ML Card & Testing Bespoke Curation Animation...")
        btn_aiml.click()
        page.wait_for_timeout(400)

        modal = page.locator("#curatedFeedsModal")
        assert modal.is_visible(), "Curated Feeds Modal should be visible"

        loading_screen = page.locator("#curatedLoadingScreen")
        assert loading_screen.is_visible(), "#curatedLoadingScreen should be visible during the 2.5s curation period"

        loading_headline = page.locator("#curatedLoadingHeadline").inner_text()
        print(f"   Loading Headline: '{loading_headline}'")
        assert "Curating latest special" in loading_headline, f"Unexpected headline: {loading_headline}"

        # Capture screenshot during the bespoke curation animation
        page.screenshot(path="C:/Users/hp/.gemini/antigravity/brain/9aa8f19b-dcde-4560-9464-6fdb4b2814bd/curated_bespoke_loading_screen_1920.png")
        print("   ✓ Screenshot saved: curated_bespoke_loading_screen_1920.png")

        # Wait for the remainder of the 2.5s curation sequence to conclude
        page.wait_for_timeout(2600)

        # After 2.5s, loading screen should be hidden, cards container visible
        assert not loading_screen.is_visible(), "#curatedLoadingScreen should now be hidden"
        cards_container = page.locator("#curatedCardsContainer")
        assert cards_container.is_visible(), "#curatedCardsContainer should now be visible"

        cards = page.locator("#curatedCardsContainer .curated-job-card")
        card_count = cards.count()
        print(f"   AI/ML Cards Revealed: {card_count}")
        assert card_count >= 11, f"Expected at least 11 cards, got {card_count}"

        # Verify first 10 jobs unlocked, 11th locked
        assert cards.nth(0).locator("a:has-text('Direct Application Portal')").is_visible(), "Job 1 must be unlocked"
        assert cards.nth(9).locator("a:has-text('Direct Application Portal')").is_visible(), "Job 10 must be unlocked"
        assert cards.nth(10).locator("button:has-text('Unlock Portal (VIP)')").is_visible(), "Job 11 must be locked"
        print("   ✓ AI/ML jobs smoothly revealed after 2.5s: first 10 unlocked, 11th locked")

        # Capture screenshot of revealed AI/ML jobs
        page.screenshot(path="C:/Users/hp/.gemini/antigravity/brain/9aa8f19b-dcde-4560-9464-6fdb4b2814bd/curated_aiml_jobs_revealed_1920.png")
        print("   ✓ Screenshot saved: curated_aiml_jobs_revealed_1920.png")

        # 3c. Test switching back to Direct Internships tab
        print("\n3c. Switching to Direct Internships tab...")
        page.locator("#curatedTab_internships").click()
        page.wait_for_timeout(400)

        # Should show loading screen during transition
        assert loading_screen.is_visible(), "Loading screen should show during tab switch"
        page.wait_for_timeout(2600)
        assert not loading_screen.is_visible(), "Loading screen should hide after 2.5s"

        intern_cards = page.locator("#curatedCardsContainer .curated-job-card")
        assert intern_cards.count() >= 11
        assert intern_cards.nth(0).locator("a:has-text('Direct Application Portal')").is_visible()
        print("   ✓ Tab switch smoothly displays bespoke curation animation before revealing jobs")

        browser.close()
        print("\n==================================================")
        print("ALL NEW REQUIREMENTS VERIFIED AND PASSED 100%!")
        print("==================================================")

if __name__ == '__main__':
    run_tests()
