# Unified Omni-Search & Pro Tier Upgrade Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform the Almond Jobs homepage into an ultra-clean, search-first discovery engine with instant omni-search, inline resume upload with criteria matching, and replace the legacy VIP popup with a modern SaaS tier comparison modal (Free vs. Pro).

**Architecture:** Combine in-memory cached job listings (Internships, Entry-Level, AI/ML Specialist) into a high-speed `/api/omni-search` backend endpoint querying by character, role, CTC package, and location. Integrate a debounced (120ms) client-side omni-search bar on the hero fold with an embedded resume intake trigger and inline results stream. Replace `#vipPassModal` with an authoritative 2-column comparative pricing matrix (Free vs. Pro) supporting 1m, 3m (30% off), and 6m (35% off) tiers with live Razorpay checkout.

**Tech Stack:** Python 3.11, FastAPI, Vanilla JavaScript (ES2022+), Tailwind CSS v4, Lucide Icons, Razorpay Checkout SDK, Playwright Chromium for E2E testing.

**Spec:** `docs/superpowers/specs/2026-11-20-unified-search-and-pro-upgrade-design.md`

## Global Constraints

- Modern Web Guidance compliance: 0 findings from `npx.cmd -y modern-web-guidance@latest legacy-scan platform --json`.
- Zero broken buttons or JavaScript syntax errors: `node -c platform/static/app.js` must exit with 0 errors.
- Strict preservation of Razorpay payment signatures, webhook validation, and user entitlement tokens.
- No coffee donation or contribution solicitations inside the Pro Upgrade modal.
- Maintain seamless mobile responsiveness down to 360px viewport width without horizontal scrollbars or clipped text.

## Review Focus

1. Partial single-letter keystrokes (e.g. typing `'s'` or `'S'`) should instantly match roles (e.g. Software Engineer, Systems Engineer) without throwing indexing errors or returning empty states.
2. Package queries (e.g. `'7 LPA'`, `'12 LPA'`) should correctly parse numeric salary benchmarks and filter jobs offering matching or higher packages.
3. Rapid typing (keystrokes < 120ms apart) should debounce properly and abort in-flight fetch requests without race condition flicker or stale card overwrites.
4. Dropping or selecting a resume in the omni-bar should cleanly open the criteria intake dialog, and submitting criteria should display matched cards in `#omniSearchResultsContainer` without navigating away from the homepage.
5. In the Pro Upgrade modal, selecting between 1-Month, 3-Month, and 6-Month duration pills must update the highlighted price, discount badges, and Razorpay checkout amount synchronously without reload.

---

### Task 1: Backend Omni-Search Engine & `/api/omni-search` Endpoint

**Files:**
- Modify: `platform/core/curated_feeds.py:480-576`
- Modify: `platform/app.py:1330-1360`
- Test: `platform/tests/verify_omni_search_api.py`

**Interfaces:**
- Consumes: `get_feed_data(feed_type: str) -> List[Dict[str, Any]]`, `estimate_job_package(role_str: str, company_str: str, feed_type: str) -> Tuple[float, str]`, `apply_vip_latest_feed_lock(items: List[Dict[str, Any]], user_is_paid: bool)`.
- Produces: `omni_search_all_feeds(query: str = "", category: str = "All", location: str = "all", min_package_lpa: float = 0.0, limit: int = 25, offset: int = 0, user_is_paid: bool = False) -> Dict[str, Any]`, and endpoint `GET /api/omni-search`.

- [ ] **Step 1: Write the failing test**

Create `platform/tests/verify_omni_search_api.py` testing:
1. `omni_search_all_feeds` returns combined results from internships, entrylevel, and aiml feeds without duplicate URLs.
2. Keystroke query `'s'` or `'soft'` returns matching software/systems jobs.
3. Package query `'7 LPA'` or `min_package_lpa=7.0` filters items where `package_inr_lpa >= 7.0`.
4. Empty query returns default high-freshness items.
5. Fast response time (<50ms).
6. FastAPI endpoint `/api/omni-search?q=engineer&limit=10` returns HTTP 200 with JSON payload `{"status": "success", "result": {"total": int, "items": list}}`.

