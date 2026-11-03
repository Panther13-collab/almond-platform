import sys
import time
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')

def test_viewports():
    viewports = [
        ("1920x1080", 1920, 1080),
        ("1440x900", 1440, 900),
        ("1366x768", 1366, 768),
        ("1280x800", 1280, 800)
    ]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        for name, width, height in viewports:
            print(f"\n--- Testing Viewport: {name} ({width}x{height}) ---")
            context = browser.new_context(viewport={"width": width, "height": height})
            page = context.new_page()
            page.goto("http://127.0.0.1:8000/", wait_until="networkidle")
            page.wait_for_timeout(800)

            btn_intern = page.locator("#heroBadge_internships")
            btn_aiml = page.locator("#heroBadge_aiml")
            btn_entry = page.locator("#heroBadge_entrylevel")

            box_intern = btn_intern.bounding_box()
            box_aiml = btn_aiml.bounding_box()
            box_entry = btn_entry.bounding_box()

            print(f"   Internships: y={box_intern['y']:.1f}, x={box_intern['x']:.1f}, w={box_intern['width']:.1f}, h={box_intern['height']:.1f}")
            print(f"   AI/ML:       y={box_aiml['y']:.1f}, x={box_aiml['x']:.1f}, w={box_aiml['width']:.1f}, h={box_aiml['height']:.1f}")
            print(f"   Entry-Level: y={box_entry['y']:.1f}, x={box_entry['x']:.1f}, w={box_entry['width']:.1f}, h={box_entry['height']:.1f}")

            # Verify all three buttons are on the exact same row (within 4px tolerance)
            y_diff_aiml = abs(box_intern['y'] - box_aiml['y'])
            y_diff_entry = abs(box_intern['y'] - box_entry['y'])

            print(f"   Vertical alignment diffs: aiml={y_diff_aiml:.1f}px, entry={y_diff_entry:.1f}px")
            assert y_diff_aiml < 5, f"AI/ML is not on same row! (diff={y_diff_aiml})"
            assert y_diff_entry < 5, f"Entry-Level is NOT on same row! (diff={y_diff_entry})"

            # Verify left-to-right ordering: Internships < AI/ML < Entry-Level
            assert box_intern['x'] < box_aiml['x'], "Internships must be to the left of AI/ML"
            assert box_aiml['x'] < box_entry['x'], "AI/ML must be to the left of Entry-Level"
            print(f"   ✓ All 3 cards are in a single horizontal row on {name}!")

            screenshot_path = f"C:/Users/hp/.gemini/antigravity/brain/9aa8f19b-dcde-4560-9464-6fdb4b2814bd/hero_single_row_{name}.png"
            page.screenshot(path=screenshot_path)
            print(f"   ✓ Screenshot saved: hero_single_row_{name}.png")

            context.close()

        browser.close()
        print("\n==================================================")
        print("ALL VIEWPORTS VERIFIED: 100% SINGLE ROW CONFIRMED!")
        print("==================================================")

if __name__ == "__main__":
    test_viewports()
