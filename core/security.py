import time
import os
import re
import html
from collections import defaultdict
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

# =====================================================================
# 1. BOT SIGNATURES & REPUTATION SHIELD
# =====================================================================
KNOWN_MALICIOUS_BOTS = [
    "sqlmap", "nikto", "masscan", "zgrab", "gobuster", "dirbuster",
    "acunetix", "nessus", "nmap", "wpscan", "havij", "openvas",
    "fuzz", "hydra", "metasploit", "pangolin", "morfeus"
]

SUSPICIOUS_UA_PATTERNS = [
    r"^$",  # Empty user agent
    r"^[a-zA-Z0-9_\-\.]{1,4}$",  # Abnormally short 1-4 character strings
    r"python-requests/(?!.*\bAlmond\b)", # Bare python requests not customized
    r"curl/(?!.*\bAlmond\b)",
    r"wget/(?!.*\bAlmond\b)"
]

# =====================================================================
# 2. SLIDING-WINDOW IP RATE LIMITER
# =====================================================================
class SlidingWindowRateLimiter:
    def __init__(self):
        # Maps client_ip -> list of request timestamps
        self.ip_history = defaultdict(list)
        # Limits: (max_requests, window_seconds)
        self.endpoint_limits = {
            "/api/find-jobs": (10, 60),          # Max 10 job searches / min (heavy I/O)
            "/api/find-linkedin-jobs": (10, 60), # Max 10 searches / min
            "/api/upload-resume": (6, 60),       # Max 6 uploads / min
            "/api/auth/signup": (5, 60),         # Max 5 signups / min (anti-bruteforce)
            "/api/auth/login": (10, 60),         # Max 10 login attempts / min
            "/api/payment/create-order": (10, 60),
            "/api/security/verify-human": (30, 60),
            "DEFAULT": (60, 60)                  # Max 60 general requests / min
        }
        self.cleanup_interval = 300
        self.last_cleanup = time.time()

    def get_client_ip(self, request: Request) -> str:
        # Check forward headers if behind reverse proxy/Cloudflare
        cf_ip = request.headers.get("cf-connecting-ip")
        if cf_ip:
            return cf_ip.strip()
        xfwd = request.headers.get("x-forwarded-for")
        if xfwd:
            return xfwd.split(",")[0].strip()
        return request.client.host if request.client else "127.0.0.1"

    def is_allowed(self, client_ip: str, path: str) -> tuple[bool, int]:
        now = time.time()
        
        # Periodic cleanup of expired records every 5 minutes
        if now - self.last_cleanup > self.cleanup_interval:
            self._cleanup(now)

        limit, window = self.endpoint_limits.get(path, self.endpoint_limits["DEFAULT"])
        timestamps = self.ip_history[f"{client_ip}:{path}"]

        # Keep timestamps within the sliding window
        valid_timestamps = [t for t in timestamps if now - t < window]
        self.ip_history[f"{client_ip}:{path}"] = valid_timestamps

        if len(valid_timestamps) >= limit:
            retry_after = int(window - (now - valid_timestamps[0])) + 1
            return False, max(retry_after, 1)

        valid_timestamps.append(now)
        return True, 0

    def _cleanup(self, now: float):
        keys_to_delete = []
        for key, timestamps in self.ip_history.items():
            valid = [t for t in timestamps if now - t < 120]
            if not valid:
                keys_to_delete.append(key)
            else:
                self.ip_history[key] = valid
        for k in keys_to_delete:
            del self.ip_history[k]
        self.last_cleanup = now

rate_limiter = SlidingWindowRateLimiter()

# =====================================================================
# 3. GLOBAL CONCURRENCY SEMAPHORE
# =====================================================================
# Protects worker threads from starvation when bots hit search simultaneously
CURRENT_SEARCH_WORKERS = 0
MAX_CONCURRENT_SEARCHES = 4

