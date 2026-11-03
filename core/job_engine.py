import urllib.request
import urllib.parse
import json
import time
import re
import copy
import threading
from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup

# Fast In-Memory Cache for Candidates with Similar Skills / Roles
_RESUME_SEARCH_CACHE: Dict[str, Dict[str, Any]] = {}
_SEARCH_CACHE_LOCK = threading.Lock()
_SEARCH_CACHE_TTL = 7200  # 2 Hours

def _get_skills_fingerprint(candidate_profile: Dict[str, Any], preferences: Dict[str, Any]) -> str:
    """Generates a normalized fingerprint for matching candidates with similar skills and search criteria."""
    raw_skills = candidate_profile.get("skills") or []
    norm_skills = sorted(list(set(re.sub(r'[^a-z0-9]', '', s.lower()) for s in raw_skills if s)))
    top_skills_str = ",".join(norm_skills[:10])
    target_role = re.sub(r'[^a-z0-9]', '', (candidate_profile.get("target_role") or "").lower())
    locations = sorted(list(set(re.sub(r'[^a-z0-9]', '', l.lower()) for l in (preferences.get("locations") or []))))
    locations_str = ",".join(locations)
    work_mode = preferences.get("work_mode", "all")
    emp_type = preferences.get("employment_type", "all")
    currency = preferences.get("currency", "INR")
    min_pkg = str(preferences.get("min_package", 15.0))
    incl_li = str(preferences.get("include_linkedin", False))
    return f"{target_role}|{top_skills_str}|{locations_str}|{work_mode}|{emp_type}|{currency}|{min_pkg}|{incl_li}"

DIRECT_ATS_DOMAINS = [
    "greenhouse.io", "lever.co", "myworkdayjobs.com", "bamboohr.com", 
    "smartrecruiters.com", "ashbyhq.com", "recruitee.com", "workable.com",
    "icims.com", "successfactors.com", "taleo.net", "jobvite.com", "pinpointhq.com",
    "breezy.hr", "applytojob.com", "oraclecloud.com", "zohorecruit.com", "zohorecruit.in",
    "manatal.com", "careers-page.com", "mercedes-benz.com", "cargill.com", "ing.com",
    "getonbrd.com", "powertofly.com", "rippling.com", "workday.com", "keka.com",
    "darwinbox.in", "darwinbox.com", "edag.com", "bosch.com", "alten.com", "segula.com",
    "forvia.com", "visteon.com", "chartindustries.com", "ltrecruitment.in", "lntedutech.com",
    "ltts.com", "brassring.com", "avature.net"
]

CITY_ALIASES = {
    "bengaluru": ["bengaluru", "bangalore", "bangaluru", "blr"],
    "bangalore": ["bengaluru", "bangalore", "bangaluru", "blr"],
    "chennai": ["chennai", "madras"],
    "coimbatore": ["coimbatore", "kovai"],
    "mumbai": ["mumbai", "bombay"],
    "delhi": ["delhi", "new delhi", "noida", "gurgaon", "gurugram", "ncr"],
    "kochi": ["kochi", "cochin", "ernakulam"],
    "thiruvananthapuram": ["trivandrum", "thiruvananthapuram"],
    "pune": ["pune", "poona"],
    "hyderabad": ["hyderabad", "secunderabad"]
}

COUNTRY_CODE_MAP = {
    "india": ["in", "ind", "india"],
    "united states": ["us", "usa", "united states"],
    "united kingdom": ["gb", "uk", "united kingdom", "england", "scotland"],
    "canada": ["ca", "can", "canada"],
    "germany": ["de", "deu", "germany", "deutschland"],
    "netherlands": ["nl", "nld", "netherlands", "holland"],
    "france": ["fr", "fra", "france"],
    "australia": ["au", "aus", "australia"],
    "singapore": ["sg", "sgp", "singapore"],
    "united arab emirates": ["ae", "are", "uae", "dubai", "abu dhabi"],
    "switzerland": ["ch", "che", "switzerland"],
    "ireland": ["ie", "irl", "ireland"],
    "spain": ["es", "esp", "spain"],
    "japan": ["jp", "jpn", "japan"],
    "brazil": ["br", "bra", "brazil"],
    "europe": ["eu", "europe", "emea"],
}

