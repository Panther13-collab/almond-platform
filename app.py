import os
import shutil
import uuid
import csv
import io
import json
import threading
import time
from typing import Optional

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Body, Query, Request
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse, Response, PlainTextResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from jinja2 import Environment, FileSystemLoader

from core.parser import extract_text_from_file, parse_candidate_profile
from core.job_engine import search_matching_jobs, fetch_linkedin_postings, _get_skills_fingerprint
from core.pitch_generator import generate_star_pitch, generate_tailored_cover_letter
from core.founder_engine import fetch_hn_founder_jobs
from core.curated_feeds import query_curated_feed, start_curated_feed_scheduler
from core.doc_exporter import (
    export_to_docx, export_to_pdf_async, export_to_csv,
    export_tech_dossier_pdf_async, export_tech_dossier_pdf,
    _export_pdf_pure_python, _export_tech_dossier_pure_python
)
from core.config import Config
from core.auth_db import (
    signup_user, login_user, is_user_paid, verify_session_token, get_user_profile,
    recover_verified_session, get_recent_contributions, grant_vip_to_email, revoke_vip_from_email,
    get_user_kanban, save_user_kanban_application, sync_full_kanban,
    send_signup_otp, verify_otp_and_signup, login_or_signup_google_user,
    record_page_visit, get_analytics_summary, get_all_users_admin,
    parse_device_hardware, is_bot_or_scanner, get_dynamic_pricing, update_tier_pricing
)
from core.payment import apply_vip_latest_feed_lock, create_razorpay_order, verify_razorpay_signature
from core.security import BotShieldMiddleware, validate_uploaded_file, acquire_search_slot, release_search_slot
from core.sitemap_generator import (
    generate_sitemap_index, generate_main_sitemap,
    generate_categories_sitemap, generate_jobs_sitemap
)
from core.seo_renderer import render_category_page
from core.legal_renderer import (
    render_terms_page, render_privacy_page, render_refund_page, render_contact_page
)

# In-Memory Cache for Composite Candidate Search Results
_API_SEARCH_CACHE = {}
_API_SEARCH_CACHE_LOCK = threading.Lock()
_API_SEARCH_CACHE_TTL = 7200  # 2 Hours

app = FastAPI(title="Almond Jobs - Direct Corporate Career Engine", version="2.0.0")

@app.middleware("http")
async def add_anti_cache_headers(request: Request, call_next):
    response = await call_next(request)
    path = request.url.path
    if path == "/" or path.endswith((".html", ".js", ".css")):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response



# Security Hardening: Bot Shield & Rate Limiting Middleware
app.add_middleware(BotShieldMiddleware)

