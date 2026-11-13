# VIP Multi-Tier Dynamic Pricing, Exit-Intent Retention & Admin Dashboard Overhaul Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a Google/ChatGPT/Anthropic standard 3-tier VIP subscription experience (1m, 3m with 30% off, 6m with 35% off on base 4299 without "MRP" text), wire checkout dismissal to multi-currency exit-intent retention modals ("movie ticket" / "dinner"), provide dynamic pricing persistence in SQLite managed directly from `/admin` without affecting active VIPs, and overhaul the admin interface into a premier 5-tab executive dashboard.

**Architecture:** 
- A persistent SQLite table `pricing_config` in `core/auth_db.py` stores base and offer prices across INR, USD, EUR, and GBP with discount labels and badges.
- Public endpoint `GET /api/pricing` serves active prices; admin endpoint `POST /api/admin/pricing` allows instant live updates during festivals without server restart or altering existing member validity.
- The candidate frontend (`templates/index.html` and `static/app.js`) presents a unified 3-tier selector for unpaid/guest visitors, while active members see their unlocked perks and progressive upgrades (1m members see 3m/6m; 3m members see 6m).
- Razorpay checkout dismissal (`modal.ondismiss`) is wired directly to `#paymentExitIntentModal`, tailored to 1-month ("movie ticket") and 3m/6m ("dinner") across all currencies.
- `templates/admin.html` is upgraded to an Anthropic/Google-style tabbed command suite with dedicated Pricing Manager, Candidate Directory with filters, VIP Grants, and Security Shield.

**Tech Stack:** FastAPI, SQLite3, Jinja2, TailwindCSS, Vanilla ES6+, Razorpay Checkout JS SDK, Pytest / Unittest.

**Spec:** User request #10 and follow-up confirmation:
- Show 1m, 3m, 6m upfront for guests/unpaid.
- Active 1m shows 3m and 6m upgrade; active 3m shows 6m upgrade; active 6m shows dominance status & extend.
- 1m: no discount (default ₹699 / $9.99); 3m: 30% off (base ₹2,599 -> ₹1,799 / $24.99); 6m: 35% off on highest base ₹4,299 -> ₹2,799 / $38.99.
- No "MRP" text; strike through base prices like ChatGPT / Claude / Gemini subscription pages.
- Admin dashboard allows individual input fields for INR, USD, EUR, GBP offer and base prices.
- Changing prices in admin dashboard reflects instantly across platform and does NOT alter existing VIP expirations.
- Exit-intent modal triggers on payment checkout dismissal across all currencies ("movie ticket" for 1m, "dinner" for 3m/6m).
- Overhaul `/admin` into an intuitive executive dashboard.

## Global Constraints

- Never use the term "MRP" in the UI; use standard struck-through original pricing (`~~₹2,599~~`).
- Never modify or truncate existing VIP candidates' `paid_until` timestamps when updating pricing.
- Admin pricing mutations must require valid admin authentication (`X-Admin-Key` header or authenticated session).
- Maintain 100% backward compatibility for all existing routes and tests.
- Razorpay order creation on backend must accept dynamic prices saved in the database.

## Review Focus

1. Unauthenticated or unpaid candidate opens `#vipPassModal`: must see 1-month, 3-month (30% off), and 6-month (35% off) with strike-through base prices and zero mention of "MRP".
2. Active 1-Month VIP candidate opens `#vipPassModal`: must see active status and only higher tiers (3-month sprint, 6-month dominance) as upgrades.
3. Candidate opens Razorpay checkout and closes/cancels it: `modal.ondismiss` must fire and open `#paymentExitIntentModal` with currency-appropriate symbol and copy ("movie ticket" for 1m, "dinner" for 3m/6m).
4. Admin modifies festival prices in `/admin`: `POST /api/admin/pricing` updates SQLite, `GET /api/pricing` returns updated numbers immediately, and existing VIP members' `paid_until` dates remain completely untouched.
5. Currency switcher (INR, USD, EUR, GBP): dynamically re-renders all 3 cards in the purchase modal with accurate symbols and prices.