STATE_REGION_MAP = {
    "tamil nadu": ["chennai", "coimbatore", "madurai", "salem", "tiruchirappalli", "tamil nadu", "tn"],
    "karnataka": ["bengaluru", "bangaluru", "bangalore", "mysore", "mysuru", "mangalore", "hubballi", "karnataka", "ka"],
    "kerala": ["kochi", "cochin", "ernakulam", "trivandrum", "thiruvananthapuram", "calicut", "kozhikode", "kerala", "kl"],
    "telangana": ["hyderabad", "secunderabad", "telangana"],
    "maharashtra": ["mumbai", "pune", "nagpur", "maharashtra"],
    "delhi": ["delhi", "new delhi", "noida", "gurgaon", "gurugram", "ncr"],
    "california": ["san francisco", "sf", "san jose", "silicon valley", "los angeles", "san diego", "ca", "california"],
    "new york": ["new york", "nyc", "manhattan", "brooklyn", "ny"],
    "texas": ["austin", "dallas", "houston", "tx"],
    "washington": ["seattle", "bellevue", "redmond", "wa"]
}

_FEED_CACHE = {}
_CACHE_TTL = 1800  # 30 minutes in seconds

def clean_job_url(raw_url: str) -> str:
    if not raw_url:
        return ""
    # Strip utm_source=freehire.me or any tracking tags
    cleaned = re.sub(r'[?&]utm_source=freehire\.me(&|$)?', '', raw_url)
    cleaned = re.sub(r'[?&]utm_[^&]+(&|$)?', '', cleaned)
    if cleaned.endswith('?') or cleaned.endswith('&'):
        cleaned = cleaned[:-1]
    return cleaned

def query_enterprise_feed(params):
    cache_key = urllib.parse.urlencode(sorted(params.items()))
    now = time.time()
    if cache_key in _FEED_CACHE:
        cached_time, cached_data = _FEED_CACHE[cache_key]
        if now - cached_time < _CACHE_TTL:
            return cached_data

    base_url = "https://freehire.me/api/v1/jobs/search"
    url = f"{base_url}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "JobHuntPlatform/2.0", "Accept": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            jobs = data.get("data", [])
            for j in jobs:
                if "url" in j:
                    j["url"] = clean_job_url(j["url"])
                if "apply_url" in j:
                    j["apply_url"] = clean_job_url(j["apply_url"])
            _FEED_CACHE[cache_key] = (now, jobs)
            return jobs
    except Exception as e:
        print(f"Error querying live feed {params}: {e}")
        if cache_key in _FEED_CACHE:
            return _FEED_CACHE[cache_key][1]
        return []

def evaluate_location_match(job, pref_locations, pref_work_mode):
    work_mode = (job.get("work_mode") or "").lower()
    location = (job.get("location") or "").lower()
    cities = [c.lower() for c in job.get("cities") or []]
    countries = [c.lower() for c in job.get("countries") or []]
    regions = [r.lower() for r in job.get("regions") or []]

    is_job_remote = (
        work_mode == "remote" or 
        "remote" in location or 
        "worldwide" in location or 
        "anywhere" in location or
        "global" in location
    )

    # 1. Work Mode strict check
    if pref_work_mode == "remote" and not is_job_remote:
        return False, "Not remote"
    elif pref_work_mode == "hybrid" and work_mode not in ["hybrid", "onsite"]:
        if not ("hybrid" in location or not is_job_remote):
            return False, "Not hybrid"
    elif pref_work_mode == "onsite" and is_job_remote and work_mode == "remote":
        return False, "Remote role excluded by onsite preference"

    # If no locations specified or user selected "any", accept all
    if not pref_locations or any(p.lower() in ["any", "all", "all locations", "anywhere"] for p in pref_locations):
        tag = "Worldwide Remote" if is_job_remote else (job.get("location") or "Global")
        return True, tag

    # 2. Check each location preference
    for pref in pref_locations:
        p = pref.strip().lower()
        if not p:
            continue

        # Worldwide remote match
        if p in ["worldwide remote", "global remote", "remote worldwide", "anywhere remote"]:
            if is_job_remote:
                return True, "Worldwide Remote"

        # India / All India match
        if p in ["all india", "india"]:
            if "in" in countries or "india" in location or any(c in location for c in ["bengaluru", "bangalore", "chennai", "mumbai", "delhi", "hyderabad", "pune", "coimbatore", "kochi"]):
                return True, "India"
            if is_job_remote and (not countries or "in" in countries or "global" in regions):
                return True, "Remote (India Eligible)"

        # Country code aliases
        matched_country = False
        for c_name, c_aliases in COUNTRY_CODE_MAP.items():
            if p == c_name or p in c_aliases:
                if any(alias in countries for alias in c_aliases) or any(alias in location for alias in c_aliases):
                    matched_country = True
                    break
        if matched_country:
            return True, pref.title()

        # Specific City Aliases (e.g., Bengaluru <-> Bangalore, Chennai <-> Madras)
        if p in CITY_ALIASES:
            c_aliases = CITY_ALIASES[p]
            if any(alias in location for alias in c_aliases) or any(alias in c for alias in c_aliases for c in cities):
                return True, pref.title()

        # State / Region aliases (when user specifies a region/state)
        matched_region = False
        for r_name, r_aliases in STATE_REGION_MAP.items():
            if p == r_name:
                if any(alias in location for alias in r_aliases) or any(alias in cities for alias in r_aliases):
                    matched_region = True
                    break
        if matched_region:
            return True, pref.title()

        # Direct city or string substring match
        if p in location or any(p in c for c in cities) or any(p in c for c in countries):
            return True, pref.title()

    # If the job is remote and user also has a general remote preference
    if is_job_remote and any("remote" in p.lower() for p in pref_locations):
        return True, "Worldwide Remote"

    return False, "Location outside preference"