# High-Performance Compression: GZip responses > 1KB (shrinks HTML/JS/JSON payloads by 75-85%)
app.add_middleware(GZipMiddleware, minimum_size=1000)

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
async def add_performance_cache_headers(request: Request, call_next):
    path = request.url.path

    # Track real-time visitor telemetry for candidate pageviews
    if not path.startswith("/static/") and path not in ["/favicon.ico", "/health", "/robots.txt", "/sitemap.xml", "/llms.txt"]:
        try:
            client_ip = request.client.host if request.client else "127.0.0.1"
            forwarded = request.headers.get("x-forwarded-for")
            if forwarded:
                client_ip = forwarded.split(",")[0].strip()
            user_agent = request.headers.get("user-agent", "")
            referrer = request.headers.get("referer", "")
            model_hint = request.headers.get("sec-ch-ua-model", "").strip('"')
            plat_hint = request.headers.get("sec-ch-ua-platform", "").strip('"')
            plat_ver = request.headers.get("sec-ch-ua-platform-version", "").strip('"')
            client_hints = {
                "model": model_hint,
                "platform": plat_hint,
                "platform_version": plat_ver
            }
            record_page_visit(path, client_ip, user_agent, referrer, client_hints=client_hints)
        except Exception:
            pass

    response = await call_next(request)
    # Static assets (images, fonts, scripts): cache for 7 days with revalidation
    if path.startswith("/static/"):
        if path.endswith(".js") or path.endswith(".css"):
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        else:
            response.headers["Cache-Control"] = "public, max-age=86400"
    elif path == "/" or path.startswith("/jobs/"):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        # HTML pages: must revalidate so updates propagate immediately
    return response

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(TEMPLATES_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.on_event("startup")
async def on_startup():
    start_curated_feed_scheduler()

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    fav_path = os.path.join(STATIC_DIR, "favicon.ico")
    if os.path.exists(fav_path):
        return FileResponse(fav_path, media_type="image/x-icon")
    return FileResponse(os.path.join(STATIC_DIR, "logo.png"), media_type="image/png")

@app.get("/robots.txt", include_in_schema=False)
async def serve_robots():
    robots_path = os.path.join(STATIC_DIR, "robots.txt")
    if os.path.exists(robots_path):
        return FileResponse(robots_path, media_type="text/plain; charset=utf-8")
    return Response(content="User-agent: *\nAllow: /\n", media_type="text/plain")

@app.get("/llms.txt", include_in_schema=False)
async def serve_llms():
    llms_path = os.path.join(STATIC_DIR, "llms.txt")
    if os.path.exists(llms_path):
        return FileResponse(llms_path, media_type="text/plain; charset=utf-8")
    return Response(content="# Almond Jobs\nhttps://almondjobs.com\n", media_type="text/plain")

@app.get("/llms-full.txt", include_in_schema=False)
async def serve_llms_full():
    llms_path = os.path.join(STATIC_DIR, "llms-full.txt")
    if os.path.exists(llms_path):
        return FileResponse(llms_path, media_type="text/plain; charset=utf-8")
    return Response(content="# Almond Jobs Full Spec\nhttps://almondjobs.com\n", media_type="text/plain")

INDEXNOW_KEY = "b7e4f8812c854e4c92da1578f56efb89"

@app.get(f"/{INDEXNOW_KEY}.txt", include_in_schema=False)
async def serve_indexnow_key():
    return PlainTextResponse(INDEXNOW_KEY)

@app.get("/indexnow-key.txt", include_in_schema=False)
async def serve_indexnow_alias():
    return PlainTextResponse(INDEXNOW_KEY)

@app.get("/sitemap.xml", include_in_schema=False)
async def sitemap_index():
    return Response(content=generate_sitemap_index(), media_type="application/xml")

@app.get("/sitemap-main.xml", include_in_schema=False)
async def sitemap_main():
    return Response(content=generate_main_sitemap(), media_type="application/xml")

@app.get("/sitemap-categories.xml", include_in_schema=False)
async def sitemap_categories():
    return Response(content=generate_categories_sitemap(), media_type="application/xml")

@app.get("/sitemap-jobs.xml", include_in_schema=False)
async def sitemap_jobs():
    return Response(content=generate_jobs_sitemap(), media_type="application/xml")

@app.get("/it-jobs", response_class=HTMLResponse)
async def serve_it_jobs():
    return HTMLResponse(content=render_category_page("it-jobs"))

@app.get("/non-it-jobs", response_class=HTMLResponse)
async def serve_non_it_jobs():
    return HTMLResponse(content=render_category_page("non-it-jobs"))

@app.get("/core-jobs", response_class=HTMLResponse)
async def serve_core_jobs():
    return HTMLResponse(content=render_category_page("core-jobs"))

@app.get("/free-jobs", response_class=HTMLResponse)
async def serve_free_jobs():
    return HTMLResponse(content=render_category_page("free-jobs"))

@app.get("/high-paying-jobs", response_class=HTMLResponse)
async def serve_high_paying_jobs():
    return HTMLResponse(content=render_category_page("high-paying-jobs"))

@app.get("/no-mediator-jobs", response_class=HTMLResponse)
@app.get("/no-consultancy-jobs", response_class=HTMLResponse)
async def serve_no_mediator_jobs():
    return HTMLResponse(content=render_category_page("no-mediator-jobs"))

@app.get("/naukri-alternative", response_class=HTMLResponse)
async def serve_naukri_alt():
    return HTMLResponse(content=render_category_page("naukri-alternative"))

@app.get("/smartrecruiters-direct", response_class=HTMLResponse)
async def serve_smartrecruiters_direct():
    return HTMLResponse(content=render_category_page("smartrecruiters-direct-jobs"))

@app.get("/almond-jobs", response_class=HTMLResponse)
@app.get("/jobs/almond-jobs", response_class=HTMLResponse)
async def serve_almond_jobs_direct():
    return HTMLResponse(content=render_category_page("almond-jobs"))

@app.get("/almond-job", response_class=HTMLResponse)
@app.get("/jobs/almond-job", response_class=HTMLResponse)
async def serve_almond_job_direct():
    return HTMLResponse(content=render_category_page("almond-job"))

@app.get("/jobs/{slug}", response_class=HTMLResponse)
async def serve_category_jobs(slug: str):
    return HTMLResponse(content=render_category_page(slug))

@app.get("/feed/{feed_type}", response_class=HTMLResponse)
async def serve_feed_page(feed_type: str):
    slug_map = {
        "internships": "direct-internships-2026",
        "aiml": "ai-ml-specialist",
        "entrylevel": "entry-level-swe"
    }
    target_slug = slug_map.get(feed_type, "software-engineer")
    return HTMLResponse(content=render_category_page(target_slug))

@app.get("/terms", response_class=HTMLResponse)
@app.get("/terms-and-conditions", response_class=HTMLResponse)
async def serve_terms():
    return HTMLResponse(content=render_terms_page())

@app.get("/privacy", response_class=HTMLResponse)
@app.get("/privacy-policy", response_class=HTMLResponse)
async def serve_privacy():
    return HTMLResponse(content=render_privacy_page())

@app.get("/refund-policy", response_class=HTMLResponse)
@app.get("/refunds", response_class=HTMLResponse)
@app.get("/refund", response_class=HTMLResponse)
async def serve_refund_policy():
    return HTMLResponse(content=render_refund_page())

@app.get("/contact", response_class=HTMLResponse)
@app.get("/contact-us", response_class=HTMLResponse)
async def serve_contact():
    return HTMLResponse(content=render_contact_page())

@app.get("/health")
@app.get("/ping")
async def health_check():
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "service": "almondjobs",
            "uptime": "100%",
            "live_feeds": "3.3M+",
            "timestamp": int(time.time())
        }
    )

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_file = os.path.join(TEMPLATES_DIR, "index.html")
    if os.path.exists(index_file):
        with open(index_file, "r", encoding="utf-8") as f:
            content = f.read()
            if Config.GA_MEASUREMENT_ID:
                content = content.replace('window.__ALMOND_GA_ID__ || ""', f'"{Config.GA_MEASUREMENT_ID}"')
            return content
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

