import os
import re

PLATFORM_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
INDEX_PATH = os.path.join(PLATFORM_DIR, "templates", "index.html")
SEO_RENDERER_PATH = os.path.join(PLATFORM_DIR, "core", "seo_renderer.py")
SITEMAP_PATH = os.path.join(PLATFORM_DIR, "core", "sitemap_generator.py")
APP_PATH = os.path.join(PLATFORM_DIR, "app.py")
LLMS_PATH = os.path.join(PLATFORM_DIR, "static", "llms.txt")

def update_index_html():
    with open(INDEX_PATH, "r", encoding="utf-8") as f:
        html = f.read()

    # 1. Update <title>
    old_title = '<title>Almond Jobs — 3.3M+ Direct Enterprise Job Openings | Official Career Platform | 0% Recruiter Spread</title>'
    new_title = '<title>Almond Jobs — Find Every Direct Almond Job | 3.3M+ Enterprise Openings (0% Recruiter Spread)</title>'
    if old_title in html:
        html = html.replace(old_title, new_title)
        print("Updated index.html <title>.")

    # 2. Update keywords to place "almond jobs, Almond Jobs, almond job, Almond job" at the absolute front
    old_kw_pattern = r'<meta name="keywords" content=".*?">'
    new_kw = '<meta name="keywords" content="almond jobs, Almond Jobs, almond job, Almond job, almondjobs, almondjob, find almond job, official almond jobs, jobs, interview, IT jobs, non-IT jobs, software engineer jobs, full stack developer, backend engineer, frontend engineer, AI ML specialist, machine learning jobs, data scientist, devops jobs, cloud architect, python developer, java developer, react developer, core engineering, mechanical engineering jobs, electrical engineering jobs, civil engineering jobs, HR jobs, talent acquisition, financial analyst jobs, marketing jobs, sales jobs, direct internships, 2026 freshers, immediate joining jobs, notice period jobs, direct company application, greenhouse jobs, lever jobs, workday jobs, ashby jobs, smartrecruiters direct, bypass recruiters, direct corporate career portals, linkedin alternative, naukri alternative, indeed alternative">'
    html = re.sub(old_kw_pattern, new_kw, html, count=1)
    print("Updated index.html <meta name='keywords'>.")

    # 3. Update meta description
    old_desc = '<meta name="description" content="Almond Jobs (almondjobs.com) is the premier active enterprise job search engine and direct ATS career intelligence portal. Indexing 3,315,000+ live verified job openings straight from Ashby, Greenhouse, Lever, and Workday with 0% recruiter spread. Live IT, AI/ML, core engineering, direct internships, and freshers hiring.">'
    new_desc = '<meta name="description" content="Almond Jobs (almondjobs.com) is the official enterprise direct career portal. Find your next Almond job from 3,315,000+ verified openings ingested directly from Ashby, Greenhouse, Lever, and Workday with 0% recruiter spread. Active, live IT, non-IT, AI/ML, core engineering, and direct corporate internships.">'
    if old_desc in html:
        html = html.replace(old_desc, new_desc)
        print("Updated index.html <meta name='description'>.")

    # 4. Update H1 pill to contain both "Almond Jobs" and "Almond Job"
    old_h1_pill = '<span>Almond Jobs &mdash; 3,315,000+ Direct Enterprise ATS Feeds</span>'
    new_h1_pill = '<span>Almond Jobs &bull; Find Every Direct Almond Job &bull; 3.3M+ Live Feeds</span>'
    if old_h1_pill in html:
        html = html.replace(old_h1_pill, new_h1_pill)
        print("Updated index.html H1 brand pill.")

    # 5. Add dedicated Almond Job search card in #aboutAlmondJobsSection
    about_target = '<div class="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs sm:text-[13px] leading-relaxed">'
    about_card = '''<!-- Keyword Focus: Almond Jobs & Almond Job Dedicated Card -->
                    <div class="p-4 rounded-2xl bg-violet-50/80 border border-violet-200 text-xs text-violet-950 space-y-1.5">
                        <h3 class="font-black text-violet-900 text-xs uppercase tracking-wider flex items-center gap-1.5">
                            <span class="text-violet-600 font-black">★</span> Official Almond Jobs Directory &amp; Almond Job Search
                        </h3>
                        <p class="text-slate-700 leading-relaxed">
                            Looking for verified <strong>Almond Jobs</strong> or searching for a high-paying <strong>Almond job</strong>? <strong>Almond Jobs (almondjobs.com)</strong> connects you directly to internal corporate applicant tracking systems across Fortune 500 &amp; high-growth tech companies with 0% recruiter spread. Every Almond job posting features 100% unrestricted direct links to official employer career gateways.
                        </p>
                    </div>

                    '''
    if about_target in html and "Official Almond Jobs Directory &amp; Almond Job Search" not in html:
        html = html.replace(about_target, about_card + about_target, 1)
        print("Added dedicated Almond Job card to about section.")

    # 6. Add links to /almond-jobs and /almond-job in the directory grid
    dir_target = '<a href="/jobs/software-engineer" class="hover:text-violet-600 transition block truncate">Software Engineer</a>'
    new_links = '<a href="/almond-jobs" class="hover:text-violet-600 font-extrabold text-violet-700 transition block truncate">★ Almond Jobs Direct</a>\n                            <a href="/almond-job" class="hover:text-violet-600 font-bold text-violet-600 transition block truncate">Find Almond Job</a>\n                            '
    if dir_target in html and '/almond-jobs' not in html:
        html = html.replace(dir_target, new_links + dir_target, 1)
        print("Added /almond-jobs and /almond-job links to directory grid.")

    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        f.write(html)
    print("Successfully updated index.html with keyword dominance!")