```python
import unittest
from fastapi.testclient import TestClient
from core.curated_feeds import omni_search_all_feeds
from app import app

class TestOmniSearchAPI(unittest.TestCase):
    def test_omni_search_query_s(self):
        res = omni_search_all_feeds(query="s", limit=15)
        self.assertGreater(res["total"], 0)
        self.assertLessEqual(len(res["items"]), 15)

    def test_omni_search_package_filter(self):
        res = omni_search_all_feeds(query="7 LPA", limit=15)
        self.assertGreater(res["total"], 0)
        for item in res["items"][:5]:
            self.assertGreaterEqual(item.get("package_inr_lpa", 0.0), 6.5)

    def test_omni_search_api_endpoint(self):
        client = TestClient(app)
        response = client.get("/api/omni-search?q=developer&limit=10")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("items", data["result"])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest platform/tests/verify_omni_search_api.py`
Expected: FAIL with `ImportError: cannot import name 'omni_search_all_feeds' from 'core.curated_feeds'`

- [ ] **Step 3: Implement `omni_search_all_feeds` in `core/curated_feeds.py` and route in `app.py`**

In `platform/core/curated_feeds.py`:
- Implement `omni_search_all_feeds(query: str = "", category: str = "All", location: str = "all", min_package_lpa: float = 0.0, limit: int = 25, offset: int = 0, user_is_paid: bool = False) -> Dict[str, Any]`:
  - Pull listings from `get_feed_data("internships")`, `get_feed_data("entrylevel")`, `get_feed_data("aiml")`.
  - De-duplicate by `url`.
  - Extract numeric LPA from query string if present (e.g. `re.search(r'(\d+(?:\.\d+)?)\s*(?:lpa|lakh|lac)', query.lower())`).
  - Filter by query tokens across `role`, `company`, `location`, `category`.
  - Attach estimated package if not present (`package_inr_lpa`, `package_display`).
  - Sort by latest timestamp descending (`date_posted_ts`).
  - Slice by `[offset : offset + limit]`.
  - Apply `apply_vip_latest_feed_lock(items, user_is_paid=user_is_paid)`.
  - Return `{"total": len(filtered), "items": items, "limit": limit, "offset": offset, "query": query}`.

In `platform/app.py`:
- Add route:
```python
@app.get("/api/omni-search")
async def api_omni_search(
    q: str = Query(""),
    location: str = Query("all"),
    category: str = Query("All"),
    min_lpa: float = Query(0.0),
    limit: int = Query(25),
    offset: int = Query(0),
    user_id: Optional[str] = Query(None)
):
    user_paid = is_user_paid(user_id) if user_id else False
    res = omni_search_all_feeds(
        query=q,
        category=category,
        location=location,
        min_package_lpa=min_lpa,
        limit=min(limit, 100),
        offset=offset,
        user_is_paid=user_paid
    )
    return JSONResponse(content={"status": "success", "result": res})
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest platform/tests/verify_omni_search_api.py`
Expected: PASS with 3 tests OK.

- [ ] **Step 5: Commit**

```bash
git add platform/core/curated_feeds.py platform/app.py platform/tests/verify_omni_search_api.py
git commit -m "feat(api): implement omni_search_all_feeds and /api/omni-search endpoint"
```

---

### Task 2: Hero Fold Minimalist Redesign & Omni-Search Bar in HTML

**Files:**
- Modify: `platform/templates/index.html:840-920`
- Test: `platform/tests/verify_hero_omni_search_markup.py`

**Interfaces:**
- Consumes: Lucide icons (`search`, `paperclip`, `x`, `sparkles`, `external-link`).
- Produces: DOM elements:
  - `#omniSearchBarContainer`: Wrapper for unified search and upload bar.
  - `#omniSearchInput`: Text input for instant role/skill/package search.
  - `#omniClearBtn`: Button to clear current search input.
  - `#omniResumeUploadBtn`: Button reading `Upload your resume to find your dream job`.
  - `#omniResumeFileInput`: Hidden file input accepting `.pdf,.docx,.txt`.
  - `#omniSearchResultsContainer`: Target container where live matching cards stream.
  - `#omniCriteriaModal`: Intake modal with `#omniCriteriaTargetRole`, `#omniCriteriaExpectedPackage`, `#omniCriteriaLocation`, `#omniCriteriaSubmitBtn`.

