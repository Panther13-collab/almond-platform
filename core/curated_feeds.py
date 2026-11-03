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

_MEMORY_CACHE: Dict[str, Dict[str, Any]] = {
    "internships": {"data": [], "timestamp": 0},
    "entrylevel": {"data": [], "timestamp": 0},
    "aiml": {"data": [], "timestamp": 0}
}
_CACHE_LOCK = threading.Lock()
_CACHE_TTL = 7200  # 2 hours in seconds

def _fetch_url_with_timeout(url: str, timeout: int = 10) -> str:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "AlmondJobs/1.0 (Direct Corporate Career Engine)"}
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
        "id": f"{feed_type}_{item.get('id', str(hash(cleaned_url))[:12])}",
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
                # Detect provider
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
                    "date_posted_ts": int(time.time()),
                    "date_posted_str": date_p or "Recent",
                    "sponsorship": "Standard",
                    "feed_type": "aiml",
                    "is_locked": False
                })
    return results

def get_feed_data(feed_type: str) -> List[Dict[str, Any]]:
    """Retrieve verified feed data with local disk and memory caching."""
    now = time.time()
    with _CACHE_LOCK:
        cached = _MEMORY_CACHE.get(feed_type)
        if cached and cached["data"] and (now - cached["timestamp"] < _CACHE_TTL):
            return cached["data"]

    # Check local disk cache
    disk_file = os.path.join(CACHE_DIR, f"{feed_type}_cache.json")
    if os.path.exists(disk_file):
        try:
            mtime = os.path.getmtime(disk_file)
            if now - mtime < _CACHE_TTL:
                with open(disk_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    with _CACHE_LOCK:
                        _MEMORY_CACHE[feed_type] = {"data": data, "timestamp": mtime}
                    return data
        except Exception as e:
            print(f"[CURATED FEEDS] Disk cache read warning ({feed_type}): {e}")

    # Fetch from live source
    data = []
    try:
        if feed_type == "internships":
            raw_text = _fetch_url_with_timeout(INTERNSHIPS_URL, timeout=12)
            raw_json = json.loads(raw_text)
            for item in raw_json:
                norm = _normalize_simplify_listing(item, "internships")
                if norm:
                    data.append(norm)

        elif feed_type == "entrylevel":
            raw_text = _fetch_url_with_timeout(NEW_GRAD_URL, timeout=12)
            raw_json = json.loads(raw_text)
            for item in raw_json:
                norm = _normalize_simplify_listing(item, "entrylevel")
                if norm:
                    data.append(norm)

        elif feed_type == "aiml":
            raw_md = _fetch_url_with_timeout(AI_COLLEGE_URL, timeout=10)
            data = _parse_speedyapply_ai(raw_md)

        # Write to disk cache
        if data:
            with open(disk_file, "w", encoding="utf-8") as f:
                json.dump(data, f)
            with _CACHE_LOCK:
                _MEMORY_CACHE[feed_type] = {"data": data, "timestamp": now}
            print(f"[CURATED FEEDS] Successfully loaded and cached {len(data)} items for '{feed_type}'")
    except Exception as e:
        print(f"[CURATED FEEDS] Live fetch failed for '{feed_type}': {e}")
        # If live fetch fails, fallback to stale disk cache if available
        if os.path.exists(disk_file):
            try:
                with open(disk_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    with _CACHE_LOCK:
                        _MEMORY_CACHE[feed_type] = {"data": data, "timestamp": now}
            except Exception:
                pass

    return data

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

    total_count = len(filtered)
    page_slice = filtered[offset : offset + limit]

    # Apply free preview vs VIP locking (free users see first 3 unlocked)
    processed_items = []
    for idx, item in enumerate(page_slice):
        item_copy = dict(item)
        absolute_idx = offset + idx
        if not user_is_paid and absolute_idx >= 3:
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