# ============================================================================
# Executive Telemetry, Traffic Analytics & Candidate Directory Endpoints
# ============================================================================

@app.get("/admin", response_class=HTMLResponse)
async def serve_admin_dashboard(
    request: Request,
    key: Optional[str] = Query(None),
    logout: Optional[int] = Query(None)
):
    """
    Zero-Cost Internal Executive Telemetry & Candidate Directory Portal.
    Protected by configurable ALMOND_ADMIN_KEY (default: almond2026).
    """
    if logout == 1:
        res = HTMLResponse("<script>document.cookie = 'almond_admin_key=; Path=/; Expires=Thu, 01 Jan 1970 00:00:01 GMT;'; window.location.href = '/admin';</script>")
        res.delete_cookie("almond_admin_key")
        return res

    cookie_key = request.cookies.get("almond_admin_key")
    provided_key = (key or cookie_key or "").strip()
    is_authenticated = bool(provided_key and provided_key == Config.ADMIN_SECRET_KEY)

    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))
    template = env.get_template("admin.html")

    if is_authenticated:
        analytics = get_analytics_summary()
        candidates = get_all_users_admin()
        genuine_count = sum(1 for c in candidates if not c.get("is_dummy"))
        dummy_count = sum(1 for c in candidates if c.get("is_dummy"))
        new_count = sum(1 for c in candidates if c.get("is_new"))
        vip_count = sum(1 for c in candidates if c.get("is_paid"))
        rendered = template.render(
            is_authenticated=True,
            admin_key=provided_key,
            auth_error=False,
            analytics=analytics,
            candidates=candidates,
            genuine_count=genuine_count,
            dummy_count=dummy_count,
            new_count=new_count,
            vip_count=vip_count,
            pricing_tiers=get_dynamic_pricing()
        )
        response = HTMLResponse(content=rendered)
        # Store secure session cookie for convenience so user stays logged in
        response.set_cookie(
            key="almond_admin_key",
            value=provided_key,
            max_age=86400 * 30,
            httponly=True,
            samesite="lax"
        )
        return response
    else:
        rendered = template.render(
            is_authenticated=False,
            admin_key="",
            auth_error=bool(provided_key),
            analytics={},
            candidates=[]
        )
        return HTMLResponse(content=rendered)

@app.get("/api/admin/metrics")
async def get_admin_metrics(request: Request, key: Optional[str] = Query(None)):
    """API endpoint for live polling of analytics telemetry and candidate directory."""
    cookie_key = request.cookies.get("almond_admin_key")
    header_key = request.headers.get("x-admin-key")
    provided_key = (key or cookie_key or header_key or "").strip()
    if provided_key != Config.ADMIN_SECRET_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid admin secret key.")
    return {
        "status": "success",
        "analytics": get_analytics_summary(),
        "candidates": get_all_users_admin()
    }

