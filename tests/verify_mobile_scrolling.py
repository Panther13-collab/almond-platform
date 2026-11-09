import sys
sys.stdout.reconfigure(encoding="utf-8")

def main():
    from playwright.sync_api import sync_playwright
    
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True)
        page = context.new_page()
        page.goto('http://127.0.0.1:8000/', wait_until='networkidle')
        page.wait_for_timeout(800)
    
        # 1. Scroll to Criteria Deck on Page 3
        print("1. Scrolling to criteria deck on Page 3...")
        page.evaluate("document.getElementById('criteria-deck').scrollIntoView({behavior: 'instant', block: 'start'})")
        page.wait_for_timeout(600)
        page.screenshot(path='C:/Users/hp/.gemini/antigravity/brain/9aa8f19b-dcde-4560-9464-6fdb4b2814bd/mobile_p3_criteria_deck.png')
        print("   ✓ Saved mobile_p3_criteria_deck.png")
    
        # 2. Scroll to Search Button on Page 3
        print("2. Scrolling to search button on Page 3...")
        page.evaluate("document.getElementById('searchJobsBtn').scrollIntoView({behavior: 'instant', block: 'center'})")
        page.wait_for_timeout(600)
        page.screenshot(path='C:/Users/hp/.gemini/antigravity/brain/9aa8f19b-dcde-4560-9464-6fdb4b2814bd/mobile_p3_search_button.png')
        print("   ✓ Saved mobile_p3_search_button.png")
    
        # 3. Scroll to Page 4 Results Stream
        print("3. Scrolling to Page 4 results stream...")
        page.evaluate("document.getElementById('results-stream').scrollIntoView({behavior: 'instant', block: 'start'})")
        page.wait_for_timeout(600)
        page.screenshot(path='C:/Users/hp/.gemini/antigravity/brain/9aa8f19b-dcde-4560-9464-6fdb4b2814bd/mobile_p4_results_stream.png')
        print("   ✓ Saved mobile_p4_results_stream.png")
    
        # 4. Test clicking 'Beat the public crowd' CTA from Page 1 on mobile
        print("4. Testing 'Beat the public crowd' navigation on mobile...")
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(500)
        page.locator("#hero button[onclick*='goToSlide(2)']").click()
        page.wait_for_timeout(1000)
    
        scrollY = page.evaluate("window.scrollY || document.documentElement.scrollTop")
        print(f"   Scroll position after clicking CTA: {scrollY:.1f}px")
        assert scrollY > 500, f"Expected smooth scroll down to workspace, got scrollY={scrollY}"
        print("   ✓ 'Beat the public crowd' CTA smoothly scrolls down to workspace on mobile!")
    
        browser.close()
    
    print("\nAll mobile scrolling verifications passed successfully!")

if __name__ == "__main__":
    main()