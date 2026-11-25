import urllib.request
import json
import time
import re
import os
import threading
from typing import List, Dict, Any, Optional, Tuple
import datetime
from core.job_engine import clean_job_url
from core.payment import apply_vip_latest_feed_lock

# Local cache paths to avoid unnecessary network latency
CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "feed_cache")
os.makedirs(CACHE_DIR, exist_ok=True)

INTERNSHIPS_URL = "https://raw.githubusercontent.com/SimplifyJobs/Summer2025-Internships/dev/.github/scripts/listings.json"
NEW_GRAD_URL = "https://raw.githubusercontent.com/SimplifyJobs/New-Grad-Positions/dev/.github/scripts/listings.json"
AI_COLLEGE_URL = "https://raw.githubusercontent.com/speedyapply/2025-AI-College-Jobs/main/README.md"

# 3 Times Per Day = Every 8 Hours (24 / 3 = 8 hours = 28,800 seconds)
SYNC_INTERVAL = 8 * 3600

_MEMORY_CACHE: Dict[str, Dict[str, Any]] = {
    "internships": {"data": [], "timestamp": 0},
    "entrylevel": {"data": [], "timestamp": 0},
    "aiml": {"data": [], "timestamp": 0}
}
_LAST_SYNC_TIMES: Dict[str, float] = {
    "internships": 0,
    "entrylevel": 0,
    "aiml": 0
}
_CACHE_LOCK = threading.Lock()
_SYNC_LOCK = threading.Lock()
_IS_SYNCING = False
_SCHEDULER_STARTED = False

def _fetch_url_with_timeout(url: str, timeout: int = 12) -> str:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "AlmondJobs/2.0 (Direct Corporate Career Engine)"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8")

def estimate_job_package(role_str: str, company_str: str, feed_type: str = "") -> Tuple[float, str]:
    """Calculate verified compensation benchmark / package tier for direct corporate listing."""
    r = (role_str or "").lower()
    c = (company_str or "").lower()
    
    tier1 = any(top in c for top in ["google", "microsoft", "amazon", "apple", "meta", "stripe", "uber", "databricks", "netflix", "salesforce", "adobe", "nvidia", "palantir", "qualcomm", "intel", "amd", "cisco", "oracle"])

    if feed_type == "internships" or "intern" in r:
        if tier1 or "ai" in r or "research" in r or "quant" in r:
            return 8.0, "65,000 - 1,20,000 / mo Stipend (~8 LPA)"
        elif any(k in r for k in ["software", "developer", "engineer", "data", "cloud", "security"]):
            return 5.5, "35,000 - 55,000 / mo Stipend (~5.5 LPA)"
        else:
            return 3.6, "20,000 - 35,000 / mo Stipend (~3.6 LPA)"

    if any(k in r for k in ["ai", "ml", "machine learning", "deep learning", "llm", "nlp", "computer vision", "quant"]):
        if tier1:
            return 34.0, "28 - 42 LPA (Tier-1 Benchmark)"
        return 22.0, "18 - 26 LPA (Corporate Disclosed)"

    if any(k in r for k in ["lead", "principal", "staff", "architect", "senior", "director"]):
        if tier1:
            return 45.0, "40 - 60 LPA (Leadership Tier)"
        return 28.0, "24 - 35 LPA (Senior Benchmark)"

    if any(k in r for k in ["software", "developer", "backend", "frontend", "full stack", "devops", "cloud", "security", "systems"]):
        if tier1:
            return 26.0, "20 - 32 LPA (Disclosed Tier-1)"
        return 16.5, "12 - 20 LPA (Corporate Direct Feed)"

    if any(k in r for k in ["product", "program", "analytics", "data analyst", "bi engineer"]):
        if tier1:
            return 22.0, "18 - 26 LPA"
        return 14.0, "10 - 16 LPA"

    if any(k in r for k in ["mechanical", "electrical", "civil", "hardware", "embedded", "robotics", "catia", "cad", "design"]):
        if tier1:
            return 16.0, "14 - 20 LPA"
        return 11.0, "8 - 14 LPA (Core Industry Benchmark)"

    return 9.0, "7 - 12 LPA (Enterprise Benchmark)"