def acquire_search_slot() -> bool:
    global CURRENT_SEARCH_WORKERS
    if CURRENT_SEARCH_WORKERS >= MAX_CONCURRENT_SEARCHES:
        return False
    CURRENT_SEARCH_WORKERS += 1
    return True

def release_search_slot():
    global CURRENT_SEARCH_WORKERS
    if CURRENT_SEARCH_WORKERS > 0:
        CURRENT_SEARCH_WORKERS -= 1

# =====================================================================
# 4. BOT SHIELD & RATE LIMITING MIDDLEWARE
# =====================================================================
class BotShieldMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        client_ip = rate_limiter.get_client_ip(request)
        ua = (request.headers.get("user-agent") or "").strip().lower()
        path = request.url.path

        # 1. Block Known Automated Attack Tools
        if any(bot in ua for bot in KNOWN_MALICIOUS_BOTS):
            return JSONResponse(
                status_code=403,
                content={
                    "error": "Forbidden",
                    "message": "Automated security scanning tools are prohibited by Almond AI Shield."
                }
            )

        # 2. Block Suspicious / Empty User Agents on API endpoints
        if path.startswith("/api/"):
            if not ua or any(re.search(pat, ua) for pat in SUSPICIOUS_UA_PATTERNS):
                # Exempt local development tests
                if client_ip not in ["127.0.0.1", "localhost", "::1"]:
                    return JSONResponse(
                        status_code=403,
                        content={
                            "error": "Access Denied",
                            "message": "Valid browser User-Agent header required."
                        }
                    )

        # 3. Rate Limiting Check
        allowed, retry_after = rate_limiter.is_allowed(client_ip, path)
        if not allowed:
            return JSONResponse(
                status_code=429,
                headers={"Retry-After": str(retry_after)},
                content={
                    "error": "Too Many Requests",
                    "message": f"Rate limit exceeded. Too many concurrent requests from your IP. Please wait {retry_after}s.",
                    "retry_after_seconds": retry_after
                }
            )

        # Process request
        response = await call_next(request)

        # 4. Inject Enterprise Security Headers (OWASP Hardening)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["X-Almond-Shield"] = "Active-Protected"

        return response

# =====================================================================
# 5. SECURE FILE UPLOAD VALIDATOR
# =====================================================================
MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB maximum size

def validate_uploaded_file(file, raw_bytes: bytes) -> str:
    """
    Validates file size, sanitizes filename against path traversal,
    and checks for valid document magic bytes.
    """
    if len(raw_bytes) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413, 
            detail="Payload Too Large. Resume file exceeds 10MB maximum limit."
        )

    # Sanitize filename against Directory Traversal (e.g., ../../../etc/passwd)
    safe_filename = os.path.basename(file.filename or "resume.pdf")
    safe_filename = re.sub(r'[^a-zA-Z0-9_\-\. ]', '_', safe_filename)

    ext = os.path.splitext(safe_filename)[1].lower()
    if ext not in [".pdf", ".docx", ".doc", ".txt"]:
        raise HTTPException(
            status_code=400, 
            detail="Unsupported file extension. Only PDF, DOCX, and TXT are accepted."
        )

    # Magic Bytes Validation
    if ext == ".pdf":
        if not raw_bytes.startswith(b"%PDF-"):
            raise HTTPException(status_code=400, detail="Corrupted or invalid PDF header structure.")
    elif ext in [".docx", ".doc"]:
        # ZIP magic bytes PK\x03\x04 for .docx or OLE CFB for .doc
        if not (raw_bytes.startswith(b"PK\x03\x04") or raw_bytes.startswith(b"\xd0\xcf\x11\xe0")):
            raise HTTPException(status_code=400, detail="Corrupted or invalid Word document header structure.")

    return safe_filename

# =====================================================================
# 6. SAFE HTML ESCAPING FOR DOCUMENT EXPORTS
# =====================================================================
def sanitize_text(text: str) -> str:
    """Escapes user input before injecting into PDF/HTML rendering templates."""
    if not text:
        return ""
    return html.escape(str(text).strip())