def evaluate_employment_type(job, pref_type):
    if not pref_type or pref_type.lower() in ["all", "all types"]:
        return True, "Any Type"

    pref = pref_type.lower()
    title = (job.get("title") or "").lower()
    desc = (job.get("description") or "").lower()[:1000]

    if pref in ["contract", "freelance", "contractor"]:
        is_contract = any(k in title or k in desc for k in ["contract", "contractor", "freelance", "freelancing", "c2c", "temporary", "consultant", "b2b"])
        if is_contract:
            return True, "Contract / Freelance"
        return False, "Not a contract/freelance role"

    elif pref in ["full-time", "fulltime", "permanent"]:
        is_contract = any(k in title for k in ["contractor", "freelance", "intern", "internship"])
        if not is_contract:
            return True, "Full-Time"
        return False, "Not full-time"

    elif pref in ["part-time", "parttime"]:
        if "part-time" in title or "part time" in title or "part-time" in desc:
            return True, "Part-Time"
        return False, "Not part-time"

    elif pref in ["internship", "intern"]:
        if "intern" in title or "internship" in title:
            return True, "Internship"
        return False, "Not an internship"

    return True, pref.title()

def evaluate_compensation(job, currency, min_val):
    enr = job.get("enrichment") or {}
    s_min = enr.get("salary_min")
    s_max = enr.get("salary_max")
    s_curr = enr.get("salary_currency")
    s_period = enr.get("salary_period", "year")

    # If user selected Any / No minimum
    if currency == "ANY" or min_val <= 0:
        if s_min or s_max:
            sal_max = s_max or s_min
            return True, f"{s_curr} {sal_max:,} / {s_period}", "Disclosed Salary"
        return True, "Competitive / Disclosed on Interview", "Unstated Salary"

    # Conversion rates (approximate market rates)
    USD_TO_INR = 87.0
    EUR_TO_INR = 94.0
    GBP_TO_INR = 110.0
    CAD_TO_INR = 63.0
    AUD_TO_INR = 56.0
    AED_TO_INR = 23.7

    if s_min or s_max:
        sal = s_max or s_min
        # Normalize job salary to annual INR LPA and monthly USD
        annual_inr_lpa = 0.0
        monthly_usd = 0.0

        if s_curr == "INR":
            annual_inr = sal if s_period == "year" else sal * 12
            annual_inr_lpa = annual_inr / 100000.0
            monthly_usd = (annual_inr / USD_TO_INR) / 12.0
        elif s_curr == "USD":
            annual_usd = sal if s_period == "year" else sal * 12
            annual_inr_lpa = (annual_usd * USD_TO_INR) / 100000.0
            monthly_usd = annual_usd / 12.0
        elif s_curr == "EUR":
            annual_eur = sal if s_period == "year" else sal * 12
            annual_inr_lpa = (annual_eur * EUR_TO_INR) / 100000.0
            monthly_usd = (annual_eur * 1.08) / 12.0
        elif s_curr == "GBP":
            annual_gbp = sal if s_period == "year" else sal * 12
            annual_inr_lpa = (annual_gbp * GBP_TO_INR) / 100000.0
            monthly_usd = (annual_gbp * 1.25) / 12.0
        elif s_curr == "CAD":
            annual_cad = sal if s_period == "year" else sal * 12
            annual_inr_lpa = (annual_cad * CAD_TO_INR) / 100000.0
            monthly_usd = (annual_cad * 0.72) / 12.0
        elif s_curr == "AUD":
            annual_aud = sal if s_period == "year" else sal * 12
            annual_inr_lpa = (annual_aud * AUD_TO_INR) / 100000.0
            monthly_usd = (annual_aud * 0.65) / 12.0
        elif s_curr == "AED":
            annual_aed = sal if s_period == "year" else sal * 12
            annual_inr_lpa = (annual_aed * AED_TO_INR) / 100000.0
            monthly_usd = (annual_aed / 3.67) / 12.0

        # Validate against chosen currency threshold
        if currency == "INR" and annual_inr_lpa < min_val:
            return False, "", "Below INR LPA threshold"
        elif currency == "USD_MO" and monthly_usd < min_val:
            return False, "", "Below USD/month threshold"
        elif currency == "USD_YR" and (monthly_usd * 12) < min_val:
            return False, "", "Below USD/year threshold"
        elif currency == "EUR" and (annual_inr_lpa * 100000 / EUR_TO_INR) < min_val:
            return False, "", "Below EUR/year threshold"
        elif currency == "GBP" and (annual_inr_lpa * 100000 / GBP_TO_INR) < min_val:
            return False, "", "Below GBP/year threshold"
        elif currency == "CAD" and (annual_inr_lpa * 100000 / CAD_TO_INR) < min_val:
            return False, "", "Below CAD/year threshold"
        elif currency == "AUD" and (annual_inr_lpa * 100000 / AUD_TO_INR) < min_val:
            return False, "", "Below AUD/year threshold"
        elif currency == "AED" and (annual_inr_lpa * 100000 / AED_TO_INR / 12) < min_val:
            return False, "", "Below AED/month threshold"

        # Format display string
        if s_curr == "INR":
            display = f"₹{round((s_min or sal)/100000, 1)} - ₹{round(sal/100000, 1)} LPA"
        elif s_curr == "USD":
            display = f"${round((s_min or sal)/1000)}k - ${round(sal/1000)}k / yr (~${round(monthly_usd):,}/mo)"
        elif s_curr == "EUR":
            display = f"€{round((s_min or sal)/1000)}k - €{round(sal/1000)}k / yr"
        elif s_curr == "GBP":
            display = f"£{round((s_min or sal)/1000)}k - £{round(sal/1000)}k / yr"
        elif s_curr == "CAD":
            display = f"C${round((s_min or sal)/1000)}k - C${round(sal/1000)}k / yr"
        elif s_curr == "AUD":
            display = f"A${round((s_min or sal)/1000)}k - A${round(sal/1000)}k / yr"
        elif s_curr == "AED":
            monthly_aed = round(sal / 12) if s_period == "year" else sal
            display = f"AED {monthly_aed:,} / mo"
        else:
            display = f"{s_curr} {s_min or sal:,} - {sal:,} / yr (~₹{round(annual_inr_lpa, 1)} LPA)"
        return True, display, "Meets disclosed salary criteria"

    else:
        # Unstated salary - check if senior market standard applies
        if currency == "USD_MO" and min_val > 0:
            display = f"Estimated ${int(min_val):,}+ / mo (Global Remote Standard)"
        elif currency == "USD_YR" and min_val > 0:
            display = f"Estimated ${int(min_val):,}+ / yr (Enterprise Band)"
        elif currency == "INR" and min_val > 0:
            display = f"Estimated > {min_val} LPA (Market Standard for Candidate Years of Experience)"
        elif currency == "EUR" and min_val > 0:
            display = f"Estimated €{int(min_val):,}+ / yr (EU Standard)"
        elif currency == "GBP" and min_val > 0:
            display = f"Estimated £{int(min_val):,}+ / yr (UK Standard)"
        elif currency == "CAD" and min_val > 0:
            display = f"Estimated C${int(min_val):,}+ / yr"
        elif currency == "AUD" and min_val > 0:
            display = f"Estimated A${int(min_val):,}+ / yr"
        elif currency == "AED" and min_val > 0:
            display = f"Estimated AED {int(min_val):,}+ / mo"
        else:
            display = "Competitive (Disclosed upon interview)"
        return True, display, "Passes unstated band"