- [ ] **Step 1: Write the failing test**

Create `platform/tests/verify_hero_omni_search_markup.py`:
- Parses `platform/templates/index.html`.
- Asserts that `#omniSearchBarContainer`, `#omniSearchInput`, `#omniResumeUploadBtn`, `#omniResumeFileInput`, and `#omniSearchResultsContainer` exist in `#hero`.
- Asserts that removed clutter (`NO BROKERS`, `NO MIDDLEMEN`, `NO DEAD POSTS`, `Freshers & Campus Notice`) does NOT exist in `#hero`.
- Asserts that `#omniCriteriaModal` exists for resume intake.

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest platform/tests/verify_hero_omni_search_markup.py`
Expected: FAIL with `AssertionError: '#omniSearchBarContainer' not found`

- [ ] **Step 3: Update `platform/templates/index.html`**

In `platform/templates/index.html`:
- Clean `#hero` container:
  - Remove top badge clusters (`AlmondJobs Direct Corporate Feed...`, `NO BROKERS`, `NO MIDDLEMEN`, `NO DEAD POSTS`, `Freshers & Campus Notice`).
  - Keep centered headline:
    - `Move first.`
    - `Apply unseen!`
    - Narrative Subheadline: `"The job market isn't oversaturated — you're just applying after the door has already closed. We ingest jobs straight from company internal servers the second they open."`
  - Insert Unified Omni-Search Bar `#omniSearchBarContainer`:
    - Responsive flex/grid container with rounded-3xl border, background blur, and focus ring.
    - Left side: Lucide `search` icon, `<input type="text" id="omniSearchInput" placeholder="Type any skill, role, package (e.g. Software Engineer, 7 LPA, Python, Bangalore)..." class="...">`, Lucide `x` clear button `#omniClearBtn`.
    - Right side: `<button type="button" id="omniResumeUploadBtn" onclick="triggerOmniResumeUpload()" class="flex items-center gap-2 px-4 py-2.5 rounded-full bg-violet-600 hover:bg-violet-700 text-white font-black text-xs sm:text-sm shadow-md ..."><i data-lucide="paperclip" class="w-4 h-4"></i><span>Upload your resume to find your dream job</span></button>` with hidden file input `<input type="file" id="omniResumeFileInput" accept=".pdf,.docx,.txt" class="hidden" onchange="handleOmniResumeSelected(event)">`.
  - Insert `#omniSearchResultsContainer`:
    - Renders directly below the search bar.
    - Header with live results count, query indicator, and quick filter chips (All, Direct Internships, Entry-Level, AI/ML Specialist).
    - Grid container `#omniResultsCardsGrid` for streaming job cards.
  - Insert `#omniCriteriaModal`:
    - Clean backdrop and modal window asking for Candidate Target Preferences:
      - Target Role / Domain (`#omniCriteriaTargetRole`)
      - Expected Package (`#omniCriteriaExpectedPackage`, e.g. "7 LPA")
      - Preferred Location (`#omniCriteriaLocation`, e.g. "Bangalore / Remote")
      - Submit button `#omniCriteriaSubmitBtn` reading `Show Matching Direct Jobs`.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest platform/tests/verify_hero_omni_search_markup.py`
Expected: PASS with 1 test OK.

- [ ] **Step 5: Commit**

```bash
git add platform/templates/index.html platform/tests/verify_hero_omni_search_markup.py
git commit -m "feat(ui): add unified omni-search bar and criteria intake markup to hero fold"
```

---

### Task 3: Client-side Instant Omni-Search, Live Stream & Resume Drop Engine

**Files:**
- Modify: `platform/static/app.js`
- Test: `platform/tests/verify_omni_search_client_js.py`

**Interfaces:**
- Consumes: `/api/omni-search?q=...`, `/api/upload-resume`, `/api/find-jobs`.
- Produces: JavaScript functions:
  - `initOmniSearch()`
  - `executeOmniSearch(query, isInitial)`
  - `renderOmniResults(data, query)`
  - `triggerOmniResumeUpload()`
  - `handleOmniResumeSelected(event)`
  - `openOmniCriteriaModal(parsedProfile)`
  - `submitOmniCriteria()`

- [ ] **Step 1: Write the failing test**

Create `platform/tests/verify_omni_search_client_js.py`:
- Uses Node.js (`node -e "..."`) or Python parser to verify:
  1. `node -c platform/static/app.js` exits with 0 (no syntax errors).
  2. The functions `initOmniSearch`, `executeOmniSearch`, `renderOmniResults`, `triggerOmniResumeUpload`, `handleOmniResumeSelected`, `openOmniCriteriaModal`, `submitOmniCriteria` exist in `app.js`.
  3. AbortController logic is implemented to cancel stale in-flight search requests.

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest platform/tests/verify_omni_search_client_js.py`
Expected: FAIL with missing functions.

