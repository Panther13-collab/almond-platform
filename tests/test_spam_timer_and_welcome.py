import asyncio
import os
import uuid
import sqlite3
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1280, "height": 850})
        
        dialog_messages = []
        page.on("dialog", lambda d: (dialog_messages.append(d.message), d.accept()))
        
        await page.goto("http://127.0.0.1:8000")
        await page.wait_for_timeout(1000)
        
        # Open auth modal in signup mode
        await page.evaluate("""() => {
            window.openProfileModal();
            window.switchAuthTab('signup');
        }""")
        await page.wait_for_timeout(600)
        
        test_email = f"candidate_{uuid.uuid4().hex[:6]}@gmail.com"
        await page.fill("#authFullNameInput", "Sri Candidate")
        await page.fill("#authEmailInput", test_email)
        await page.fill("#authPasswordInput", "EliteAlmond2026!")
        
        # Submit to get OTP
        await page.click("#authSubmitBtn")
        
        # Wait for OTP step to appear (SMTP dispatch)
        await page.wait_for_selector("#authOtpStep:not(.hidden)", timeout=15000)
        await page.wait_for_timeout(500)
        
        out_dir = r"C:\Users\hp\.gemini\antigravity\brain\9aa8f19b-dcde-4560-9464-6fdb4b2814bd"
        
        # 1. Capture OTP step with 120s timer and Spam notice
        shot1 = os.path.join(out_dir, "step1_otp_120s_timer_and_spam_notice.png")
        await page.screenshot(path=shot1)
        print("Captured shot 1:", shot1)
        
        timer_text = await page.locator("#resendTimerNotice").text_content()
        print("Timer text found:", timer_text.strip())
        
        spam_visible = await page.locator("#authSpamNotice").is_visible()
        print("Spam guidance box visible:", spam_visible)
        
        # Get OTP code from almond_auth.db
        conn = sqlite3.connect(r"d:\Projects\AntigtavityApps\JobHunt\SK\platform\data\almond_auth.db")
        cur = conn.cursor()
        cur.execute("SELECT otp_code FROM email_otps WHERE email = ?", (test_email,))
        row = cur.fetchone()
        conn.close()
        
        if not row:
            raise Exception("OTP row not found in database!")
        otp_code = row[0]
        print(f"Retrieved real OTP code: {otp_code}")
        
        # Fill OTP and verify
        await page.fill("#authOtpInput", otp_code)
        await page.click("#authVerifyOtpBtn")
        
        # Wait for welcome view to appear
        await page.wait_for_selector("#authWelcomeView:not(.hidden)", timeout=10000)
        await page.wait_for_timeout(500)
        
        # 2. Capture the in-app Welcome View!
        shot2 = os.path.join(out_dir, "step2_in_app_welcome_celebration_modal.png")
        await page.screenshot(path=shot2)
        print("Captured shot 2:", shot2)
        
        welcome_visible = await page.locator("#authWelcomeView").is_visible()
        print("In-app Welcome View visible:", welcome_visible)
        
        welcome_title = await page.locator("#authWelcomeView h3").text_content()
        print("Welcome Title text:", welcome_title.strip())
        
        if dialog_messages:
            print("ALERT WARNING: Native browser alert was triggered:", dialog_messages)
        else:
            print("SUCCESS: Zero native browser alerts triggered! Modern in-app modal active.")
            
        # Click Enter Platform & Explore Feeds
        await page.click("#authWelcomeView button")
        await page.wait_for_timeout(800)
        
        shot3 = os.path.join(out_dir, "step3_logged_in_dashboard.png")
        await page.screenshot(path=shot3)
        print("Captured shot 3:", shot3)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
