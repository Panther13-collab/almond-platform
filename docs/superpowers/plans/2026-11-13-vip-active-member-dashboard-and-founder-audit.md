# VIP Active Member Dashboard & Founder Platform Audit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform the VIP modal for active VIP members into a rich Member Status & Benefits Dashboard with tier upgrade options (3-month, 6-month) and a community contribute CTA, while performing an end-to-end Founder Skill Copywriting & Experience Audit across all platform sub-pages and modals.

**Architecture:** 
1. Backend: Enhance `core/auth_db.py` and `core/config.py` to support multi-tier VIP subscriptions (1-month = 30d, 3-month = 90d, 6-month = 180d) with duration-stacking on upgrades, returning candidate tier details via `/api/auth/me`.
2. Frontend Templates: Structure `#vipPassModal` with two distinct dynamic views (`#vipModalPurchaseView` for unpaid guests, `#vipModalActiveMemberView` for active VIP members). Provide benefits breakdown, multi-tier upgrade selectors, and a bottom contribute CTA.
3. Client JavaScript: Wire `openVipPassModal()` to detect `isUserPaid()`, render candidate's active validity, and power multi-tier Razorpay checkouts with multi-currency parity (INR, USD, EUR, GBP) without "approx/eq." wording.
4. Founder Copywriting: Audit and polish copy across side drawer, profile settings, search states, tracker exports, and contribute modals.

**Tech Stack:** Python 3.14, FastAPI, SQLite / Supabase PostgreSQL, Vanilla JS (ES6+), Tailwind CSS, Lucide Icons, Razorpay Standard Checkout.

**Spec:** User request #10:
- When a user with active VIP clicks "VIP Active ✓" (top navbar or profile), do NOT show the purchase view.
- Show active VIP member perks vs standard feed.
- Show upgrade options: 1-month users can upgrade to 3-month or 6-month; 6-month users see current top-tier benefits first then extension options.
- At the bottom of the active VIP modal, include a "Contribute / Buy Us a Coffee" CTA.
- Candidate profile shows VIP tier and contribute CTA.
- Founder Skill copywriting audit across all sub-pages, profile settings, and platform messaging.

## Global Constraints
- No "equivalent", "approx", or "eq." wording in currency displays.
- Keep pricing parity clean across ₹ INR, $ USD, € EUR, £ GBP.
- Duration stacking: Upgrading or extending VIP adds to existing remaining time rather than resetting from `now`.
- Preserve backward compatibility with existing tests and payment flows.

## Review Focus
- Unpaid candidates opening `#vipPassModal` MUST see the standard 1-Month purchase view.
- Paid candidates opening `#vipPassModal` MUST see the active member status, benefits, upgrade choices, and contribute CTA.
- Profile modal MUST display active VIP tier and provide direct shortcuts to manage VIP and contribute.
- Upgrading to 3-month or 6-month via Razorpay verification MUST properly credit 90 or 180 days and set the correct plan code (`vip_pass_90d` or `vip_pass_180d`).
- Founder voice across all sub-pages MUST feel direct, authoritative, anti-broker, and candidate-centric.

---

### Task 1: Backend Multi-Tier Support & Duration Stacking

**Files:**
- Modify: `platform/core/config.py`
- Modify: `platform/core/auth_db.py`
- Modify: `platform/core/payment.py`
- Modify: `platform/app.py`
- Test: `platform/tests/verify_vip_active_modal_and_upgrades.py`

**Interfaces:**
- Consumes: Razorpay order & signature verification parameters (`plan_name`, `amount_inr`, `user_id`).
- Produces: `record_successful_payment` with duration stacking (30d, 90d, 180d), enriched `/api/auth/me` with `plan_tier` and pricing parity map.

