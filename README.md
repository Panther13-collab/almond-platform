# Almond AI — Direct ATS Intelligence & Career Platform

Almond AI is a production-grade enterprise intelligence platform designed to eliminate recruiter markups, middlemen spreads, and ghost postings. It matches candidates directly with verified ATS endpoints (SmartRecruiters, Lever, Greenhouse, Ashby, Workday) and generates STAR-grounded application dossiers.

## Features
- **Direct ATS Verification:** 100% direct application links with zero recruiter spread or middleman commission.
- **Proof-of-Human Presence Barrier:** Interactive hold-to-verify protection (mouse, touch, spacebar) that completely halts automated bot crawling and scraping.
- **Multi-Currency Band Engine:** Dynamic salary band filtering across INR (LPA), USD, EUR, GBP, CAD, AUD, and AED with automatic currency normalization.
- **Dynamic Postings Telemetry:** Real-time crawler telemetry simulation reflecting active index updates and pruning.
- **Candidate Dossier Export:** Instant compilation into formatted PDF, Word (.docx), and CSV trackers.
- **Cloudflare-Hardened Security:** Sliding-window IP rate limiting, automated scanner blocking (`sqlmap`, `nikto`), search concurrency semaphores, and strict OWASP security headers.
- **Integrated Payments & Auth:** Supabase Auth + PostgreSQL metadata persistence and Razorpay checkout flow (UPI, Cards, NetBanking).

## Tech Stack
- **Backend:** FastAPI, Uvicorn, Python 3.10+
- **Database & Auth:** Supabase (PostgreSQL + GoTrue Auth)
- **Payment Processing:** Razorpay
- **Document Synthesis:** Playwright (Chromium), Python-Docx, PyPDF
- **Frontend:** HTML5, Modern CSS, Tailwind CSS, Vanilla JS, Lucide Icons

## Quick Start (Local Development)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Panther13-collab/almond-platform.git
   cd almond-platform
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables:**
   ```bash
   cp .env.example .env
   # Add your live SUPABASE_URL, SUPABASE_ANON_KEY, and RAZORPAY_KEY_ID in .env
   ```

4. **Launch the application:**
   ```bash
   uvicorn app:app --host 127.0.0.1 --port 8000 --reload
   ```
   Open your browser at `http://127.0.0.1:8000`.

## Cloud Deployment (Render.com)

1. Link this repository to **Render.com** as a **Web Service**.
2. Set Build Command: `pip install -r requirements.txt`
3. Set Start Command: `uvicorn app:app --host 0.0.0.0 --port $PORT`
4. In Render's **Environment Variables** dashboard, add:
   - `SUPABASE_URL`
   - `SUPABASE_ANON_KEY`
   - `SUPABASE_SERVICE_ROLE_KEY`
   - `RAZORPAY_KEY_ID`
   - `RAZORPAY_KEY_SECRET`
   - `ENVIRONMENT=production`
