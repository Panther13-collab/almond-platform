"""
Almond Jobs — Programmatic XML Sitemap Generator
Generates Google Search Console, Bing, and AI crawler compliant XML sitemaps.
Includes Sitemap Index, Core URLs, Category Hubs, and Live Job Openings.
"""

import time
from datetime import datetime, timezone
from typing import List, Dict, Any
from core.curated_feeds import get_feed_data

BASE_URL = "https://almondjobs.com"

# High-Intent Categories spanning IT, Non-IT, Core Engineering, Freshers, and Immediate Joiners
CATEGORIES = [
    # Brand & Exact-Match Queries (Almond Jobs & Almond Job)
    ("almond-jobs", "Almond Jobs Official Directory", "1.0"),
    ("almond-job", "Almond Job Search Engine", "1.0"),
    # Core IT & Tech
    ("software-engineer", "Software Engineer Jobs", "0.9"),
    ("full-stack-developer", "Full Stack Developer Jobs", "0.9"),
    ("backend-engineer", "Backend Engineer Jobs", "0.9"),
    ("frontend-engineer", "Frontend Engineer Jobs", "0.9"),
    ("ai-ml-specialist", "AI ML Specialist Jobs", "1.0"),
    ("machine-learning-engineer", "Machine Learning Engineer Jobs", "0.9"),
    ("data-scientist", "Data Scientist Jobs", "0.9"),
    ("data-engineer", "Data Engineer Jobs", "0.8"),
    ("devops-engineer", "DevOps & Cloud Engineer Jobs", "0.8"),
    ("cloud-architect", "Cloud Architect AWS GCP Jobs", "0.8"),
    ("python-developer", "Python Developer Jobs", "0.8"),
    ("react-developer", "React Frontend Developer Jobs", "0.8"),
    ("cybersecurity-engineer", "Cybersecurity Engineer Jobs", "0.8"),
    ("mobile-developer", "iOS and Android Mobile Developer Jobs", "0.8"),

    # Non-IT, Management & Business
    ("product-manager", "Product Manager Jobs", "0.9"),
    ("associate-product-manager", "Associate Product Manager APM Jobs", "0.8"),
    ("ui-ux-designer", "UI UX Product Designer Jobs", "0.8"),
    ("human-resources", "Human Resources & Talent Acquisition Jobs", "0.8"),
    ("financial-analyst", "Financial Analyst & FP&A Jobs", "0.8"),
    ("marketing-manager", "B2B Marketing & Growth Jobs", "0.8"),
    ("sales-executive", "Enterprise Sales & Business Development Jobs", "0.7"),
    ("operations-manager", "Business Operations Jobs", "0.7"),

    # Core Engineering
    ("mechanical-engineer", "Mechanical Engineering Core Jobs", "0.8"),
    ("electrical-engineer", "Electrical & Embedded Systems Jobs", "0.8"),
    ("civil-engineer", "Civil & Structural Engineering Jobs", "0.7"),

    # Status & Urgency
    ("direct-internships-2026", "Direct Corporate Internships 2026", "1.0"),
    ("entry-level-swe", "Entry Level & New Grad Software Jobs", "1.0"),
    ("freshers-hiring-2026", "Campus Freshers Hiring 2026", "0.9"),
    ("immediate-joiners", "Immediate Joining Tech Jobs", "0.9"),
    ("15-days-notice-jobs", "15 Days Notice Period Direct Openings", "0.9"),
    ("remote-tech-jobs", "Remote Worldwide Software Jobs", "0.9"),

    # Direct ATS Feeds
    ("greenhouse-direct-jobs", "Greenhouse Direct Corporate Postings", "0.8"),
    ("lever-direct-jobs", "Lever Direct Corporate Postings", "0.8"),
    ("ashby-direct-jobs", "Ashby HQ Direct Corporate Postings", "0.8"),
    ("workday-direct-jobs", "Workday Enterprise Direct Jobs", "0.8"),
    ("founder-direct-jobs", "YC & Hacker News Founder Direct Jobs", "0.9"),
]

def _iso_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")

def generate_sitemap_index() -> str:
    """Master sitemap index pointing to sub-sitemaps."""
    today = _iso_now()
    xml = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
        f'  <sitemap><loc>{BASE_URL}/sitemap-main.xml</loc><lastmod>{today}</lastmod></sitemap>',
        f'  <sitemap><loc>{BASE_URL}/sitemap-categories.xml</loc><lastmod>{today}</lastmod></sitemap>',
        f'  <sitemap><loc>{BASE_URL}/sitemap-jobs.xml</loc><lastmod>{today}</lastmod></sitemap>',
        '</sitemapindex>'
    ]
    return '\n'.join(xml)

def generate_main_sitemap() -> str:
    """Core platform pages sitemap."""
    today = _iso_now()
    pages = [
        ("/", "always", "1.0"),
        ("/feed/internships", "hourly", "1.0"),
        ("/feed/aiml", "hourly", "1.0"),
        ("/feed/entrylevel", "hourly", "1.0"),
        ("/kage-preview", "daily", "0.7"),
    ]
    xml = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
    ]
    for path, changefreq, priority in pages:
        xml.append('  <url>')
        xml.append(f'    <loc>{BASE_URL}{path}</loc>')
        xml.append(f'    <lastmod>{today}</lastmod>')
        xml.append(f'    <changefreq>{changefreq}</changefreq>')
        xml.append(f'    <priority>{priority}</priority>')
        xml.append('  </url>')
    xml.append('</urlset>')
    return '\n'.join(xml)

def generate_categories_sitemap() -> str:
    """High-intent category and keyword landing pages."""
    today = _iso_now()
    xml = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
    ]
    for slug, _, priority in CATEGORIES:
        xml.append('  <url>')
        xml.append(f'    <loc>{BASE_URL}/jobs/{slug}</loc>')
        xml.append(f'    <lastmod>{today}</lastmod>')
        xml.append('    <changefreq>daily</changefreq>')
        xml.append(f'    <priority>{priority}</priority>')
        xml.append('  </url>')
    xml.append('</urlset>')
    return '\n'.join(xml)

def generate_jobs_sitemap() -> str:
    """Live direct enterprise job openings."""
    today = _iso_now()
    all_jobs: List[Dict[str, Any]] = []

    for f_type in ["internships", "aiml", "entrylevel"]:
        feed_items = get_feed_data(f_type)
        all_jobs.extend(feed_items[:400])

    xml = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
    ]

    seen_slugs = set()
    for item in all_jobs:
        company = (item.get("company") or "direct").lower().replace(" ", "-").replace("/", "-")
        role = (item.get("role") or "opening").lower().replace(" ", "-").replace("/", "-")
        # sanitize slug
        clean_slug = "".join(c for c in f"{company}-{role}" if c.isalnum() or c == "-")[:80]
        if not clean_slug or clean_slug in seen_slugs:
            continue
        seen_slugs.add(clean_slug)

        xml.append('  <url>')
        xml.append(f'    <loc>{BASE_URL}/jobs/{clean_slug}</loc>')
        xml.append(f'    <lastmod>{today}</lastmod>')
        xml.append('    <changefreq>daily</changefreq>')
        xml.append('    <priority>0.8</priority>')
        xml.append('  </url>')

    xml.append('</urlset>')
    return '\n'.join(xml)
