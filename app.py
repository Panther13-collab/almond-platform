import os
import shutil
import uuid
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Body, Query
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import json

from core.parser import extract_text_from_file, parse_candidate_profile
from core.job_engine import search_matching_jobs, fetch_linkedin_postings
from core.pitch_generator import generate_star_pitch, generate_tailored_cover_letter
from core.founder_engine import fetch_hn_founder_jobs
from core.curated_feeds import query_curated_feed
from core.doc_exporter import (
    export_to_docx, export_to_pdf_async, export_to_csv,
    export_tech_dossier_pdf_async, export_tech_dossier_pdf,
    _export_pdf_pure_python, _export_tech_dossier_pure_python
)
from core.config import Config
from core.auth_db import (
    signup_user, login_user, is_user_paid, verify_session_token, get_user_profile,
    get_user_kanban, save_user_kanban_application, sync_full_kanban,
    send_signup_otp, verify_otp_and_signup
)
from core.payment import create_razorpay_order, verify_razorpay_signature
from core.security import BotShieldMiddleware, validate_uploaded_file, acquire_search_slot, release_search_slot

app = FastAPI(title="Almond Jobs - Direct Corporate Career Engine", version="2.0.0")

# Security Hardening: Bot Shield & Rate Limiting Middleware
app.add_middleware(BotShieldMiddleware)

# Secure CORS Policy (Restricts open wildcards with credentials)
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition", "X-Almond-Shield"],
)