---

### Task 1: Dynamic Pricing Schema & Backend API (`core/auth_db.py`, `app.py`)

**Files:**
- Modify: `platform/core/auth_db.py`
- Modify: `platform/app.py`
- Test: `platform/tests/verify_dynamic_pricing_api.py`

**Interfaces:**
- Consumes: `get_db()` from `core/auth_db.py`, `Config` from `core/config.py`.
- Produces: 
  - `get_dynamic_pricing() -> dict`
  - `update_tier_pricing(tier_id: str, data: dict) -> dict`
  - Endpoint `GET /api/pricing`
  - Endpoint `POST /api/admin/pricing`

- [ ] **Step 1: Write the failing test for dynamic pricing**
  Create `platform/tests/verify_dynamic_pricing_api.py` asserting:
  - `GET /api/pricing` returns 3 tiers (`1m`, `3m`, `6m`) with default offer and strike prices.
  - Text contains no "MRP".
  - `POST /api/admin/pricing` with valid key updates prices.
  - Existing user's `paid_until` remains unchanged after pricing update.

- [ ] **Step 2: Run test to verify it fails**
  Run: `python -m unittest tests/verify_dynamic_pricing_api.py`
  Expected: FAIL (missing table / endpoint)

- [ ] **Step 3: Implement `pricing_config` table and helpers in `core/auth_db.py`**
  - In `init_db()`, create table `pricing_config`:
    `(tier_id TEXT PRIMARY KEY, plan_code TEXT, name TEXT, duration_days INTEGER, inr_price INTEGER, inr_original INTEGER, usd_price REAL, usd_original REAL, eur_price REAL, eur_original REAL, gbp_price REAL, gbp_original REAL, discount_pct INTEGER, discount_label TEXT, badge_text TEXT, is_active INTEGER DEFAULT 1, updated_at REAL)`.
  - Seed default values:
    - `1m`: ₹699 / $9.99 / €9.99 / £9.99 (0% discount, original same as price)
    - `3m`: ₹1,799 / $24.99 / €24.99 / £24.99 (30% off, original ₹2,599 / $34.99 / €34.99 / £34.99)
    - `6m`: ₹2,799 / $38.99 / €38.99 / £38.99 (35% off on base ₹4,299 / $59.99 / €59.99 / £59.99)
  - Implement `get_dynamic_pricing()` and `update_tier_pricing(tier_id, data)`.

- [ ] **Step 4: Implement endpoints in `app.py`**
  - Add `GET /api/pricing`: returns dynamic pricing dictionary.
  - Add `POST /api/admin/pricing`: validates admin key, updates `pricing_config`, returns updated pricing.
  - In `create_razorpay_order`, validate amount against dynamic prices when available.

- [ ] **Step 5: Run test to verify it passes**
  Run: `python -m unittest tests/verify_dynamic_pricing_api.py`
  Expected: PASS

- [ ] **Step 6: Commit**
  `git add core/auth_db.py app.py tests/verify_dynamic_pricing_api.py && git commit -m "feat(pricing): add dynamic pricing database schema and admin API"`

---

### Task 2: Candidate Multi-Tier VIP Pass Modal (`templates/index.html`, `static/app.js`)

**Files:**
- Modify: `platform/templates/index.html`
- Modify: `platform/static/app.js`
- Test: `platform/tests/verify_vip_3tier_modal.py`

**Interfaces:**
- Consumes: `/api/pricing` and `get_dynamic_pricing()`.
- Produces: 3-tier selectable purchase view (`#vipModalPurchaseView`) for guests/unpaid, with upgrade view for active members.