- [ ] **Step 3: Implement client logic in `platform/static/app.js`**

In `platform/static/app.js`:
- `let omniSearchAbortController = null;`
- `let omniSearchDebounceTimer = null;`
- `let omniCurrentProfile = null;`
- Implement `initOmniSearch()`:
  - Attaches `input` listener on `#omniSearchInput`.
  - Debounces by 120ms:
    ```javascript
    clearTimeout(omniSearchDebounceTimer);
    omniSearchDebounceTimer = setTimeout(() => {
        const query = searchInput.value.trim();
        executeOmniSearch(query);
    }, 120);
    ```
  - Attaches click on `#omniClearBtn` to clear input and re-execute default feed.
  - Executes `executeOmniSearch("", true)` on DOMContentLoaded to populate initial live crawl feed cards below the bar.
- Implement `executeOmniSearch(query, isInitial)`:
  - Aborts in-flight controller if pending.
  - Fetches `/api/omni-search?q=${encodeURIComponent(query)}&limit=20`.
  - Calls `renderOmniResults(data.result, query)`.
- Implement `renderOmniResults(result, query)`:
  - Renders total matching count in `#omniResultsCountBadge`.
  - For each job, creates card with:
    - Role title (unredacted or VIP badge if locked).
    - Company name & verified logo / letter mark.
    - Location badge & Package badge (e.g. `₹7 - ₹12 LPA`).
    - Corporate ATS provider tag (`Greenhouse`, `Lever`, `Ashby`, `Workday`, `Direct Portal`).
    - Freshness badge (`Today`, `1d ago`).
    - Action button: Direct Link to Apply (or Unlock with Pro if locked).
  - Handles empty state gracefully (`"No matching openings found for '${query}'. Try searching by role, skill, or LPA..."`).
- Implement `triggerOmniResumeUpload()` and `handleOmniResumeSelected(event)`:
  - Triggers click on `#omniResumeFileInput`.
  - When file selected:
    - Shows subtle spinner in upload button.
    - POSTs `FormData` with file to `/api/upload-resume`.
    - Stores `omniCurrentProfile = data.profile`.
    - Populates `#omniCriteriaTargetRole` with `profile.current_role || profile.skills[0] || ""`.
    - Opens `#omniCriteriaModal`.
- Implement `submitOmniCriteria()`:
  - Reads values from criteria fields.
  - Calls `/api/find-jobs` with profile and criteria preferences.
  - Renders returned matched cards into `#omniSearchResultsContainer`.
  - Closes criteria modal and smoothly scrolls to `#omniSearchResultsContainer`.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest platform/tests/verify_omni_search_client_js.py`
Expected: PASS with 0 syntax errors and all functions defined.

- [ ] **Step 5: Commit**

```bash
git add platform/static/app.js platform/tests/verify_omni_search_client_js.py
git commit -m "feat(ui): implement debounced omni-search, live results stream, and resume intake engine"
```

---

### Task 4: Title Bar "✨ Upgrade" & SaaS 2-Column Comparison Pricing Matrix Modal

**Files:**
- Modify: `platform/templates/index.html:660-672, 2613-2820`
- Modify: `platform/static/app.js`
- Test: `platform/tests/verify_upgrade_saas_modal.py`

**Interfaces:**
- Consumes: Razorpay checkout script, active auth token/session.
- Produces:
  - `#topUpgradeBtn` in title bar with text `✨ Upgrade`.
  - `#vipPassModal` transformed into a 2-Column SaaS pricing matrix:
    - `#freeTierColumn`: Left column, Free Forever (₹0), feature checklist, disabled "Current Plan" button.
    - `#proTierColumn`: Right column, Pro Corporate Access, duration toggle pills (1m, 3m [30% OFF], 6m [35% OFF]), feature checklist, and dynamic Razorpay checkout CTA button.
  - Active Pro member view: Shows active expiration date and allows stacking duration (+30, +90, +180 days).

