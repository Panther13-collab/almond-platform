# Swiss Minimalist Luxury Platform Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redesign Almond Jobs with the approved **Direction B: Swiss Minimalist Luxury** aesthetic (warm almond cream `#faf8f5`, onyx typography, champagne borders, emerald live indicators), replace the rigid slide-snapping with a fluid modern web app flow, implement high-density atomic job cards, and verify everything locally on localhost (ZERO git push until user confirmation).

**Architecture:**
- **Design System (Direction B):** Unified palette across the entire application canvas (`#faf8f5` background, `#ffffff` card surfaces, `#e8dfd1` subtle warm borders, `#0f172a` primary headings, `#059669` emerald verified accents, `#dfb76c` royal gold highlights). Complete removal of the disjointed SVG jagged crack and split forest-green background.
- **Unified App Layout:** Single fluid scroll experience with smooth section anchors (`#hero`, `#search-deck`, `#feed-stream`, `#kanban-view`). Hero header with real-time enterprise ticker &rarr; Quick Power Search Deck with adaptive CV Dropzone &rarr; Live High-Density Atomic Job Stream with 3-tab switcher (`Direct ATS Feeds 3.3M+`, `YC & Founder Direct`, `Application Kanban`) &rarr; Docked SEO Disambiguation Drawer &rarr; 4-Column Directory Footer.
- **Atomic Job Cards:** Compact 3-line card structure maximizing information density on laptop/mobile screens without vertical bloat (Logo + Title + ATS Badge + Live Ping &bull; Comp + Location + Match Score &bull; Apply Direct ↗ + STAR Pitch ✨ + Save ⭐).
- **Execution & Verification:** Test locally with all unit tests and a live local Uvicorn server (`http://127.0.0.1:8000/`). Zero remote git push.

**Tech Stack:** FastAPI, Jinja2 / HTML5, Tailwind CSS, Vanilla JavaScript (ES6+), Playwright / Python unittest.

**Spec:** User directive for **Direction B (Swiss Minimalist Luxury)**, unified app flow, high-density cards, and localhost verification without git push.

## Global Constraints

- **STRICTLY NO GIT PUSH:** Only commit locally if needed, but DO NOT run `git push`. All verification must happen on localhost (`http://127.0.0.1:8000/`).
- **Preserve All API Contracts & Logic:** `/api/search`, `/api/upload-cv`, `/health`, `/kanban/*`, resume parsing, STAR pitch generation, and Razorpay checkout modal must remain 100% functional.
- **Maintain SEO & Legal Integrity:** Preserve all JSON-LD schemas, meta keywords, canonical tags, entity disambiguation drawer (`almondjobs vs agriculture`), and single email `almondjobs.official@gmail.com`.
- **Zero Layout Breakages:** Fully responsive on mobile (390px), laptop (1366x768), and desktop (1920x1080).
- **100% Test Pass:** All 49+ tests in `platform/tests/` must pass locally.

## Review Focus

1. *Natural scroll vs. slide transitions:* Ensure navigation links (`Home`, `Search`, `Live Postings`, etc.) smoothly scroll to target sections without jumping, locking, or horizontal displacement.
2. *Adaptive CV vector extraction:* Dragging or uploading a CV must smoothly collapse the upload dropzone and reveal the candidate's verified vector and skills cloud.
3. *Atomic Job Cards rendering:* Cards must render compactly in 3 lines with verified company ATS badge (Ashby, Greenhouse, Lever, Workday) and unrestricted direct link.
4. *Visual tonal unity:* Background must remain consistent (`#faf8f5`) across all sections with clean champagne borders (`#e8dfd1`) and zero contrasting dark green splits.
5. *Localhost availability:* Local server must boot cleanly on `127.0.0.1:8000` and respond to requests in <50ms.

---

### Task 1: Design System & Template Unification (Direction B Swiss Luxury)

**Files:**
- Modify: `platform/templates/index.html`
- Test: `platform/tests/verify_swiss_luxury_design.py`

- [x] **Step 1: Write verification test for Swiss Minimalist Luxury design system**
  - Verify unified background `#faf8f5` / warm cream across canvas.
  - Verify removal of SVG jagged golden crack and dark split background.
  - Verify fluid container structure (`#search-deck`, `#feed-stream`, `#enterpriseEntityDrawer`, `#bottomDirectoryFooter`).
  - Verify presence of the real-time live telemetry ticker in the header.

- [x] **Step 2: Run test to observe failure**
  - Run `python tests/verify_swiss_luxury_design.py` and confirm failure on un-restructured HTML.