- [ ] **Step 1: Write test verifying 3-tier UI structure**
  Create `platform/tests/verify_vip_3tier_modal.py` asserting:
  - `#vipModalPurchaseView` contains cards or selector for `1m`, `3m`, and `6m`.
  - Contains strikethrough styling (`line-through`) for 3m and 6m base prices.
  - Zero occurrences of "MRP" in the modal.
  - 3m has "30% OFF", 6m has "35% OFF".

- [ ] **Step 2: Run test to verify it fails**
  Run: `python -m unittest tests/verify_vip_3tier_modal.py`
  Expected: FAIL

- [ ] **Step 3: Update `templates/index.html`**
  - In `#vipModalPurchaseView`, replace single-tier card with a modern 3-tier selector grid:
    - 1-Month VIP Pass (₹699 / $9.99) - Standard
    - 3-Month Career Sprint (~~₹2,599~~ ₹1,799, 30% OFF) - Popular
    - 6-Month Career Dominance (~~₹4,299~~ ₹2,799, 35% OFF) - Best Value
  - Currency switcher (INR, USD, EUR, GBP) updates numbers across all 3 cards.
  - Checkout CTA reflects selected tier: e.g. "Unlock 3-Month Career Sprint — ₹1,799".

- [ ] **Step 4: Update `static/app.js`**
  - Implement `window.selectVipTier(tierId)` to switch active card, update CTA button, and set target order tier.
  - Fetch `/api/pricing` on boot or modal open to ensure live festival pricing is used.
  - Maintain upgrade tier filtering for active members:
    - If user on 1m: show 3m & 6m upgrades.
    - If user on 3m: show 6m upgrade.
    - If user on 6m: show dominance status and extension.

- [ ] **Step 5: Run test to verify it passes**
  Run: `python -m unittest tests/verify_vip_3tier_modal.py`
  Expected: PASS

- [ ] **Step 6: Commit**
  `git add templates/index.html static/app.js tests/verify_vip_3tier_modal.py && git commit -m "feat(vip): 3-tier subscription cards with strikethrough pricing and no MRP text"`

---

### Task 3: Checkout Dismissal Retention Modal Wiring (`static/app.js`, `templates/index.html`)

**Files:**
- Modify: `platform/static/app.js`
- Modify: `platform/templates/index.html`
- Test: `platform/tests/verify_exit_intent_dismissal.py`

**Interfaces:**
- Consumes: Razorpay `modal.ondismiss` callback.
- Produces: `window.openPaymentExitIntent(planName, amount, currencySymbol)` triggered automatically when candidate closes Razorpay checkout.

- [ ] **Step 1: Write test for exit intent dismissal**
  Create `platform/tests/verify_exit_intent_dismissal.py` verifying:
  - `triggerRazorpayCheckout` options include `modal.ondismiss` calling `openPaymentExitIntent`.
  - Exit-intent supports all 4 currencies (`₹`, `$`, `€`, `£`).
  - 1-month displays "movie ticket" copy.
  - 3-month and 6-month display "dinner" copy.

- [ ] **Step 2: Run test to verify it fails**
  Run: `python -m unittest tests/verify_exit_intent_dismissal.py`
  Expected: FAIL

- [ ] **Step 3: Update `triggerRazorpayCheckout` in `static/app.js`**
  - In `options.modal.ondismiss`, call `window.openPaymentExitIntent(planName, finalAmount, currencySymbol)`.
  - Save full checkout context in `window._lastExitIntentData` so "Continue My Career Upgrade" reopens the exact same tier and currency.

- [ ] **Step 4: Update `window.openPaymentExitIntent` in `static/app.js`**
  - Format currency symbols properly: `INR` -> `₹`, `USD` -> `$`, `EUR` -> `€`, `GBP` -> `£`.
  - Plan comparison logic:
    - 1-Month: Title "A Career Upgrade Costs Less Than a Movie Ticket", message "Your career upgrade deserves at least the price of a movie ticket. For just {symbol}{amount}, you unlock 30 full days of direct corporate applications..."
    - 3-Month / 6-Month: Title "Transform Your Career for the Price of Dinner", message "Your career transformation deserves at least the price of a weekend dinner. For just {symbol}{amount}, unlock continuous direct ATS access..."

