import os
import shutil
import uuid
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Body
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import json

from core.parser import extract_text_from_file, parse_candidate_profile
from core.job_engine import search_matching_jobs, fetch_linkedin_postings
from core.pitch_generator import generate_star_pitch
from core.doc_exporter import export_to_docx, export_to_pdf_async, export_to_csv
from core.config import Config
from core.auth_db import signup_user, login_user, is_user_paid
from core.payment import create_razorpay_order, verify_razorpay_signature
from core.security import BotShieldMiddleware, validate_uploaded_file, acquire_search_slot, release_search_slot

app = FastAPI(title="Almond AI - Direct ATS Global Job Engine", version="2.0.0")

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

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(TEMPLATES_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_file = os.path.join(TEMPLATES_DIR, "index.html")
    if os.path.exists(index_file):
        with open(index_file, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Almond AI Platform is starting up...</h1>"

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
    user_id = payload.get("user_id", "")
    paid = is_user_paid(user_id) if user_id else False
    return JSONResponse(content={
        "status": "success", 
        "user_id": user_id, 
        "is_paid": paid,
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

    if not order_id or not payment_id:
        raise HTTPException(status_code=400, detail="Missing payment verification fields.")

    res = verify_razorpay_signature(user_id, order_id, payment_id, signature, amount_inr)
    if res.get("status") == "error":
        raise HTTPException(status_code=400, detail=res.get("message"))
    return JSONResponse(content=res)

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
    if not profile:
        raise HTTPException(status_code=400, detail="Candidate profile is required.")

    if not acquire_search_slot():
        raise HTTPException(
            status_code=429, 
            detail="Platform is experiencing high query volume. Please try again in a few seconds."
        )

    try:
        li_jobs = fetch_linkedin_postings(profile, preferences, limit=10)
        return JSONResponse(content={"status": "success", "total": len(li_jobs), "jobs": li_jobs})
    finally:
        release_search_slot()

@app.post("/api/get-pitch")
async def get_pitch(payload: dict = Body(...)):
    profile = payload.get("profile", {})
    job = payload.get("job", {})
    pitch = generate_star_pitch(profile, job)
    return JSONResponse(content={"status": "success", "pitch": pitch})

@app.post("/api/download-dossier")
async def download_dossier(payload: dict = Body(...)):
    profile = payload.get("profile", {})
    jobs = payload.get("jobs", [])
    doc_format = payload.get("format", "pdf").lower()

    if not jobs:
        raise HTTPException(status_code=400, detail="No jobs to export.")

    cand_slug = (profile.get("name") or "Candidate").replace(" ", "_")
    
    if doc_format == "docx":
        out_name = f"{cand_slug}_Almond_Job_Dossier.docx"
        out_path = os.path.join(UPLOAD_DIR, out_name)
        export_to_docx(profile, jobs, out_path)
        return FileResponse(out_path, filename=out_name, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

    elif doc_format == "csv":
        out_name = f"{cand_slug}_Almond_Job_Tracker.csv"
        out_path = os.path.join(UPLOAD_DIR, out_name)
        export_to_csv(jobs, out_path)
        return FileResponse(out_path, filename=out_name, media_type="text/csv")

    else: # default pdf
        out_name = f"{cand_slug}_Almond_Job_Dossier.pdf"
        out_path = os.path.join(UPLOAD_DIR, out_name)
        await export_to_pdf_async(profile, jobs, out_path)
        return FileResponse(out_path, filename=out_name, media_type="application/pdf")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
