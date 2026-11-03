import asyncio
import os
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1280, "height": 800})
        await page.goto("http://127.0.0.1:8000")
        await page.wait_for_timeout(1000)
        
        # Open profile/auth modal and switch to signup
        await page.evaluate("""() => {
            if (typeof window.openProfileModal === 'function') {
                window.openProfileModal();
            } else {
                document.getElementById('profileModal').classList.remove('hidden');
            }
            if (typeof window.switchAuthTab === 'function') {
                window.switchAuthTab('signup');
            }
        }""")
        await page.wait_for_timeout(600)
        
        # Fill details
        import uuid
        test_email = f"test_{uuid.uuid4().hex[:6]}@example.com"
        await page.fill("#authFullNameInput", "Almond Candidate")
        await page.fill("#authEmailInput", test_email)
        await page.fill("#authPasswordInput", "SecureCandidate123!")
        
        # Submit
        await page.click("#authSubmitBtn")
        await page.wait_for_timeout(2500)
        
        out_dir = r"C:\Users\hp\.gemini\antigravity\brain\9aa8f19b-dcde-4560-9464-6fdb4b2814bd"
        out_path = os.path.join(out_dir, "verified_otp_modal_step.png")
        await page.screenshot(path=out_path)
        print("Captured screenshot successfully at:", out_path)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
