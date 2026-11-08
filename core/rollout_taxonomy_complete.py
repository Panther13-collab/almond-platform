import os
import re

PLATFORM_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SEO_RENDERER_PATH = os.path.join(PLATFORM_DIR, "core", "seo_renderer.py")
SITEMAP_PATH = os.path.join(PLATFORM_DIR, "core", "sitemap_generator.py")
APP_PATH = os.path.join(PLATFORM_DIR, "app.py")
INDEX_PATH = os.path.join(PLATFORM_DIR, "templates", "index.html")

NEW_CATEGORY_DICT_ENTRIES = '''    "it-jobs": {
        "title": "IT Jobs 2026 — 3.3M+ Direct Enterprise Portals (0% Recruiter Spread)",
        "h1": "Direct IT & Information Technology Openings",
        "description": "Bypass recruiter gatekeepers. Ingesting live IT, software development, cloud, and systems engineering roles directly from enterprise ATS servers with zero agency spread.",
        "keywords": "IT jobs, information technology jobs, software jobs 2026, tech jobs direct company, IT career openings",
        "feed_fallback": "entrylevel"
    },
    "non-it-jobs": {
        "title": "Non-IT Jobs 2026 — Direct Corporate Career Openings (0% Recruiter Spread)",
        "h1": "Direct Non-IT & Corporate Management Openings",
        "description": "Explore verified non-IT career openings across Human Resources, Product Management, Finance, FP&A, Operations, and B2B Sales direct from enterprise career gateways.",
        "keywords": "non-IT jobs, non tech jobs in corporate, corporate office jobs, HR jobs, finance jobs, operations manager, sales jobs",
        "feed_fallback": "entrylevel"
    },
    "core-jobs": {
        "title": "Core Jobs 2026 — Mechanical, Electrical & Civil Engineering Direct Feeds",
        "h1": "Direct Core Engineering Openings",
        "description": "Verified core engineering positions across mechanical CAD design, robotics, electrical embedded systems, VLSI, and civil structural engineering with direct employer links.",
        "keywords": "core jobs, core engineering jobs 2026, mechanical core jobs, electrical engineering jobs, civil engineering vacancies, direct corporate engineering",
        "feed_fallback": "entrylevel"
    },
    "free-jobs": {
        "title": "Free Jobs & 100% Direct Application Career Portals (Zero Fees Guaranteed)",
        "h1": "100% Free Direct Application Job Portals",
        "description": "No hidden charges, zero registration fees, zero recruiter markups. Apply directly to verified Fortune 500 & high-growth startup career hubs for free.",
        "keywords": "free jobs, free job search site, free job application portal, 100% free job vacancies, apply to jobs for free, genuine free job vacancies without registration fee",
        "feed_fallback": "entrylevel"
    },
    "high-paying-jobs": {
        "title": "High-Paying Jobs 2026 — Premium IT, AI & Corporate Career Feeds",
        "h1": "Verified High-Paying & High CTC Career Openings",
        "description": "Target unadvertised high-paying software engineering, AI/ML leadership, product management, and corporate executive openings with verified compensation.",
        "keywords": "high-paying jobs, high salary IT jobs, highest paying tech careers, high CTC software jobs, premium engineering vacancies, career jobs",
        "feed_fallback": "aiml"
    },
    "career-jobs": {
        "title": "Career Jobs 2026 — Long-Term Corporate Growth Openings (0% Broker Cuts)",
        "h1": "High-Growth Enterprise Career Openings",
        "description": "Accelerate your career trajectory with direct enterprise positions at industry-leading technology, finance, and engineering organizations.",
        "keywords": "career jobs, best career opportunities 2026, long term corporate careers, high growth tech jobs, enterprise career hubs",
        "feed_fallback": "entrylevel"
    },
    "no-mediator-jobs": {
        "title": "No-Mediator Jobs — Direct Company Ingestion (0% Recruiter Spread)",
        "h1": "Direct Corporate Jobs Without Mediators or Agents",
        "description": "Say goodbye to placement agencies and middlemen. Apply directly to employer internal ATS pipelines (Ashby, Greenhouse, Lever, Workday) with zero commission deductions.",
        "keywords": "no-mediator jobs, no consultancy jobs, jobs without consultancy, zero broker jobs, direct company hiring without consultants, genuine job vacancies without middleman",
        "feed_fallback": "entrylevel"
    },
    "no-consultancy-jobs": {
        "title": "Jobs Without Consultancy 2026 — 100% Direct Company Hiring",
        "h1": "Direct Company Hiring (Zero Consultancy Spread)",
        "description": "Stop dealing with consultancy registration fees and commission cuts. Ingest verified corporate openings directly from hiring managers and internal ATS servers.",
        "keywords": "jobs without consultancy, no consultancy jobs, zero consultancy job portal, direct company application portals, direct HR email jobs, direct corporate hiring",
        "feed_fallback": "entrylevel"
    },
    "service-jobs": {
        "title": "Service Jobs & Corporate Operations Careers 2026 | Almond Direct",
        "h1": "Corporate Service & Technical Operations Openings",
        "description": "Explore verified service operations, customer engineering, technical services, and enterprise solutions roles with direct application links.",
        "keywords": "service job, corporate service jobs, customer engineering vacancies, enterprise support roles, service sector careers",
        "feed_fallback": "entrylevel"
    },
    "hot-jobs": {
        "title": "Hot Jobs & Urgent Hiring Vacancies — Apply Direct Today",
        "h1": "Urgent Hiring & Hot Corporate Job Openings",
        "description": "Fast-track corporate vacancies with active hiring budgets. Apply today before listings are flooded on public job boards.",
        "keywords": "hot jobs, urgent hiring today, urgent requirement software developer, active hiring corporate jobs, fast track applications",
        "feed_fallback": "entrylevel"
    },
    "temporary-jobs": {
        "title": "Temporary & Fast-Track Contract Jobs 2026 — Direct Company Portals",
        "h1": "Temporary, Contract & Fast-Track Corporate Openings",
        "description": "Verified high-compensation contract, temporary, and contract-to-hire tech and business roles with direct corporate links.",
        "keywords": "temporary jobs, contract to hire jobs, tech contract roles, fast track temporary employment, temporary corporate vacancies",
        "feed_fallback": "entrylevel"
    },
    "naukri-alternative": {
        "title": "Naukri Alternative — Direct Corporate ATS Feeds (Zero Recruiter Spam)",
        "h1": "The Modern Alternative to Naukri for Direct Enterprise Careers",
        "description": "Frustrated with recruiter spam, expired reposts, and consultancy calls on Naukri? Almond Jobs queries company ATS servers the exact second roles open.",
        "keywords": "Naukri alternative, Naukri jobs without consultancy, best site like Naukri without fake calls, bypass Naukri consultancies, direct company hiring alternative",
        "feed_fallback": "entrylevel"
    },
    "linkedin-jobs-alternative": {
        "title": "LinkedIn Jobs Alternative — Apply Before the 800-Applicant Swarm",
        "h1": "The Direct Corporate Alternative to LinkedIn Jobs",
        "description": "By the time a job appears on LinkedIn, 800+ people have already applied. Almond Jobs gives you unadvertised direct ATS access so you move first.",
        "keywords": "LinkedIn jobs alternative, apply to jobs before 800 applicants on LinkedIn, unadvertised jobs hidden from LinkedIn, best alternative to LinkedIn jobs",
        "feed_fallback": "entrylevel"
    },
    "smartrecruiters-direct-jobs": {
        "title": "SmartRecruiters Direct Jobs — Search Verified Enterprise Openings",
        "h1": "Direct SmartRecruiters Corporate Career Feeds",
        "description": "Instant real-time search across 45,000+ unlisted openings hosted on SmartRecruiters enterprise pipelines. Apply with 0% recruiter spread.",
        "keywords": "SmartRecruiters direct jobs, SmartRecruiters job search, companies hiring on SmartRecruiters, smartrecruiters portal",
        "feed_fallback": "entrylevel"
    },
    "greenhouse-direct-jobs": {
        "title": "Greenhouse Direct Jobs — Search boards.greenhouse.io Career Portals",
        "h1": "Direct Greenhouse Enterprise Career Openings",
        "description": "Search and apply directly to thousands of high-growth technology and enterprise companies hosting their career boards on Greenhouse.",
        "keywords": "Greenhouse direct corporate jobs, boards.greenhouse.io job listings, greenhouse software jobs, greenhouse tech openings",
        "feed_fallback": "entrylevel"
    },
    "lever-direct-jobs": {
        "title": "Lever Direct Jobs — Search jobs.lever.co Corporate Career Portals",
        "h1": "Direct Lever Corporate Career Openings",
        "description": "Verified direct corporate pipelines across top Silicon Valley and global tech companies using Lever ATS.",
        "keywords": "Lever direct company jobs, jobs.lever.co enterprise directory, lever tech jobs, lever direct application",
        "feed_fallback": "entrylevel"
    },
    "workday-direct-jobs": {
        "title": "Workday Direct Jobs — Enterprise Fortune 500 Career Portals",
        "h1": "Direct Workday Enterprise Career Openings",
        "description": "Direct application pathways to Fortune 500 internal career gateways powered by Workday with tailored STAR application pitches.",
        "keywords": "Workday enterprise career portals, myworkdayjobs direct openings, workday enterprise jobs, workday direct application",
        "feed_fallback": "entrylevel"
    },
    "ashby-direct-jobs": {
        "title": "Ashby Direct Jobs — Search jobs.ashbyhq.com High-Growth Tech Roles",
        "h1": "Direct Ashby HQ Startup & Enterprise Career Openings",
        "description": "Direct links to top Y Combinator and tier-1 venture-backed startups hiring on Ashby HQ ATS.",
        "keywords": "Ashby direct jobs, jobs.ashbyhq.com live openings, ashby tech jobs, YC startup hiring ashby",
        "feed_fallback": "aiml"
    },
'''

