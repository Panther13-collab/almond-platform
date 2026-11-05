import urllib.request
import json
import time
import re
import os
import threading
from typing import List, Dict, Any, Optional
from core.job_engine import clean_job_url

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

def query_curated_feed(
    feed_type: str = "internships",
    query: str = "",
    category: str = "All",
    time_filter: str = "all",
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

    # Always sort by freshness (latest first) by default
    filtered.sort(key=lambda x: x.get("date_posted_ts", 0), reverse=True)

    total_count = len(filtered)
    page_slice = filtered[offset : offset + limit]

    # Apply free preview vs VIP locking (first 10 jobs 100% unlocked with direct links across all tabs & categories)
    processed_items = []
    for idx, item in enumerate(page_slice):
        item_copy = dict(item)
        # Recalculate dynamic freshness relative to right now
        posted_ts = item_copy.get("date_posted_ts", 0)
        if posted_ts and posted_ts > 100000:
            diff_days = max(0, (now_ts - posted_ts) // 86400)
            item_copy["date_posted_str"] = f"{diff_days}d ago" if diff_days > 0 else "Today"

        absolute_idx = offset + idx
        # TEST MODE: Display all curated feed links unblurred without payment restriction for testers
        # When VIP link restriction is re-enabled, set TEST_MODE_UNLOCKED_LINKS = False
        TEST_MODE_UNLOCKED_LINKS = True

        if not TEST_MODE_UNLOCKED_LINKS and not user_is_paid and absolute_idx >= 10:
            item_copy["is_locked"] = True
            item_copy["real_url"] = item_copy.get("url")
            item_copy["url"] = "#unlock-pro"
        else:
            item_copy["is_locked"] = False
        processed_items.append(item_copy)

    return {
        "total": total_count,
        "items": processed_items,
        "categories": all_categories,
        "feed_type": feed_type
    }
