import sys
import requests
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://127.0.0.1:8000"

def test_api_search_jobs():
    print("\n--- 1. Testing /api/find-jobs Backend API ---")
    payload = {
        "profile": {
            "name": "Alex Tester",
            "email": "alex.test@example.com",
            "current_role": "Full Stack Engineer",
            "years_experience": 4,
            "skills": ["Python", "FastAPI", "React", "TypeScript", "PostgreSQL", "Docker", "AWS"],
            "raw_text": "Experienced full stack engineer with Python, React, AWS, Docker."
        },
        "preferences": {
            "role": "Full Stack Engineer",
            "location": "Remote",
            "work_mode": "Remote",
            "yoe": 4
        }
    }
    resp = requests.post(f"{BASE_URL}/api/find-jobs", json=payload, timeout=60)
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()
    assert data["status"] == "success"

    ats_jobs = data.get("jobs", [])
    linkedin_jobs = data.get("linkedin_jobs", [])
    print(f"   Received {len(ats_jobs)} ATS jobs and {len(linkedin_jobs)} LinkedIn jobs.")
    assert len(ats_jobs) > 3, f"Expected more than 3 ATS jobs to verify unblocking, got {len(ats_jobs)}"

    # Verify that EVERY ATS job has is_locked == False and a genuine direct apply URL
    for idx, j in enumerate(ats_jobs):
        assert j.get("is_locked") is False, f"Job #{idx} is locked: {j}"
        url = j.get("url", "")
        assert url != "#unlock-pro", f"Job #{idx} has locked placeholder URL: {url}"
        assert url.startswith("http"), f"Job #{idx} does not have valid http link: {url}"

    print(f"   ✓ All {len(ats_jobs)} ATS jobs are 100% unlocked with direct URLs (index >= 3 included)!")

    for idx, j in enumerate(linkedin_jobs):
        assert j.get("is_locked") is False, f"LinkedIn Job #{idx} is locked: {j}"
        url = j.get("url", "")
        assert url != "#unlock-pro", f"LinkedIn Job #{idx} has locked placeholder URL: {url}"
        assert url.startswith("http"), f"LinkedIn Job #{idx} does not have valid http link: {url}"

    print(f"   ✓ All {len(linkedin_jobs)} LinkedIn jobs are 100% unlocked with direct URLs!")

def test_api_curated_feeds():
    print("\n--- 2. Testing /api/curated-feeds Backend API ---")
    resp = requests.get(f"{BASE_URL}/api/curated-feeds?feed_type=internships&limit=25&offset=0", timeout=10)
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    res = resp.json().get("result", {})
    items = res.get("items", [])
    print(f"   Received {len(items)} curated internship items (testing index 0 to {len(items)-1}).")
    assert len(items) >= 15, f"Expected at least 15 items, got {len(items)}"

    for idx, item in enumerate(items):
        assert item.get("is_locked") is False, f"Curated item #{idx} is locked: {item}"
        url = item.get("url", "")
        assert url != "#unlock-pro", f"Curated item #{idx} has locked placeholder URL: {url}"
        assert url.startswith("http"), f"Curated item #{idx} does not have valid http link: {url}"

    print(f"   ✓ All {len(items)} curated directory items are 100% unlocked with direct application links!")