def update_seo_renderer():
    with open(SEO_RENDERER_PATH, "r", encoding="utf-8") as f:
        code = f.read()

    new_categories = '''    "almond-jobs": {
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
'''

    if '"almond-jobs":' not in code:
        code = code.replace('CATEGORY_DETAILS = {\n', 'CATEGORY_DETAILS = {\n' + new_categories, 1)
        with open(SEO_RENDERER_PATH, "w", encoding="utf-8") as f:
            f.write(code)
        print("Added 'almond-jobs' and 'almond-job' to CATEGORY_DETAILS in seo_renderer.py.")

def update_sitemap():
    with open(SITEMAP_PATH, "r", encoding="utf-8") as f:
        code = f.read()

    new_sitemap_entries = '''    # Brand & Exact-Match Queries (Almond Jobs & Almond Job)
    ("almond-jobs", "Almond Jobs Official Directory", "1.0"),
    ("almond-job", "Almond Job Search Engine", "1.0"),\n'''

    if '("almond-jobs"' not in code:
        code = code.replace('CATEGORIES = [\n', 'CATEGORIES = [\n' + new_sitemap_entries, 1)
        with open(SITEMAP_PATH, "w", encoding="utf-8") as f:
            f.write(code)
        print("Added 'almond-jobs' and 'almond-job' to sitemap CATEGORIES.")

def update_app_routes():
    with open(APP_PATH, "r", encoding="utf-8") as f:
        code = f.read()

    new_routes = '''@app.get("/almond-jobs", response_class=HTMLResponse)
@app.get("/jobs/almond-jobs", response_class=HTMLResponse)
async def serve_almond_jobs_direct():
    return HTMLResponse(content=render_category_page("almond-jobs"))

@app.get("/almond-job", response_class=HTMLResponse)
@app.get("/jobs/almond-job", response_class=HTMLResponse)
async def serve_almond_job_direct():
    return HTMLResponse(content=render_category_page("almond-job"))

'''

    if 'serve_almond_jobs_direct' not in code:
        target = '@app.get("/jobs/{slug}", response_class=HTMLResponse)'
        code = code.replace(target, new_routes + target, 1)
        with open(APP_PATH, "w", encoding="utf-8") as f:
            f.write(code)
        print("Added dedicated /almond-jobs and /almond-job routes to app.py.")

if __name__ == "__main__":
    update_index_html()
    update_seo_renderer()
    update_sitemap()
    update_app_routes()
    print("ALL KEYWORD DOMINANCE UPDATES COMPLETE!")