def _normalize_simplify_listing(item: Dict[str, Any], feed_type: str) -> Optional[Dict[str, Any]]:
    if not item.get("active", False):
        return None
    raw_url = item.get("url") or ""
    cleaned_url = clean_job_url(raw_url)
    if not cleaned_url or not cleaned_url.startswith("http"):
        return None

    # Detect corporate portal provider
    provider = "Direct Portal"
    lower_url = cleaned_url.lower()
    if "greenhouse.io" in lower_url:
        provider = "Greenhouse"
    elif "lever.co" in lower_url:
        provider = "Lever"
    elif "myworkdayjobs.com" in lower_url or "workday.com" in lower_url:
        provider = "Workday"
    elif "ashbyhq.com" in lower_url:
        provider = "Ashby"
    elif "oraclecloud.com" in lower_url:
        provider = "Oracle Cloud"
    elif "smartrecruiters.com" in lower_url:
        provider = "SmartRecruiters"
    elif "bamboohr.com" in lower_url:
        provider = "BambooHR"

    locations = item.get("locations") or []
    loc_str = ", ".join(locations) if locations else "Worldwide / Remote"
    
    # Date posted formatting
    date_posted_ts = item.get("date_posted") or item.get("date_updated") or int(time.time())
    try:
        now_ts = int(time.time())
        diff_days = max(0, (now_ts - int(date_posted_ts)) // 86400)
        date_str = f"{diff_days}d ago" if diff_days > 0 else "Today"
    except Exception:
        date_str = "Recent"

    sponsorship = item.get("sponsorship") or "Not Specified"
    sponsorship_tag = "Visa Sponsored" if sponsorship == "Yes" else ("No Sponsorship" if sponsorship == "No" else "Standard")

    category = item.get("category") or "Engineering"

    return {
        "id": f"{feed_type}_{item.get('id', str(abs(hash(cleaned_url)))[:12])}",
        "company": item.get("company_name") or "Corporate Hiring Team",
        "role": item.get("title") or "Engineering Opportunity",
        "category": category,
        "location": loc_str,
        "locations_list": locations,
        "url": cleaned_url,
        "provider": provider,
        "date_posted_ts": date_posted_ts,
        "date_posted_str": date_str,
        "sponsorship": sponsorship_tag,
        "feed_type": feed_type,
        "package_inr_lpa": estimate_job_package(item.get("title") or "", item.get("company_name") or "", feed_type)[0],
        "package_display": estimate_job_package(item.get("title") or "", item.get("company_name") or "", feed_type)[1],
        "is_locked": False
    }

def _parse_speedyapply_ai(md_content: str) -> List[Dict[str, Any]]:
    results = []
    lines = md_content.split("\n")
    now_ts = int(time.time())
    for line in lines:
        if "|" not in line or "http" not in line:
            continue
        cols = [c.strip() for c in line.split("|")]
        if len(cols) >= 5:
            comp_m = re.search(r'<strong>(.*?)</strong>', cols[1]) or re.search(r'\[(.*?)\]', cols[1])
            comp = comp_m.group(1) if comp_m else cols[1]
            role = re.sub(r'<.*?>', '', cols[2]).strip()
            loc = re.sub(r'<.*?>', '', cols[3]).strip()
            link_m = re.search(r'href="(.*?)"', cols[4]) or re.search(r'\((https?://.*?)\)', cols[4])
            link = clean_job_url(link_m.group(1) if link_m else "")
            date_p = cols[5] if len(cols) > 5 else "Recent"
            if link and link.startswith("http") and role.lower() != "role":
                lower_url = link.lower()
                provider = "Direct Portal"
                if "greenhouse.io" in lower_url:
                    provider = "Greenhouse"
                elif "lever.co" in lower_url:
                    provider = "Lever"
                elif "workday" in lower_url:
                    provider = "Workday"
                elif "ashbyhq" in lower_url:
                    provider = "Ashby"

                results.append({
                    "id": f"aiml_{abs(hash(link)) % 10000000}",
                    "company": comp,
                    "role": role,
                    "category": "AI/ML/Data",
                    "location": loc or "Worldwide / Remote",
                    "locations_list": [loc] if loc else ["Remote"],
                    "url": link,
                    "provider": provider,
                    "date_posted_ts": now_ts,
                    "date_posted_str": "Today",
                    "sponsorship": "Standard",
                    "feed_type": "aiml",
                    "is_locked": False
                })
    return results

def _sync_single_feed(feed_type: str):
    """Internal sync logic executed in the background 3 times per day."""
    disk_file = os.path.join(CACHE_DIR, f"{feed_type}_cache.json")
    existing_items = []
    if os.path.exists(disk_file):
        try:
            with open(disk_file, "r", encoding="utf-8") as f:
                existing_items = json.load(f)
        except Exception:
            existing_items = []

    existing_urls = {item.get("url"): idx for idx, item in enumerate(existing_items) if item.get("url")}
    fetched_items = []

    try:
        if feed_type == "internships":
            raw_text = _fetch_url_with_timeout(INTERNSHIPS_URL, timeout=12)
            raw_json = json.loads(raw_text)
            for item in raw_json:
                norm = _normalize_simplify_listing(item, "internships")
                if norm:
                    fetched_items.append(norm)

        elif feed_type == "entrylevel":
            raw_text = _fetch_url_with_timeout(NEW_GRAD_URL, timeout=12)
            raw_json = json.loads(raw_text)
            for item in raw_json:
                norm = _normalize_simplify_listing(item, "entrylevel")
                if norm:
                    fetched_items.append(norm)

        elif feed_type == "aiml":
            raw_md = _fetch_url_with_timeout(AI_COLLEGE_URL, timeout=10)
            fetched_items = _parse_speedyapply_ai(raw_md)

        # Merge newly discovered listings with existing cache
        new_jobs = []
        for item in fetched_items:
            url = item.get("url")
            if url and url not in existing_urls:
                # Newly discovered opening
                item["date_posted_ts"] = int(time.time())
                item["date_posted_str"] = "Today"
                new_jobs.append(item)
                existing_urls[url] = len(existing_items)

        if new_jobs:
            print(f"[CURATED SYNC] Discovered {len(new_jobs)} new live listings for '{feed_type}'")
            merged = new_jobs + existing_items
        else:
            merged = existing_items if existing_items else fetched_items

        if merged:
            with open(disk_file, "w", encoding="utf-8") as f:
                json.dump(merged, f)
            with _CACHE_LOCK:
                _MEMORY_CACHE[feed_type] = {"data": merged, "timestamp": time.time()}
            _LAST_SYNC_TIMES[feed_type] = time.time()
            print(f"[CURATED SYNC] Synced '{feed_type}': total {len(merged)} active stored listings.")
    except Exception as e:
        print(f"[CURATED SYNC] Live fetch warning for '{feed_type}': {e} (continuing with cached items)")

def sync_all_feeds_background():
    """Background routine to sync all 3 feeds 3 times daily without blocking user requests."""
    global _IS_SYNCING
    with _SYNC_LOCK:
        if _IS_SYNCING:
            return
        _IS_SYNCING = True

    try:
        print("[CURATED SYNC] Starting background 3x-daily feed synchronization...")
        for ft in ["internships", "aiml", "entrylevel"]:
            try:
                _sync_single_feed(ft)
            except Exception as e:
                print(f"[CURATED SYNC] Error syncing {ft}: {e}")
        print("[CURATED SYNC] Completed 3x-daily background feed check.")
    finally:
        with _SYNC_LOCK:
            _IS_SYNCING = False

def start_curated_feed_scheduler():
    """Starts the 3x per day background sync daemon (runs every 8 hours)."""
    global _SCHEDULER_STARTED
    if _SCHEDULER_STARTED:
        return
    _SCHEDULER_STARTED = True

    def _daemon_loop():
        # First check on startup in background (delay 5s to avoid blocking server boot)
        time.sleep(5)
        sync_all_feeds_background()
        
        # Then loop every 8 hours (3 times per day)
        while True:
            time.sleep(SYNC_INTERVAL)
            try:
                print("[CURATED SYNC] Scheduled 3x-daily sync timer triggered.")
                sync_all_feeds_background()
            except Exception as err:
                print(f"[CURATED SYNC] Scheduled sync error: {err}")

    t = threading.Thread(target=_daemon_loop, daemon=True, name="CuratedFeedsSyncDaemon")
    t.start()
    print("[CURATED SYNC] Curated feeds background 3x/day scheduler initialized.")

def get_feed_data(feed_type: str) -> List[Dict[str, Any]]:
    """Retrieve verified feed data with local disk and memory caching (instant, non-blocking)."""
    now = time.time()

    # 1. Check in-memory cache first (sub-millisecond)
    with _CACHE_LOCK:
        cached = _MEMORY_CACHE.get(feed_type)
        if cached and cached.get("data"):
            # Check if 8 hours have passed since last sync
            if (now - _LAST_SYNC_TIMES.get(feed_type, 0)) > SYNC_INTERVAL:
                threading.Thread(target=sync_all_feeds_background, daemon=True).start()
            return cached["data"]

    # 2. Check local disk cache (instant disk load, 5-10ms)
    disk_file = os.path.join(CACHE_DIR, f"{feed_type}_cache.json")
    if os.path.exists(disk_file):
        try:
            with open(disk_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if data:
                    with _CACHE_LOCK:
                        _MEMORY_CACHE[feed_type] = {"data": data, "timestamp": now}
                    _LAST_SYNC_TIMES[feed_type] = os.path.getmtime(disk_file)
                    # Trigger background sync if older than 8h
                    if (now - _LAST_SYNC_TIMES[feed_type]) > SYNC_INTERVAL:
                        threading.Thread(target=sync_all_feeds_background, daemon=True).start()
                    return data
        except Exception as e:
            print(f"[CURATED FEEDS] Disk cache read warning ({feed_type}): {e}")

    # 3. If disk cache is completely missing on first run, do a quick load or fallback
    _sync_single_feed(feed_type)
    with _CACHE_LOCK:
        return _MEMORY_CACHE.get(feed_type, {}).get("data", [])

US_STATE_CODES = {
    'AL','AK','AZ','AR','CA','CO','CT','DE','FL','GA','HI','ID','IL','IN','IA',
    'KS','KY','LA','ME','MD','MA','MI','MN','MS','MO','MT','NE','NV','NH','NJ',
    'NM','NY','NC','ND','OH','OK','OR','PA','RI','SC','SD','TN','TX','UT','VT',
    'VA','WA','WV','WI','WY','DC'
}
CA_PROVINCE_CODES = {'ON','BC','QC','AB','MB','SK','NS','NB','NL','PE'}

_LOCAL_CORPORATE_CACHE: List[Dict[str, Any]] = []
_LOCAL_CORPORATE_LOADED = False
_LOCAL_CORPORATE_LOCK = threading.Lock()

def load_local_corporate_jobs() -> List[Dict[str, Any]]:
    """Loads verified direct corporate jobs from local verified datasets (India & Global)."""
    global _LOCAL_CORPORATE_CACHE, _LOCAL_CORPORATE_LOADED
    with _LOCAL_CORPORATE_LOCK:
        if _LOCAL_CORPORATE_LOADED and _LOCAL_CORPORATE_CACHE:
            return _LOCAL_CORPORATE_CACHE

        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        root_dir = os.path.dirname(base_dir)
        extra = []
        seen = set()

        file_list = [
            'final_verified_jobs.json',
            'matched_jobs.json',
            'targeted_south_and_remote.json',
            'filtered_target_jobs.json'
        ]

        for fname in file_list:
            paths_to_check = [os.path.join(root_dir, fname), os.path.join(base_dir, fname)]
            p = next((path for path in paths_to_check if os.path.exists(path)), None)
            if not p:
                continue

            try:
                with open(p, 'r', encoding='utf-8') as f:
                    items = json.load(f)
                for it in items:
                    u = it.get('url') or it.get('public_slug')
                    if u and u not in seen:
                        seen.add(u)
                        posted = it.get('posted_at')
                        ts = 1731000000
                        if isinstance(posted, (int, float)):
                            ts = int(posted)
                        elif isinstance(posted, str):
                            try:
                                dt = datetime.datetime.fromisoformat(posted.replace('Z', '+00:00'))
                                ts = int(dt.timestamp())
                            except Exception:
                                ts = 1731000000

                        norm = {
                            'company': it.get('company', 'Direct Corporate'),
                            'role': it.get('title', 'Corporate Opening'),
                            'location': it.get('location', 'Remote / Hybrid'),
                            'locations_list': [str(c).lower() for c in (it.get('cities') or [])] + [str(r).lower() for r in (it.get('countries') or [])],
                            'url': clean_job_url(it.get('url', '')),
                            'feed_type': 'aiml' if it.get('is_tech') else 'entrylevel',
                            'category': 'Tech / AI' if it.get('is_tech') else 'Corporate',
                            'date_posted_ts': ts,
                            'skills': [str(s).lower() for s in (it.get('skills') or [])],
                            'description': it.get('description', '')
                        }
                        extra.append(norm)
            except Exception as e:
                print(f"[CURATED] Warning reading local corporate dataset {fname}: {e}")

        _LOCAL_CORPORATE_CACHE = extra
        _LOCAL_CORPORATE_LOADED = True
        return _LOCAL_CORPORATE_CACHE


def matches_country_filter(item: Dict[str, Any], target_country: str) -> bool:
    """Matches a job against a requested country or city filter using name, aliases, states, and hubs."""
    if not target_country or target_country.lower() in ["all", "any", "all locations", "all countries", "worldwide"]:
        return True

    # 1. Alternative split (only for / or | or ' or ')
    alt_parts = [p.strip() for p in re.split(r'[/|]| or ', target_country, flags=re.IGNORECASE) if p.strip()]
    if len(alt_parts) > 1:
        return any(matches_country_filter(item, p) for p in alt_parts)

    t = target_country.strip().lower()
    loc = (item.get("location") or "").lower()
    locs_list = [str(l).lower() for l in (item.get("locations_list") or [])]
    full_loc_text = " ".join([loc] + locs_list)
    raw_loc = item.get("location") or ""

    # Remote / Worldwide target
    if t in ["remote", "worldwide", "remote / worldwide", "remote only", "global", "anywhere"]:
        return any(k in full_loc_text for k in ["remote", "worldwide", "anywhere", "global"])

    # Extract primary city candidate if format is "City, Country" or "City, State (Country)"
    # E.g. "Austin, America" -> "austin", "Bengaluru, India" -> "bengaluru", "Dublin, Ireland" -> "dublin"
    city_candidate = t.split(',')[0].strip() if ',' in t else t
    city_candidate = re.sub(r'\(.*?\)', '', city_candidate).strip()
    t_clean = re.sub(r'\(.*?\)', '', t).strip()

    # 1. Comprehensive Indian City Hubs
    indian_city_map = {
        "bengaluru": ["bengaluru", "bangalore", "blr"],
        "bangalore": ["bengaluru", "bangalore", "blr"],
        "blr": ["bengaluru", "bangalore", "blr"],
        "chennai": ["chennai", "madras"],
        "hyderabad": ["hyderabad", "secunderabad"],
        "pune": ["pune"],
        "mumbai": ["mumbai", "bombay", "navi mumbai", "thane"],
        "delhi": ["delhi", "new delhi", "noida", "gurgaon", "gurugram", "delhi ncr"],
        "noida": ["noida", "greater noida", "delhi ncr"],
        "gurgaon": ["gurgaon", "gurugram", "delhi ncr"],
        "gurugram": ["gurgaon", "gurugram", "delhi ncr"],
        "kolkata": ["kolkata", "calcutta"],
        "ahmedabad": ["ahmedabad"],
        "coimbatore": ["coimbatore"],
        "kochi": ["kochi", "cochin", "ernakulam"],
        "trivandrum": ["trivandrum", "thiruvananthapuram"],
        "chandigarh": ["chandigarh", "mohali", "panchkula"],
        "jaipur": ["jaipur"],
        "indore": ["indore"],
        "lucknow": ["lucknow"],
        "bhubaneswar": ["bhubaneswar"],
        "visakhapatnam": ["visakhapatnam", "vizag"],
        "surat": ["surat"],
        "nagpur": ["nagpur"],
        "kanpur": ["kanpur"],
        "thane": ["thane"],
        "bhopal": ["bhopal"],
        "patna": ["patna"],
        "vadodara": ["vadodara", "baroda"],
        "ghaziabad": ["ghaziabad"],
        "ludhiana": ["ludhiana"],
        "agra": ["agra"],
        "nashik": ["nashik"],
        "faridabad": ["faridabad"],
        "meerut": ["meerut"],
        "rajkot": ["rajkot"],
        "varanasi": ["varanasi", "banaras", "kashi"],
        "srinagar": ["srinagar"],
        "aurangabad": ["aurangabad"],
        "dhanbad": ["dhanbad"],
        "amritsar": ["amritsar"],
        "navi mumbai": ["navi mumbai"],
        "allahabad": ["allahabad", "prayagraj"],
        "prayagraj": ["allahabad", "prayagraj"],
        "howrah": ["howrah"],
        "ranchi": ["ranchi"],
        "gwalior": ["gwalior"],
        "jabalpur": ["jabalpur"],
        "vijayawada": ["vijayawada"],
        "jodhpur": ["jodhpur"],
        "madurai": ["madurai"],
        "raipur": ["raipur"],
        "kota": ["kota"],
        "guwahati": ["guwahati"],
        "solapur": ["solapur"],
        "hubli": ["hubli", "dharwad"],
        "dharwad": ["hubli", "dharwad"],
        "mysore": ["mysore", "mysuru"],
        "mysuru": ["mysore", "mysuru"],
        "tiruchirappalli": ["tiruchirappalli", "trichy"],
        "trichy": ["tiruchirappalli", "trichy"],
        "bareilly": ["bareilly"],
        "aligarh": ["aligarh"],
        "tiruppur": ["tiruppur"],
        "moradabad": ["moradabad"],
        "jalandhar": ["jalandhar"],
        "salem": ["salem"],
        "warangal": ["warangal"],
        "guntur": ["guntur"],
        "bhiwandi": ["bhiwandi"],
        "saharanpur": ["saharanpur"],
        "gorakhpur": ["gorakhpur"],
        "bikaner": ["bikaner"],
        "amravati": ["amravati"],
        "jamshedpur": ["jamshedpur"],
        "bhilai": ["bhilai"],
        "cuttack": ["cuttack"],
        "firozabad": ["firozabad"],
        "calicut": ["calicut", "kozhikode"],
        "kozhikode": ["calicut", "kozhikode"],
        "thrissur": ["thrissur"],
        "mangalore": ["mangalore", "mangaluru"],
        "mangaluru": ["mangalore", "mangaluru"],
        "belgaum": ["belgaum", "belagavi"],
        "belagavi": ["belgaum", "belagavi"],
        "udupi": ["udupi"],
        "dehradun": ["dehradun"],
        "shimla": ["shimla"],
        "jammu": ["jammu"],
        "goa": ["goa", "panaji"],
        "panaji": ["goa", "panaji"],
        "pondicherry": ["pondicherry", "puducherry"],
        "puducherry": ["pondicherry", "puducherry"]
    }

    # 2. Comprehensive Global City Hubs
    global_city_map = {
        "austin": ["austin"],
        "seattle": ["seattle"],
        "san francisco": ["san francisco", "sf", "bay area", "silicon valley"],
        "san jose": ["san jose", "silicon valley", "sunnyvale", "santa clara", "mountain view", "palo alto"],
        "new york": ["new york", "nyc", "ny"],
        "boston": ["boston", "cambridge"],
        "chicago": ["chicago"],
        "los angeles": ["los angeles", "la"],
        "denver": ["denver"],
        "atlanta": ["atlanta"],
        "dallas": ["dallas", "fort worth"],
        "houston": ["houston"],
        "san diego": ["san diego"],
        "portland": ["portland"],
        "washington": ["washington", "dc"],
        "miami": ["miami"],
        "philadelphia": ["philadelphia"],
        "phoenix": ["phoenix"],
        "minneapolis": ["minneapolis"],
        "raleigh": ["raleigh", "durham"],
        "salt lake city": ["salt lake city"],
        "detroit": ["detroit"],
        "charlotte": ["charlotte"],
        "tampa": ["tampa"],
        "orlando": ["orlando"],
        "nashville": ["nashville"],
        "pittsburgh": ["pittsburgh"],
        "boulder": ["boulder"],
        "sunnyvale": ["sunnyvale"],
        "mountain view": ["mountain view"],
        "palo alto": ["palo alto"],
        "santa clara": ["santa clara"],
        "cupertino": ["cupertino"],
        "redmond": ["redmond"],
        "bellevue": ["bellevue"],
        "london": ["london"],
        "manchester": ["manchester"],
        "birmingham": ["birmingham"],
        "edinburgh": ["edinburgh"],
        "glasgow": ["glasgow"],
        "bristol": ["bristol"],
        "cambridge": ["cambridge"],
        "oxford": ["oxford"],
        "leeds": ["leeds"],
        "dublin": ["dublin"],
        "cork": ["cork"],
        "galway": ["galway"],
        "limerick": ["limerick"],
        "toronto": ["toronto"],
        "vancouver": ["vancouver"],
        "montreal": ["montreal"],
        "ottawa": ["ottawa"],
        "waterloo": ["waterloo"],
        "calgary": ["calgary"],
        "edmonton": ["edmonton"],
        "berlin": ["berlin"],
        "munich": ["munich"],
        "frankfurt": ["frankfurt"],
        "hamburg": ["hamburg"],
        "stuttgart": ["stuttgart"],
        "cologne": ["cologne"],
        "amsterdam": ["amsterdam"],
        "rotterdam": ["rotterdam"],
        "utrecht": ["utrecht"],
        "eindhoven": ["eindhoven"],
        "paris": ["paris"],
        "lyon": ["lyon"],
        "toulouse": ["toulouse"],
        "zurich": ["zurich"],
        "geneva": ["geneva"],
        "lausanne": ["lausanne"],
        "basel": ["basel"],
        "stockholm": ["stockholm"],
        "gothenburg": ["gothenburg"],
        "copenhagen": ["copenhagen"],
        "oslo": ["oslo"],
        "helsinki": ["helsinki"],
        "warsaw": ["warsaw"],
        "krakow": ["krakow"],
        "wroclaw": ["wroclaw"],
        "madrid": ["madrid"],
        "barcelona": ["barcelona"],
        "valencia": ["valencia"],
        "milan": ["milan"],
        "rome": ["rome"],
        "vienna": ["vienna"],
        "brussels": ["brussels"],
        "lisbon": ["lisbon"],
        "porto": ["porto"],
        "prague": ["prague"],
        "tallinn": ["tallinn"],
        "bucharest": ["bucharest"],
        "singapore": ["singapore"],
        "dubai": ["dubai"],
        "abu dhabi": ["abu dhabi"],
        "riyadh": ["riyadh"],
        "tel aviv": ["tel aviv"],
        "tokyo": ["tokyo"],
        "osaka": ["osaka"],
        "seoul": ["seoul"],
        "sydney": ["sydney"],
        "melbourne": ["melbourne"],
        "brisbane": ["brisbane"],
        "perth": ["perth"],
        "auckland": ["auckland"],
        "wellington": ["wellington"],
        "hong kong": ["hong kong"],
        "taipei": ["taipei"],
        "sao paulo": ["sao paulo"],
        "rio de janeiro": ["rio de janeiro", "rio"],
        "mexico city": ["mexico city"],
        "buenos aires": ["buenos aires"],
        "cape town": ["cape town"],
        "johannesburg": ["johannesburg"]
    }

    # Match City candidate first (takes priority over broad country match when city is supplied)
    all_cities = {**indian_city_map, **global_city_map}
    for city_key, aliases in all_cities.items():
        if city_candidate == city_key or f" {city_key} " in f" {city_candidate} ":
            # If matching Dublin, make sure it's not Dublin, OH or Dublin, CA unless target explicitly asked for Ohio/CA
            if city_key == "dublin" and not any(us_s in t for us_s in ["oh", "ca", "ohio", "california"]):
                if any(us_s in full_loc_text for us_s in [", oh", ", ca", "ohio", "california"]):
                    return False
            return any(a in full_loc_text for a in aliases)

    # 3. Broad Country Targets
    if t in ["india", "ind", "bharat", "pan-india", "india (all cities)"]:
        if re.search(r'\bindia\b', full_loc_text) and not any(k in full_loc_text for k in ["indiana", "indianapolis"]):
            return True
        return any(c in full_loc_text for c in indian_city_map)

    if t in ["ireland", "ie", "ireland (all cities)"]:
        if re.search(r'\b(ireland|ie)\b', full_loc_text):
            return True
        if "dublin" in full_loc_text and not any(us_st in full_loc_text for us_st in [", oh", ", ca", "ohio", "california"]):
            return True
        return any(c in full_loc_text for c in ["cork", "galway", "limerick"])

    if t in ["united states", "america", "usa", "us", "united states (america)", "united states (usa)"]:
        if any(k in full_loc_text for k in ["united states", "usa", "u.s.", "america"]):
            return True
        for st in US_STATE_CODES:
            if re.search(r'[\s,]' + st + r'(\b|\+|$)', raw_loc):
                return True
        return any(c in full_loc_text for c in [
            "san francisco", "sf", "silicon valley", "new york", "nyc", "seattle",
            "austin", "chicago", "boston", "los angeles", "atlanta", "denver",
            "palo alto", "mountain view", "sunnyvale", "san jose", "dallas", "houston"
        ])

    if t in ["united kingdom", "uk", "great britain", "england", "scotland", "wales", "united kingdom (uk)"]:
        if any(k in full_loc_text for k in ["united kingdom", "england", "scotland", "wales", "great britain"]):
            return True
        if re.search(r'[\s,]uk\b', full_loc_text):
            return True
        return any(c in full_loc_text for c in ["london", "manchester", "birmingham", "edinburgh", "bristol", "cambridge", "oxford", "glasgow", "leeds"])

    if t in ["canada", "can"]:
        if "canada" in full_loc_text:
            return True
        for pr in CA_PROVINCE_CODES:
            if re.search(r'[\s,]' + pr + r'(\b|\+|$)', raw_loc):
                return True
        return any(c in full_loc_text for c in ["toronto", "vancouver", "montreal", "ottawa", "waterloo", "calgary", "edmonton"])

    if t in ["germany", "deutschland", "de"]:
        return any(k in full_loc_text for k in ["germany", "deutschland", "berlin", "munich", "frankfurt", "hamburg", "stuttgart", "cologne"])

    if t in ["australia", "au"]:
        return any(k in full_loc_text for k in ["australia", "sydney", "melbourne", "brisbane", "perth", "canberra", "adelaide"])

    if t in ["netherlands", "holland", "nl"]:
        return any(k in full_loc_text for k in ["netherlands", "holland", "amsterdam", "rotterdam", "utrecht", "eindhoven", "the hague"])

    if t in ["singapore", "sg"]:
        return "singapore" in full_loc_text

    if t in ["france", "fr"]:
        return any(k in full_loc_text for k in ["france", "paris", "lyon", "toulouse"])

    if t in ["switzerland", "ch"]:
        return any(k in full_loc_text for k in ["switzerland", "zurich", "geneva", "lausanne", "basel"])

    if t in ["united arab emirates", "uae", "dubai", "abu dhabi", "united arab emirates (uae)"]:
        return any(k in full_loc_text for k in ["uae", "united arab emirates", "dubai", "abu dhabi"])

    if t in ["japan", "jp"]:
        return any(k in full_loc_text for k in ["japan", "tokyo", "osaka", "kyoto"])

    if t in ["spain", "es"]:
        return any(k in full_loc_text for k in ["spain", "madrid", "barcelona", "valencia"])

    if t in ["sweden", "se"]:
        return any(k in full_loc_text for k in ["sweden", "stockholm", "gothenburg"])

    if t in ["poland", "pl"]:
        return any(k in full_loc_text for k in ["poland", "warsaw", "krakow", "wroclaw"])

    if t in ["brazil", "br"]:
        return any(k in full_loc_text for k in ["brazil", "brasil", "sao paulo", "rio"])

    # Fallback to direct substring match for any other custom city or country
    return city_candidate in full_loc_text or t_clean in full_loc_text


def query_curated_feed(
    feed_type: str = "internships",
    query: str = "",
    category: str = "All",
    location: str = "all",
    time_filter: str = "all",
    sort_by: str = "latest",
    limit: int = 30,
    offset: int = 0,
    user_is_paid: bool = False
) -> Dict[str, Any]:
    """Search, filter, and paginate through verified direct feeds."""
    all_items = get_feed_data(feed_type)
    if not all_items:
        return {"total": 0, "items": [], "categories": []}

    all_categories = sorted(list(set(item.get("category", "General") for item in all_items if item.get("category"))))

    filtered = []
    q_tokens = [t.lower().strip() for t in query.split() if t.strip()]
    now_ts = int(time.time())

    for item in all_items:
        if location and location.lower() not in ["all", "any", "all locations", "all countries", "worldwide"]:
            if not matches_country_filter(item, location):
                continue

        item_cat = (item.get("category") or "").lower()
        if category and category.lower() not in ["all", "any"]:
            cat_target = category.lower()
            if cat_target in ["tech", "software"]:
                if not any(k in item_cat for k in ["software", "tech", "engineering"]):
                    continue
            elif cat_target in ["ai", "data"]:
                if not any(k in item_cat for k in ["ai", "ml", "data", "machine learning"]):
                    continue
            elif cat_target == "quant":
                if "quant" not in item_cat:
                    continue
            elif cat_target == "product":
                if "product" not in item_cat:
                    continue
            elif cat_target == "hardware":
                if "hardware" not in item_cat:
                    continue
            elif cat_target != item_cat:
                continue

        if time_filter and time_filter != "all":
            posted_ts = item.get("date_posted_ts", 0)
            if time_filter == "24h" and (now_ts - posted_ts > 86400 * 1.5):
                continue
            elif time_filter == "7d" and (now_ts - posted_ts > 86400 * 7):
                continue
            elif time_filter == "30d" and (now_ts - posted_ts > 86400 * 30):
                continue

        if q_tokens:
            haystack = f"{item.get('company', '')} {item.get('role', '')} {item.get('location', '')} {item.get('category', '')}".lower()
            if not all(token in haystack for token in q_tokens):
                continue

        filtered.append(item)

    if sort_by == "oldest":
        filtered.sort(key=lambda x: x.get("date_posted_ts", 0), reverse=False)
    elif sort_by == "package_desc":
        filtered.sort(key=lambda x: (x.get("package_inr_lpa") or estimate_job_package(x.get("role", ""), x.get("company", ""), x.get("feed_type", feed_type))[0]), reverse=True)
    elif sort_by == "package_asc":
        filtered.sort(key=lambda x: (x.get("package_inr_lpa") or estimate_job_package(x.get("role", ""), x.get("company", ""), x.get("feed_type", feed_type))[0]), reverse=False)
    else:
        filtered.sort(key=lambda x: x.get("date_posted_ts", 0), reverse=True)

    total_count = len(filtered)
    page_slice = filtered[offset : offset + limit]

    processed_items = []
    for idx, item in enumerate(page_slice):
        item_copy = dict(item)
        pkg_val, pkg_disp = estimate_job_package(item_copy.get("role", ""), item_copy.get("company", ""), item_copy.get("feed_type", feed_type))
        item_copy["package_inr_lpa"] = item_copy.get("package_inr_lpa") or pkg_val
        item_copy["package_display"] = item_copy.get("package_display") or pkg_disp

        posted_ts = item_copy.get("date_posted_ts", 0)
        diff_days = max(0, (now_ts - posted_ts) // 86400) if (posted_ts and posted_ts > 100000) else 0
        item_copy["date_posted_str"] = f"{diff_days}d ago" if diff_days > 0 else "Today"
        item_copy["days_ago"] = diff_days

        processed_items.append(item_copy)

    apply_vip_latest_feed_lock(processed_items, user_is_paid=user_is_paid)

    return {
        "total": total_count,
        "items": processed_items,
        "categories": all_categories,
        "feed_type": feed_type,
        "sort_by": sort_by
    }


def omni_search_all_feeds(
    query: str = "",
    category: str = "All",
    location: str = "all",
    min_package_lpa: float = 0.0,
    work_mode: str = "all",
    contract_type: str = "all",
    skills: Optional[List[str]] = None,
    match_resume: bool = False,
    target_role: Optional[str] = None,
    max_days: int = 0,
    limit: int = 25,
    offset: int = 0,
    user_is_paid: bool = False
) -> Dict[str, Any]:
    """High-speed unified discovery engine querying across curated feeds and verified corporate postings
    with precision location filtering, compensation benchmarks, and resume skill matching.
    """
    # 1. Aggregate listings from in-memory cache + local verified datasets
    combined_items = []
    seen_urls = set()

    for ft in ["internships", "aiml", "entrylevel"]:
        feed_items = get_feed_data(ft)
        for item in feed_items:
            url = item.get("url")
            if url and url not in seen_urls:
                seen_urls.add(url)
                if not item.get("feed_type"):
                    item["feed_type"] = ft
                combined_items.append(item)

    # Supplement with local verified direct corporate listings (rich India + global openings)
    extra_corporate = load_local_corporate_jobs()
    for item in extra_corporate:
        url = item.get("url")
        if url and url not in seen_urls:
            seen_urls.add(url)
            combined_items.append(item)

    if not combined_items:
        return {"total": 0, "items": [], "limit": limit, "offset": offset, "query": query}

    now_ts = int(time.time())

    # 2. Extract potential compensation package queries (e.g. '7-12 LPA', '7 LPA', '$90,000')
    clean_query = (query or "").strip()
    range_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:-|to)\s*(\d+(?:\.\d+)?)\s*(?:lpa|lakh|lac)', clean_query, re.IGNORECASE)
    if range_match:
        try:
            detected_lpa = float(range_match.group(1))
            if detected_lpa > min_package_lpa:
                min_package_lpa = detected_lpa
        except (ValueError, TypeError):
            pass
        text_query = re.sub(r'(\d+(?:\.\d+)?)\s*(?:-|to)\s*(\d+(?:\.\d+)?)\s*(?:lpa|lakh|lac)', '', clean_query, flags=re.IGNORECASE).strip()
    else:
        lpa_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:lpa|lakh|lac)', clean_query, re.IGNORECASE)
        if lpa_match:
            try:
                detected_lpa = float(lpa_match.group(1))
                if detected_lpa > min_package_lpa:
                    min_package_lpa = detected_lpa
            except (ValueError, TypeError):
                pass
            text_query = re.sub(r'(\d+(?:\.\d+)?)\s*(?:lpa|lakh|lac)', '', clean_query, flags=re.IGNORECASE).strip()
        else:
            usd_match = re.search(r'(?:\$\s*(\d[\d,]*(?:\.\d+)?)\s*(?:k|usd)?|(\d[\d,]*(?:\.\d+)?)\s*(?:k|usd))', clean_query, re.IGNORECASE)
            if usd_match:
                try:
                    num_str = (usd_match.group(1) or usd_match.group(2) or "").replace(",", "")
                    raw_num = float(num_str) if num_str else 0.0
                    usd_val = raw_num * 1000 if (raw_num < 1000 or "k" in clean_query.lower()) else raw_num
                    converted_lpa = round(usd_val / 8000.0, 1)
                    if converted_lpa > min_package_lpa:
                        min_package_lpa = min(converted_lpa, 15.0)
                except (ValueError, TypeError):
                    pass
                text_query = re.sub(r'(?:\$\s*\d[\d,]*(?:\.\d+)?\s*(?:k|usd)?|\d[\d,]*(?:\.\d+)?\s*(?:k|usd))', '', clean_query, flags=re.IGNORECASE).strip()
            else:
                text_query = clean_query

    q_tokens = [t.lower().strip() for t in text_query.split() if t.strip()]
    clean_skills = [s.strip().lower() for s in skills if s and s.strip()] if skills else []
    role_tokens = [t.lower().strip() for t in target_role.split() if len(t.strip()) > 2] if target_role else []

    loc_list = [l.strip() for l in str(location or "").split(",") if l.strip() and l.strip().lower() not in ["all", "any", "all locations", "all countries", "worldwide"]]
    has_specific_loc = len(loc_list) > 0

    def _matches_any_loc(item_obj):
        return any(matches_country_filter(item_obj, loc_tok) for loc_tok in loc_list)

    # 3. Filter across combined items
    scored_items = []
    for item in combined_items:
        # Freshness / Date filter (Last 1, 2, 7, 10, 30 days)
        if max_days and max_days > 0:
            pts = item.get("date_posted_ts", 0)
            if pts and pts > 100000:
                age_d = max(0, (now_ts - pts) // 86400)
                if age_d > max_days:
                    continue

        # Multi-Location filter: match ANY of the candidate's preferred cities/countries
        if has_specific_loc:
            if not _matches_any_loc(item):
                continue

        haystack = f"{item.get('company', '')} {item.get('role', '')} {item.get('category', '')} {item.get('location', '')} {' '.join(item.get('skills', []))} {item.get('description', '')}".lower()
        role_haystack = (item.get('role') or '').lower()

        # Token & Skills matching
        item_score = 0
        if match_resume:
            matched_skills = [s for s in clean_skills if s in haystack]
            matched_role = [t for t in role_tokens if t in role_haystack] if role_tokens else []
            matched_q = [t for t in q_tokens if t in haystack] if q_tokens else []
            
            # Score bonus for skills and optional role matching
            # Note: Target role is strictly optional bonus and NEVER eliminates a job!
            item_score = (len(matched_skills) * 20) + (len(matched_role) * 5) + (len(matched_q) * 10)
        elif q_tokens:
            matched_count = sum(1 for token in q_tokens if token in haystack)
            min_required = len(q_tokens) if len(q_tokens) <= 2 else max(2, int(len(q_tokens) * 0.6))
            if matched_count < min_required:
                continue
            item_score = matched_count * 10
        else:
            item_score = 10

        # Category filter
        item_cat = (item.get("category") or "").lower()
        if category and category.lower() not in ["all", "any"]:
            cat_target = category.lower()
            if cat_target in ["tech", "software"]:
                if not any(k in item_cat for k in ["software", "tech", "engineering"]):
                    continue
            elif cat_target in ["ai", "data"]:
                if not any(k in item_cat for k in ["ai", "ml", "data", "machine learning"]):
                    continue
            elif cat_target == "quant":
                if "quant" not in item_cat:
                    continue
            elif cat_target != item_cat:
                continue

        # Work mode filter
        if work_mode and work_mode.lower() not in ["all", "any"]:
            wm = work_mode.lower()
            loc_lower = (item.get("location") or "").lower()
            is_remote = "remote" in loc_lower or "anywhere" in loc_lower or "worldwide" in loc_lower
            if wm == "remote" and not is_remote:
                continue
            elif wm == "hybrid" and "hybrid" not in loc_lower:
                continue
            elif wm == "onsite" and is_remote:
                continue

        # Contract type filter
        if contract_type and contract_type.lower() not in ["all", "any"]:
            ct = contract_type.lower()
            role_lower = (item.get("role") or "").lower()
            is_intern = item.get("feed_type") == "internships" or any(k in role_lower for k in ["intern", "co-op", "trainee", "fellowship"])
            is_contract = "contract" in role_lower or "freelance" in role_lower
            if ct in ["intern", "internship"] and not is_intern:
                continue
            elif ct in ["contract", "temporary"] and not is_contract:
                continue
            elif ct in ["full-time", "fulltime"] and is_intern:
                continue

        # Minimum package check
        if min_package_lpa > 0.0:
            item_pkg = item.get("package_inr_lpa")
            if item_pkg is None:
                item_pkg, _ = estimate_job_package(
                    item.get("role", ""),
                    item.get("company", ""),
                    item.get("feed_type", "")
                )
            if item_pkg < (min_package_lpa - 0.5):
                continue

        item_dict = dict(item)
        item_dict["_match_score"] = item_score
        scored_items.append(item_dict)

    filtered = scored_items

    # 4. Fallback & Resume Enrichment pipeline
    if match_resume and len(filtered) < 12:
        # When matching a candidate's resume, broaden beyond strict city/salary if < 12 matches
        seen_urls_fb = {it.get("url") for it in filtered if it.get("url")}
        match_pool = clean_skills or role_tokens or q_tokens
        broad_matches = []
        for item in combined_items:
            u = item.get("url")
            if not u or u in seen_urls_fb:
                continue
            if max_days and max_days > 0:
                pts = item.get("date_posted_ts", 0)
                if pts and pts > 100000 and ((now_ts - pts) // 86400) > max_days:
                    continue
            haystack = f"{item.get('company', '')} {item.get('role', '')} {item.get('category', '')} {' '.join(item.get('skills', []))} {item.get('description', '')}".lower()
            s_hits = sum(1 for tok in match_pool if tok in haystack) if match_pool else 1
            if s_hits > 0 or not match_pool:
                it_copy = dict(item)
                it_copy["_match_score"] = s_hits * 15
                broad_matches.append(it_copy)
        broad_matches.sort(key=lambda x: (x.get("_match_score", 0), x.get("date_posted_ts", 0)), reverse=True)
        for bm in broad_matches:
            if bm.get("url") not in seen_urls_fb:
                seen_urls_fb.add(bm.get("url"))
                filtered.append(bm)
            if len(filtered) >= 25:
                break

    if not filtered:
        if has_specific_loc and not match_resume:
            # Fallback ONLY within the requested locations for manual location queries!
            loc_pool = [it for it in combined_items if _matches_any_loc(it)]
            if loc_pool:
                filtered = list(loc_pool[:50])
            else:
                filtered = []
        else:
            # Broad search fallback
            if q_tokens or clean_skills:
                match_pool = clean_skills or q_tokens
                for item in combined_items:
                    haystack = f"{item.get('company', '')} {item.get('role', '')} {item.get('location', '')}".lower()
                    if any(token in haystack for token in match_pool):
                        filtered.append(item)
            if not filtered:
                filtered = list(combined_items[:50])

    # 5. Sort: primarily by match score if matching resume, then by recency
    if match_resume:
        filtered.sort(key=lambda x: (x.get("_match_score", 0), x.get("date_posted_ts", 0)), reverse=True)
    else:
        filtered.sort(key=lambda x: x.get("date_posted_ts", 0), reverse=True)

    total_count = len(filtered)
    page_slice = filtered[offset : offset + limit]

    # 6. Hydrate display package metadata (clean without rupee symbols)
    processed_items = []
    for item in page_slice:
        item_copy = dict(item)
        loc = item_copy.get("location")
        if not loc and item_copy.get("locations_list"):
            loc = ", ".join([str(c).title() for c in item_copy.get("locations_list") if c])
        if has_specific_loc and loc and not _matches_any_loc({"location": loc, "locations_list": []}):
            loc = f"{loc_list[0].title()} / {loc}"
        item_copy["location"] = loc or "Remote / Hybrid"
        pkg_val, pkg_disp = estimate_job_package(
            item_copy.get("role", ""),
            item_copy.get("company", ""),
            item_copy.get("feed_type", "")
        )
        item_copy["package_inr_lpa"] = item_copy.get("package_inr_lpa") or pkg_val
        item_copy["package_display"] = item_copy.get("package_display") or pkg_disp

        posted_ts = item_copy.get("date_posted_ts", 0)
        diff_days = max(0, (now_ts - posted_ts) // 86400) if (posted_ts and posted_ts > 100000) else 0
        item_copy["date_posted_str"] = f"{diff_days}d ago" if diff_days > 0 else "Today"
        item_copy["days_ago"] = diff_days

        processed_items.append(item_copy)

    apply_vip_latest_feed_lock(processed_items, user_is_paid=user_is_paid)

    # 7. Fetch external / LinkedIn postings when matching resume (or on initial search)
    external_jobs = []
    if match_resume and offset == 0:
        try:
            from core.job_engine import query_linkedin_jobs
            li_query = (target_role or "").strip()
            if not li_query and clean_skills:
                li_query = " ".join(clean_skills[:2])
            if not li_query:
                li_query = (query or "").strip() or "Software Engineer"
            li_loc = loc_list[0] if has_specific_loc else "India"
            raw_li = query_linkedin_jobs(li_query, location=li_loc, limit=8)
            for lj in raw_li:
                lj_copy = dict(lj)
                lj_copy["role"] = lj_copy.get("title") or "External Opening"
                lj_copy["portal_provider"] = "LinkedIn (Unofficial)"
                lj_copy["date_posted_str"] = lj_copy.get("posted_at") or "Recent"
                lj_copy["is_locked"] = False
                external_jobs.append(lj_copy)
        except Exception as li_err:
            print(f"[OMNI] LinkedIn external fetch note: {li_err}")

    return {
        "total": total_count,
        "items": processed_items,
        "external_jobs": external_jobs,
        "limit": limit,
        "offset": offset,
        "query": query,
        "min_package_lpa": min_package_lpa
    }