def update_seo_renderer():
    with open(SEO_RENDERER_PATH, "r", encoding="utf-8") as f:
        code = f.read()

    if '"it-jobs":' not in code:
        code = code.replace('CATEGORY_DETAILS = {\n', 'CATEGORY_DETAILS = {\n' + NEW_CATEGORY_DICT_ENTRIES, 1)
        with open(SEO_RENDERER_PATH, "w", encoding="utf-8") as f:
            f.write(code)
        print("Updated CATEGORY_DETAILS in seo_renderer.py with 18 high-intent categories.")

def update_sitemap():
    with open(SITEMAP_PATH, "r", encoding="utf-8") as f:
        code = f.read()

    new_sitemap_categories = '''    # High-Intent Working Professional & Competitor Clusters
    ("it-jobs", "IT Jobs 2026 Direct Enterprise Feeds", "1.0"),
    ("non-it-jobs", "Non-IT Corporate Career Openings", "1.0"),
    ("core-jobs", "Core Engineering Jobs 2026", "1.0"),
    ("free-jobs", "Free Direct Application Job Portals", "1.0"),
    ("high-paying-jobs", "High-Paying IT & Tech Careers", "1.0"),
    ("career-jobs", "Career Growth Corporate Openings", "1.0"),
    ("no-mediator-jobs", "No-Mediator Direct Corporate Jobs", "1.0"),
    ("no-consultancy-jobs", "Jobs Without Consultancy Direct Apply", "1.0"),
    ("service-jobs", "Corporate Service Operations Careers", "0.9"),
    ("hot-jobs", "Hot Jobs & Urgent Hiring Vacancies", "1.0"),
    ("temporary-jobs", "Temporary & Contract Tech Jobs", "0.9"),
    ("naukri-alternative", "Naukri Alternative Direct Feeds", "1.0"),
    ("linkedin-jobs-alternative", "LinkedIn Jobs Alternative", "1.0"),
    ("smartrecruiters-direct-jobs", "SmartRecruiters Direct Openings", "1.0"),
'''

    if '("it-jobs"' not in code:
        code = code.replace('CATEGORIES = [\n', 'CATEGORIES = [\n' + new_sitemap_categories, 1)
        with open(SITEMAP_PATH, "w", encoding="utf-8") as f:
            f.write(code)
        print("Updated CATEGORIES in sitemap_generator.py.")

