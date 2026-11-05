import sys
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')

devices_to_test = [
    ("iPhone_13", {"width": 390, "height": 844, "is_mobile": True, "has_touch": True, "device_scale_factor": 3}),
    ("Pixel_7", {"width": 412, "height": 915, "is_mobile": True, "has_touch": True, "device_scale_factor": 2.6}),
    ("Galaxy_S20", {"width": 360, "height": 800, "is_mobile": True, "has_touch": True, "device_scale_factor": 3})
]

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    
    for dev_name, dev_config in devices_to_test:
        print(f"\n--- Diagnosing Mobile: {dev_name} ({dev_config['width']}x{dev_config['height']}) ---")
        context = browser.new_context(
            viewport={"width": dev_config["width"], "height": dev_config["height"]},
            is_mobile=dev_config["is_mobile"],
            has_touch=dev_config["has_touch"],
            device_scale_factor=dev_config["device_scale_factor"],
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1"
        )
        page = context.new_page()
        page.goto("http://127.0.0.1:8000/", wait_until="networkidle")
        page.wait_for_timeout(1000)

        # Check Page 1
        p1_path = f"C:/Users/hp/.gemini/antigravity/brain/9aa8f19b-dcde-4560-9464-6fdb4b2814bd/mobile_p1_{dev_name}.png"
        page.screenshot(path=p1_path)
        print(f"   ✓ Captured Page 1: mobile_p1_{dev_name}.png")

        # Measure scroll heights of sections
        p1_height = page.evaluate("document.getElementById('hero').scrollHeight")
        p2_height = page.evaluate("document.getElementById('discovery').scrollHeight")
        p3_height = page.evaluate("document.getElementById('workspace').scrollHeight")
        p4_height = page.evaluate("document.getElementById('results-stream').scrollHeight")
        viewport_h = dev_config["height"]

        print(f"   Screen Height: {viewport_h}px")
        print(f"   Page 1 scrollHeight: {p1_height}px (Overflow: {p1_height - viewport_h}px)")
        print(f"   Page 2 scrollHeight: {p2_height}px (Overflow: {p2_height - viewport_h}px)")
        print(f"   Page 3 scrollHeight: {p3_height}px (Overflow: {p3_height - viewport_h}px)")
        print(f"   Page 4 scrollHeight: {p4_height}px (Overflow: {p4_height - viewport_h}px)")

        # Try to go to Page 2
        page.evaluate("goToSlide(1)")
        page.wait_for_timeout(1000)
        p2_path = f"C:/Users/hp/.gemini/antigravity/brain/9aa8f19b-dcde-4560-9464-6fdb4b2814bd/mobile_p2_{dev_name}.png"
        page.screenshot(path=p2_path)
        print(f"   ✓ Captured Page 2: mobile_p2_{dev_name}.png")

        # Try to go to Page 3
        page.evaluate("goToSlide(2)")
        page.wait_for_timeout(1000)
        p3_path = f"C:/Users/hp/.gemini/antigravity/brain/9aa8f19b-dcde-4560-9464-6fdb4b2814bd/mobile_p3_{dev_name}.png"
        page.screenshot(path=p3_path)
        print(f"   ✓ Captured Page 3: mobile_p3_{dev_name}.png")

        context.close()

    browser.close()
    print("\nMobile diagnostics completed!")
