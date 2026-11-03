import os
import sys
import time

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

from playwright.sync_api import sync_playwright
from PIL import Image

ARTIFACT_DIR = r"C:\Users\hp\.gemini\antigravity\brain\9aa8f19b-dcde-4560-9464-6fdb4b2814bd"

def run():
    print("Running Playwright verification for increased zoom & vertical gap on Page 2...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        
        # 1440x900 viewport
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto("http://127.0.0.1:8000/", wait_until="networkidle")
        time.sleep(1)
        
        # Go to Slide 1
        page.evaluate("() => window.goToSlide(1)")
        time.sleep(1.2)
        
        # Check background transform
        bg_tf = page.evaluate("() => document.getElementById('persistentHeroBg').style.transform")
        print(f"Page 2 background transform: '{bg_tf}'")
        assert "scale(1.28)" in bg_tf, f"Expected scale(1.28), got: {bg_tf}"
        assert "-8.5%" in bg_tf, f"Expected -8.5% translate, got: {bg_tf}"
        
        # Check vertical gap classes on grid
        grid_class = page.evaluate("() => document.querySelector('#discovery .grid').className")
        print(f"Grid classes: '{grid_class}'")
        assert "gap-y-6" in grid_class and "lg:gap-y-7" in grid_class, "Expected gap-y-6 lg:gap-y-7 on grid"
        
        # Capture 1440x900 screenshot
        path_1440 = os.path.join(ARTIFACT_DIR, "page2_hero_out_vertical_gap_1440.png")
        page.screenshot(path=path_1440)
        print(f"Captured 1440x900 screenshot: {path_1440}")
        
        # Crop character area on left to showcase hero coming out
        im = Image.open(path_1440)
        w, h = im.size
        char_crop = im.crop((0, 0, int(w * 0.45), h))
        crop_path = os.path.join(ARTIFACT_DIR, "page2_hero_character_came_out_comparison.png")
        char_crop.save(crop_path)
        print(f"Captured character comparison crop: {crop_path}")
        
        # 1920x1080 viewport
        page_fhd = browser.new_page(viewport={"width": 1920, "height": 1080})
        page_fhd.goto("http://127.0.0.1:8000/", wait_until="networkidle")
        time.sleep(1)
        page_fhd.evaluate("() => window.goToSlide(1)")
        time.sleep(1.2)
        path_1920 = os.path.join(ARTIFACT_DIR, "page2_hero_out_vertical_gap_1920.png")
        page_fhd.screenshot(path=path_1920)
        print(f"Captured 1920x1080 screenshot: {path_1920}")
        
        # Test Card 4 Intern Search
        page.fill("#p2QuickKeywordInput", "Python")
        time.sleep(0.3)
        page.click("button[onclick='executeP2InternSearch()']")
        time.sleep(1.2)
        assert page.is_visible("#curatedFeedsModal"), "Curated modal should be visible"
        assert page.input_value("#curatedSearchInput") == "Python", "Search query should be Python"
        print("PASS: Card 4 intern search verified.")
        page.click("button[onclick='closeCuratedFeedsModal()']")
        time.sleep(0.4)
        
        # Test Card 2 Entry-Level Search
        page.fill("#p2RoleSearchInput", "Data")
        time.sleep(0.3)
        page.click("button[onclick='executeP2EntrySearch()']")
        time.sleep(1.2)
        assert page.is_visible("#curatedFeedsModal"), "Curated modal should be visible"
        assert page.input_value("#curatedSearchInput") == "Data", "Search query should be Data"
        print("PASS: Card 2 entry-level search verified.")
        page.click("button[onclick='closeCuratedFeedsModal()']")
        
        browser.close()
        print("\nALL CHECKS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run()