@app.get("/api/admin/export-users")
async def export_candidates_csv(request: Request, key: Optional[str] = Query(None)):
    """Export all registered candidates as a clean, downloadable CSV spreadsheet with account classification."""
    cookie_key = request.cookies.get("almond_admin_key")
    provided_key = (key or cookie_key or "").strip()
    if provided_key != Config.ADMIN_SECRET_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid admin secret key.")

    candidates = get_all_users_admin()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Candidate ID", "Full Name", "Email", "Account Classification", "Sign-in Provider", "Device / Hardware Model", "Plan", "VIP Status", "VIP Expiration", "Registration Date"])
    for c in candidates:
        writer.writerow([
            c.get("id", ""),
            c.get("full_name", ""),
            c.get("email", ""),
            "Test / Dummy" if c.get("is_dummy") else "Genuine Candidate",
            c.get("auth_provider", "email"),
            c.get("device_display", "Desktop / Web Browser"),
            c.get("plan", "free"),
            "VIP ACTIVE" if c.get("is_paid") else "Standard Free",
            c.get("paid_until_str", "N/A"),
            c.get("created_at_str", "")
        ])

    csv_content = output.getvalue()
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="almond_candidates_export.csv"'}
    )


@app.get("/api/pricing")
async def api_get_pricing():
    """Retrieve dynamic multi-tier subscription pricing across all currencies."""
    tiers = get_dynamic_pricing()
    return JSONResponse(content={"success": True, "tiers": tiers})


@app.post("/api/admin/pricing")
async def api_admin_update_pricing(request: Request, payload: dict = Body(...)):
    """Admin endpoint to update pricing, strike base prices, discounts and badges without touching existing VIP validity."""
    cookie_key = request.cookies.get("almond_admin_key")
    header_key = request.headers.get("x-admin-key")
    query_key = payload.get("key")
    provided_key = (query_key or cookie_key or header_key or "").strip()

    if provided_key != Config.ADMIN_SECRET_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid admin secret key.")

    tier_id = str(payload.get("tier_id", "") or "").strip().lower()
    if not tier_id:
        raise HTTPException(status_code=400, detail="Missing required 'tier_id'.")

    try:
        updated_tiers = update_tier_pricing(tier_id, payload)
        return JSONResponse(content={"success": True, "message": f"Pricing updated for tier '{tier_id}'.", "tiers": updated_tiers})
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/admin/grant-vip")
async def api_admin_grant_vip(request: Request, payload: dict = Body(...)):
    """Executive admin endpoint to grant or revoke 1-Month VIP access for an email address."""
    cookie_key = request.cookies.get("almond_admin_key")
    header_key = request.headers.get("x-admin-key")
    query_key = payload.get("key")
    provided_key = (query_key or cookie_key or header_key or "").strip()

    if provided_key != Config.ADMIN_SECRET_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid admin secret key.")

    email = (payload.get("email") or "").strip().lower()
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="A valid candidate email address is required.")

    action = (payload.get("action") or "grant").lower()
    duration_days = int(payload.get("duration_days", 30))

    if action == "revoke":
        res = revoke_vip_from_email(email)
    else:
        res = grant_vip_to_email(email, duration_days=duration_days, granted_by="Admin Portal")

    return JSONResponse(content=res)

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

def _resolve_request_device(request: Request, payload_device: str = "") -> str:
    if payload_device and payload_device.strip():
        return payload_device.strip()
    ua = request.headers.get("user-agent", "")
    model_hint = request.headers.get("sec-ch-ua-model", "").strip('"')
    plat_hint = request.headers.get("sec-ch-ua-platform", "").strip('"')
    plat_ver = request.headers.get("sec-ch-ua-platform-version", "").strip('"')
    dev_info = parse_device_hardware(ua, {"model": model_hint, "platform": plat_hint, "platform_version": plat_ver})
    return dev_info.get("display") or dev_info.get("model") or "Desktop Browser"

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
async def api_verify_otp_and_signup(request: Request, payload: dict = Body(...)):
    email = payload.get("email", "")
    otp = payload.get("otp", "")
    password = payload.get("password", "")
    full_name = payload.get("full_name", "")
    device_model = _resolve_request_device(request, payload.get("device_model", ""))
    if not email or not otp or not password:
        raise HTTPException(status_code=400, detail="Email, verification code, and password are required.")
    res = verify_otp_and_signup(email, otp, password, full_name, device_model=device_model)
    if res.get("status") == "error":
        raise HTTPException(status_code=400, detail=res.get("message"))
    return JSONResponse(content=res)

@app.post("/api/auth/signup")
async def api_signup(request: Request, payload: dict = Body(...)):
    email = payload.get("email", "")
    password = payload.get("password", "")
    full_name = payload.get("full_name", "")
    device_model = _resolve_request_device(request, payload.get("device_model", ""))
    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password are required.")
    res = signup_user(email, password, full_name, device_model=device_model)
    if res.get("status") == "error":
        raise HTTPException(status_code=400, detail=res.get("message"))
    return JSONResponse(content=res)

@app.post("/api/auth/login")
async def api_login(request: Request, payload: dict = Body(...)):
    email = payload.get("email", "")
    password = payload.get("password", "")
    device_model = _resolve_request_device(request, payload.get("device_model", ""))
    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password are required.")
    res = login_user(email, password, device_model=device_model)
    if res.get("status") == "error":
        raise HTTPException(status_code=401, detail=res.get("message"))
    return JSONResponse(content=res)