def calculate_cvmatch_score(job, candidate_profile):
    title = (job.get("title") or "").lower()
    job_skills = set(s.lower() for s in job.get("skills") or [])
    candidate_skills = set(s.lower() for s in candidate_profile.get("skills") or [])
    enr = job.get("enrichment") or {}
    reqs = enr.get("requirements") or []
    
    # 1. Keywords Match (30 pts)
    matched_skills = job_skills.intersection(candidate_skills) if job_skills else set()
    keyword_score = (len(matched_skills) / max(len(job_skills), 1)) * 30 if job_skills else 15

    # 2. High-Value Skill Gaps Analysis
    gap_skills = list(job_skills.difference(candidate_skills))
    TECH_BENCHMARKS = [
        "kubernetes", "docker", "aws", "gcp", "azure", "terraform", "kafka", "redis", 
        "graphql", "postgresql", "fastapi", "react", "typescript", "golang", "python", 
        "microservices", "ci/cd", "helm", "spark", "pytorch", "grpc", "distributed systems",
        "sql", "nosql", "linux", "git", "rest api"
    ]
    desc_text = f"{title} {' '.join(r.get('text', '') for r in reqs)}".lower()
    for tech in TECH_BENCHMARKS:
        if tech in desc_text and tech not in candidate_skills and tech not in gap_skills:
            gap_skills.append(tech)
            if len(gap_skills) >= 4:
                break

    # 3. Requirements Coverage (40 pts)
    req_pts = 0
    if reqs:
        matched_reqs = 0
        for r in reqs:
            t = (r.get("text") or "").lower()
            if any(s in t for s in candidate_skills):
                matched_reqs += 1
        req_pts = (matched_reqs / len(reqs)) * 40
    else:
        req_pts = 25 if any(s in title for s in candidate_skills) else 15

    # 4. Title Match (20 pts)
    cand_role = (candidate_profile.get("current_role") or "").lower()
    title_pts = 10
    cand_tokens = [w for w in re.split(r'\W+', cand_role) if len(w) > 2]
    if any(tok in title for tok in cand_tokens):
        title_pts = 20
    elif any(s in title for s in candidate_skills):
        title_pts = 16

    # 5. Experience Seniority (10 pts)
    sen_pts = 10

    total_score = round(keyword_score + req_pts + title_pts + sen_pts)
    return min(total_score, 99), list(matched_skills), gap_skills[:4]