- [ ] **Step 1: Write the failing test**

Create `platform/tests/verify_upgrade_saas_modal.py`:
- Parses `platform/templates/index.html`:
  - Checks `#topUpgradeBtn` exists with text containing `Upgrade` (replaces legacy `👑 VIP Pass`).
  - Checks `#freeTierColumn` exists with "Free Forever" / ₹0 / $0 and feature list.
  - Checks `#proTierColumn` exists with duration pills: 1 Month (`#proTierPill_1m`), 3 Months (`#proTierPill_3m`), 6 Months (`#proTierPill_6m`).
  - Checks absence of coffee donation/contribution solicitations.
  - Checks Razorpay checkout CTA `#proTierCheckoutBtn`.

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest platform/tests/verify_upgrade_saas_modal.py`
Expected: FAIL with `#topUpgradeBtn` or `#freeTierColumn` not found.

- [ ] **Step 3: Implement Title Bar Upgrade Button & 2-Column SaaS Matrix Modal**

In `platform/templates/index.html`:
- Update line 660:
  ```html
  <button type="button" id="topUpgradeBtn" onclick="openUpgradeModal()" class="flex bg-gradient-to-r from-amber-500 via-yellow-500 to-amber-600 hover:from-amber-400 hover:to-yellow-400 text-slate-950 font-black text-[11px] sm:text-xs px-3 sm:px-4 py-1.5 sm:py-2 rounded-full shadow-xs hover:scale-105 active:scale-95 transition-all cursor-pointer whitespace-nowrap items-center gap-1.5">
      <span>✨</span>
      <span id="topUpgradeLabel">Upgrade</span>
  </button>
  ```
- Replace contents of `#vipModalPurchaseView` (lines 2631-2751) with a modern 2-Column Grid (`grid grid-cols-1 md:grid-cols-2 gap-6`):
  - **Left Column: Free Tier** (`#freeTierColumn`):
    - Header: `Free Tier` &bull; `Public Access`
    - Price: `₹0` / `Free Forever`
    - Features:
      - Standard public job listings across direct portals
      - Basic keyword & role search
      - Standard directory links
      - Community application tips
    - Footer Button: `<button disabled class="w-full py-3 rounded-2xl bg-slate-100 text-slate-400 font-extrabold text-xs cursor-default">Current Plan</button>`
  - **Right Column: Pro Tier** (`#proTierColumn`, visually prominent with border-amber-400, amber gradient header, and subtle shadow):
    - Header: `👑 Pro Tier` &bull; `Corporate Direct Access`
    - Duration Pills Selector:
      - 1 Month: `₹699` / `$19.99`
      - 3 Months (Selected by default): `₹1,799` / `$49.99` (Badge: `30% OFF`)
      - 6 Months: `₹2,799` / `$79.99` (Badge: `35% OFF`)
    - Currency selector toggle (INR, USD, EUR, GBP).
    - Features:
      - ⚡ **First-Wave Ingestion:** Apply within 48h of internal corporate opening before candidate saturation.
      - 🎯 **0% Recruiter Spread:** Direct HR & hiring manager portals (Greenhouse, Lever, Ashby, Workday).
      - 🔍 **Unredacted Signals:** Disclosed compensation bands, hiring lead titles, and company priority metrics.
      - 📑 **1-Click Dossiers & Tracker Exports:** Unlimited PDF, Word, and Kanban application tracking.
      - 🚀 **Continuous Search Coverage:** Active alerts and automated daily matches.
    - Footer CTA: `<button type="button" id="proTierCheckoutBtn" onclick="executeVipPassCheckout()" class="w-full py-3.5 px-6 rounded-2xl bg-gradient-to-r from-amber-500 via-amber-400 to-yellow-500 hover:from-amber-400 hover:to-yellow-400 active:scale-98 text-slate-950 font-black text-sm tracking-wide shadow-lg shadow-amber-500/20 flex items-center justify-center gap-2 cursor-pointer transition">🚀 Upgrade to Pro — <span id="proCheckoutPriceLabel">₹1,799</span></button>`
  - Ensure `#vipModalActiveMemberView` remains intact for active Pro members, displaying their active subscription expiry date and duration stacking options (+30d, +90d, +180d).

