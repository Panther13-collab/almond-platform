# Founder Platform Restructure & De-duplication Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Streamline Page 3 (Workspace) and Page 4 (Results Stream) by eliminating duplicate content, removing the intrusive in-stream SEO essay, creating an adaptive single-card CV vector hub, and enhancing real-time telemetry while ensuring 100% zero-downtime platform availability.

**Architecture:**
- **Page 3 (Workspace):** Replace the dual-card empty placeholder layout with an adaptive CV vector hub (minimalist dropzone before upload; clean extracted vector after upload). Streamline compensation to a single currency+number+preset control (removing redundant slider) and compact location typeahead so the entire screen fits above-the-fold on 1366x768 screens without scrolling.
- **Page 4 (Results Stream):** Excise the 500-word `#aboutAlmondJobsSection` from the scrollable job cards flow and re-dock it into a crawlable, collapsible footer drawer (`<details>` accordion) that satisfies Googlebot/LLM crawlers while keeping the job stream 100% pure and uncluttered for human job seekers.
- **Global Polish:** Deduplicate category directory links into the single 4-column footer, refine copy to eliminate 8x buzzword repetition, and add a live corporate ATS hiring ticker to the top telemetry bar.

**Tech Stack:** FastAPI, Jinja2 / Vanilla HTML5 & Tailwind CSS, JavaScript (ES6+), Schema.org JSON-LD.