def generate_dynamic_search_queries(candidate_profile, pref_locations=None):
    cand_skills = candidate_profile.get("skills", [])
    cand_role = candidate_profile.get("current_role", "")

    queries = []

    # Map candidate domain to high-yield queries
    # Mobile
    mobile_keys = ["flutter", "react native", "swift", "kotlin", "ios", "android", "dart"]
    matched_mobile = [s for s in mobile_keys if s in cand_skills]
    if matched_mobile:
        queries.append({"q": f"{matched_mobile[0]} developer", "limit": 40})
        queries.append({"q": "mobile developer", "limit": 40})

    # AI / LLM / GenAI
    ai_keys = ["ai", "llm", "machine learning", "agentic ai", "langchain", "prompt engineering", "deep learning"]
    if any(k in cand_skills for k in ai_keys):
        queries.append({"q": "ai engineer", "limit": 40})
        queries.append({"q": "ai automation", "limit": 40})
        queries.append({"q": "llm engineer", "limit": 40})

    # Scraping / Automation
    scraping_keys = ["web scraping", "playwright", "puppeteer", "selenium", "scrapy"]
    if any(k in cand_skills for k in scraping_keys):
        queries.append({"q": "web scraping", "limit": 40})
        queries.append({"q": "playwright", "limit": 40})
        queries.append({"q": "python crawler", "limit": 40})

    # Python Backend
    if "python" in cand_skills:
        queries.append({"q": "python developer", "limit": 40})
        queries.append({"skills": "python", "limit": 40})

    # Frontend
    fe_keys = ["react", "vue", "angular", "nextjs", "typescript"]
    matched_fe = [s for s in fe_keys if s in cand_skills]
    if matched_fe:
        queries.append({"q": f"{matched_fe[0]} developer", "limit": 40})
        queries.append({"q": "frontend engineer", "limit": 40})

    # DevOps / Cloud
    devops_keys = ["devops", "kubernetes", "docker", "terraform", "aws", "gcp", "azure"]
    if any(k in cand_skills for k in devops_keys) or "devops" in cand_role.lower():
        queries.append({"q": "devops engineer", "limit": 40})
        queries.append({"q": "cloud engineer", "limit": 40})

    # Mechanical / CAD / Automotive Design / Trim
    cad_keys = ["catia", "catia v5", "ug nx", "nx", "solidworks", "creo", "cad", "trim design", "interior trim", "plastic trim", "mechanical engineering", "mechanical design", "dfmea", "cpm"]
    if any(k in cand_skills for k in cad_keys) or "design" in cand_role.lower():
        queries.append({"q": "design engineer", "limit": 40})
        queries.append({"q": "mechanical design engineer", "limit": 40})
        queries.append({"q": "cad engineer", "limit": 40})
        if "catia" in cand_skills or "catia v5" in cand_skills:
            queries.append({"q": "catia design engineer", "limit": 40})
        if "ug nx" in cand_skills or "nx" in cand_skills:
            queries.append({"q": "nx design engineer", "limit": 40})
        if "interior trim" in cand_skills or "plastic trim" in cand_skills or "trim design" in cand_skills:
            queries.append({"q": "trim design engineer", "limit": 40})

    # Location-targeted searches if specific cities/states are provided
    if pref_locations:
        for loc in pref_locations:
            l_clean = loc.strip().lower()
            if l_clean not in ["worldwide remote", "global remote", "any", "all", "worldwide"]:
                if any(k in cand_skills for k in cad_keys) or "design" in cand_role.lower():
                    queries.append({"q": f"design engineer {l_clean}", "limit": 40})
                    queries.append({"q": f"catia {l_clean}", "limit": 40})
                    queries.append({"q": f"mechanical design {l_clean}", "limit": 40})
                elif "python" in cand_skills:
                    queries.append({"q": f"python {l_clean}", "limit": 40})
                elif matched_mobile:
                    queries.append({"q": f"{matched_mobile[0]} {l_clean}", "limit": 40})
                else:
                    queries.append({"q": f"{cand_role} {l_clean}", "limit": 40})

    # Role Fallback
    if cand_role and len(cand_role) > 3:
        clean_role = re.sub(r'[^a-zA-Z\s]', '', cand_role).strip()
        if clean_role and not any(clean_role.lower() in q.get("q", "").lower() for q in queries):
            queries.append({"q": clean_role[:30], "limit": 40})

    # Dynamic queries from candidate skills (including user-added skills)
    for s in cand_skills:
        s_clean = s.strip()
        if len(s_clean) >= 2:
            s_lower = s_clean.lower()
            if not any(s_lower in q.get("q", "").lower() for q in queries):
                queries.append({"q": f"{s_clean} developer", "limit": 40})
                if len(queries) >= 16:
                    break

    if not queries:
        queries = [{"q": "software engineer", "limit": 40}]

    return queries

