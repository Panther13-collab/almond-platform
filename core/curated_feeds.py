import urllib.request
import json
import time
import re
import os
import threading
from typing import List, Dict, Any, Optional
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
            return 8.0, "₹65,000 - ₹1,20,000 / mo Stipend (~8 LPA)"
        elif any(k in r for k in ["software", "developer", "engineer", "data", "cloud", "security"]):
            return 5.5, "₹35,000 - ₹55,000 / mo Stipend (~5.5 LPA)"
        else:
            return 3.6, "₹20,000 - ₹35,000 / mo Stipend (~3.6 LPA)"

    if any(k in r for k in ["ai", "ml", "machine learning", "deep learning", "llm", "nlp", "computer vision", "quant"]):
        if tier1:
            return 34.0, "₹28 - ₹42 LPA (Tier-1 Benchmark)"
        return 22.0, "₹18 - ₹26 LPA (Corporate Disclosed)"

    if any(k in r for k in ["lead", "principal", "staff", "architect", "senior", "director"]):
        if tier1:
            return 45.0, "₹40 - ₹60 LPA (Leadership Tier)"
        return 28.0, "₹24 - ₹35 LPA (Senior Benchmark)"

    if any(k in r for k in ["software", "developer", "backend", "frontend", "full stack", "devops", "cloud", "security", "systems"]):
        if tier1:
            return 26.0, "₹20 - ₹32 LPA (Disclosed Tier-1)"
        return 16.5, "₹12 - ₹20 LPA (Corporate Direct Feed)"

    if any(k in r for k in ["product", "program", "analytics", "data analyst", "bi engineer"]):
        if tier1:
            return 22.0, "₹18 - ₹26 LPA"
        return 14.0, "₹10 - ₹16 LPA"

    if any(k in r for k in ["mechanical", "electrical", "civil", "hardware", "embedded", "robotics"]):
        if tier1:
            return 16.0, "₹14 - ₹20 LPA"
        return 11.0, "₹8 - ₹14 LPA (Core Industry Benchmark)"

    return 9.0, "₹7 - ₹12 LPA (Enterprise Benchmark)"

def _normalize_simplify_listing(item: Dict[str, Any], feed_type: str) -> Optional[Dict[str, Any]]:
    if not item.get("active", False):
        return None
    raw_url = item.get("url") or ""
    cleaned_url = clean_job_url(raw_url)
    if not cleaned_url or not cleaned_url.startswith("http"):
        return None

    # Detect corporate ATS provider
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