@app.get("/api/auth/google/config")
async def api_google_config():
    return JSONResponse(content={
        "configured": Config.is_google_auth_configured(),
        "client_id": Config.GOOGLE_CLIENT_ID
    })

@app.get("/api/auth/google/login")
async def api_google_login(request: Request):
    if not Config.GOOGLE_CLIENT_ID:
        html_setup = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Google Sign-In Configuration Required</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-50 text-slate-800 flex items-center justify-center min-h-screen p-4 font-sans">
    <div class="max-w-md w-full bg-white rounded-3xl p-8 shadow-xl border border-slate-200 text-center space-y-4">
        <div class="w-12 h-12 rounded-2xl bg-amber-100 text-amber-700 flex items-center justify-center mx-auto text-xl font-bold">!</div>
        <h2 class="text-xl font-black text-slate-950">Google OAuth Credentials Needed</h2>
        <p class="text-xs text-slate-600 leading-relaxed">
            To enable real Google Account Chooser sign-in, please add your <strong>GOOGLE_CLIENT_ID</strong> and <strong>GOOGLE_CLIENT_SECRET</strong> from Google Cloud Console into <code>platform/.env</code>.
        </p>
        <div class="pt-4 border-t border-slate-100 flex flex-col gap-2">
            <a href="/?login=manual" class="px-5 py-2.5 rounded-xl bg-violet-600 hover:bg-violet-700 text-white font-bold text-xs transition">
                Return to Login with Email & Password
            </a>
            <a href="/" class="text-xs font-semibold text-slate-500 hover:text-slate-800">
                Back to Almond Jobs Home
            </a>
        </div>
    </div>
</body>
</html>"""
        return HTMLResponse(content=html_setup, status_code=200)

    import urllib.parse
    # Construct base redirect uri
    redirect_uri = str(request.url_for("api_google_callback"))
    if request.headers.get("x-forwarded-proto") == "https" or "almondjobs.com" in request.headers.get("host", ""):
        redirect_uri = redirect_uri.replace("http://", "https://")

    params = {
        "client_id": Config.GOOGLE_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "prompt": "select_account",
        "access_type": "offline"
    }
    google_auth_url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(params)
    return RedirectResponse(url=google_auth_url)

@app.get("/api/auth/google/callback")
async def api_google_callback(request: Request, code: str = None, error: str = None):
    if error or not code:
        return RedirectResponse(url="/?auth_error=" + (error or "cancelled"))

    import urllib.parse
    import urllib.request
    import json
    import base64

    redirect_uri = str(request.url_for("api_google_callback"))
    if request.headers.get("x-forwarded-proto") == "https" or "almondjobs.com" in request.headers.get("host", ""):
        redirect_uri = redirect_uri.replace("http://", "https://")

    token_url = "https://oauth2.googleapis.com/token"
    token_data = urllib.parse.urlencode({
        "code": code,
        "client_id": Config.GOOGLE_CLIENT_ID,
        "client_secret": Config.GOOGLE_CLIENT_SECRET,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code"
    }).encode("utf-8")

    try:
        req = urllib.request.Request(token_url, data=token_data, headers={"Content-Type": "application/x-www-form-urlencoded"})
        with urllib.request.urlopen(req) as resp:
            token_payload = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"[AUTH_GOOGLE] Token exchange error: {e}")
        return RedirectResponse(url="/?auth_error=exchange_failed")

    id_token_str = token_payload.get("id_token", "")
    email = ""
    full_name = ""
    google_id = ""

    if id_token_str:
        try:
            token_parts = id_token_str.split(".")
            if len(token_parts) >= 2:
                payload_b64 = token_parts[1] + "=" * (-len(token_parts[1]) % 4)
                jwt_payload = json.loads(base64.urlsafe_b64decode(payload_b64).decode("utf-8"))
                email = jwt_payload.get("email", "").strip().lower()
                full_name = jwt_payload.get("name", "").strip()
                google_id = jwt_payload.get("sub", "").strip()
        except Exception as e:
            print(f"[AUTH_GOOGLE] JWT decode error: {e}")

    # Fallback to UserInfo endpoint if email wasn't in id_token
    access_token = token_payload.get("access_token", "")
    if not email and access_token:
        try:
            userinfo_req = urllib.request.Request(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            with urllib.request.urlopen(userinfo_req) as resp:
                uinfo = json.loads(resp.read().decode("utf-8"))
                email = uinfo.get("email", "").strip().lower()
                full_name = uinfo.get("name", "").strip()
                google_id = uinfo.get("sub", "").strip()
        except Exception as e:
            print(f"[AUTH_GOOGLE] UserInfo fetch error: {e}")

    if not email:
        return RedirectResponse(url="/?auth_error=no_email_returned")

    # Detect device hardware model
    detected_device = _resolve_request_device(request)

    # Log in or register the candidate with exact device logging
    res = login_or_signup_google_user(email, full_name, google_id, device_model=detected_device)
    token = res.get("token", "")
    user_id = res.get("user_id", "")
    full_name = res.get("full_name", full_name or email.split("@")[0])
    is_paid = "true" if res.get("is_paid") else "false"

    clean_name = str(full_name).replace('"', '\\"').replace('\n', ' ')
    clean_email = str(email).replace('"', '\\"').replace('\n', ' ')
    clean_token = str(token).replace('"', '\\"')
    clean_uid = str(user_id).replace('"', '\\"')

    html_success = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Connecting to Almond Jobs...</title>
</head>
<body style="background:#f8fafc; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; display:flex; align-items:center; justify-content:center; height:100vh; margin:0;">
    <div style="background:white; padding:36px 48px; border-radius:24px; box-shadow:0 20px 40px rgba(0,0,0,0.08); text-align:center; max-width:400px; border:1px solid #e2e8f0;">
        <div style="width:48px; height:48px; border-radius:50%; background:#ecfdf5; color:#059669; display:flex; align-items:center; justify-content:center; font-size:24px; margin:0 auto 16px;">✓</div>
        <h3 style="margin:0 0 6px 0; color:#0f172a; font-size:18px; font-weight:800;">Welcome, {clean_name}</h3>
        <p style="margin:0 0 16px 0; color:#64748b; font-size:13px;">Signed in as <strong>{clean_email}</strong></p>
        <p style="margin:0; color:#94a3b8; font-size:12px;">Opening your Almond Jobs dashboard...</p>
    </div>
    <script>
        try {{
            localStorage.setItem("almond_session_token", "{clean_token}");
            localStorage.setItem("almond_auth_token", "{clean_token}");
            localStorage.setItem("almond_user_id", "{clean_uid}");
            localStorage.setItem("almond_user_email", "{clean_email}");
            localStorage.setItem("almond_user_name", "{clean_name}");
            localStorage.setItem("almond_is_paid", "{is_paid}");
            sessionStorage.setItem("almond_login_event", "google_success");
        }} catch(e) {{
            console.error("Storage error:", e);
        }}
        setTimeout(function() {{
            window.location.href = "/?login=success";
        }}, 400);
    </script>
</body>
</html>"""
    return HTMLResponse(content=html_success, status_code=200)