**Spec:** [`founder_skill_platform_restructure_audit.md`](file:///C:/Users/hp/.gemini/antigravity/brain/9aa8f19b-dcde-4560-9464-6fdb4b2814bd/founder_skill_platform_restructure_audit.md)

## Global Constraints

- Never break existing JavaScript event handlers or API contracts (`/api/search`, `/api/upload-cv`, `/health`, `/kanban/*`).
- Maintain 100% crawlability for Googlebot and LLMs (preserve all schema.org JSON-LD, entity disambiguation keywords, and canonical URLs).
- Strictly maintain single official email: `almondjobs.official@gmail.com`.
- Zero broken styles on mobile (390px), laptop (1366x768), and desktop (1920x1080).
- All unit tests (39+ existing) must pass before pushing.
- Deploy to Render and verify live production endpoints return HTTP 200 OK.

## Review Focus

1. *Resume upload before vs. after state:* When no resume is uploaded, the UI must not show broken or empty vector cards; once uploaded, it must smoothly transition to the parsed vector without page reload.
2. *Currency & Salary filter interaction:* Selecting currency tabs (INR, USD, EUR, GBP) or typing a number must update `currentCurrency` and `currentMinPackage` in `app.js` and trigger filtered search correctly.
3. *Googlebot crawlability:* The entity disambiguation text inside the collapsible drawer must be present in raw server-rendered HTML so search crawlers index it without executing JavaScript.
4. *Job stream scrollability:* In Page 4, the job card list must scroll smoothly without being blocked or disrupted by bottom footers or drawers.
5. *Mobile responsiveness:* At screen widths < 1024px, the adaptive cards and compact parameter controls must stack cleanly without horizontal overflow.

---

### Task 1: Streamline Page 3 Workspace (Adaptive CV Hub & Compact Parameters)

**Files:**
- Modify: `platform/templates/index.html` (Page 3 section: lines ~52955-83799)
- Modify: `platform/static/app.js` (Event bindings for resume upload toggle, salary presets, location typeahead)
- Test: `platform/tests/verify_workspace_streamlining.py`

- [ ] **Step 1: Write verification test for Page 3 streamlining**
  - Verify that `#workspace` contains the adaptive CV dropzone and vector container.
  - Verify that redundant `#packageRangeSlider` is removed, while `#packageNumberInput` and `.currency-tab` remain functional.
  - Verify that the misplaced "Who We Are" button is removed from the skills card.
  - Verify that the layout classes enforce compact height (`h-full lg:max-h-screen`).

- [ ] **Step 2: Run test to observe failure**
  - Execute `python tests/verify_workspace_streamlining.py`.
  - Confirm failure on current un-streamlined HTML.

- [ ] **Step 3: Update `platform/templates/index.html` for Page 3**
  - Replace the bulky dual-card left column with an adaptive single-container Smart CV Hub:
    - Default state: Clean drag-and-drop zone with format pills (`PDF, DOCX, TXT`) and browse button.
    - Parsed state: Auto-collapses the upload zone into a compact pill (`✓ Resume Parsed • candidate.pdf [Change]`) and reveals candidate name, experience badge, target role, and editable skill tags with `[x]` remove.
    - Remove the misplaced "Who We Are" button from the skills section.
  - Update right column:
    - Retain `#packageNumberInput` with currency tabs (`INR, USD, EUR, GBP, CAD, AUD, $/Mo`).
    - Replace the range slider with 4 sleek quick presets (`₹10L`, `₹20L`, `₹35L`, `₹50L+`).
    - Streamline location search into a compact input with quick pills (`Worldwide Remote`, `All India`, `Bengaluru`, `USA`, `Europe`).
    - Consolidate work arrangement and contract type into compact segmented rows.
    - Preserve primary action button `#searchJobsBtn`.

- [ ] **Step 4: Update `platform/static/app.js` for adaptive CV hub & salary presets**
  - In `handleResumeUploadSuccess()` / `renderParsedProfile()`, ensure the upload box seamlessly collapses and displays the active vector card.
  - Add click handlers for the 4 salary preset buttons updating `#packageNumberInput`.
  - Ensure re-upload button restores the upload dropzone if the user wants to upload a different resume.

- [ ] **Step 5: Run verification test**
  - Execute `python tests/verify_workspace_streamlining.py` and confirm PASS.

- [ ] **Step 6: Commit Task 1 changes**
  - Git commit: `feat(ui): streamline Page 3 workspace into adaptive CV hub and compact parameters deck`.

---

### Task 2: Purify Page 4 Results Stream (Docked SEO Disambiguation Drawer)

**Files:**
- Modify: `platform/templates/index.html` (Page 4 `#results-stream` & `#aboutAlmondJobsSection`)
- Modify: `platform/static/app.js`
- Test: `platform/tests/verify_page4_purification.py`

- [ ] **Step 1: Write verification test for Page 4 purification**
  - Verify that `#aboutAlmondJobsSection` is NOT inside `#resultsScrollContainer`.
  - Verify that `#resultsScrollContainer` contains only job feed tabs, controls, and empty/loading states.
  - Verify that the entity disambiguation text and keywords are preserved in a docked `<details>` or footer drawer.
  - Verify that duplicate category pill links are removed from the in-stream section.

- [ ] **Step 2: Run test to observe failure**
  - Execute `python tests/verify_page4_purification.py`.
  - Confirm failure on current HTML.

- [ ] **Step 3: Update `platform/templates/index.html` for Page 4**
  - Move `#aboutAlmondJobsSection` out of `#resultsScrollContainer`.
  - Convert it into a sleek, docked expandable drawer positioned just above `#bottomDirectoryFooter`:
    ```html
    <details id="enterpriseEntityDrawer" class="w-full max-w-6xl mx-auto my-3 px-4 sm:px-8 group">
      <summary class="cursor-pointer list-none flex items-center justify-between py-2 px-4 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold transition">
        <span class="flex items-center gap-2">
          <i data-lucide="info" class="w-3.5 h-3.5 text-violet-600"></i>
          <span>Enterprise Career Intelligence & Entity Disambiguation (Almond Jobs vs. Agriculture)</span>
        </span>
        <span class="text-[10px] text-slate-500 font-mono group-open:rotate-180 transition-transform">▼</span>
      </summary>
      <!-- Crawlable disambiguation content for Googlebot & LLMs -->
      ...
    </details>
    ```
  - Remove redundant category pills from the drawer since they are already in the footer directory.

- [ ] **Step 4: Run verification test**
  - Execute `python tests/verify_page4_purification.py` and confirm PASS.

- [ ] **Step 5: Commit Task 2 changes**
  - Git commit: `feat(ui): purify Page 4 job stream and dock crawlable SEO disambiguation drawer`.

---

### Task 3: Deduplication, Global Copy Polish & Real-Time Telemetry Ticker

**Files:**
- Modify: `platform/templates/index.html`
- Modify: `platform/static/app.js`
- Test: `platform/tests/verify_telemetry_and_dedup.py`

- [ ] **Step 1: Write verification test**
  - Verify presence of real-time telemetry ticker in the header.
  - Verify deduplication of directory links across slides.
  - Verify clean copy across hero, bento, and footer.

- [ ] **Step 2: Run test to observe failure**
  - Confirm failure.

- [ ] **Step 3: Update `templates/index.html` & `app.js` for real-time telemetry**
  - In the top header telemetry container, add an animated ticker element:
    ```html
    <div id="liveTelemetryTicker" class="hidden md:flex items-center gap-2 text-xs font-mono text-emerald-800 bg-emerald-50/90 border border-emerald-300/80 px-3.5 py-1.5 rounded-full shadow-xs">
      <span class="w-2 h-2 rounded-full bg-emerald-500 animate-ping"></span>
      <span id="livePostingsCount" class="font-black text-slate-950">3,315,258</span>
      <span class="text-emerald-800 font-bold">Live Feeds</span>
      <span class="text-slate-300">|</span>
      <span id="tickerFeedItem" class="text-emerald-900 font-semibold truncate max-w-[280px]">Stripe (Dublin) +4 roles</span>
    </div>
    ```
  - In `app.js`, add an automatic 4-second ticker rotation displaying real enterprise feeds (e.g. `Google (Bengaluru) +7 roles`, `Databricks (Remote) +3 roles`, `Uber (Amsterdam) +5 roles`, `OpenAI (SF) +2 roles`).

- [ ] **Step 4: Global Copy & Link Polish**
  - Refine buzzword density so "3.3M+ Feeds" and "0% Recruiter Spread" are positioned with authority without unnecessary repetitive clutter.
  - Ensure the bottom footer remains the single definitive directory for all 18 category hubs and legal policies.

- [ ] **Step 5: Run test & verify pass**
  - Execute `python tests/verify_telemetry_and_dedup.py`.

- [ ] **Step 6: Commit Task 3 changes**
  - Git commit: `feat(polish): add live ATS telemetry ticker and finalize global content deduplication`.

---

### Task 4: Full Regression Testing & Production Zero-Downtime Deployment Verification

**Files:**
- Test: Full unit test suite (`python -m unittest discover -s tests -p "test_*.py"`)
- Script: `platform/tests/verify_complete_taxonomy_and_email.py`
- Production check: `urllib.request` to `https://almondjobs.com/` and core hubs

- [ ] **Step 1: Run full platform test suite**
  - Run all 39+ unit tests in `platform/tests/`.
  - Confirm 100% PASS with 0 failures and 0 errors.

- [ ] **Step 2: Push to `origin main`**
  - Push all committed changes to `https://github.com/Panther13-collab/almond-platform.git`.
  - Triggers Render automatic zero-downtime deployment.

- [ ] **Step 3: Live production verification loop**
  - Query production endpoints:
    - `https://almondjobs.com/health` (HTTP 200)
    - `https://almondjobs.com/` (HTTP 200)
    - `https://almondjobs.com/almond-jobs` (HTTP 200)
    - `https://almondjobs.com/it-jobs` (HTTP 200)
    - `https://almondjobs.com/terms` (HTTP 200)
    - `https://almondjobs.com/contact` (HTTP 200)
  - Verify live response times, title tag, and page integrity.
