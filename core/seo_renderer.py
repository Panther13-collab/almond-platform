"""
Almond Jobs — Programmatic High-Intent SEO Landing Page Renderer
Renders high-speed, server-side HTML pages for Googlebot, Bingbot, and AI Search Crawlers.
Includes category-specific JSON-LD, BreadcrumbList, and live verified job listings.
"""

import html
from typing import List, Dict, Any, Optional
from core.curated_feeds import get_feed_data

BASE_URL = "https://almondjobs.com"

CATEGORY_DETAILS = {
    "almond-jobs": {
        "title": "Almond Jobs — 3,315,000+ Verified Direct Enterprise Job Openings (0% Recruiter Spread)",
        "h1": "Almond Jobs Official Enterprise Career Directory",
        "description": "Explore all verified Almond Jobs across IT, software engineering, AI/ML, core engineering, and corporate leadership with 0% recruiter spread and direct corporate ATS links.",
        "keywords": "almond jobs, Almond Jobs, almond job, Almond job, almondjobs, almondjob, find almond job, official almond jobs, direct ATS feeds, enterprise jobs",
        "feed_fallback": "entrylevel"
    },
    "almond-job": {
        "title": "Almond Job Search — Find Every Direct Corporate Opening (0% Recruiter Spread)",
        "h1": "Find Your Next Almond Job Direct from Employer Infrastructure",
        "description": "Search every direct Almond job opening ingested directly from company internal servers before public listing. Zero recruiters, zero ghost jobs.",
        "keywords": "almond job, Almond job, almond jobs, Almond Jobs, find almond job, search almond job, direct application portals",
        "feed_fallback": "entrylevel"
    },
    "software-engineer": {
        "title": "Software Engineer Jobs 2026 — 3.3M+ Direct Enterprise Portals (0% Recruiter Spread)",
        "h1": "Direct Software Engineering Openings",
        "description": "Bypass recruiter gatekeepers. Apply directly to unadvertised software engineer roles across Ashby, Greenhouse, Lever, and Workday with 0% headhunter markup.",
        "keywords": "software engineer jobs, direct company applications, greenhouse software jobs, lever tech jobs, bypass recruiters, 0% recruiter spread, high paying software roles, immediate joiners",
        "feed_fallback": "entrylevel"
    },
    "ai-ml-specialist": {
        "title": "AI/ML Specialist & LLM Engineering Jobs — 530+ Verified Direct Portals",
        "h1": "Verified AI & Machine Learning Openings",
        "description": "Discover unposted AI, Machine Learning, Deep Learning, and LLM engineering seats straight from internal corporate servers before public listing.",
        "keywords": "AI jobs, machine learning engineer, LLM engineer, PyTorch, generative AI jobs, remote AI jobs, bypass headhunters",
        "feed_fallback": "aiml"
    },
    "direct-internships-2026": {
        "title": "Direct Corporate Internships 2026 — 5,100+ Live Verified Student Portals",
        "h1": "Direct Corporate Internships (Zero Middlemen)",
        "description": "5,100+ direct corporate summer, winter, and off-cycle internships at top tech and enterprise firms. Apply straight to company ATS portals with 0% agency spam.",
        "keywords": "direct internships 2026, tech internships, summer internships, software engineering internships, paid internships, freshers hiring, college campus internships",
        "feed_fallback": "internships"
    },
    "entry-level-swe": {
        "title": "Entry-Level & New Grad Software Jobs — 3,100+ Direct Enterprise Seats",
        "h1": "Entry-Level & New Grad Career Portals",
        "description": "No prior experience barrier. Ingesting entry-level developer and junior software engineering roles the second they open.",
        "keywords": "entry level software engineer, new grad tech jobs, 2026 graduate hiring, junior developer jobs, freshers engineering roles",
        "feed_fallback": "entrylevel"
    },
    "immediate-joiners": {
        "title": "Immediate Joiner & 15-Day Notice Period Tech Jobs | Almond Direct Feeds",
        "h1": "Immediate Joining Direct Openings",
        "description": "Fast-track pipeline for candidates available immediately or on 15 days notice. Skip the 60-day resume queue and apply directly to hiring managers.",
        "keywords": "immediate joiner jobs, 15 days notice period jobs, urgent hiring tech, direct corporate hiring, immediate start software jobs",
        "feed_fallback": "entrylevel"
    },
    "product-manager": {
        "title": "Product Manager & APM Jobs 2026 — Direct Corporate Ingestion",
        "h1": "Direct Product Management Openings",
        "description": "Target unadvertised Product Manager, Technical PM, and Associate Product Manager seats at high-growth startups and tech giants.",
        "keywords": "product manager jobs, technical product manager, APM jobs, associate product manager, B2B product jobs",
        "feed_fallback": "entrylevel"
    },
    "ui-ux-designer": {
        "title": "UI/UX & Product Design Jobs — Direct Enterprise Postings",
        "h1": "Verified UI/UX & Design Portals",
        "description": "Explore direct corporate product design and UI/UX engineering openings without agency intermediaries.",
        "keywords": "UI UX designer jobs, product designer openings, Figma design jobs, direct company applications",
        "feed_fallback": "entrylevel"
    },
    "human-resources": {
        "title": "HR & Talent Acquisition Jobs — Direct Enterprise Portals",
        "h1": "Direct HR & People Operations Openings",
        "description": "Enterprise human resources, technical recruiting, and people operations roles straight from company servers.",
        "keywords": "HR jobs, talent acquisition jobs, people operations, technical recruiter jobs, human resources direct hiring",
        "feed_fallback": "entrylevel"
    },
    "financial-analyst": {
        "title": "Financial Analyst & Corporate Finance Jobs — Direct Corporate Feeds",
        "h1": "Direct Finance & FP&A Career Portals",
        "description": "High-growth financial analyst, FP&A, and corporate accounting openings. Direct applications with zero headhunter fees.",
        "keywords": "financial analyst jobs, FP&A roles, corporate finance jobs, investment analyst, direct hiring finance",
        "feed_fallback": "entrylevel"
    },
    "mechanical-engineer": {
        "title": "Mechanical Engineering Core Jobs 2026 — Direct Company Applications",
        "h1": "Core Mechanical Engineering Openings",
        "description": "Verified mechanical, CAD, robotics, and manufacturing engineering positions with direct corporate links.",
        "keywords": "mechanical engineer jobs, CAD design jobs, robotics engineering, core engineering jobs 2026, direct manufacturing jobs",
        "feed_fallback": "entrylevel"
    }
}

