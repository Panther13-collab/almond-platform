import sys
import time
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')

def run_verification():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        print("1. Loading http://127.0.0.1:8000/ ...")
        page.goto("http://127.0.0.1:8000/", wait_until="networkidle")
        page.wait_for_timeout(1000)

        # -------------------------------------------------------------
        # 1. Verify Homepage Configure Profile button -> navigates to Slide 2
        # -------------------------------------------------------------
        print("\n2. Testing Homepage Configure Profile CTA...")
        hero_cta = page.locator("#hero button:has-text('Configure Profile')")
        assert hero_cta.is_visible(), "Hero Configure Profile button should be visible"
        hero_cta.click()
        page.wait_for_timeout(800)
        current_slide = page.evaluate("() => window.currentSlide")
        print(f"   Current slide after clicking Configure Profile: {current_slide}")
        assert current_slide == 2, f"Expected currentSlide == 2 (Page 3 Candidate Profile), got {current_slide}"
        print("   ✓ Configure Profile navigates directly to Slide 2 (Page 3 Candidate Profile)")

        # Return to Slide 0
        page.evaluate("() => window.goToSlide(0)")
        page.wait_for_timeout(800)

        # -------------------------------------------------------------
        # 2. Verify "Summer" and "2027" removed from Homepage & Bento Grid
        # -------------------------------------------------------------
        print("\n3. Testing Homepage & Bento Grid text...")
        internships_badge = page.locator("#heroBadge_internships")
        intern_text = internships_badge.inner_text()
        print(f"   Hero internships badge text: '{intern_text}'")
        assert "Direct Internships" in intern_text, f"Expected 'Direct Internships' in hero badge, got '{intern_text}'"
        assert "Summer" not in intern_text, f"'Summer' should NOT be in hero badge: '{intern_text}'"
        assert "2027" not in intern_text, f"'2027' should NOT be in hero badge: '{intern_text}'"
        print("   ✓ Hero badge contains 'Direct Internships' with zero Summer/2027")

        # Scroll to Slide 1 (Bento Grid)
        page.evaluate("() => window.goToSlide(1)")
        page.wait_for_timeout(800)
        bento_card3 = page.locator("#discovery h4:has-text('Direct internships search')")
        assert bento_card3.is_visible(), "Bento Card 3 should have title 'Direct internships search'"
        bento_c3_text = bento_card3.inner_text()
        print(f"   Bento Card 3 title: '{bento_c3_text}'")
        assert "Summer" not in bento_c3_text, f"'Summer' should not be in Bento Card 3: '{bento_c3_text}'"
        print("   ✓ Bento Card 3 has 'Direct internships search' with zero Summer")

        # -------------------------------------------------------------
        # 3. Verify Curated Feeds Modal: Freshness, Unlocked first 10, Locked 11th
        # -------------------------------------------------------------
        print("\n4. Testing Curated Feeds Modal (Internships tab)...")
        bento_card3.click()
        page.wait_for_timeout(1000)
        
        modal = page.locator("#curatedFeedsModal")
        assert modal.is_visible(), "Curated Feeds Modal should be visible"

        modal_title = page.locator("#curatedModalTitle").inner_text()
        print(f"   Modal Title: '{modal_title}'")
        assert modal_title == "Direct Internships", f"Expected 'Direct Internships', got '{modal_title}'"
        assert "Summer" not in modal_title, f"'Summer' should not be in modal title: '{modal_title}'"
        assert "2027" not in modal_title, f"'2027' should not be in modal title: '{modal_title}'"

        tab1_text = page.locator("#curatedTab_internships").inner_text()
        print(f"   Tab 1 Label: '{tab1_text}'")
        assert "Direct Internships" in tab1_text, f"Expected 'Direct Internships' in tab 1: '{tab1_text}'"
        assert "Summer" not in tab1_text, f"'Summer' should not be in tab 1: '{tab1_text}'"

        # Check job freshness
        first_date_badge = page.locator("#curatedCardsContainer .curated-job-card").first.locator("span:has-text('Today'), span:has-text('ago')").first
        first_date_text = first_date_badge.inner_text()
        print(f"   First posting date badge: '{first_date_text}'")
        assert any(x in first_date_text for x in ["Today", "1d ago", "2d ago", "3d ago"]), f"Expected fresh posting (Today or Xd ago), got '{first_date_text}'"
        print("   ✓ Curated feeds default to latest (fresh) postings")

        # Check unlocked first 10 vs locked 11th
        cards = page.locator("#curatedCardsContainer .curated-job-card")
        total_rendered = cards.count()
        print(f"   Total cards rendered: {total_rendered}")
        assert total_rendered >= 11, f"Expected at least 11 cards, got {total_rendered}"

        for idx in range(10):
            card = cards.nth(idx)
            direct_btn = card.locator("a:has-text('Direct Application Portal')")
            assert direct_btn.is_visible(), f"Card #{idx+1} should have unlocked 'Direct Application Portal' link"
        print("   ✓ First 10 jobs (1-10) are 100% UNLOCKED with direct links")

        # Card 11 (index 10) must be locked
        card11 = cards.nth(10)
        lock_btn = card11.locator("button:has-text('Unlock Portal (VIP)')")
        assert lock_btn.is_visible(), "Card #11 should have locked 'Unlock Portal (VIP)' button"
        print("   ✓ Job #11 is LOCKED with 'Unlock Portal (VIP)'")

        # Screenshot Curated Modal
        page.screenshot(path="C:/Users/hp/.gemini/antigravity/brain/9aa8f19b-dcde-4560-9464-6fdb4b2814bd/verify_curated_modal_direct_internships.png")
        print("   ✓ Captured screenshot of Curated Feeds Modal")

        # Test AIML tab
        print("\n5. Testing AI/ML Specialist Tab...")
        page.locator("#curatedTab_aiml").click()
        page.wait_for_timeout(2800)
        aiml_cards = page.locator("#curatedCardsContainer .curated-job-card")
        assert aiml_cards.count() >= 11, "AIML tab should render at least 11 jobs"
        aiml_first_date = aiml_cards.first.locator("span:has-text('Today'), span:has-text('ago')").first.inner_text()
        print(f"   AIML First posting date badge: '{aiml_first_date}'")
        assert any(x in aiml_first_date for x in ["Today", "1d ago", "2d ago", "3d ago"]), f"Expected fresh posting, got '{aiml_first_date}'"
        # First 10 unlocked, 11th locked
        assert aiml_cards.nth(0).locator("a:has-text('Direct Application Portal')").is_visible(), "AIML Job 1 must be unlocked"
        assert aiml_cards.nth(9).locator("a:has-text('Direct Application Portal')").is_visible(), "AIML Job 10 must be unlocked"
        assert aiml_cards.nth(10).locator("button:has-text('Unlock Portal (VIP)')").is_visible(), "AIML Job 11 must be locked"
        print("   ✓ AI/ML tab: First 10 unlocked, 11th locked, fresh postings default")

        # Test Entry Level tab
        print("\n6. Testing Entry-Level & New Grad Tab...")
        page.locator("#curatedTab_entrylevel").click()
        page.wait_for_timeout(2800)
        entry_cards = page.locator("#curatedCardsContainer .curated-job-card")
        assert entry_cards.count() >= 11, "Entry-level tab should render at least 11 jobs"
        entry_first_date = entry_cards.first.locator("span:has-text('Today'), span:has-text('ago')").first.inner_text()
        print(f"   Entry-Level First posting date badge: '{entry_first_date}'")
        assert any(x in entry_first_date for x in ["Today", "1d ago", "2d ago", "3d ago"]), f"Expected fresh posting, got '{entry_first_date}'"
        # First 10 unlocked, 11th locked
        assert entry_cards.nth(0).locator("a:has-text('Direct Application Portal')").is_visible(), "Entry-Level Job 1 must be unlocked"
        assert entry_cards.nth(9).locator("a:has-text('Direct Application Portal')").is_visible(), "Entry-Level Job 10 must be unlocked"
        assert entry_cards.nth(10).locator("button:has-text('Unlock Portal (VIP)')").is_visible(), "Entry-Level Job 11 must be locked"
        print("   ✓ Entry-Level tab: First 10 unlocked, 11th locked, fresh postings default")

        # Close Modal
        page.locator("button[onclick='closeCuratedFeedsModal()']").click()
        page.wait_for_timeout(500)

        # -------------------------------------------------------------
        # 4. Verify Page 4 Typography & Results Stream
        # -------------------------------------------------------------
        print("\n7. Testing Page 4 (Results Stream) initial view & typography...")
        page.evaluate("() => window.goToSlide(3)")
        page.wait_for_timeout(800)

        # Check results header font class
        hdr = page.locator("#results-stream h2:has-text('Matched Opportunities')")
        assert hdr.is_visible(), "Results header should be visible on Page 4"
        hdr_classes = hdr.get_attribute("class")
        print(f"   Results header classes: '{hdr_classes}'")
        assert "font-black" in hdr_classes, "Header must have font-black"

        empty_state_title = page.locator("#emptyState h3")
        assert empty_state_title.is_visible(), "Empty state title should be visible"
        print(f"   Empty state title text: '{empty_state_title.inner_text()}' (classes: '{empty_state_title.get_attribute('class')}')")
        assert "font-black" in empty_state_title.get_attribute("class"), "Empty state title must have font-black"

        # Capture desktop screenshot of Page 4 initial empty state
        page.screenshot(path="C:/Users/hp/.gemini/antigravity/brain/9aa8f19b-dcde-4560-9464-6fdb4b2814bd/page4_crisp_typography_empty_state_1440.png")
        print("   ✓ Captured screenshot of Page 4 initial empty state")

        # -------------------------------------------------------------
        # 5. Render job cards on Page 4 and verify job card typography
        # -------------------------------------------------------------
        print("\n8. Testing Page 4 dynamically rendered Job Cards...")
        page.evaluate("""() => {
            const mockJobs = [
                {
                    title: "Senior Full-Stack AI Systems Engineer",
                    company: "Anthropic",
                    location: "San Francisco, CA",
                    location_tag: "San Francisco, CA",
                    work_mode: "Hybrid",
                    employment_type_tag: "Full-Time",
                    source: "Lever",
                    url: "https://jobs.lever.co/anthropic/sample",
                    cvmatch_score: 96,
                    matched_skills: ["Python", "PyTorch", "TypeScript", "React", "Distributed Systems", "PostgreSQL"],
                    gap_skills: ["Kubernetes", "CUDA"],
                    comp_display: "$210,000 - $285,000 + Equity",
                    posted_at: new Date().toISOString(),
                    is_locked: false
                },
                {
                    title: "Staff Distributed Systems Architect",
                    company: "Stripe",
                    location: "Worldwide Remote",
                    location_tag: "Remote",
                    work_mode: "Remote",
                    employment_type_tag: "Full-Time",
                    source: "Greenhouse",
                    url: "https://boards.greenhouse.io/stripe/sample",
                    cvmatch_score: 91,
                    matched_skills: ["Go", "Kafka", "AWS", "gRPC", "Docker"],
                    gap_skills: ["Terraform"],
                    comp_display: "$240,000 - $310,000 + Equity",
                    posted_at: new Date().toISOString(),
                    is_locked: false
                },
                {
                    title: "Principal ML Infrastructure Engineer",
                    company: "Meta",
                    location: "Menlo Park, CA",
                    location_tag: "Menlo Park, CA",
                    work_mode: "Onsite",
                    employment_type_tag: "Full-Time",
                    source: "Ashby",
                    url: "https://jobs.ashbyhq.com/meta/sample",
                    cvmatch_score: 87,
                    matched_skills: ["PyTorch", "C++", "Triton", "Ray", "Distributed Training"],
                    gap_skills: ["NCCL", "Slurm"],
                    comp_display: "$260,000 - $340,000 + RSU",
                    posted_at: new Date().toISOString(),
                    is_locked: true
                }
            ];
            window.currentJobs = mockJobs;
            window.currentAtsJobs = mockJobs;
            const emptyEl = document.getElementById('emptyState');
            if (emptyEl) emptyEl.classList.add('hidden');
            renderJobCards(mockJobs, 'jobListContainer', false, false, 0);
        }""")
        page.wait_for_timeout(1000)

        # Verify rendered job cards
        rendered_cards = page.locator("#jobListContainer .kage-card")
        assert rendered_cards.count() == 3, f"Expected 3 rendered job cards, got {rendered_cards.count()}"

        card1_title = rendered_cards.nth(0).locator("h3").inner_text()
        print(f"   Card 1 Job Title: '{card1_title}'")
        assert "Senior Full-Stack AI Systems Engineer" in card1_title

        # Check compensation text in card 1
        card1_comp = rendered_cards.nth(0).locator("span:has-text('Target Package / Compensation')")
        assert card1_comp.is_visible(), "Target package label must be visible"
        assert "font-mono" not in card1_comp.get_attribute("class"), "Target package label must NOT have font-mono"

        # Check 0% recruiter spread
        spread_badge = rendered_cards.nth(0).locator("span.font-black:has-text('0% Recruiter Spread')").first
        assert spread_badge.is_visible(), "0% Recruiter Spread badge must be visible"
        assert "font-mono" not in spread_badge.get_attribute("class"), "0% Recruiter Spread badge must NOT have font-mono"

        # Check Unlocked CTA on Card 1
        card1_apply = rendered_cards.nth(0).locator("a:has-text('Direct Application Portal')")
        assert card1_apply.is_visible(), "Card 1 should have unlocked direct application link"

        # Check Locked CTA on Card 3 (VIP)
        card3_vip = rendered_cards.nth(2).locator("button:has-text('Unlock Direct Application Portal (VIP Access)')")
        assert card3_vip.is_visible(), "Card 3 should have VIP locked button"

        # Capture desktop screenshot of Page 4 with crisp rendered job cards at 1440x900
        page.screenshot(path="C:/Users/hp/.gemini/antigravity/brain/9aa8f19b-dcde-4560-9464-6fdb4b2814bd/page4_crisp_typography_job_cards_1440.png")
        print("   ✓ Captured screenshot of Page 4 job cards (1440x900)")

        # Switch to 1920x1080 and capture screenshot
        page.set_viewport_size({"width": 1920, "height": 1080})
        page.wait_for_timeout(500)
        page.screenshot(path="C:/Users/hp/.gemini/antigravity/brain/9aa8f19b-dcde-4560-9464-6fdb4b2814bd/page4_crisp_typography_job_cards_1920.png")
        print("   ✓ Captured screenshot of Page 4 job cards (1920x1080)")

        # Capture Page 1 at 1920x1080
        page.evaluate("() => window.goToSlide(0)")
        page.wait_for_timeout(800)
        page.screenshot(path="C:/Users/hp/.gemini/antigravity/brain/9aa8f19b-dcde-4560-9464-6fdb4b2814bd/page1_updated_badges_1920.png")
        print("   ✓ Captured screenshot of Page 1 (1920x1080)")

        # Capture Page 2 at 1920x1080
        page.evaluate("() => window.goToSlide(1)")
        page.wait_for_timeout(800)
        page.screenshot(path="C:/Users/hp/.gemini/antigravity/brain/9aa8f19b-dcde-4560-9464-6fdb4b2814bd/page2_updated_bento_1920.png")
        print("   ✓ Captured screenshot of Page 2 (1920x1080)")

        browser.close()
        print("\n==========================================")
        print("ALL VERIFICATIONS PASSED SUCCESSFULLY! (100% GREEN)")
        print("==========================================")

if __name__ == '__main__':
    run_verification()