def query_linkedin_jobs(query, location="Worldwide", limit=12):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }
    url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={urllib.parse.quote(query)}&location={urllib.parse.quote(location)}&start=0"
    req = urllib.request.Request(url, headers=headers)
    jobs = []
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
            soup = BeautifulSoup(html, "html.parser")
            for li in soup.find_all("li")[:limit]:
                title_el = li.find(["h3", "h4"], class_=lambda c: c and "title" in c)
                comp_el = li.find(["h4", "a"], class_=lambda c: c and "subtitle" in c)
                loc_el = li.find("span", class_=lambda c: c and "location" in c)
                link_el = li.find("a", class_=lambda c: c and ("link" in c or "card" in c))
                time_el = li.find("time")

                if title_el and link_el:
                    clean_link = link_el.get("href", "").split("?")[0]
                    t_text = title_el.text.strip()
                    c_text = comp_el.text.strip() if comp_el else "Confidential"
                    l_text = loc_el.text.strip() if loc_el else "Worldwide"
                    p_date = ""
                    if time_el:
                        p_date = time_el.get("datetime") or time_el.text.strip()
                    if not p_date:
                        p_date = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

                    id_match = re.search(r"-(\d+)$", clean_link)
                    jid = id_match.group(1) if id_match else str(abs(hash(clean_link)))

                    is_remote = any(k in t_text.lower() or k in l_text.lower() for k in ["remote", "worldwide", "anywhere"])

                    jobs.append({
                        "id": f"li_{jid}",
                        "public_slug": f"li_{jid}",
                        "title": t_text,
                        "company": c_text,
                        "location": l_text,
                        "url": clean_link,
                        "source": "LinkedIn",
                        "source_type": "linkedin",
                        "is_linkedin": True,
                        "posted_at": p_date,
                        "work_mode": "remote" if is_remote else "onsite",
                        "cities": [l_text],
                        "countries": [],
                        "regions": ["global"] if is_remote else [],
                        "skills": [],
                        "description": f"LinkedIn Posting: {t_text} at {c_text} ({l_text}). Third-party source.",
                        "is_third_party": True,
                        "disclaimer": "These posters may not be valid since these are posted in a third party."
                    })
    except Exception as e:
        print(f"Error querying LinkedIn for '{query}': {e}")
    return jobs

