# Design Document: Unified Omni-Search & Pro Tier Upgrade Redesign

- **Date**: 2026-11-20
- **Author**: Antigravity Pair Programming
- **Status**: Ready for User Review & Approval
- **Target Repository**: `platform` (Almond Jobs)

---

## 1. Intent and Why

### The Problem
The current landing page has accumulated excessive text blocks, badges, notices, and slogans (`AlmondJobs Direct Corporate Feed...`, `NO BROKERS`, `NO MIDDLEMEN`, `NO DEAD POSTS`, Fresher & campus notices) that overwhelm first-time visitors. When candidates land on modern job search platforms, they expect a clean, direct search experience: a search bar where they can either search for jobs/skills directly or upload their resume immediately.

Furthermore, the existing "👑 VIP Pass" modal is perceived as visually cluttered and ad-hoc rather than a professional, trustworthy SaaS tier comparison (like ChatGPT Plus, Claude Pro, or Gemini Advanced).

### The Solution
1. **Minimalist Clean Homepage Fold**: Strip away the cluttered top badges, anti-broker banners, and fresher notices. Keep the clean brand headline (`Move first. Apply unseen.`) and the core anti-oversaturation thesis.
2. **Unified Omni-Search & Resume Bar**: Place a sleek, responsive input at the center of the first fold.
   - **Left**: Instant debounced live search as the user types every character (`'S'` -> Software Engineer, `'7 LPA'` -> matching CTC, skills, locations, companies) querying across all active feeds.
   - **Right**: Integrated action button: `📎 Upload your resume to find your dream job`.
3. **Streamlined Intake & Results Stream**: Uploading a resume immediately triggers the Criteria Intake Modal (Expected CTC, Preferred Location, Target Domain). Submitting instantly ranks and displays direct job cards directly beneath the search bar on the homepage.
4. **Professional SaaS "Upgrade" Matrix**: Replace `👑 VIP Pass` in the title bar with a clean `✨ Upgrade` button. Clicking opens a modern 2-column comparison matrix (**Free Tier** vs. **Pro Tier**) with feature checklists, duration toggles (1-Month, 3-Month with 30% OFF, 6-Month with 35% OFF), location-aware multi-currency pricing (INR, USD, EUR, GBP), and live Razorpay checkout.

---

## 2. Goals, Non-Goals, and Anti-Goals

### Goals
- Ultra-clean, minimalist first fold that loads instantaneously.
- Instant, letter-by-letter live filtering across all stored job feeds (Direct Internships, Entry-Level, AI/ML Specialist, and direct crawled portals) rendered directly beneath the search bar.
- Direct resume upload integrated into the search bar with instant criteria capture and inline matched results.
- Replace the VIP Pass popup with an authoritative SaaS tier comparison modal (Free vs. Pro) matching ChatGPT/Claude standards.
- Zero modern web guidance legacy findings (`0 findings`).
- Maintain 100% backward compatibility with existing Razorpay order creation, payment verification, session management, and auth tokens.

### Non-Goals
- Changing the backend crawler infrastructure or replacing SQLite/Supabase databases.
- Modifying backend pricing logic (pricing remains ₹699 / ₹1,799 / ₹2,799 and foreign parity $19.99 / $49.99 / $79.99).
- Modifying candidate profile modal or account settings.

### Anti-Goals
- Never break mobile responsiveness: The search bar and upload chip must stack gracefully on small phone viewports without horizontal overflow or text clipping.
- Never display coffee contribution solicitations inside the Pro Upgrade modal.

---

## 3. Approaches Considered & Trade-offs

### Approach 1: Unified Omni-Search & Resume Bar (Selected)
- **Concept**: A single cohesive input container combining instant keyword/letter search on the left and an embedded `Upload your resume to find your dream job` button on the right.
- **Pros**: Matches top-tier search experiences (Perplexity, ChatGPT); candidates can act immediately without scrolling; zero cognitive clutter.
- **Cons**: Requires precise CSS handling to wrap or stack on screens below 640px.
- **Selection Reason**: Chosen by user for maximum simplicity, elegance, and immediate utility.

### Approach 2: Split Action Blocks
- **Concept**: Separate full-width search input with a distinct drag-and-drop box stacked beneath it.
- **Pros**: Simpler mobile wrapping.
- **Cons**: Adds extra vertical height, separates the two primary entry actions, and feels like traditional job boards rather than a modern search engine.

---

## 4. Architectural Decisions & Builder Review Resolutions

Following our engineering review, the following implementation choices have been settled:

1. **Page Architecture & Coexistence**:
   - The `#omniSearchResultsContainer` renders inline directly beneath the hero search bar.
   - The full Kanban Application Tracker, Deep CV Matcher, and Dossier Export tools remain fully accessible via the top navigation drawer and side panel, ensuring zero loss of advanced candidate tools.