@app.post("/api/auth/google")
async def api_google_auth(request: Request, payload: dict = Body(...)):
    credential = payload.get("credential", "").strip()
    email = payload.get("email", "").strip().lower()
    full_name = payload.get("name", "").strip()
    google_id = payload.get("google_id", "").strip()
    device_model = _resolve_request_device(request, payload.get("device_model", ""))

    # Parse and extract verified claims from Google Identity Services JWT credential
    if credential and not email:
        try:
            import json
            import base64
            token_parts = credential.split(".")
            if len(token_parts) >= 2:
                payload_b64 = token_parts[1] + "=" * (-len(token_parts[1]) % 4)
                decoded_bytes = base64.urlsafe_b64decode(payload_b64)
                jwt_payload = json.loads(decoded_bytes.decode("utf-8"))
                email = jwt_payload.get("email", "").strip().lower()
                full_name = jwt_payload.get("name", "").strip()
                google_id = jwt_payload.get("sub", "").strip()
        except Exception as e:
            print(f"[AUTH_GOOGLE] JWT decode note: {e}")

    if not email:
        raise HTTPException(status_code=400, detail="Google authentication did not provide a valid email.")

    res = login_or_signup_google_user(email, full_name, google_id, device_model=device_model)
    if res.get("status") == "error":
        raise HTTPException(status_code=400, detail=res.get("message"))
    return JSONResponse(content=res)