def fetch_linkedin_postings(candidate_profile, preferences, limit=10, offset=0):
    currency = preferences.get("currency", "INR")
    min_val = float(preferences.get("min_package", 15.0))
    pref_locations = preferences.get("locations", ["Worldwide Remote"])
    pref_work_mode = preferences.get("work_mode", "all")
    pref_employment_type = preferences.get("employment_type", "all")

    search_queries = generate_dynamic_search_queries(candidate_profile, pref_locations)

    target_locations = []
    if pref_locations:
        for p in pref_locations:
            p_clean = p.strip()
            if p_clean.lower() not in ["worldwide remote", "global remote", "any", "all"]:
                target_locations.append(p_clean)
    if not target_locations:
        target_locations = ["Worldwide"]

    # Select base queries (avoiding redundant city suffix if querying location separately)
    base_queries = []
    for sq in search_queries:
        q_val = sq.get("q", "")
        if q_val and not any(loc.lower() in q_val.lower() for loc in target_locations):
            if q_val not in base_queries:
                base_queries.append(q_val)
    if not base_queries:
        base_queries = [candidate_profile.get("current_role") or "Design Engineer"]

    linkedin_results = []
    seen_li_urls = set()
    pool_target = max(limit + offset + 15, 35)
    per_loc_quota = max(6, (pool_target + len(target_locations) - 1) // len(target_locations))
    for loc in target_locations:
        loc_count = 0
        for q_str in base_queries[:5]:
            if loc_count >= per_loc_quota or len(linkedin_results) >= pool_target:
                break
            li_jobs = query_linkedin_jobs(q_str, location=loc, limit=10)
            for lj in li_jobs:
                if lj["url"] in seen_li_urls:
                    continue
                seen_li_urls.add(lj["url"])

                loc_ok, loc_tag = evaluate_location_match(lj, pref_locations, pref_work_mode)
                if not loc_ok and pref_work_mode == "remote" and lj["work_mode"] != "remote":
                    continue

                type_ok, type_tag = evaluate_employment_type(lj, pref_employment_type)
                if not type_ok:
                    continue

                comp_ok, comp_display, _ = evaluate_compensation(lj, currency, min_val)
                if not comp_ok:
                    continue

                cand_skills = set(s.lower() for s in candidate_profile.get("skills", []))
                matched_cand_skills = [s for s in cand_skills if s in lj["title"].lower()]
                lj_score = 70 + len(matched_cand_skills) * 4
                cand_role = (candidate_profile.get("current_role") or "").lower()
                if any(w in lj["title"].lower() for w in cand_role.split() if len(w) > 3):
                    lj_score += 10
                lj_score = min(lj_score, 92)

                lj["cvmatch_score"] = lj_score
                lj["matched_skills"] = matched_cand_skills
                lj["location_tag"] = loc_tag if loc_ok else lj["location"]
                lj["comp_display"] = comp_display
                lj["employment_type_tag"] = type_tag
                lj["is_linkedin"] = True
                lj["disclaimer"] = "These posters may not be valid since these are posted in a third party."
                linkedin_results.append(lj)
                loc_count += 1
                if loc_count >= per_loc_quota:
                    break

    linkedin_results.sort(key=lambda x: (x.get("cvmatch_score", 0), x.get("posted_at") or ""), reverse=True)
    sliced = linkedin_results[offset : offset + limit]
    has_more = len(linkedin_results) > (offset + limit)
    return sliced, has_more, len(linkedin_results)

def search_matching_jobs(candidate_profile, preferences):
    fingerprint = _get_skills_fingerprint(candidate_profile, preferences)
    now = time.time()

    # Instant return if similar skills / role was already queried recently
    with _SEARCH_CACHE_LOCK:
        cached = _RESUME_SEARCH_CACHE.get(fingerprint)
        if cached and (now - cached.get("timestamp", 0) < _SEARCH_CACHE_TTL):
            print(f"[SEARCH CACHE] Instant cache hit for candidate skills fingerprint: {fingerprint[:40]}...")
            return copy.deepcopy(cached["result"])

    currency = preferences.get("currency", "INR")
    min_val = float(preferences.get("min_package", 15.0))
    pref_locations = preferences.get("locations", ["Worldwide Remote"])
    pref_work_mode = preferences.get("work_mode", "all")
    pref_employment_type = preferences.get("employment_type", "all")
    include_linkedin = bool(preferences.get("include_linkedin", False))

    # Generate dynamic queries matching the candidate's exact resume and locations
    search_queries = generate_dynamic_search_queries(candidate_profile, pref_locations)

    all_jobs = {}
    for q in search_queries[:12]:
        jobs = query_enterprise_feed(q)
        for j in jobs:
            slug = j.get("public_slug")
            if slug and slug not in all_jobs:
                all_jobs[slug] = j
        time.sleep(0.12)

    # Filter & rank Direct ATS jobs
    verified_results = []
    for slug, j in all_jobs.items():
        if j.get("closed_at") is not None:
            continue

        # Strict Direct ATS filter
        url = (j.get("url") or "").lower()
        source_type = (j.get("source_type") or "").lower()
        is_direct = any(d in url for d in DIRECT_ATS_DOMAINS) or source_type in ["ats", "company"]
        if not is_direct:
            continue

        # Location filter
        loc_ok, loc_tag = evaluate_location_match(j, pref_locations, pref_work_mode)
        if not loc_ok:
            continue

        # Employment type filter (Contract/Freelance/Full-time)
        type_ok, type_tag = evaluate_employment_type(j, pref_employment_type)
        if not type_ok:
            continue

        # Compensation filter
        comp_ok, comp_display, comp_reason = evaluate_compensation(j, currency, min_val)
        if not comp_ok:
            continue

        # Match score & Skill Gap analysis
        score, matched_skills, gap_skills = calculate_cvmatch_score(j, candidate_profile)
        if score < 45:
            continue

        j["cvmatch_score"] = score
        j["matched_skills"] = matched_skills
        j["gap_skills"] = gap_skills
        j["location_tag"] = loc_tag
        j["comp_display"] = comp_display
        j["employment_type_tag"] = type_tag
        j["is_linkedin"] = False
        verified_results.append(j)

    verified_results.sort(key=lambda x: (x.get("cvmatch_score", 0), x.get("posted_at") or ""), reverse=True)

    linkedin_results = []
    if include_linkedin:
        li_res, _, _ = fetch_linkedin_postings(candidate_profile, preferences, limit=10, offset=0)
        linkedin_results = li_res

    final_result = {
        "ats_jobs": verified_results,
        "linkedin_jobs": linkedin_results
    }

    # Store in fast cache for similar skills lookups
    with _SEARCH_CACHE_LOCK:
        _RESUME_SEARCH_CACHE[fingerprint] = {
            "result": copy.deepcopy(final_result),
            "timestamp": time.time()
        }

    return final_result