def update_app_routes():
    with open(APP_PATH, "r", encoding="utf-8") as f:
        code = f.read()

    new_aliases = '''@app.get("/it-jobs", response_class=HTMLResponse)
async def serve_it_jobs():
    return HTMLResponse(content=render_category_page("it-jobs"))

@app.get("/non-it-jobs", response_class=HTMLResponse)
async def serve_non_it_jobs():
    return HTMLResponse(content=render_category_page("non-it-jobs"))

@app.get("/core-jobs", response_class=HTMLResponse)
async def serve_core_jobs():
    return HTMLResponse(content=render_category_page("core-jobs"))

@app.get("/free-jobs", response_class=HTMLResponse)
async def serve_free_jobs():
    return HTMLResponse(content=render_category_page("free-jobs"))

@app.get("/high-paying-jobs", response_class=HTMLResponse)
async def serve_high_paying_jobs():
    return HTMLResponse(content=render_category_page("high-paying-jobs"))

@app.get("/no-mediator-jobs", response_class=HTMLResponse)
@app.get("/no-consultancy-jobs", response_class=HTMLResponse)
async def serve_no_mediator_jobs():
    return HTMLResponse(content=render_category_page("no-mediator-jobs"))

@app.get("/naukri-alternative", response_class=HTMLResponse)
async def serve_naukri_alt():
    return HTMLResponse(content=render_category_page("naukri-alternative"))

@app.get("/smartrecruiters-direct", response_class=HTMLResponse)
async def serve_smartrecruiters_direct():
    return HTMLResponse(content=render_category_page("smartrecruiters-direct-jobs"))

'''

    if 'serve_it_jobs' not in code:
        target = '@app.get("/almond-jobs", response_class=HTMLResponse)'
        code = code.replace(target, new_aliases + target, 1)
        with open(APP_PATH, "w", encoding="utf-8") as f:
            f.write(code)
        print("Updated app.py with high-intent alias routes.")