@app.post("/api/auth/me")
async def api_me(payload: dict = Body(...)):
    token = (payload.get("token") or "").strip()
    user_id = (payload.get("user_id") or "").strip()
    email = (payload.get("email") or "").strip().lower()
    full_name = (payload.get("full_name") or "").strip()

    user_data = None
    if token:
        user_data = verify_session_token(token, email=email, full_name=full_name)
    elif user_id:
        user_data = recover_verified_session(user_id, email=email, full_name=full_name)

    if user_data:
        actual_id = user_data.get("id") or user_data.get("user_id")
        paid = is_user_paid(actual_id)
        profile = get_user_profile(actual_id) or user_data
        return JSONResponse(content={
            "status": "success",
            "is_authenticated": True,
            "token": user_data.get("token") or token,
            "user_id": actual_id,
            "email": profile.get("email", ""),
            "full_name": profile.get("full_name", ""),
            "plan": profile.get("plan", "free"),
            "plan_tier": profile.get("plan_tier", "1m" if paid else "free"),
            "paid_until": profile.get("paid_until", 0),
            "paid_until_formatted": profile.get("paid_until_formatted", ""),
            "remaining_str": profile.get("remaining_str", ""),
            "is_paid": paid,
            "price_inr": Config.PRICE_INR,
            "price_usd": Config.PRICE_USD,
            "vip_price_inr": getattr(Config, "VIP_PRICE_INR", 699),
            "vip_tiers": getattr(Config, "VIP_TIERS", {})
        })

    return JSONResponse(content={
        "status": "success",
        "is_authenticated": False,
        "invalid_token": bool(token),
        "is_paid": False,
        "plan_tier": "free",
        "price_inr": Config.PRICE_INR,
        "price_usd": Config.PRICE_USD,
        "vip_price_inr": getattr(Config, "VIP_PRICE_INR", 699),
        "vip_tiers": getattr(Config, "VIP_TIERS", {})
    })

@app.get("/api/contributions/recent")
async def api_recent_contributions(limit: int = Query(20, ge=1, le=50)):
    items = get_recent_contributions(limit=limit)
    return JSONResponse(content={"status": "success", "contributions": items})

@app.post("/api/security/verify-human")
async def api_verify_human_session(request: Request, payload: dict = Body(default={})):
    """
    Session-level Human Presence and Anti-Bot Verification Endpoint.
    Validates telemetry hold timing bounds and sets session cookie.
    """
    hold_duration_ms = payload.get("hold_duration_ms")
    if hold_duration_ms is not None:
        try:
            val = float(hold_duration_ms)
            if val < 800 or val > 5000:
                raise HTTPException(status_code=400, detail="Invalid verification telemetry duration.")
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail="Malformed telemetry parameters.")

    response = JSONResponse(content={"status": "success", "verified": True})
    response.set_cookie(
        key="almond_human_verified",
        value="1",
        httponly=False,
        samesite="lax",
        secure=request.url.scheme == "https"
    )
    return response

@app.post("/api/payment/create-order")
@app.post("/api/create-order")
async def api_create_order(payload: dict = Body(...)):
    token = str(payload.get("token", "") or "")
    user_id = str(payload.get("user_id", "") or "")
    if token:
        user_data = verify_session_token(token)
        if user_data:
            user_id = user_data.get("id") or user_data.get("user_id") or user_id
    currency = str(payload.get("currency", "INR") or "INR")
    receipt = payload.get("receipt")
    plan_name = str(payload.get("plan_name", "") or "")
    purchase_type = str(payload.get("purchase_type", "vip_pass") or "vip_pass")

    try:
        if payload.get("amount") is not None:
            amount_paise = int(payload.get("amount"))
        else:
            default_inr = Config.VIP_TEST_PRICE_INR if purchase_type == "vip_pass" else Config.PRICE_INR
            amount_inr = int(payload.get("amount_inr", default_inr))
            amount_paise = amount_inr * 100
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="Invalid payment amount.")

    if amount_paise < 100:
        raise HTTPException(status_code=400, detail="Minimum order amount is 100 paise (INR 1.00).")

    res = create_razorpay_order(
        user_id=user_id,
        amount_paise=amount_paise,
        currency=currency,
        receipt=receipt,
        plan_name=plan_name,
        purchase_type=purchase_type,
    )
    if res.get("status") == "error":
        raise HTTPException(status_code=res.get("http_status", 500), detail=res.get("message"))
    return JSONResponse(content=res)