- [ ] **Step 1: Write test for multi-tier plan calculations and stacking in `tests/verify_vip_active_modal_and_upgrades.py`**
- [ ] **Step 2: Run test to verify it fails**
- [ ] **Step 3: Update `core/config.py` with multi-tier pricing constants**
- [ ] **Step 4: Update `core/auth_db.py` for 90d and 180d plan codes and duration stacking**
- [ ] **Step 5: Update `core/payment.py` and `app.py` `/api/auth/me` endpoint to return tier metadata**
- [ ] **Step 6: Run test to verify it passes**
- [ ] **Step 7: Commit Task 1 changes**

---

### Task 2: Dual-View `#vipPassModal` & Profile Updates in `templates/index.html`

**Files:**
- Modify: `platform/templates/index.html`
- Test: `platform/tests/verify_vip_active_modal_and_upgrades.py`

**Interfaces:**
- Consumes: DOM containers `#vipPassModal`, `#profileModal`.
- Produces: `#vipModalPurchaseView` (for unpaid candidates) and `#vipModalActiveMemberView` (for paid VIP members with active perks, upgrade tiers, and contribute footer).

- [ ] **Step 1: Write test checking the presence of active VIP view, perks list, upgrade cards, and contribute CTA in `index.html`**
- [ ] **Step 2: Run test to verify it fails**
- [ ] **Step 3: Implement `#vipModalPurchaseView` and `#vipModalActiveMemberView` inside `#vipPassModal` in `templates/index.html`**
- [ ] **Step 4: Update candidate profile modal in `templates/index.html` with active VIP management and bottom contribute CTA**
- [ ] **Step 5: Run test to verify it passes**
- [ ] **Step 6: Commit Task 2 changes**

---

### Task 3: Client JavaScript Dynamic Switching & Upgrade Checkouts in `static/app.js`

**Files:**
- Modify: `platform/static/app.js`
- Test: `platform/tests/verify_vip_active_modal_and_upgrades.py`

**Interfaces:**
- Consumes: `isUserPaid()`, `localStorage`, `triggerRazorpayCheckout`.
- Produces: `openVipPassModal()` dynamic view toggle, `selectVipUpgradeTier()`, `selectVipUpgradeCurrency()`, `executeVipUpgradeCheckout()`.

- [ ] **Step 1: Write test verifying JavaScript functions and dynamic switching logic**
- [ ] **Step 2: Run test to verify it fails**
- [ ] **Step 3: Implement dynamic view switching in `openVipPassModal` in `static/app.js`**
- [ ] **Step 4: Implement upgrade tier selection and checkout execution in `static/app.js`**
- [ ] **Step 5: Update candidate profile syncing to save and restore `almond_plan` and `almond_paid_until`**
- [ ] **Step 6: Run test to verify it passes**
- [ ] **Step 7: Commit Task 3 changes**

---

### Task 4: Comprehensive Founder Skill Copywriting & Experience Audit

**Files:**
- Modify: `platform/templates/index.html`
- Modify: `platform/static/app.js`
- Test: `platform/tests/verify_vip_active_modal_and_upgrades.py`

**Interfaces:**
- Evaluates: Side drawer, modals, hero labels, filter tags, search empty/error states, export headers.
- Produces: Unified founder voice with high conviction, anti-broker clarity, and candidate empowerment.

- [ ] **Step 1: Audit all sub-pages, side drawer manifesto, and modals against founder voice criteria**
- [ ] **Step 2: Refine copy for maximum authority, clarity, and attraction**
- [ ] **Step 3: Verify no placeholder text, awkward phrasing, or currency discrepancies remain**
- [ ] **Step 4: Run full regression test suite**
- [ ] **Step 5: Commit Task 4 changes**

---

### Task 5: End-to-End Verification, Push to Remote & Verification Report

**Files:**
- Verify: Full test suite (`tests/verify_*.py`)
- Deploy: Git push to `origin main` for automatic Render deployment

- [ ] **Step 1: Run all existing verification test suites**
- [ ] **Step 2: Commit all updates cleanly**
- [ ] **Step 3: Push to `origin main`**
- [ ] **Step 4: Confirm successful push and summarize deliverable for user**