- [ ] **Step 5: Run test to verify it passes**
  Run: `python -m unittest tests/verify_exit_intent_dismissal.py`
  Expected: PASS

- [ ] **Step 6: Commit**
  `git add static/app.js templates/index.html tests/verify_exit_intent_dismissal.py && git commit -m "feat(checkout): wire Razorpay ondismiss to multi-currency exit-intent retention modal"`

---

### Task 4: Executive Admin Dashboard Overhaul (`templates/admin.html`)

**Files:**
- Modify: `platform/templates/admin.html`
- Modify: `platform/app.py`
- Test: `platform/tests/verify_admin_dashboard_v2.py`

**Interfaces:**
- Consumes: Admin session authentication, `/api/pricing`, `/api/admin/pricing`, `/api/admin/metrics`.
- Produces: 5-tab executive dashboard (Overview, Pricing & Offers, Candidate Directory, VIP Grants, Security Shield).

- [ ] **Step 1: Write test for Admin Dashboard tabbed layout and pricing inputs**
  Create `platform/tests/verify_admin_dashboard_v2.py` asserting:
  - Contains navigation tabs: `tab-overview`, `tab-pricing`, `tab-candidates`, `tab-grants`, `tab-security`.
  - Pricing tab contains individual editable inputs for INR, USD, EUR, GBP (base and offer prices) for 1m, 3m, 6m.
  - Contains no "MRP" label.
  - Candidate filter pills exist: All, Genuine, VIP, New, Dummy.

- [ ] **Step 2: Run test to verify it fails**
  Run: `python -m unittest tests/verify_admin_dashboard_v2.py`
  Expected: FAIL

- [ ] **Step 3: Redesign `templates/admin.html`**
  - Add top executive navigation pill bar (Google / Anthropic Console aesthetic):
    - 📊 Overview
    - 🏷️ Pricing & Offers Manager
    - 👥 Candidates & Filters
    - 👑 VIP Grants
    - 🛡️ Security Shield
  - Build Tab 2 (Pricing Manager):
    - Clean card layout for 1-Month, 3-Month, and 6-Month.
    - Editable fields: Offer Price & Original Price for INR, USD, EUR, GBP, plus discount badge text.
    - Instant AJAX "Save Pricing Changes" button submitting to `/api/admin/pricing` with toast notifications.
  - Build Tab 3 (Candidates):
    - Filter pills (All, Genuine, VIP Active, New Signups, Test/Dummy).
    - Search bar and CSV download button.
  - Build Tab 4 (VIP Grants):
    - Quick grant/revoke form with duration selector (30d, 90d, 180d) and live audit list.
  - Build Tab 5 (Security Shield):
    - Bot shield metrics, blocked scanners table, hardware breakdown.

- [ ] **Step 4: Run test to verify it passes**
  Run: `python -m unittest tests/verify_admin_dashboard_v2.py`
  Expected: PASS

- [ ] **Step 5: Commit**
  `git add templates/admin.html app.py tests/verify_admin_dashboard_v2.py && git commit -m "feat(admin): overhaul admin dashboard to 5-tab executive console with live pricing manager"`

---

### Task 5: Full Regression Testing & Production Deployment Preparation

**Files:**
- Run all test suites in `platform/tests/`

- [ ] **Step 1: Run all test suites**
  Run: `python -m unittest discover -s tests -p "verify_*.py"`
  Ensure 100% pass across all test files.

- [ ] **Step 2: Verify git status and clean working tree**
  Run: `git status`

- [ ] **Step 3: Commit and push to main**
  Push to `origin main` to trigger automatic Render deployment.