@app.post("/api/payment/verify")
@app.post("/api/verify-payment")
async def api_verify_payment(payload: dict = Body(...)):
    token = str(payload.get("token", "") or "")
    user_id = str(payload.get("user_id", "") or "")
    if token:
        user_data = verify_session_token(token)
        if user_data:
            user_id = user_data.get("id") or user_data.get("user_id") or user_id
    order_id = str(payload.get("order_id") or payload.get("razorpay_order_id") or "").strip()
    payment_id = str(payload.get("payment_id") or payload.get("razorpay_payment_id") or "").strip()
    signature = str(payload.get("signature") or payload.get("razorpay_signature") or "").strip()
    plan_name = str(payload.get("plan_name", "") or "")
    purchase_type = str(payload.get("purchase_type", "vip_pass") or "vip_pass")

    try:
        if payload.get("amount_inr") is not None:
            amount_inr = int(payload.get("amount_inr"))
        elif payload.get("amount") is not None:
            amount_inr = int(int(payload.get("amount")) / 100)
        else:
            amount_inr = Config.PRICE_INR
    except (TypeError, ValueError):
        amount_inr = Config.PRICE_INR

    if not order_id or not payment_id or not signature:
        raise HTTPException(
            status_code=400,
            detail="Missing payment verification fields (razorpay_order_id, razorpay_payment_id, razorpay_signature).",
        )

    supporter_name = payload.get("supporter_name", "")
    supporter_message = payload.get("supporter_message", "")
    res = verify_razorpay_signature(
        user_id, order_id, payment_id, signature, amount_inr, plan_name,
        purchase_type=purchase_type,
        supporter_name=supporter_name,
        supporter_message=supporter_message
    )
    if res.get("status") == "error":
        raise HTTPException(status_code=res.get("http_status", 400), detail=res.get("message"))
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
        profile = {
            "name": "Direct Candidate",
            "role": preferences.get("role") or "Software Engineer / Professional",
            "skills": ["Software", "Engineering", "Python", "Problem Solving", "Cloud"],
            "yoe": 2
        }

    # Concurrency limiter to protect thread pool from simultaneous bot attacks
    if not acquire_search_slot():
        raise HTTPException(
            status_code=429, 
            detail="Platform is experiencing high query volume. Please try again in a few seconds."
        )

    try:
        user_is_paid = is_user_paid(user_id) if user_id else False
        cache_key = _get_skills_fingerprint(profile, preferences)

        ats_jobs = None
        linkedin_jobs = None
        founder_jobs = None

        with _API_SEARCH_CACHE_LOCK:
            cached = _API_SEARCH_CACHE.get(cache_key)
            if cached and (time.time() - cached.get("timestamp", 0) < _API_SEARCH_CACHE_TTL):
                cached_data = cached["data"]
                ats_jobs = [dict(j) for j in cached_data.get("ats_jobs", [])]
                linkedin_jobs = [dict(j) for j in cached_data.get("linkedin_jobs", [])]
                founder_jobs = [dict(j) for j in cached_data.get("founder_jobs", [])]

        if ats_jobs is None:
            result = search_matching_jobs(profile, preferences)
            ats_jobs = result.get("ats_jobs", [])
            linkedin_jobs = result.get("linkedin_jobs", [])

            founder_jobs = []
            try:
                founder_jobs = fetch_hn_founder_jobs(profile, preferences)
            except Exception as fe:
                print(f"[SEARCH] Founder direct fetch error: {fe}")

            with _API_SEARCH_CACHE_LOCK:
                _API_SEARCH_CACHE[cache_key] = {
                    "timestamp": time.time(),
                    "data": {
                        "ats_jobs": [dict(j) for j in ats_jobs],
                        "linkedin_jobs": [dict(j) for j in linkedin_jobs],
                        "founder_jobs": [dict(j) for j in founder_jobs]
                    }
                }

        # Latest feed gating (Today through 6 days ago requires active VIP Pass)
        apply_vip_latest_feed_lock(ats_jobs, user_is_paid=user_is_paid)
        apply_vip_latest_feed_lock(linkedin_jobs, user_is_paid=user_is_paid)
        apply_vip_latest_feed_lock(founder_jobs, user_is_paid=user_is_paid)

        return JSONResponse(content={
            "status": "success", 
            "total": len(ats_jobs), 
            "jobs": ats_jobs,
            "linkedin_jobs": linkedin_jobs,
            "founder_jobs": founder_jobs,
            "is_paid": user_is_paid,
            "price_inr": Config.PRICE_INR,
            "price_usd": Config.PRICE_USD,
            "vip_price_inr": getattr(Config, "VIP_PRICE_INR", 699)
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
        user_id = str(payload.get("user_id", "") or "")
        user_is_paid = is_user_paid(user_id) if user_id else False
        li_jobs, has_more, total_found = fetch_linkedin_postings(profile, preferences, limit=limit, offset=offset)
        li_jobs = [dict(j) for j in li_jobs]
        apply_vip_latest_feed_lock(li_jobs, user_is_paid=user_is_paid)
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
        user_id = str(payload.get("user_id", "") or "")
        user_is_paid = is_user_paid(user_id) if user_id else False
        founder_jobs = [dict(j) for j in fetch_hn_founder_jobs(profile, preferences)]
        apply_vip_latest_feed_lock(founder_jobs, user_is_paid=user_is_paid)
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

    # Determine entitlement: Free tier has latest 0-6d links locked with upgrade CTA
    user_paid = is_user_paid(user_id) if user_id else bool(payload.get("is_paid"))
    # Server-side guard: enforce VIP lock on export jobs if user is not paid
    jobs = apply_vip_latest_feed_lock([dict(x) for x in jobs], user_is_paid=user_paid)
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
    location: str = Query("all"),
    time_filter: str = Query("all"),
    sort_by: str = Query("latest"),
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
        location=location,
        time_filter=time_filter,
        sort_by=sort_by,
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
