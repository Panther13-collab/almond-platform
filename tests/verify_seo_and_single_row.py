import os
import sys
import time
import requests
import subprocess
from playwright.sync_api import sync_playwright

# Ensure utf-8 output on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

BASE_URL = "http://127.0.0.1:8000"
ARTIFACT_DIR = r"C:\Users\hp\.gemini\antigravity\brain\9aa8f19b-dcde-4560-9464-6fdb4b2814bd"

def test_endpoints():
    print("[1/3] Testing SEO & AI Crawler Endpoints...")
    endpoints = [
        ("/robots.txt", "text/plain"),
        ("/llms.txt", "text/plain"),
        ("/llms-full.txt", "text/plain"),
        ("/sitemap.xml", "application/xml"),
        ("/sitemap-main.xml", "application/xml"),
        ("/sitemap-categories.xml", "application/xml"),
        ("/sitemap-jobs.xml", "application/xml"),
        ("/jobs/software-engineer", "text/html"),
        ("/jobs/ai-ml-specialist", "text/html"),
        ("/jobs/direct-internships-2026", "text/html"),
        ("/jobs/product-manager", "text/html"),
        ("/feed/internships", "text/html"),
        ("/feed/aiml", "text/html"),
        ("/feed/entrylevel", "text/html"),
    ]

    for path, expected_content_type in endpoints:
        url = BASE_URL + path
        resp = requests.get(url, timeout=10)
        assert resp.status_code == 200, f"Failed {path}: status {resp.status_code}"
        assert expected_content_type in resp.headers.get("content-type", ""), f"Content-type mismatch for {path}: {resp.headers.get('content-type')}"
        print(f"  ✓ {path} -> 200 OK ({len(resp.content)} bytes, {resp.headers.get('content-type')})")

    # Content validations
    robots_text = requests.get(BASE_URL + "/robots.txt").text
    assert "User-agent: Googlebot" in robots_text
    assert "User-agent: GPTBot" in robots_text
    assert "Sitemap: https://almondjobs.com/sitemap.xml" in robots_text
    print("  ✓ /robots.txt validates with standard crawlers & sitemaps")

    llms_text = requests.get(BASE_URL + "/llms.txt").text
    assert "Almond Jobs" in llms_text
    assert "Zero Recruiter Spread" in llms_text
    print("  ✓ /llms.txt validates with Markdown AI manifest")

    sitemap_xml = requests.get(BASE_URL + "/sitemap.xml").text
    assert "<sitemapindex" in sitemap_xml
    assert "sitemap-categories.xml" in sitemap_xml
    print("  ✓ /sitemap.xml validates as valid sitemap index")

    category_html = requests.get(BASE_URL + "/jobs/software-engineer").text
    assert "Direct Software Engineering Openings" in category_html
    assert 'application/ld+json' in category_html
    assert 'JobPosting' in category_html
    print("  ✓ /jobs/software-engineer validates with Google Jobs JobPosting Schema")


def test_browser_and_single_row():
    print("\n[2/3] Testing Browser Rendering & Single-Row Badges...")
    viewports = [
        ("Desktop_1920x1080", 1920, 1080),
        ("Laptop_1440x900", 1440, 900),
        ("Laptop_1366x768", 1366, 768),
        ("Laptop_1280x800", 1280, 800),
        ("Tablet_iPad_768x1024", 768, 1024),
        ("Mobile_iPhone13_390x844", 390, 844)
    ]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        for name, width, height in viewports:
            page = browser.new_page(viewport={"width": width, "height": height})
            page.goto(BASE_URL, wait_until="networkidle")
            
            # Check badges
            b1 = page.locator("#heroBadge_internships")
            b2 = page.locator("#heroBadge_aiml")
            b3 = page.locator("#heroBadge_entrylevel")
            
            assert b1.is_visible(), f"Badge 1 not visible on {name}"
            assert b2.is_visible(), f"Badge 2 not visible on {name}"
            assert b3.is_visible(), f"Badge 3 not visible on {name}"
            
            # Check bounding boxes to verify Y-coordinate alignment on desktop / laptops
            box1 = b1.bounding_box()
            box2 = b2.bounding_box()
            box3 = b3.bounding_box()
            
            # If width >= 1024, all three badges MUST have the same Y coordinate (single horizontal row!)
            if width >= 1024:
                diff_1_2 = abs(box1["y"] - box2["y"])
                diff_2_3 = abs(box2["y"] - box3["y"])
                assert diff_1_2 < 5, f"Badge 1 and 2 not aligned on {name}: {box1['y']} vs {box2['y']}"
                assert diff_2_3 < 5, f"Badge 2 and 3 not aligned on {name}: {box2['y']} vs {box3['y']}"
                print(f"  ✓ {name}: Badges Y-coordinates identical: ({box1['y']:.1f}, {box2['y']:.1f}, {box3['y']:.1f}) -> SINGLE ROW GUARANTEED")
            else:
                diff_1_2 = abs(box1["y"] - box2["y"])
                diff_2_3 = abs(box2["y"] - box3["y"])
                assert diff_1_2 < 5 and diff_2_3 < 5, f"Badges wrapped on {name}: ({box1['y']}, {box2['y']}, {box3['y']})"
                print(f"  ✓ {name}: Badges on single row ({box1['y']:.1f}, {box2['y']:.1f}, {box3['y']:.1f})")

            # Screenshot hero section
            hero_box = page.locator("#heroBadge_internships").evaluate(
                "el => el.closest('.overflow-x-auto').getBoundingClientRect()"
            )
            out_img = os.path.join(ARTIFACT_DIR, f"badges_single_row_{name}.png")
            page.screenshot(path=out_img, clip={
                "x": max(0, hero_box["x"] - 50),
                "y": max(0, hero_box["y"] - 30),
                "width": min(width, hero_box["width"] + 100),
                "height": hero_box["height"] + 60
            })
            page.close()

        # Check category landing page rendering
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto(BASE_URL + "/jobs/software-engineer", wait_until="networkidle")
        h1_text = page.locator("h1").text_content()
        assert "Direct Software Engineering Openings" in h1_text
        cat_img = os.path.join(ARTIFACT_DIR, "seo_landing_page_software_engineer.png")
        page.screenshot(path=cat_img, full_page=True)
        print("  ✓ Programmatic SEO page /jobs/software-engineer rendered cleanly")
        page.close()

        browser.close()

def main():
    test_endpoints()
    test_browser_and_single_row()
    print("\n[3/3] ALL SEO DOMINANCE & SINGLE-ROW BADGE VERIFICATIONS PASSED!")

if __name__ == "__main__":
    main()