def update_index_html_directory():
    with open(INDEX_PATH, "r", encoding="utf-8") as f:
        html = f.read()

    target_non_it = '<a href="/jobs/product-manager" class="hover:text-violet-600 transition block truncate">Product Manager</a>'
    new_non_it_links = '<a href="/jobs/non-it-jobs" class="hover:text-violet-600 font-extrabold text-violet-700 transition block truncate">★ Non-IT Jobs Direct</a>\n                            <a href="/jobs/career-jobs" class="hover:text-violet-600 font-bold transition block truncate">Career Jobs Hub</a>\n                            '

    target_core = '<a href="/jobs/mechanical-engineer" class="hover:text-violet-600 transition block truncate">Mechanical Core</a>'
    new_core_links = '<a href="/jobs/core-jobs" class="hover:text-emerald-700 font-extrabold transition block truncate">★ Core Jobs Direct</a>\n                            <a href="/jobs/no-mediator-jobs" class="hover:text-emerald-700 font-bold transition block truncate">No-Mediator Jobs</a>\n                            '

    target_ats = '<a href="/jobs/greenhouse-direct-jobs" class="hover:text-violet-600 transition block truncate">Greenhouse Direct</a>'
    new_ats_links = '<a href="/jobs/naukri-alternative" class="hover:text-amber-700 font-extrabold transition block truncate">★ Naukri Alternative</a>\n                            <a href="/jobs/smartrecruiters-direct-jobs" class="hover:text-violet-600 font-bold transition block truncate">SmartRecruiters Direct</a>\n                            '

    if target_non_it in html and '/jobs/non-it-jobs' not in html:
        html = html.replace(target_non_it, new_non_it_links + target_non_it, 1)

    if target_core in html and '/jobs/core-jobs' not in html:
        html = html.replace(target_core, new_core_links + target_core, 1)

    if target_ats in html and '/jobs/naukri-alternative' not in html:
        html = html.replace(target_ats, new_ats_links + target_ats, 1)

    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        f.write(html)
    print("Updated Slide 4 directory in index.html with new category links.")

if __name__ == "__main__":
    update_seo_renderer()
    update_sitemap()
    update_app_routes()
    update_index_html_directory()
    print("TAXONOMY ROLLOUT COMPLETE!")