def test_ui_browser_display():
    print("\n--- 3. Testing Frontend UI with Playwright ---")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto(BASE_URL, wait_until="networkidle")
        page.wait_for_timeout(600)

        # 3A. Verify VIP Access modal opens from top navbar
        print("   Testing VIP Access modal trigger from navbar...")
        vip_btn = page.locator("button:has-text('VIP Access')").first
        assert vip_btn.is_visible(), "VIP Access navbar button should be visible"
        vip_btn.click()
        page.wait_for_timeout(400)

        vip_modal = page.locator("#vipPricingModal")
        assert vip_modal.is_visible(), "VIP Pricing Modal should open upon clicking navbar CTA"
        heading_text = page.locator("#vipBannerHeading").inner_text()
        print(f"   ✓ VIP Pricing Modal opened successfully with heading: '{heading_text}'")
        
        # Close VIP modal
        page.locator("#vipPricingModal button:has-text('✕')").click()
        page.wait_for_timeout(300)

        # 3B. Verify Curated Feeds Modal (Direct Internships)
        print("   Testing Curated Feeds Modal links...")
        page.locator("#heroBadge_internships").click()
        # Allow 2.5s curation UX loader to complete and render cards
        page.wait_for_timeout(3200)

        curated_modal = page.locator("#curatedFeedsModal")
        assert curated_modal.is_visible(), "Curated Feeds Modal should be visible"
        
        # Check rendered links inside modal
        cards = page.locator("#curatedCardsContainer .curated-job-card")
        card_count = cards.count()
        print(f"   Found {card_count} rendered curated job cards in modal.")
        assert card_count >= 10, f"Expected at least 10 cards, got {card_count}"

        # Confirm NO card has 'Unlock Portal (VIP)'
        locked_btns = page.locator("#curatedCardsContainer button:has-text('Unlock Portal (VIP)')")
        assert locked_btns.count() == 0, f"Expected 0 locked buttons, found {locked_btns.count()}"

        # Confirm all cards have direct links
        direct_links = page.locator("#curatedCardsContainer a:has-text('Direct Application Portal')")
        print(f"   Found {direct_links.count()} active direct application links in curated modal.")
        assert direct_links.count() == card_count, "Every card should have an active direct link"

        # Check href of card at index 12 (which was previously locked at >= 10)
        href_sample = direct_links.nth(11).get_attribute("href")
        assert href_sample and href_sample.startswith("http"), f"Sample href must be direct http link, got {href_sample}"
        print(f"   ✓ Sample item #12 direct link: {href_sample}")

        # Close modal
        page.evaluate("() => window.closeCuratedFeedsModal()")
        page.wait_for_timeout(300)

        # 3C. Perform Resume Search & inspect Page 4 Results Stream
        print("   Testing Page 4 Results Stream rendering with multiple jobs...")
        # Populate candidate profile in client-side runtime
        page.evaluate("""async () => {
            window.currentCandidateProfile = {
                name: "Alex Tester",
                email: "alex.test@example.com",
                current_role: "Full Stack Engineer",
                years_experience: 4,
                skills: ["Python", "FastAPI", "React", "TypeScript", "PostgreSQL", "Docker", "AWS"],
                raw_text: "Experienced full stack engineer with Python, React, AWS, Docker."
            };
            window.currentPreferences = {
                role: "Full Stack Engineer",
                location: "Remote",
                work_mode: "Remote",
                yoe: 4
            };
            const r = await fetch('/api/find-jobs', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    profile: window.currentCandidateProfile,
                    preferences: window.currentPreferences
                })
            });
            const data = await r.json();
            window.currentJobs = data.jobs || [];
            window.currentAtsJobs = data.jobs || [];
            window.currentLinkedinJobs = data.linkedin_jobs || [];
            window.currentFounderJobs = data.founder_jobs || [];
            if (typeof window.renderJobCards === 'function') {
                window.renderJobCards(data.jobs || [], 'jobListContainer', false);
            }
            return data.jobs.length;
        }""")
        page.wait_for_timeout(500)

        # Confirm Page 4 result container has jobs
        rendered_job_cards = page.locator("#jobListContainer .kage-card")
        job_card_count = rendered_job_cards.count()
        print(f"   Rendered {job_card_count} job cards in results stream.")
        assert job_card_count > 3, f"Expected > 3 job cards, got {job_card_count}"

        # Verify NO cards have 'Unlock Direct Application Portal (VIP Access)'
        locked_apply_btns = page.locator("#jobListContainer button:has-text('Unlock Direct Application Portal')")
        assert locked_apply_btns.count() == 0, f"Found {locked_apply_btns.count()} locked buttons; expected 0!"

        # Verify NO cards have blurred endpoints
        blurred_spans = page.locator("#jobListContainer span.blur-\\[4px\\]")
        assert blurred_spans.count() == 0, f"Found {blurred_spans.count()} blurred spans; expected 0!"

        # Verify cards past index 3 (e.g. index 3, 4, 5) have direct application links and AI pitch buttons
        for test_idx in range(min(job_card_count, 8)):
            card = rendered_job_cards.nth(test_idx)
            apply_link = card.locator("a.direct-apply-link")
            assert apply_link.count() == 1, f"Card #{test_idx+1} missing direct-apply-link!"
            href = apply_link.get_attribute("href")
            assert href and href.startswith("http"), f"Card #{test_idx+1} href must be real URL, got: {href}"

            pitch_btn = card.locator("button.generate-pitch-btn")
            assert pitch_btn.count() == 1, f"Card #{test_idx+1} missing AI Pitch button!"

            cover_btn = card.locator("button.generate-cover-letter-btn")
            assert cover_btn.count() == 1, f"Card #{test_idx+1} missing Cover Letter button!"

        print(f"   ✓ Confirmed: All job cards (including cards 4, 5, 6, 7, 8) have unblurred direct portal links and full AI tools!")

        # Screenshot proof
        screenshot_path = "C:/Users/hp/.gemini/antigravity/brain/9aa8f19b-dcde-4560-9464-6fdb4b2814bd/unrestricted_links_verification.png"
        page.screenshot(path=screenshot_path)
        print(f"   ✓ Verification screenshot saved to {screenshot_path}")

        browser.close()

if __name__ == "__main__":
    test_api_search_jobs()
    test_api_curated_feeds()
    test_ui_browser_display()
    print("\n=======================================================")
    print("ALL VERIFICATIONS PASSED: 100% UNRESTRICTED DIRECT LINKS")
    print("=======================================================")