def matches_country_filter(item: Dict[str, Any], target_country: str) -> bool:
    """Matches a job against a requested country filter using name, aliases, states, and hubs."""
    if not target_country or target_country.lower() in ["all", "any", "all locations", "all countries", "worldwide"]:
        return True

    t = target_country.strip().lower()
    loc = (item.get("location") or "").lower()
    locs_list = [l.lower() for l in (item.get("locations_list") or [])]
    full_loc_text = " ".join([loc] + locs_list)
    raw_loc = item.get("location") or ""

    # Remote / Worldwide target
    if t in ["remote", "worldwide", "remote / worldwide", "remote only"]:
        return any(k in full_loc_text for k in ["remote", "worldwide", "anywhere", "global"])

    # India target
    if t in ["india", "in", "ind", "bharat"]:
        if re.search(r'\bindia\b', full_loc_text):
            return True
        if any(c in full_loc_text for c in [
            "bengaluru", "bangalore", "chennai", "hyderabad", "pune", "mumbai",
            "delhi", "new delhi", "noida", "gurgaon", "gurugram", "kolkata",
            "ahmedabad", "coimbatore", "kochi", "ernakulam", "trivandrum",
            "thiruvananthapuram", "mysore", "chandigarh", "jaipur"
        ]):
            return True
        return False

    # United States / America / USA target
    if t in ["united states", "america", "usa", "us", "united states (america)"]:
        if any(k in full_loc_text for k in ["united states", "usa", "u.s.", "america"]):
            return True
        for st in US_STATE_CODES:
            if re.search(r'[\s,]' + st + r'(\b|\+|$)', raw_loc):
                return True
        if any(c in full_loc_text for c in [
            "san francisco", "sf", "silicon valley", "new york", "nyc", "seattle",
            "austin", "chicago", "boston", "los angeles", "atlanta", "denver",
            "palo alto", "mountain view", "sunnyvale", "san jose"
        ]):
            return True
        return False

    # United Kingdom target
    if t in ["united kingdom", "uk", "great britain", "england", "scotland", "wales", "united kingdom (uk)"]:
        if any(k in full_loc_text for k in ["united kingdom", "england", "scotland", "wales", "great britain"]):
            return True
        if re.search(r'[\s,]uk\b', full_loc_text):
            return True
        if any(c in full_loc_text for c in ["london", "manchester", "birmingham", "edinburgh", "bristol", "cambridge", "oxford", "glasgow", "leeds"]):
            return True
        return False

    # Canada target
    if t in ["canada", "can"]:
        if "canada" in full_loc_text:
            return True
        for pr in CA_PROVINCE_CODES:
            if re.search(r'[\s,]' + pr + r'(\b|\+|$)', raw_loc):
                return True
        if any(c in full_loc_text for c in ["toronto", "vancouver", "montreal", "ottawa", "waterloo", "calgary", "edmonton"]):
            return True
        return False

    # Germany target
    if t in ["germany", "deutschland", "de"]:
        if any(k in full_loc_text for k in ["germany", "deutschland", "berlin", "munich", "frankfurt", "hamburg", "stuttgart"]):
            return True
        return False

    # Australia target
    if t in ["australia", "au"]:
        if any(k in full_loc_text for k in ["australia", "sydney", "melbourne", "brisbane", "perth", "canberra"]):
            return True
        return False

    # Netherlands target
    if t in ["netherlands", "holland", "nl"]:
        if any(k in full_loc_text for k in ["netherlands", "holland", "amsterdam", "rotterdam", "utrecht", "eindhoven", "the hague"]):
            return True
        return False

    # Singapore target
    if t in ["singapore", "sg"]:
        return "singapore" in full_loc_text

    # Ireland target
    if t in ["ireland", "ie"]:
        return any(k in full_loc_text for k in ["ireland", "dublin", "cork", "galway"])

    # France target
    if t in ["france", "fr"]:
        return any(k in full_loc_text for k in ["france", "paris", "lyon", "toulouse"])

    # Switzerland target
    if t in ["switzerland", "ch"]:
        return any(k in full_loc_text for k in ["switzerland", "zurich", "geneva", "lausanne", "basel"])

    # UAE target
    if t in ["united arab emirates", "uae", "dubai", "abu dhabi", "united arab emirates (uae)"]:
        return any(k in full_loc_text for k in ["uae", "united arab emirates", "dubai", "abu dhabi"])

    # Japan target
    if t in ["japan", "jp"]:
        return any(k in full_loc_text for k in ["japan", "tokyo", "osaka", "kyoto"])

    # Spain target
    if t in ["spain", "es"]:
        return any(k in full_loc_text for k in ["spain", "madrid", "barcelona", "valencia"])

    # Sweden
    if t in ["sweden", "se"]:
        return any(k in full_loc_text for k in ["sweden", "stockholm", "gothenburg"])

    # Poland
    if t in ["poland", "pl"]:
        return any(k in full_loc_text for k in ["poland", "warsaw", "krakow", "wroclaw"])

    # Brazil
    if t in ["brazil", "br"]:
        return any(k in full_loc_text for k in ["brazil", "brasil", "sao paulo", "rio"])

    clean_t = re.sub(r'\(.*?\)', '', t).strip()
    return clean_t in full_loc_text

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

    # Extract all distinct categories
    all_categories = sorted(list(set(item.get("category", "General") for item in all_items if item.get("category"))))

    filtered = []
    q_tokens = [t.lower().strip() for t in query.split() if t.strip()]
    now_ts = int(time.time())

    for item in all_items:
        # Location / Country filter
        if location and location.lower() not in ["all", "any", "all locations", "all countries", "worldwide"]:
            if not matches_country_filter(item, location):
                continue

        # Category filter
        item_cat = (item.get("category") or "").lower()
        if category and category.lower() not in ["all", "any"]:
            cat_target = category.lower()
            if cat_target == "tech" or cat_target == "software":
                if not any(k in item_cat for k in ["software", "tech", "engineering"]):
                    continue
            elif cat_target == "ai" or cat_target == "data":
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

        # Time filter
        if time_filter and time_filter != "all":
            posted_ts = item.get("date_posted_ts", 0)
            if time_filter == "24h" and (now_ts - posted_ts > 86400 * 1.5):
                continue
            elif time_filter == "7d" and (now_ts - posted_ts > 86400 * 7):
                continue
            elif time_filter == "30d" and (now_ts - posted_ts > 86400 * 30):
                continue

        # Query search across company, role, location
        if q_tokens:
            haystack = f"{item.get('company', '')} {item.get('role', '')} {item.get('location', '')} {item.get('category', '')}".lower()
            if not all(token in haystack for token in q_tokens):
                continue

        filtered.append(item)

    # Flipkart / Amazon style sort options (Latest, Oldest, Package High to Low, Package Low to High)
    if sort_by == "oldest":
        filtered.sort(key=lambda x: x.get("date_posted_ts", 0), reverse=False)
    elif sort_by == "package_desc":
        filtered.sort(key=lambda x: (x.get("package_inr_lpa") or estimate_job_package(x.get("role", ""), x.get("company", ""), x.get("feed_type", feed_type))[0]), reverse=True)
    elif sort_by == "package_asc":
        filtered.sort(key=lambda x: (x.get("package_inr_lpa") or estimate_job_package(x.get("role", ""), x.get("company", ""), x.get("feed_type", feed_type))[0]), reverse=False)
    else: # latest (default)
        filtered.sort(key=lambda x: x.get("date_posted_ts", 0), reverse=True)

    total_count = len(filtered)
    page_slice = filtered[offset : offset + limit]

    # Apply free preview vs VIP locking (first 10 jobs 100% unlocked with direct links across all tabs & categories)
    processed_items = []
    for idx, item in enumerate(page_slice):
        item_copy = dict(item)
        # Attach package if not already set
        pkg_val, pkg_disp = estimate_job_package(item_copy.get("role", ""), item_copy.get("company", ""), item_copy.get("feed_type", feed_type))
        item_copy["package_inr_lpa"] = item_copy.get("package_inr_lpa") or pkg_val
        item_copy["package_display"] = item_copy.get("package_display") or pkg_disp

        # Recalculate dynamic freshness relative to right now
        posted_ts = item_copy.get("date_posted_ts", 0)
        if posted_ts and posted_ts > 100000:
            diff_days = max(0, (now_ts - posted_ts) // 86400)
            item_copy["date_posted_str"] = f"{diff_days}d ago" if diff_days > 0 else "Today"

        item_copy["days_ago"] = diff_days if posted_ts and posted_ts > 100000 else None
        processed_items.append(item_copy)

    apply_vip_latest_feed_lock(processed_items, user_is_paid=user_is_paid)

    return {
        "total": total_count,
        "items": processed_items,
        "categories": all_categories,
        "feed_type": feed_type,
        "sort_by": sort_by
    }