2. **Data Sourcing & Performance (Fast Omni-Search API)**:
   - Rather than embedding 6MB of static JSON into the HTML page, a high-speed `/api/omni-search?q=...&limit=25` endpoint is introduced (or queries the already cached in-memory jobs table).
   - Keystrokes are debounced at 120ms. When query is empty, the container displays a compact row of "🔥 Live Corporate Openings (Crawled Today)" with smooth infinite scroll or "Load More".

3. **Resume Parsing Pipeline**:
   - Leverages our existing, battle-tested Python backend endpoints (`POST /api/upload-resume` to extract text and pre-fill criteria, and `POST /api/find-jobs` to compute vector similarity and return ranked matches).
   - This avoids bundling heavy, fragile PDF libraries in client JS and guarantees accurate parsing on both mobile and desktop.

4. **Entitlement & Gating in Search Results**:
   - Free users can freely search, view company names, roles, packages, and direct corporate links (Greenhouse, Lever, Ashby, Workday).
   - VIP/Pro priority indicators (such as first-wave direct ingestion badges) indicate Pro advantages, encouraging upgrade without creating annoying roadblocks on free searches.

5. **Upgrade Modal for Existing Pro Subscribers**:
   - When an active Pro subscriber clicks `✨ Upgrade`, the Pro column displays their active status (`Active Pro Member — Valid until [Date]`), and the duration pills allow them to extend coverage by +30, +90, or +180 days with automatic duration stacking onto their expiration date.

6. **Display Capping & Mobile Ergonomics**:
   - Live search results are capped at 20 cards per view with a "Load more results" button.
   - On desktop, the search bar is a single horizontal flexbox (`[ 🔍 Search input ... ] [ 📎 Upload resume ]`).
   - On screens < 640px, the input and upload chip stack gracefully with comfortable touch targets.

---

## 5. Component Breakdown

### A. Title Bar Header
- **Target**: Replace `#topVipPassBtn` text from `👑 VIP Pass` to `✨ Upgrade`.
- **Target**: Retain `Who We Are?` and `Candidate Profile` icon buttons.

### B. Hero Fold Redesign (`#hero`)
- Remove top badge clusters (`AlmondJobs Direct Corporate Feed...`, `NO BROKERS`, `NO MIDDLEMEN`, `NO DEAD POSTS`, campus notice banner).
- Keep centered headline:
  - `Move first. Apply unseen!`
  - Subtitle: `The job market isn't oversaturated — you're just applying after the door has already closed. We ingest jobs straight from company internal servers the second they open.`
- Insert **Omni-Search Bar**:
  - Container with rounded-3xl styling, backdrop blur, border, subtle focus ring.
  - Text input for typing roles, skills, or packages.
  - Right-aligned button: `Upload your resume to find your dream job`.
- Insert **Results Stream** (`#omniSearchResultsContainer`):
  - Card grid: Title, Company, Location, Salary/Package, Source tag, Direct link.

### C. Criteria Modal (`#criteriaModal`)
- Modal displays on resume selection.
- Collects:
  - Target Role / Domain
  - Expected Package (CTC in LPA or $ USD)
  - Preferred Location (Remote, Bangalore, Mumbai, etc.)
- "Find Matching Jobs" button triggers ranking and renders cards into the results stream.

### D. SaaS "Upgrade" Modal (`#vipPassModal`)
- 2-Column Side-by-Side Matrix:
  - **Left Column**: Free Tier
    - Badge: Free Forever (₹0)
    - Features: Standard directory links, basic keyword search, public postings.
    - Button: Current Plan (disabled).
  - **Right Column**: Pro Tier (Highlighted)
    - Badge: 👑 Pro Corporate Access
    - Duration pills: 1 Month (₹699 / $19.99), 3 Months (₹1,799 / $49.99 — 30% OFF), 6 Months (₹2,799 / $79.99 — 35% OFF).
    - Features: 0% Recruiter Spread, First-Wave Direct Ingestion, Unredacted Titles & Contacts, 1-Click Dossiers & Application Tracker, Continuous Search Coverage.
    - Button: `🚀 Upgrade to Pro — [Price]` -> Launches Razorpay checkout.

---

## 6. Verification & Test Plan
- Run `node -c platform/static/app.js` to ensure 0 syntax errors.
- Run `npx modern-web-guidance legacy-scan` to ensure 0 legacy findings.
- Playwright Headless Chromium automated tests:
  - Test live typing in omni-search input and verify instant card updates.
  - Test clicking the "Upload resume" button and submitting criteria.
  - Test clicking the "Upgrade" button in navbar, verifying 2-column layout, switching 1m/3m/6m durations, and verifying price calculations.
- Run full regression test suites (`verify_*.py`).