- [x] **Step 3: Restructure `platform/templates/index.html`**
  - Set body background to `#faf8f5` with text `#0f172a`.
  - Replace the 4 fragmented full-screen slide containers with a unified modern app flow:
    - **Header**: Luxury minimalist navbar with logo, real-time ticker (`#liveTelemetryTicker`), Contribute button, and navigation pills.
    - **Hero & Value Banner**: High-impact editorial hero with punchy authority copy, proof pills (`3.3M+ Live Feeds`, `0% Recruiter Spread`, `100% Unrestricted Links`), and 1-click scroll to search.
    - **Unified Search & CV Intelligence Deck (`#search-deck`)**:
      - Left: Adaptive Smart CV Dropzone (starts as clean minimalist upload box with `PDF, DOCX, TXT`, collapses into parsed vector with skill badges on upload).
      - Right: Compact Target Parameters (unified salary number input with currency switcher + 5 quick presets: `No Min`, `10 LPA`, `20 LPA`, `35 LPA`, `50+ LPA` / USD equivalents; location typeahead with quick pills; compact segmented work mode).
      - Full-width high-contrast action button: `Search 3.3M+ Direct Portals →`.
    - **Live Matched Opportunities Stream (`#feed-stream`)**:
      - Results toolbar with count badge, export actions (PDF, DOCX, CSV), and 3-tab switcher (`Direct Live Feeds`, `YC & Founder Direct`, `Application Kanban`).
      - Results scroll container for high-density atomic job cards.
      - Secondary auxiliary LinkedIn toggle.
    - **Docked Entity Disambiguation Drawer (`#enterpriseEntityDrawer`)**:
      - Sleek `<details>` drawer above footer for Googlebot & LLM crawlability.
    - **4-Column Directory Footer (`#bottomDirectoryFooter`)**:
      - All 18 category hubs, official email `almondjobs.official@gmail.com`, and legal compliance links.

- [x] **Step 4: Run test and confirm pass**
  - Run `python tests/verify_swiss_luxury_design.py` and verify PASS.

---

### Task 2: High-Density Atomic Cards & Fluid Navigation in `static/app.js`

**Files:**
- Modify: `platform/static/app.js`
- Test: `platform/tests/verify_atomic_cards_and_navigation.py`

- [x] **Step 1: Write verification test for atomic cards & navigation**
  - Verify `renderJobCards` produces atomic 3-line cards with luxury styling.
  - Verify `goToSlide` safely handles smooth scrolling to sections (`#hero`, `#search-deck`, `#feed-stream`, `#kanbanBoardContainer`).
  - Verify `setSalaryPreset`, location pills, and resume upload integration.

- [x] **Step 2: Run test to observe failure**
  - Run `python tests/verify_atomic_cards_and_navigation.py`.

- [x] **Step 3: Update `static/app.js`**
  - Update `renderJobCards()` to generate the new **High-Density Atomic Card**:
    - Line 1: Company Logo / Initials + Title (bold text-slate-900) + Verified ATS Pill (`Ashby`, `Greenhouse`, `Lever`, `Workday`) + Live Ping Dot + Date.
    - Line 2: Compensation Badge (`₹25-40 LPA` or `$140k`) + Location (`Bengaluru • Hybrid`) + Match Score Pill (`94% Match`).
    - Line 3: Action Buttons (`Apply Direct (0% Recruiter Spread) ↗`, `Tailored Cover Letter / Pitch ✨`, `Inspect Match 🔍`, `Save / Track ⭐`).
  - Upgrade `goToSlide(idx)` to seamlessly scroll to target element ID:
    - 0 &rarr; `#hero`
    - 1 &rarr; `#search-deck`
    - 2 &rarr; `#search-deck`
    - 3 &rarr; `#feed-stream`
  - Ensure adaptive CV upload collapse & expand logic functions seamlessly.

- [x] **Step 4: Run test and confirm pass**
  - Run `python tests/verify_atomic_cards_and_navigation.py`.

---

### Task 3: Regression Suite & Localhost Live Verification

**Files:**
- Verify: Full test suite (all 49+ tests)
- Launch: Local Uvicorn server on `http://127.0.0.1:8000/`
- Test: Playwright / HTTP checks against local server
- Local Screenshots: Capture mobile (390x844) and laptop (1366x768) screenshots into artifact directory

- [x] **Step 1: Run full regression test suite**
  - Execute `python -m unittest discover -s tests -p "verify_*.py"`.
  - Confirm 100% PASS on all tests (54/54 tests passed).

- [x] **Step 2: Start local Uvicorn development server**
  - Start server locally on port 8000 using `python -m uvicorn app:app --host 127.0.0.1 --port 8000`.

- [x] **Step 3: Verify local endpoints and capture screenshots**
  - Probe `http://127.0.0.1:8000/` and `http://127.0.0.1:8000/health`.
  - Run headless browser capture of laptop view (`1366x768`) and mobile view (`390x844`).
  - Verify that the warm cream background, atomic cards, and fluid scrolling render flawlessly.

- [ ] **Step 4: Present results to user for confirmation before any git push**
  - Provide local URLs, test results, and screenshots for user review.