In `platform/static/app.js`:
- Define `window.openUpgradeModal = window.openVipPassModal;`
- Update `selectVipPurchaseTier(tier)` to update `#proCheckoutPriceLabel`, active styles on `#proTierPill_1m`, `#proTierPill_3m`, `#proTierPill_6m`, and synchronize prices with the selected currency.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest platform/tests/verify_upgrade_saas_modal.py`
Expected: PASS with 1 test OK.

- [ ] **Step 5: Commit**

```bash
git add platform/templates/index.html platform/static/app.js platform/tests/verify_upgrade_saas_modal.py
git commit -m "feat(ui): redesign Upgrade modal into 2-column SaaS comparative pricing matrix"
```

---

### Task 5: End-to-End Browser Verification Test & Modern Web Guidance Audit

**Files:**
- Create: `platform/tests/verify_omni_search_and_upgrade_browser_e2e.py`
- Modify: `platform/templates/index.html` (cache buster query string `?v=...`)

**Interfaces:**
- Consumes: Running FastAPI app instance, Playwright Headless Chromium.
- Produces: Verified end-to-end user workflows, 0 browser console errors, 0 modern-web-guidance legacy findings.

- [ ] **Step 1: Write the browser E2E Playwright test**

Create `platform/tests/verify_omni_search_and_upgrade_browser_e2e.py`:
- Spins up local test server or connects to `http://127.0.0.1:8000`.
- Launches Playwright Chromium with `browser.new_context(viewport={'width': 1280, 'height': 800})`.
- Injects `sessionStorage.setItem("almond_human_verified", "true")` to bypass human verification popup.
- Verifies:
  1. Loads homepage `http://127.0.0.1:8000/`.
  2. Hero fold displays centered headline (`Move first. Apply unseen!`) and `#omniSearchInput`.
  3. Types `'s'` into `#omniSearchInput`, waits 300ms, asserts `#omniResultsCardsGrid` contains at least 3 matching cards.
  4. Types `'7 LPA'` into `#omniSearchInput`, asserts cards update to reflect package filter.
  5. Clicks `#omniResumeUploadBtn`, verifies file input is clickable.
  6. Clicks `#topUpgradeBtn` in title bar, asserts `#vipPassModal` opens and is visible.
  7. Asserts both Free Tier column and Pro Tier column are displayed side-by-side.
  8. Clicks 1-Month pill (`#proTierPill_1m`), asserts price label updates to `₹699`.
  9. Clicks 6-Month pill (`#proTierPill_6m`), asserts price label updates to `₹2,799`.
  10. Asserts zero JavaScript runtime errors or console error messages during the entire session.

- [ ] **Step 2: Run browser E2E test to verify all flows pass**

Run: `python platform/tests/verify_omni_search_and_upgrade_browser_e2e.py`
Expected: All assertions PASS with `[PASS] Browser E2E Omni-Search and SaaS Upgrade verified cleanly.`

- [ ] **Step 3: Run Modern Web Guidance Audit**

Run: `npx.cmd -y modern-web-guidance@latest legacy-scan platform --json`
Expected: 0 legacy findings.

- [ ] **Step 4: Run full regression test suite**

Run: `python -m unittest discover -s platform/tests -p "verify_*.py"`
Expected: All tests PASS.

- [ ] **Step 5: Commit & update cache buster**

Update cache buster in `templates/index.html` to `?v=20261120_v16_omni_search_and_pro_upgrade`.
```bash
git add platform/templates/index.html platform/tests/verify_omni_search_and_upgrade_browser_e2e.py
git commit -m "test(e2e): verify omni-search, criteria intake, and SaaS Pro Upgrade modal in browser"
```

---