@app.middleware("http")
async def add_dev_cache_headers(request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/static") or request.url.path == "/":
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(TEMPLATES_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    fav_path = os.path.join(STATIC_DIR, "favicon.ico")
    if os.path.exists(fav_path):
        return FileResponse(fav_path, media_type="image/x-icon")
    return FileResponse(os.path.join(STATIC_DIR, "logo.png"), media_type="image/png")

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_file = os.path.join(TEMPLATES_DIR, "index.html")
    if os.path.exists(index_file):
        with open(index_file, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Almond Jobs Platform is starting up...</h1>"

@app.get("/template/{template_id}", response_class=HTMLResponse)
async def serve_template(template_id: int):
    template_map = {
        1: "template_1_executive_terminal.html",
        2: "template_2_split_studio.html",
        3: "template_3_bento_grid.html",
        4: "template_4_stepper_funnel.html",
        5: "template_5_neural_matrix.html"
    }
    filename = template_map.get(template_id)
    if not filename:
        raise HTTPException(status_code=404, detail="Template not found. Please choose 1 to 5.")
    filepath = os.path.join(TEMPLATES_DIR, filename)
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    raise HTTPException(status_code=404, detail=f"Template file {filename} not found.")

@app.get("/kage-preview", response_class=HTMLResponse)
async def serve_kage_preview():
    filepath = os.path.join(TEMPLATES_DIR, "kage_preview.html")
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    raise HTTPException(status_code=404, detail="kage_preview.html not found.")

@app.post("/api/upload-resume")
async def upload_resume(file: UploadFile = File(...)):
    raw_bytes = await file.read()
    safe_filename = validate_uploaded_file(file, raw_bytes)

    file_id = f"{uuid.uuid4().hex[:8]}_{safe_filename}"
    saved_path = os.path.join(UPLOAD_DIR, file_id)

    with open(saved_path, "wb") as buffer:
        buffer.write(raw_bytes)

    raw_text = extract_text_from_file(saved_path)
    if not raw_text:
        raise HTTPException(status_code=400, detail="Could not extract text layer from the uploaded file.")

    profile = parse_candidate_profile(raw_text)
    profile["file_name"] = safe_filename
    profile["file_id"] = file_id

    return JSONResponse(content={"status": "success", "profile": profile})

@app.post("/api/auth/send-otp")
async def api_send_otp(payload: dict = Body(...)):
    email = payload.get("email", "")
    if not email:
        raise HTTPException(status_code=400, detail="Please enter your personal email address.")
    res = send_signup_otp(email)
    if res.get("status") == "error":
        raise HTTPException(status_code=400, detail=res.get("message"))
    return JSONResponse(content=res)

@app.post("/api/auth/verify-otp-and-signup")
async def api_verify_otp_and_signup(payload: dict = Body(...)):
    email = payload.get("email", "")
    otp = payload.get("otp", "")
    password = payload.get("password", "")
    full_name = payload.get("full_name", "")
    if not email or not otp or not password:
        raise HTTPException(status_code=400, detail="Email, verification code, and password are required.")
    res = verify_otp_and_signup(email, otp, password, full_name)
    if res.get("status") == "error":
        raise HTTPException(status_code=400, detail=res.get("message"))
    return JSONResponse(content=res)

@app.post("/api/auth/signup")
async def api_signup(payload: dict = Body(...)):
    email = payload.get("email", "")
    password = payload.get("password", "")
    full_name = payload.get("full_name", "")
    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password are required.")
    res = signup_user(email, password, full_name)
    if res.get("status") == "error":
        raise HTTPException(status_code=400, detail=res.get("message"))
    return JSONResponse(content=res)

@app.post("/api/auth/login")
async def api_login(payload: dict = Body(...)):
    email = payload.get("email", "")
    password = payload.get("password", "")
    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password are required.")
    res = login_user(email, password)
    if res.get("status") == "error":
        raise HTTPException(status_code=401, detail=res.get("message"))
    return JSONResponse(content=res)

@app.post("/api/auth/me")
async def api_me(payload: dict = Body(...)):
    token = payload.get("token", "")
    user_id = payload.get("user_id", "")
    
    user_data = None
    if token:
        user_data = verify_session_token(token)
    elif user_id:
        user_data = get_user_profile(user_id)
        
    if user_data:
        actual_id = user_data.get("id") or user_data.get("user_id")
        paid = is_user_paid(actual_id)
        profile = get_user_profile(actual_id) or user_data
        return JSONResponse(content={
            "status": "success",
            "is_authenticated": True,
            "user_id": actual_id,
            "email": profile.get("email", ""),
            "full_name": profile.get("full_name", ""),
            "plan": profile.get("plan", "free"),
            "paid_until": profile.get("paid_until", 0),
            "remaining_str": profile.get("remaining_str", ""),
            "is_paid": paid,
            "price_inr": Config.PRICE_INR,
            "price_usd": Config.PRICE_USD
        })

    return JSONResponse(content={
        "status": "success",
        "is_authenticated": False,
        "is_paid": False,
        "price_inr": Config.PRICE_INR,
        "price_usd": Config.PRICE_USD
    })

@app.post("/api/payment/create-order")
async def api_create_order(payload: dict = Body(...)):
    user_id = payload.get("user_id", "")
    amount_inr = int(payload.get("amount_inr", Config.PRICE_INR))
    res = create_razorpay_order(user_id, amount_inr)
    if res.get("status") == "error":
        raise HTTPException(status_code=500, detail=res.get("message"))
    return JSONResponse(content=res)

@app.post("/api/payment/verify")
async def api_verify_payment(payload: dict = Body(...)):
    user_id = payload.get("user_id", "")
    order_id = payload.get("order_id", "")
    payment_id = payload.get("payment_id", "")
    signature = payload.get("signature", "")
    amount_inr = int(payload.get("amount_inr", Config.PRICE_INR))
    plan_name = payload.get("plan_name", "")

    if not order_id or not payment_id:
        raise HTTPException(status_code=400, detail="Missing payment verification fields.")

    res = verify_razorpay_signature(user_id, order_id, payment_id, signature, amount_inr, plan_name)
    if res.get("status") == "error":
        raise HTTPException(status_code=400, detail=res.get("message"))
    return JSONResponse(content=res)

@app.post("/api/kanban/get")
async def api_get_kanban(payload: dict = Body(...)):
    token = payload.get("token", "")
    user_id = payload.get("user_id", "")
    if token:
        user_data = verify_session_token(token)
        if user_data:
            user_id = user_data.get("id") or user_data.get("user_id")
    data = get_user_kanban(user_id)
    return JSONResponse(content={"status": "success", "kanban": data})

@app.post("/api/kanban/sync")
async def api_sync_kanban(payload: dict = Body(...)):
    token = payload.get("token", "")
    user_id = payload.get("user_id", "")
    if token:
        user_data = verify_session_token(token)
        if user_data:
            user_id = user_data.get("id") or user_data.get("user_id")
    kanban = payload.get("kanban", {})
    updated = sync_full_kanban(user_id, kanban)
    return JSONResponse(content={"status": "success", "kanban": updated})

@app.post("/api/kanban/add")
async def api_add_kanban(payload: dict = Body(...)):
    token = payload.get("token", "")
    user_id = payload.get("user_id", "")
    if token:
        user_data = verify_session_token(token)
        if user_data:
            user_id = user_data.get("id") or user_data.get("user_id")
    application = payload.get("application", {})
    res = save_user_kanban_application(user_id, application)
    return JSONResponse(content={"status": "success", "result": res})

@app.post("/api/find-jobs")
async def find_jobs(payload: dict = Body(...)):
    profile = payload.get("profile")
    preferences = payload.get("preferences", {})
    user_id = payload.get("user_id", "")
    if not profile:
        raise HTTPException(status_code=400, detail="Candidate profile is required.")

    # Concurrency limiter to protect thread pool from simultaneous bot attacks
    if not acquire_search_slot():
        raise HTTPException(
            status_code=429, 
            detail="Platform is experiencing high query volume. Please try again in a few seconds."
        )

    try:
        user_is_paid = is_user_paid(user_id) if user_id else False
        result = search_matching_jobs(profile, preferences)
        ats_jobs = result.get("ats_jobs", [])
        linkedin_jobs = result.get("linkedin_jobs", [])

        # Fetch direct YC & Hacker News Founder Direct opportunities
        founder_jobs = []
        try:
            founder_jobs = fetch_hn_founder_jobs(profile, preferences)
        except Exception as fe:
            print(f"[SEARCH] Founder direct fetch error: {fe}")

        # If user has not purchased Pro access, lock jobs past index 3
        if not user_is_paid:
            for idx, j in enumerate(ats_jobs):
                if idx >= 3:
                    j["is_locked"] = True
                    j["real_url"] = j.get("url")
                    j["url"] = "#unlock-pro"
                else:
                    j["is_locked"] = False

            for idx, j in enumerate(linkedin_jobs):
                if idx >= 2:
                    j["is_locked"] = True
                    j["real_url"] = j.get("url")
                    j["url"] = "#unlock-pro"
                else:
                    j["is_locked"] = False
        else:
            for j in ats_jobs:
                j["is_locked"] = False
            for j in linkedin_jobs:
                j["is_locked"] = False

        return JSONResponse(content={
            "status": "success", 
            "total": len(ats_jobs), 
            "jobs": ats_jobs,
            "linkedin_jobs": linkedin_jobs,
            "founder_jobs": founder_jobs,
            "is_paid": user_is_paid,
            "price_inr": Config.PRICE_INR,
            "price_usd": Config.PRICE_USD
        })
    finally:
        release_search_slot()

@app.post("/api/find-linkedin-jobs")
async def find_linkedin_jobs(payload: dict = Body(...)):
    profile = payload.get("profile")
    preferences = payload.get("preferences", {})
    offset = int(payload.get("offset", 0))
    limit = int(payload.get("limit", 10))
    if not profile:
        raise HTTPException(status_code=400, detail="Candidate profile is required.")

    if not acquire_search_slot():
        raise HTTPException(
            status_code=429, 
            detail="Platform is experiencing high query volume. Please try again in a few seconds."
        )

    try:
        li_jobs, has_more, total_found = fetch_linkedin_postings(profile, preferences, limit=limit, offset=offset)
        return JSONResponse(content={
            "status": "success", 
            "total": total_found, 
            "jobs": li_jobs,
            "has_more": has_more,
            "offset": offset + len(li_jobs)
        })
    finally:
        release_search_slot()

@app.post("/api/get-pitch")
async def get_pitch(payload: dict = Body(...)):
    profile = payload.get("profile", {})
    job = payload.get("job", {})
    pitch = generate_star_pitch(profile, job)
    return JSONResponse(content={"status": "success", "pitch": pitch})

@app.post("/api/get-cover-letter")
async def get_cover_letter(payload: dict = Body(...)):
    profile = payload.get("profile", {})
    job = payload.get("job", {})
    cover_letter = generate_tailored_cover_letter(profile, job)
    return JSONResponse(content={"status": "success", "cover_letter": cover_letter})

@app.post("/api/find-founder-jobs")
async def find_founder_jobs(payload: dict = Body(...)):
    profile = payload.get("profile")
    preferences = payload.get("preferences", {})
    if not profile:
        raise HTTPException(status_code=400, detail="Candidate profile is required.")

    if not acquire_search_slot():
        raise HTTPException(
            status_code=429, 
            detail="Platform is experiencing high query volume. Please try again in a few seconds."
        )

    try:
        founder_jobs = fetch_hn_founder_jobs(profile, preferences)
        return JSONResponse(content={"status": "success", "total": len(founder_jobs), "jobs": founder_jobs})
    finally:
        release_search_slot()

@app.post("/api/download-dossier")
async def download_dossier(payload: dict = Body(...)):
    profile = payload.get("profile", {})
    jobs = payload.get("jobs", [])
    doc_format = payload.get("format", "pdf").lower()
    user_id = payload.get("user_id")

    if not jobs:
        raise HTTPException(status_code=400, detail="No jobs to export.")

    # Determine entitlement: Free tier has links 4+ locked with upgrade CTA
    user_paid = is_user_paid(user_id) if user_id else bool(payload.get("is_paid"))
    cand_slug = (profile.get("name") or "Candidate").replace(" ", "_")
    
    if doc_format == "docx":
        out_name = f"{cand_slug}_Almond_Job_Dossier.docx"
        out_path = os.path.join(UPLOAD_DIR, out_name)
        export_to_docx(profile, jobs, out_path, is_paid=user_paid)
        return FileResponse(out_path, filename=out_name, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

    elif doc_format == "csv":
        out_name = f"{cand_slug}_Almond_Job_Tracker.csv"
        out_path = os.path.join(UPLOAD_DIR, out_name)
        export_to_csv(jobs, out_path, is_paid=user_paid)
        return FileResponse(out_path, filename=out_name, media_type="text/csv")

    else: # default pdf
        out_name = f"{cand_slug}_Almond_Job_Dossier.pdf"
        out_path = os.path.join(UPLOAD_DIR, out_name)
        try:
            await export_to_pdf_async(profile, jobs, out_path, is_paid=user_paid)
        except Exception as pdf_err:
            print(f"[DOWNLOAD_DOSSIER] Playwright async failed ({pdf_err}), falling back to pure-Python PDF.")
            _export_pdf_pure_python(profile, jobs, out_path, is_paid=user_paid)

        return FileResponse(out_path, filename=out_name, media_type="application/pdf")

@app.get("/api/curated-feeds")
async def get_curated_feeds(
    feed_type: str = Query("internships"),
    query: str = Query(""),
    category: str = Query("All"),
    time_filter: str = Query("all"),
    limit: int = Query(25),
    offset: int = Query(0),
    user_id: Optional[str] = Query(None)
):
    """Retrieve filtered, high-freshness direct corporate feeds (Internships, Entry-Level, AI/ML Specialist)."""
    user_paid = is_user_paid(user_id) if user_id else False
    res = query_curated_feed(
        feed_type=feed_type,
        query=query,
        category=category,
        time_filter=time_filter,
        limit=min(limit, 100),
        offset=offset,
        user_is_paid=user_paid
    )
    return JSONResponse(content={"status": "success", "result": res})

@app.post("/api/export-tech-dossier")
async def export_tech_dossier(payload: dict = Body(...)):
    """Generate and return a clean, single-page Silicon Valley technical dossier PDF."""
    profile = payload.get("profile", {})
    if not profile:
        raise HTTPException(status_code=400, detail="Candidate profile is required.")

    cand_slug = (profile.get("name") or "Candidate").replace(" ", "_")
    out_name = f"{cand_slug}_1Page_Tech_Dossier.pdf"
    out_path = os.path.join(UPLOAD_DIR, out_name)
    try:
        await export_tech_dossier_pdf_async(profile, out_path)
    except Exception as e:
        print(f"[EXPORT_TECH_DOSSIER] Playwright async failed ({e}), using pure-Python fallback.")
        _export_tech_dossier_pure_python(profile, out_path)

    return FileResponse(out_path, filename=out_name, media_type="application/pdf")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
