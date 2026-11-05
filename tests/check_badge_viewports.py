import sys
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')

viewports = [
    ("Desktop_1920x1080", 1920, 1080),
    ("Laptop_1440x900", 1440, 900),
    ("Laptop_1366x768", 1366, 768),
    ("Laptop_1280x800", 1280, 800),
    ("Tablet_1024x768", 1024, 768),
    ("Tablet_iPad_768x1024", 768, 1024),
    ("Mobile_iPhone13_390x844", 390, 844),
]

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    for name, w, h in viewports:
        page = browser.new_page(viewport={"width": w, "height": h})
        page.goto("http://127.0.0.1:8000/", wait_until="networkidle")
        page.wait_for_timeout(300)

        b1 = page.locator("#heroBadge_internships").bounding_box()
        b2 = page.locator("#heroBadge_aiml").bounding_box()
        b3 = page.locator("#heroBadge_entrylevel").bounding_box()

        y_diff = max(abs(b1['y'] - b2['y']), abs(b2['y'] - b3['y']))
        assert y_diff < 2, f"Cards not on single row in {name}! y_diff={y_diff}"
        
        screenshot_path = f"C:/Users/hp/.gemini/antigravity/brain/9aa8f19b-dcde-4560-9464-6fdb4b2814bd/badge_row_{name}.png"
        page.screenshot(path=screenshot_path)
        print(f"✓ {name}: Cards in single row (y_diff={y_diff:.1f}px) - Screenshot saved.", flush=True)

        page.close()
    browser.close()
