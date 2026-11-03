import sys
import time
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')

def run_verification():
    print("==================================================")
    print("TEST SUITE: PAGE 4 BACKGROUND & NEW MARKETING COPY")
    print("==================================================")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = context.new_page()

        print("\n1. Loading http://127.0.0.1:8000/ ...")
        page.goto("http://127.0.0.1:8000/", wait_until="networkidle")
        page.wait_for_timeout(1000)

        # ------------------------------------------------------------------
        # 2. Check Homepage Copy Updates
        # ------------------------------------------------------------------
        print("\n2. Checking Homepage Copy Updates...")
        p1_narrative = page.locator("#hero p.text-slate-600").inner_text()
        print(f"   Homepage Subheadline: '{p1_narrative}'")
        assert "job market isn't oversaturated" in p1_narrative.lower(), "Expected anti-oversaturation hook in subheadline"
        assert "door has already closed" in p1_narrative.lower(), "Expected closed-door reference in subheadline"
        assert "company internal servers" in p1_narrative.lower(), "Expected company internal servers in subheadline"

        p1_cta = page.locator("#hero button[onclick*='goToSlide(2)']").inner_text()
        print(f"   Homepage CTA Button: '{p1_cta}'")
        assert "Beat the public crowd" in p1_cta, f"Expected 'Beat the public crowd', got '{p1_cta}'"
        print("   ✓ Homepage subheadline and 'Beat the public crowd' button verified!")

        page.screenshot(path="C:/Users/hp/.gemini/antigravity/brain/9aa8f19b-dcde-4560-9464-6fdb4b2814bd/p1_beat_the_public_crowd_1920.png")
        print("   ✓ Saved screenshot: p1_beat_the_public_crowd_1920.png")

        # ------------------------------------------------------------------
        # 3. Check Page 2 Bento Card Copy Updates
        # ------------------------------------------------------------------
        print("\n3. Checking Page 2 Bento Card Copy Updates...")
        page.evaluate("goToSlide(1)")
        page.wait_for_timeout(1000)

        # Card 1: 3.3M+ Live Jobs
        card1_text = page.locator("#discovery .md\\:col-span-2 p").inner_text()
        print(f"   Page 2 Card 1 Text: '{card1_text}'")
        assert "unadvertised engineering seats" in card1_text, "Card 1 missing 'unadvertised engineering seats'"
        assert "Quiet applications. Loud offers." in card1_text, "Card 1 missing 'Quiet applications. Loud offers.'"

        # Card 5: 0% Recruiter Spread
        card5_text = page.locator("#discovery div[onclick*=\"'middlemen'\"] p").inner_text()
        print(f"   Page 2 Card 5 Text: '{card5_text}'")
        assert "No ghost listings. No zombie posts." in card5_text, "Card 5 missing 'No ghost listings. No zombie posts.'"
        assert "Only real openings with real budgets." in card5_text, "Card 5 missing 'Only real openings with real budgets.'"

        # Card 6: Verified Compensation
        card6_text = page.locator("#discovery div[onclick*=\"'brokers'\"] p").inner_text()
        print(f"   Page 2 Card 6 Text: '{card6_text}'")
        assert "Stop feeding algorithms built to reject you." in card6_text, "Card 6 missing 'Stop feeding algorithms built to reject you.'"
        assert "Apply using Almond, where humans read." in card6_text, "Card 6 missing 'Apply using Almond, where humans read.'"

        # Card 7: Founder Direct Access
        card7_text = page.locator("#discovery div[onclick*=\"'deadposts'\"] p").inner_text()
        print(f"   Page 2 Card 7 Text: '{card7_text}'")
        assert "technical dossier directly in front of leads and founders" in card7_text, "Card 7 missing technical dossier text"

        print("   ✓ Page 2 Bento cards verified with new marketing copy!")
        page.screenshot(path="C:/Users/hp/.gemini/antigravity/brain/9aa8f19b-dcde-4560-9464-6fdb4b2814bd/p2_updated_marketing_copy_1920.png")
        print("   ✓ Saved screenshot: p2_updated_marketing_copy_1920.png")

        # ------------------------------------------------------------------
        # 4. Check Page 3 Background
        # ------------------------------------------------------------------
        print("\n4. Checking Page 3 Background...")
        page.evaluate("goToSlide(2)")
        page.wait_for_timeout(1000)

        bg_scale_p3 = page.evaluate("document.getElementById('persistentHeroBg').style.transform")
        bg_opacity_p3 = page.evaluate("document.getElementById('persistentHeroBg').style.opacity")
        print(f"   Page 3 persistentHeroBg transform: '{bg_scale_p3}', opacity: '{bg_opacity_p3}'")
        assert "1.28" in bg_scale_p3, "Page 3 should maintain zoom 1.28"
        assert bg_opacity_p3 == "1", "Page 3 background opacity should be 1"

        page.screenshot(path="C:/Users/hp/.gemini/antigravity/brain/9aa8f19b-dcde-4560-9464-6fdb4b2814bd/p3_split_steady_hero_1920.png")
        print("   ✓ Saved screenshot: p3_split_steady_hero_1920.png")

        # ------------------------------------------------------------------
        # 5. Check Page 4 Background & Synchronization
        # ------------------------------------------------------------------
        print("\n5. Checking Page 4 (#results-stream) Background...")
        page.evaluate("goToSlide(3)")
        page.wait_for_timeout(1000)

        # 5a. Check section class
        p4_section = page.locator("#results-stream")
        p4_classes = p4_section.get_attribute("class")
        print(f"   Page 4 section classes: '{p4_classes}'")
        assert "bg-transparent" in p4_classes, "Page 4 section must be bg-transparent"

        # 5b. Check persistent hero background visibility and zoom on Slide 3
        bg_scale_p4 = page.evaluate("document.getElementById('persistentHeroBg').style.transform")
        bg_opacity_p4 = page.evaluate("document.getElementById('persistentHeroBg').style.opacity")
        print(f"   Page 4 persistentHeroBg transform: '{bg_scale_p4}', opacity: '{bg_opacity_p4}'")
        assert "1.28" in bg_scale_p4, "Page 4 should maintain same zoom 1.28 as Page 3"
        assert bg_opacity_p4 == "1", "Page 4 background opacity should be 1 (visible character)"

        # 5c. Check split SVG and golden crack in Page 4
        gold_crack_p4 = page.locator("#results-stream .split-crack-bg path[stroke*='goldCrackGrad_rs']")
        assert gold_crack_p4.is_visible(), "Page 4 golden jagged crack must be visible"

        right_green_p4 = page.locator("#results-stream .split-crack-bg g[clip-path*='rightGreenClip_rs']")
        assert right_green_p4.count() > 0, "Page 4 right forest green clip must exist"

        print("   ✓ Page 4 background perfectly matches Page 3 (Left: Hero BG | Center: Golden Crack | Right: Forest Green)")
        page.screenshot(path="C:/Users/hp/.gemini/antigravity/brain/9aa8f19b-dcde-4560-9464-6fdb4b2814bd/p4_split_golden_crack_matching_p3_1920.png")
        print("   ✓ Saved screenshot: p4_split_golden_crack_matching_p3_1920.png")

        # Also capture at 1440x900
        context_1440 = browser.new_context(viewport={"width": 1440, "height": 900})
        page_1440 = context_1440.new_page()
        page_1440.goto("http://127.0.0.1:8000/", wait_until="networkidle")
        page_1440.wait_for_timeout(800)
        page_1440.evaluate("goToSlide(3)")
        page_1440.wait_for_timeout(800)
        page_1440.screenshot(path="C:/Users/hp/.gemini/antigravity/brain/9aa8f19b-dcde-4560-9464-6fdb4b2814bd/p4_split_golden_crack_matching_p3_1440.png")
        print("   ✓ Saved screenshot: p4_split_golden_crack_matching_p3_1440.png")
        context_1440.close()

        browser.close()

    print("\n==================================================")
    print("ALL VERIFICATIONS COMPLETED & PASSED 100%!")
    print("==================================================")

if __name__ == "__main__":
    run_verification()