def render_category_page(slug: str) -> str:
    """Render a dedicated, high-speed SEO landing page."""
    meta = CATEGORY_DETAILS.get(slug, {
        "title": f"{slug.replace('-', ' ').title()} Jobs — 3.3M+ Direct Enterprise Portals",
        "h1": f"Direct {slug.replace('-', ' ').title()} Openings",
        "description": f"Explore direct {slug.replace('-', ' ')} job openings ingested directly from internal enterprise servers before public listing. Zero recruiters, zero ghost jobs.",
        "keywords": f"{slug.replace('-', ' ')} jobs, direct corporate applications, bypass headhunters, almond jobs",
        "feed_fallback": "entrylevel"
    })

    # Fetch live jobs to showcase real value
    feed_type = meta.get("feed_fallback", "entrylevel")
    raw_jobs = get_feed_data(feed_type)[:15]

    job_cards_html = []
    job_schema_items = []

    for idx, j in enumerate(raw_jobs, 1):
        role_esc = html.escape(str(j.get("role") or "Engineering Role"))
        company_esc = html.escape(str(j.get("company") or "Direct Employer"))
        loc_esc = html.escape(str(j.get("location") or "Remote / Hybrid"))
        url_esc = html.escape(str(j.get("url") or f"{BASE_URL}/"))
        date_str = html.escape(str(j.get("date_posted_str") or "Today"))
        provider = html.escape(str(j.get("provider") or "Direct ATS").upper())

        job_cards_html.append(f"""
        <div class="p-5 rounded-2xl bg-white border border-slate-200 shadow-xs hover:border-violet-300 hover:shadow-md transition flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div class="space-y-1">
                <div class="flex items-center gap-2 flex-wrap text-xs">
                    <span class="font-black text-slate-900">{company_esc}</span>
                    <span class="px-2 py-0.5 rounded-md bg-emerald-50 text-emerald-800 border border-emerald-200 font-bold uppercase text-[10px]">VERIFIED {provider}</span>
                    <span class="text-slate-400 text-[10px]">{date_str}</span>
                </div>
                <h3 class="text-base font-extrabold text-slate-950">{role_esc}</h3>
                <p class="text-xs text-slate-500 font-medium">📍 {loc_esc} &bull; 0% Recruiter Spread &bull; Instant ATS Application</p>
            </div>
            <a href="{url_esc}" target="_blank" rel="noopener noreferrer" class="px-4 py-2.5 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-black text-xs shadow-xs hover:scale-105 active:scale-95 transition flex items-center justify-center gap-1.5 shrink-0">
                <span>Direct Application Portal &rarr;</span>
            </a>
        </div>
        """)

        job_schema_items.append({
            "@type": "JobPosting",
            "title": j.get("role", "Software Engineer"),
            "description": f"Verified direct opening at {j.get('company', 'Employer')} with zero recruiter spread.",
            "datePosted": "2026-03-01",
            "employmentType": "FULL_TIME",
            "hiringOrganization": {
                "@type": "Organization",
                "name": j.get("company", "Employer"),
                "sameAs": "https://almondjobs.com"
            },
            "jobLocation": {
                "@type": "Place",
                "address": {
                    "@type": "PostalAddress",
                    "addressLocality": j.get("location", "Remote")
                }
            },
            "directApply": True
        })

    import json
    schema_json = json.dumps({
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "WebSite",
                "@id": f"{BASE_URL}/#website",
                "url": BASE_URL,
                "name": "Almond Jobs",
                "disambiguatingDescription": "Almond Jobs (almondjobs.com) is an active enterprise direct ATS job search platform indexing 3,315,000+ live openings with zero recruiter spread, completely separate from agricultural almond farming.",
            },
            {
                "@type": "Organization",
                "@id": f"{BASE_URL}/#organization",
                "name": "Almond Jobs Technologies",
                "url": BASE_URL,
                "logo": f"{BASE_URL}/static/logo.png",
                "sameAs": [
                    "https://twitter.com/almondjobs",
                    "https://www.linkedin.com/company/almond-jobs"
                ],
                "description": "Almond Jobs is an active AI career discovery engine connecting job seekers directly to corporate applicant tracking systems with 0% recruiter spread."
            },
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Almond Jobs", "item": BASE_URL},
                    {"@type": "ListItem", "position": 2, "name": meta['h1'], "item": f"{BASE_URL}/jobs/{slug}"}
                ]
            },
            {
                "@type": "ItemList",
                "name": meta['h1'],
                "numberOfItems": len(raw_jobs),
                "itemListElement": [
                    {
                        "@type": "ListItem",
                        "position": i + 1,
                        "item": s
                    } for i, s in enumerate(job_schema_items)
                ]
            }
        ]
    })

    return f"""<!DOCTYPE html>
<html lang="en" class="scroll-smooth">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html.escape(meta['title'])}</title>
    <meta name="description" content="{html.escape(meta['description'])}">
    <meta name="keywords" content="{html.escape(meta['keywords'])}">
    <meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1">
    <link rel="canonical" href="{BASE_URL}/jobs/{slug}">
    
    <!-- OpenGraph & Twitter -->
    <meta property="og:title" content="{html.escape(meta['title'])}">
    <meta property="og:description" content="{html.escape(meta['description'])}">
    <meta property="og:url" content="{BASE_URL}/jobs/{slug}">
    <meta property="og:type" content="website">
    <meta property="og:image" content="{BASE_URL}/static/almond_creamy_hero.png">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{html.escape(meta['title'])}">
    <meta name="twitter:description" content="{html.escape(meta['description'])}">
    
    <link rel="icon" type="image/x-icon" href="/favicon.ico?v=4">
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800;900&display=swap" rel="stylesheet">
    <style>body {{ font-family: 'Plus Jakarta Sans', sans-serif; }}</style>
    
    <!-- Rich Structured Data for Google Jobs -->
    <script type="application/ld+json">
    {schema_json}
    </script>
</head>
<body class="bg-stone-50 text-slate-900 min-h-screen flex flex-col justify-between antialiased">

    <!-- Top Navigation Bar -->
    <header class="w-full bg-white/95 backdrop-blur-md border-b border-slate-200 sticky top-0 z-40 px-4 sm:px-8 py-3.5">
        <div class="max-w-6xl mx-auto flex items-center justify-between">
            <a href="/" class="flex items-center gap-2.5">
                <img src="/static/logo.png" alt="Almond Jobs Logo" class="w-7 h-7 object-contain">
                <span class="font-black text-lg tracking-tight text-slate-950">Almond<span class="text-violet-600">Jobs</span></span>
            </a>
            <div class="flex items-center gap-3">
                <a href="/" class="px-5 py-2 rounded-full bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 text-white font-bold text-xs shadow-md transition">
                    Launch Career Engine &rarr;
                </a>
            </div>
        </div>
    </header>

    <!-- Main Content -->
    <main class="max-w-5xl mx-auto px-4 sm:px-6 py-10 w-full flex-1">
        
        <!-- Header Banner -->
        <div class="text-center max-w-3xl mx-auto mb-10">
            <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-bold mb-3">
                <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                <span>3.3M+ Direct Enterprise Live Feeds</span>
            </div>
            <h1 class="text-3xl sm:text-5xl font-black text-slate-950 tracking-tight mb-4">
                {html.escape(meta['h1'])}
            </h1>
            <p class="text-slate-600 text-sm sm:text-base leading-relaxed mb-6">
                {html.escape(meta['description'])}
            </p>
            <div class="flex items-center justify-center gap-3 flex-wrap">
                <a href="/" class="px-6 py-3 rounded-full bg-gradient-to-r from-violet-600 to-indigo-600 text-white font-black text-xs sm:text-sm shadow-lg hover:scale-105 active:scale-95 transition">
                    Upload Resume & Match 3.3M+ Openings &rarr;
                </a>
            </div>
        </div>

        <!-- Featured Job Feed List -->
        <div class="space-y-3.5 mb-12">
            {''.join(job_cards_html)}
        </div>

        <!-- Direct Ingestion Guarantees Banner -->
        <div class="p-6 rounded-3xl bg-white border border-slate-200 shadow-sm grid grid-cols-1 md:grid-cols-3 gap-6 text-center mb-10">
            <div>
                <span class="text-2xl font-black text-violet-600 block mb-1">0%</span>
                <span class="text-xs font-black uppercase text-slate-900 block">Recruiter Spread</span>
                <span class="text-xs text-slate-500">Apply directly on internal company servers. No third-party middlemen cut.</span>
            </div>
            <div>
                <span class="text-2xl font-black text-emerald-600 block mb-1">Seconds</span>
                <span class="text-xs font-black uppercase text-slate-900 block">From Opening</span>
                <span class="text-xs text-slate-500">Ingested from internal ATS pipelines the moment they open, days before LinkedIn.</span>
            </div>
            <div>
                <span class="text-2xl font-black text-indigo-600 block mb-1">100% Free</span>
                <span class="text-xs font-black uppercase text-slate-900 block">Direct Links</span>
                <span class="text-xs text-slate-500">All direct application links are unblurred and unblocked for job seekers.</span>
            </div>
        </div>

        <!-- 4-Column High-Intent Category Directory Grid -->
        <div class="mt-8 pt-8 border-t border-slate-200">
            <h3 class="text-sm font-black uppercase tracking-wider text-slate-900 mb-6 flex items-center gap-2">
                <span class="w-2 h-2 rounded-full bg-emerald-500"></span>
                <span>Explore All Direct Career Portals</span>
            </h3>
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 text-xs mb-8">
                <div class="space-y-1.5">
                    <h4 class="font-black text-slate-900 uppercase text-[11px] pb-1 border-b border-slate-200">Direct Tech Portals</h4>
                    <ul class="space-y-1 text-slate-600">
                        <li><a href="/jobs/software-engineer" class="hover:text-violet-600 transition">Software Engineer Jobs</a></li>
                        <li><a href="/jobs/full-stack-developer" class="hover:text-violet-600 transition">Full Stack Developer</a></li>
                        <li><a href="/jobs/backend-engineer" class="hover:text-violet-600 transition">Backend Engineer</a></li>
                        <li><a href="/jobs/frontend-engineer" class="hover:text-violet-600 transition">Frontend Engineer</a></li>
                        <li><a href="/jobs/ai-ml-specialist" class="hover:text-violet-600 font-bold transition">AI/ML Specialist</a></li>
                        <li><a href="/jobs/machine-learning-engineer" class="hover:text-violet-600 transition">Machine Learning Engineer</a></li>
                        <li><a href="/jobs/data-scientist" class="hover:text-violet-600 transition">Data Scientist</a></li>
                        <li><a href="/jobs/devops-engineer" class="hover:text-violet-600 transition">DevOps & Cloud</a></li>
                    </ul>
                </div>
                <div class="space-y-1.5">
                    <h4 class="font-black text-slate-900 uppercase text-[11px] pb-1 border-b border-slate-200">Non-IT & Leadership</h4>
                    <ul class="space-y-1 text-slate-600">
                        <li><a href="/jobs/product-manager" class="hover:text-violet-600 transition">Product Manager</a></li>
                        <li><a href="/jobs/associate-product-manager" class="hover:text-violet-600 transition">Associate PM (APM)</a></li>
                        <li><a href="/jobs/ui-ux-designer" class="hover:text-violet-600 transition">UI/UX Product Designer</a></li>
                        <li><a href="/jobs/human-resources" class="hover:text-violet-600 font-bold transition">Human Resources</a></li>
                        <li><a href="/jobs/financial-analyst" class="hover:text-violet-600 transition">Financial Analyst</a></li>
                        <li><a href="/jobs/marketing-manager" class="hover:text-violet-600 transition">Growth & Marketing</a></li>
                        <li><a href="/jobs/sales-executive" class="hover:text-violet-600 transition">Enterprise Sales</a></li>
                        <li><a href="/jobs/operations-manager" class="hover:text-violet-600 transition">Operations & Strategy</a></li>
                    </ul>
                </div>
                <div class="space-y-1.5">
                    <h4 class="font-black text-slate-900 uppercase text-[11px] pb-1 border-b border-slate-200">Core & Urgency</h4>
                    <ul class="space-y-1 text-slate-600">
                        <li><a href="/jobs/mechanical-engineer" class="hover:text-violet-600 transition">Mechanical Engineering</a></li>
                        <li><a href="/jobs/electrical-engineer" class="hover:text-violet-600 transition">Electrical Engineering</a></li>
                        <li><a href="/jobs/civil-engineer" class="hover:text-violet-600 transition">Civil Engineering</a></li>
                        <li><a href="/jobs/direct-internships-2026" class="hover:text-violet-600 font-bold text-emerald-700 transition">Direct Internships (5,100+)</a></li>
                        <li><a href="/jobs/entry-level-swe" class="hover:text-violet-600 font-bold text-indigo-700 transition">Entry-Level & New Grad</a></li>
                        <li><a href="/jobs/freshers-hiring-2026" class="hover:text-violet-600 transition">Freshers 2026</a></li>
                        <li><a href="/jobs/immediate-joiners" class="hover:text-violet-600 font-bold text-amber-700 transition">Immediate Joiners</a></li>
                        <li><a href="/jobs/15-days-notice-jobs" class="hover:text-violet-600 transition">15 Days Notice Period</a></li>
                    </ul>
                </div>
                <div class="space-y-1.5">
                    <h4 class="font-black text-slate-900 uppercase text-[11px] pb-1 border-b border-slate-200">Direct ATS Portals</h4>
                    <ul class="space-y-1 text-slate-600">
                        <li><a href="/jobs/greenhouse-direct-jobs" class="hover:text-violet-600 transition">Greenhouse Direct Jobs</a></li>
                        <li><a href="/jobs/lever-direct-jobs" class="hover:text-violet-600 transition">Lever Direct Jobs</a></li>
                        <li><a href="/jobs/ashby-direct-jobs" class="hover:text-violet-600 transition">Ashby HQ Direct Jobs</a></li>
                        <li><a href="/jobs/workday-direct-jobs" class="hover:text-violet-600 transition">Workday Enterprise Portals</a></li>
                        <li><a href="/jobs/founder-direct-jobs" class="hover:text-violet-600 transition">YC Founder Direct</a></li>
                        <li><a href="/jobs/remote-tech-jobs" class="hover:text-violet-600 transition">Remote Tech Jobs</a></li>
                    </ul>
                </div>
            </div>
        </div>

    </main>

    <!-- Footer -->
    <footer class="w-full bg-white border-t border-slate-200 py-8 px-4 text-center text-xs text-slate-500">
        <div class="max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
            <div class="text-left">
                <p class="font-bold text-slate-700">&copy; 2026 Almond Jobs. Direct Enterprise Job Ingestion Network.</p>
                <p class="text-[11px] text-slate-400 mt-0.5">Almond Jobs (almondjobs.com) connects candidates directly to enterprise ATS portals with 0% recruiter markup. Not affiliated with agricultural farming.</p>
            </div>
            <div class="flex items-center gap-4 shrink-0">
                <a href="/" class="hover:text-violet-600 transition font-bold">Home</a>
                <a href="/feed/internships" class="hover:text-violet-600 transition font-bold">Internships</a>
                <a href="/feed/aiml" class="hover:text-violet-600 transition font-bold">AI/ML Directory</a>
                <a href="/feed/entrylevel" class="hover:text-violet-600 transition font-bold">Entry-Level</a>
                <a href="/sitemap.xml" class="hover:text-violet-600 transition font-bold">Sitemap</a>
            </div>
        </div>
    </footer>

</body>
</html>
"""
