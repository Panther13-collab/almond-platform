import re
import os
import sqlite3
import hashlib
import hmac
import secrets
import time
import uuid
from core.config import Config

# Data directory and SQLite DB path
DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
os.makedirs(DATA_DIR, exist_ok=True)
DB_PATH = os.path.join(DATA_DIR, "almond_auth.db")

AUTH_SECRET_KEY = getattr(Config, "AUTH_SECRET_KEY", "almond_direct_ats_secret_key_2026")

# In-memory mock store kept for legacy compatibility
MOCK_USERS = {}
MOCK_PAYMENTS = {}

supabase_client = None
supabase_admin = None

if Config.is_supabase_configured():
    try:
        from supabase import create_client, Client
        supabase_client: Client = create_client(Config.SUPABASE_URL, Config.SUPABASE_ANON_KEY)
        if Config.SUPABASE_SERVICE_ROLE_KEY:
            supabase_admin: Client = create_client(Config.SUPABASE_URL, Config.SUPABASE_SERVICE_ROLE_KEY)
        else:
            supabase_admin = supabase_client
        print(f"[AUTH_DB] Successfully connected to live Supabase project ({Config.SUPABASE_URL})")
    except Exception as e:
        print(f"[AUTH_DB] Warning: Could not initialize Supabase client: {e}")
        supabase_client = None
        supabase_admin = None
else:
    print("[AUTH_DB] Notice: Running with local persistent SQLite storage. Supabase keys not provided.")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize local SQLite database for bulletproof offline & fast authentication."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                full_name TEXT,
                is_paid INTEGER DEFAULT 0,
                plan TEXT DEFAULT 'free',
                paid_until REAL DEFAULT 0,
                created_at REAL,
                updated_at REAL,
                auth_provider TEXT DEFAULT 'email'
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                payment_id TEXT UNIQUE,
                order_id TEXT,
                amount_inr REAL,
                plan_name TEXT,
                status TEXT,
                created_at REAL,
                FOREIGN KEY (user_id) REFERENCES users (id)
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS candidate_applications (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                job_id TEXT NOT NULL,
                company TEXT NOT NULL,
                role TEXT NOT NULL,
                status TEXT NOT NULL,
                url TEXT,
                applied_at REAL,
                updated_at REAL,
                notes TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS email_otps (
                email TEXT PRIMARY KEY,
                otp_code TEXT NOT NULL,
                expires_at REAL NOT NULL,
                attempts INTEGER DEFAULT 0
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS site_traffic (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                path TEXT NOT NULL,
                visitor_hash TEXT NOT NULL,
                device TEXT DEFAULT 'desktop',
                device_model TEXT DEFAULT '',
                device_brand TEXT DEFAULT '',
                is_bot INTEGER DEFAULT 0,
                referrer TEXT DEFAULT '',
                timestamp REAL NOT NULL
            );
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users (email);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_payments_user_id ON payments (user_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_cand_apps_user ON candidate_applications (user_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_traffic_date ON site_traffic (date);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_traffic_path ON site_traffic (path);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_traffic_visitor ON site_traffic (visitor_hash);")
        
        # Auto-migrate existing database tables if columns are missing
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN paid_until REAL DEFAULT 0;")
        except Exception:
            pass
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN auth_provider TEXT DEFAULT 'email';")
        except Exception:
            pass
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN device_model TEXT DEFAULT '';")
        except Exception:
            pass
        try:
            cursor.execute("ALTER TABLE site_traffic ADD COLUMN is_bot INTEGER DEFAULT 0;")
        except Exception:
            pass
        try:
            cursor.execute("ALTER TABLE site_traffic ADD COLUMN device_model TEXT DEFAULT '';")
        except Exception:
            pass
        try:
            cursor.execute("ALTER TABLE site_traffic ADD COLUMN device_brand TEXT DEFAULT '';")
        except Exception:
            pass
        try:
            cursor.execute("ALTER TABLE payments ADD COLUMN plan_name TEXT DEFAULT '';")
        except Exception:
            pass

        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_traffic_is_bot ON site_traffic (is_bot);")
        except Exception:
            pass

        # Retroactively classify historical vulnerability scanner and bot probes
        try:
            cursor.execute("""
                UPDATE site_traffic 
                SET is_bot = 1 
                WHERE is_bot = 0 AND (
                    path LIKE '%.php%' OR 
                    path LIKE '%wp-%' OR 
                    path LIKE '%xmlrpc%' OR 
                    path LIKE '%phpmyadmin%' OR 
                    path LIKE '%.env%' OR 
                    path LIKE '%.git%' OR
                    path LIKE '%cgi-bin%' OR
                    path LIKE '%boaform%'
                );
            """)
        except Exception:
            pass

        conn.commit()

# Run initialization at import
init_db()

def _hash_password(password: str, salt: str = None) -> tuple:
    if not salt:
        salt = secrets.token_hex(16)
    pw_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000).hex()
    return pw_hash, salt

def _create_token(user_id: str, email: str) -> str:
    timestamp = str(int(time.time()))
    data = f"{user_id}:{email}:{timestamp}"
    signature = hmac.new(AUTH_SECRET_KEY.encode("utf-8"), data.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"alm.{user_id}.{timestamp}.{signature}"

def _format_remaining_str(is_paid: bool, paid_until: float, now: float) -> str:
    if not (is_paid and paid_until > now):
        return ""
    diff = paid_until - now
    if diff < 86400:
        hours = max(1, int(diff / 3600))
        return f"{hours}h left"
    days = int(diff / 86400)
    return f"{days}d left"

def _lookup_supabase_user_meta(user_id: str, email: str = "") -> dict:
    """Best-effort lookup in Supabase Admin so ephemeral SQLite restarts preserve accounts and VIP state."""
    if not supabase_admin:
        return {}
    clean_email = (email or "").strip().lower()
    try:
        resp = supabase_admin.auth.admin.get_user_by_id(user_id)
        u = getattr(resp, "user", None)
        if u and getattr(u, "email", ""):
            meta = getattr(u, "user_metadata", None) or {}
            return {"email": u.email.strip().lower(), "meta": meta, "supa_id": u.id}
    except Exception:
        pass
    if clean_email:
        try:
            users_list = supabase_admin.auth.admin.list_users()
            for u in users_list or []:
                u_email = (getattr(u, "email", "") or "").strip().lower()
                if u_email == clean_email:
                    meta = getattr(u, "user_metadata", None) or {}
                    if meta.get("local_user_id") == user_id or getattr(u, "id", "") == user_id:
                        return {"email": u_email, "meta": meta, "supa_id": u.id}
        except Exception:
            pass
    return {}

def _rehydrate_user_row(user_id: str, email: str, full_name: str = "", supa_meta: dict = None) -> dict:
    """Re-insert an already-verified candidate into local SQLite after an ephemeral container restart."""
    now = time.time()
    clean_email = (email or "").strip().lower()
    meta = supa_meta or {}
    name_val = (meta.get("full_name") or full_name or clean_email.split("@")[0]).strip()
    is_paid = 1 if meta.get("is_paid") else 0
    plan = meta.get("plan") or ("vip_pass_30d" if is_paid else "free")
    paid_until = float(meta.get("paid_until") or 0)
    pw_hash, salt = _hash_password(secrets.token_urlsafe(24))

    with get_db() as conn:
        cursor = conn.cursor()
        # Recover payment status from SQLite payments if present
        if not is_paid:
            cursor.execute(
                "SELECT plan_name, created_at FROM payments WHERE user_id = ? AND status = 'captured' ORDER BY created_at DESC LIMIT 1",
                (user_id,)
            )
            prow = cursor.fetchone()
            if prow:
                is_paid = 1
                plan = prow["plan_name"] or "vip_pass_30d"
                paid_until = float(prow["created_at"] or now) + (30 * 86400)

        cursor.execute(
            """
            INSERT OR IGNORE INTO users (id, email, password_hash, salt, full_name, is_paid, plan, paid_until, created_at, updated_at, auth_provider)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'session_rehydrated')
            """,
            (user_id, clean_email, pw_hash, salt, name_val, is_paid, plan, paid_until, now, now)
        )
        conn.commit()
        cursor.execute("SELECT id, email, full_name, is_paid, plan, paid_until, created_at FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        if not row:
            cursor.execute("SELECT id, email, full_name, is_paid, plan, paid_until, created_at FROM users WHERE email = ?", (clean_email,))
            row = cursor.fetchone()
        if not row:
            return None
        row_paid_until = row["paid_until"] or 0
        row_is_paid = bool(row["is_paid"]) and (row_paid_until == 0 or row_paid_until > now)
        return {
            "id": row["id"],
            "user_id": row["id"],
            "email": row["email"],
            "full_name": row["full_name"] or name_val,
            "is_paid": row_is_paid,
            "plan": row["plan"],
            "paid_until": row_paid_until,
            "remaining_str": _format_remaining_str(row_is_paid, row_paid_until, now),
            "created_at": row["created_at"]
        }

def recover_verified_session(user_id: str, email: str = "", full_name: str = "") -> dict:
    """Recover session when client holds user_id+email present in SQLite or Supabase (e.g. after ephemeral reset)."""
    clean_email = (email or "").strip().lower()
    if not user_id:
        return None
    prof = get_user_profile(user_id)
    if prof and (not clean_email or prof.get("email", "").lower() == clean_email):
        return {
            "id": prof["user_id"],
            "user_id": prof["user_id"],
            "email": prof["email"],
            "full_name": prof["full_name"],
            "is_paid": prof["is_paid"],
            "plan": prof["plan"],
            "paid_until": prof["paid_until"],
            "remaining_str": prof["remaining_str"],
            "token": _create_token(prof["user_id"], prof["email"])
        }
    supa = _lookup_supabase_user_meta(user_id, clean_email)
    if supa and supa.get("email"):
        rehydrated = _rehydrate_user_row(user_id, supa["email"], full_name=full_name, supa_meta=supa.get("meta"))
        if rehydrated:
            rehydrated["token"] = _create_token(rehydrated["user_id"], rehydrated["email"])
            return rehydrated
    return None

def verify_session_token(token: str, email: str = "", full_name: str = "") -> dict:
    if not token or not token.startswith("alm."):
        return None
    try:
        parts = token.split(".")
        if len(parts) != 4:
            return None
        _, user_id, timestamp, sig = parts
        
        # Check token expiration (30 days validity)
        if time.time() - int(timestamp) > 30 * 86400:
            return None
            
        # Verify HMAC signature against SQLite first
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, email, full_name, is_paid, plan, paid_until, created_at FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            if row:
                data = f"{user_id}:{row['email']}:{timestamp}"
                expected_sig = hmac.new(AUTH_SECRET_KEY.encode("utf-8"), data.encode("utf-8"), hashlib.sha256).hexdigest()
                if not hmac.compare_digest(sig, expected_sig):
                    return None
                
                now = time.time()
                paid_until = row["paid_until"] or 0
                is_paid = bool(row["is_paid"]) and (paid_until == 0 or paid_until > now)

                return {
                    "id": row["id"],
                    "user_id": row["id"],
                    "email": row["email"],
                    "full_name": row["full_name"],
                    "is_paid": is_paid,
                    "plan": row["plan"],
                    "paid_until": paid_until,
                    "remaining_str": _format_remaining_str(is_paid, paid_until, now),
                    "created_at": row["created_at"]
                }

        # Fallback when ephemeral SQLite restarted: verify cryptographic HMAC directly via email / Supabase
        supa = _lookup_supabase_user_meta(user_id, email)
        clean_email = (email or supa.get("email") or "").strip().lower()
        if not clean_email:
            return None
        data = f"{user_id}:{clean_email}:{timestamp}"
        expected_sig = hmac.new(AUTH_SECRET_KEY.encode("utf-8"), data.encode("utf-8"), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected_sig):
            return None
        return _rehydrate_user_row(user_id, clean_email, full_name=full_name, supa_meta=supa.get("meta"))
    except Exception as e:
        print(f"[AUTH_DB] Token verification note: {e}")
        return None


EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")

# Known disposable and temporary email domains
DISPOSABLE_EMAIL_DOMAINS = {
    "mailinator.com", "tempmail.com", "10minutemail.com", "guerrillamail.com",
    "throwawaymail.com", "yopmail.com", "trashmail.com", "getnada.com",
    "dispostable.com", "sharklasers.com", "guerrillamailblock.com",
    "fakemailgenerator.com", "temp-mail.org", "maildrop.cc", "inboxkitten.com",
    "mohmal.com", "burnermail.io", "trashmail.net", "crazymailing.com",
    "emailondeck.com", "generator.email", "temporary-mail.net", "nada.ltd"
}

# Generic dummy usernames
DUMMY_EMAIL_USERNAMES = {
    "test", "demo", "sample", "fake", "dummy", "temp", "asdf", "qwer", "zxcv",
    "noreply", "abc", "xyz", "admin", "null", "undefined", "aaaa", "bbbb", "cccc", "dddd"
}

def is_valid_candidate_email(email: str) -> tuple:
    """
    Strict email validation:
    - Blocks disposable / temporary mail services
    - Blocks repeating character dummy addresses (e.g. aaaa@gmail.com, bbbb@gmail.com)
    - Blocks placeholder usernames (e.g. test@, dummy@, asdf@)
    - Validates standard domain structure
    """
    clean = (email or "").strip().lower()
    if not clean or "@" not in clean:
        return False, "Please enter a valid personal email address."
    
    parts = clean.split("@")
    if len(parts) != 2:
        return False, "Please enter a valid email address."
    
    username, domain = parts[0], parts[1]
    
    if len(username) < 3:
        return False, "Email username must be at least 3 characters long."
    
    # Check domain format
    if "." not in domain or domain.startswith(".") or domain.endswith("."):
        return False, "Please enter a valid email domain (e.g. gmail.com, outlook.com)."
    
    tld = domain.split(".")[-1]
    if len(tld) < 2 or not tld.isalpha():
        return False, "Invalid email domain extension."
        
    # Block disposable email services
    if domain in DISPOSABLE_EMAIL_DOMAINS:
        return False, "Temporary and disposable email addresses are not permitted. Please use a permanent email address."
        
    # Block single repeated character dummy emails (e.g. aaaa@, bbbb@, 1111@)
    if len(set(username)) == 1 and len(username) >= 3:
        return False, "Test or repeating character email addresses (e.g. aaaa@, bbbb@) are not accepted."
        
    # Block common dummy usernames
    if username in DUMMY_EMAIL_USERNAMES:
        return False, "Generic placeholder usernames are not accepted. Please use your personal or work email."
        
    # Standard format check
    if not EMAIL_REGEX.match(clean):
        return False, "Please enter a valid email address format."
        
    return True, ""

def send_signup_otp(email: str) -> dict:
    """Validate email format and dispatch a secure 6-digit OTP code for candidate verification."""
    clean_email = (email or "").strip().lower()
    
    # Strict email validation
    is_valid, err_msg = is_valid_candidate_email(clean_email)
    if not is_valid:
        return {
            "status": "error",
            "message": err_msg
        }

    # Check if user already exists
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE email = ?", (clean_email,))
        if cursor.fetchone():
            return {
                "status": "error",
                "message": "An account with this email already exists. Please log in directly."
            }

        otp_code = f"{secrets.randbelow(900000) + 100000}"
        expires_at = time.time() + 600 # 10 minutes

        cursor.execute("""
            INSERT INTO email_otps (email, otp_code, expires_at, attempts)
            VALUES (?, ?, ?, 0)
            ON CONFLICT(email) DO UPDATE SET
                otp_code = excluded.otp_code,
                expires_at = excluded.expires_at,
                attempts = 0
        """, (clean_email, otp_code, expires_at))
        conn.commit()

    print(f"\n=======================================================")
    print(f"[AUTH_OTP] DISPATCHING VERIFICATION CODE TO {clean_email}")
    print(f"=======================================================\n")

    # Live email delivery via SMTP (Gmail, Resend, Brevo, SendGrid)
    from core.email_sender import send_otp_email
    email_delivery = send_otp_email(clean_email, otp_code)

    # Strictly require real email delivery — Never expose OTP to the frontend
    if not email_delivery.get("delivered"):
        # Delete un-delivered OTP from database so no orphaned codes exist
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM email_otps WHERE email = ?", (clean_email,))
            conn.commit()
            
        delivery_err = email_delivery.get("error", "")
        print(f"[AUTH_OTP] FAILED TO DISPATCH EMAIL TO {clean_email}: {delivery_err}")
        return {
            "status": "error",
            "message": "We could not deliver a verification email to this address. Please ensure your email is active and typed correctly, or configure SMTP credentials on your host."
        }

    return {
        "status": "success",
        "message": f"A 6-digit verification code has been dispatched to {clean_email}. Please check your inbox and spam folder.",
        "email": clean_email
    }

def verify_otp_and_signup(email: str, otp_code: str, password: str, full_name: str = "", device_model: str = "") -> dict:
    """Verify submitted 6-digit OTP code and create candidate account with device model logging."""
    clean_email = email.strip().lower()
    clean_otp = str(otp_code).strip()

    is_valid, err_msg = is_valid_candidate_email(clean_email)
    if not is_valid:
        return {"status": "error", "message": err_msg}
    if not clean_otp or len(clean_otp) != 6:
        return {"status": "error", "message": "Please enter the full 6-digit verification code."}
    if not password or len(password) < 6:
        return {"status": "error", "message": "Password must be at least 6 characters long."}

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT otp_code, expires_at, attempts FROM email_otps WHERE email = ?", (clean_email,))
        row = cursor.fetchone()

        if not row:
            return {
                "status": "error",
                "message": "No active verification code found for this email. Please request a new code."
            }

        stored_otp = row["otp_code"]
        expires_at = row["expires_at"]
        attempts = row["attempts"]

        now = time.time()
        if now > expires_at:
            cursor.execute("DELETE FROM email_otps WHERE email = ?", (clean_email,))
            conn.commit()
            return {
                "status": "error",
                "message": "Verification code has expired. Please request a new code."
            }

        if attempts >= 5:
            cursor.execute("DELETE FROM email_otps WHERE email = ?", (clean_email,))
            conn.commit()
            return {
                "status": "error",
                "message": "Too many incorrect attempts. Please request a new code."
            }

        if clean_otp != stored_otp:
            cursor.execute("UPDATE email_otps SET attempts = attempts + 1 WHERE email = ?", (clean_email,))
            conn.commit()
            return {
                "status": "error",
                "message": "Incorrect verification code. Please check your email and try again."
            }

        # Code matches! Delete the OTP
        cursor.execute("DELETE FROM email_otps WHERE email = ?", (clean_email,))
        conn.commit()

    # Now create account with hardware device info
    return signup_user(clean_email, password, full_name, device_model=device_model)

def signup_user(email: str, password: str, full_name: str = "", device_model: str = "") -> dict:
    """Sign up a new candidate user into persistent SQLite and sync with Supabase, capturing hardware device model."""
    clean_email = email.strip().lower()
    if not clean_email or "@" not in clean_email:
        return {"status": "error", "message": "Please provide a valid email address."}
    if not password or len(password) < 6:
        return {"status": "error", "message": "Password must be at least 6 characters long."}

    user_id = str(uuid.uuid4())
    pw_hash, salt = _hash_password(password)
    now = time.time()
    clean_device = (device_model or "").strip()

    # 1. Insert into local persistent SQLite DB
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO users (id, email, password_hash, salt, full_name, is_paid, plan, paid_until, created_at, updated_at, auth_provider, device_model)
                VALUES (?, ?, ?, ?, ?, 0, 'free', 0, ?, ?, 'email', ?)
                """,
                (user_id, clean_email, pw_hash, salt, full_name.strip(), now, now, clean_device)
            )
            conn.commit()
    except sqlite3.IntegrityError:
        return {"status": "error", "message": "An account with this email already exists. Please log in."}
    except Exception as e:
        return {"status": "error", "message": f"Database error: {str(e)}"}

    # 2. Mirror into Supabase Auth with auto email confirmation (ZERO transactional emails sent, preventing bounces)
    if supabase_admin:
        try:
            supabase_admin.auth.admin.create_user({
                "email": clean_email,
                "password": password,
                "email_confirm": True,
                "user_metadata": {
                    "full_name": full_name.strip(),
                    "is_paid": False,
                    "local_user_id": user_id,
                    "device_model": clean_device
                }
            })
        except Exception as e:
            print(f"[AUTH_DB] Supabase admin create_user note: {e}")

    # Generate session token
    token = _create_token(user_id, clean_email)

    return {
        "status": "success",
        "user_id": user_id,
        "email": clean_email,
        "full_name": full_name.strip() or clean_email.split("@")[0],
        "is_paid": False,
        "plan": "free",
        "device_model": clean_device,
        "token": token
    }

def login_user(email: str, password: str, device_model: str = "") -> dict:
    """Authenticate an existing user via SQLite credentials and record current device model."""
    clean_email = email.strip().lower()
    if not clean_email or not password:
        return {"status": "error", "message": "Email and password are required."}

    clean_device = (device_model or "").strip()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, email, password_hash, salt, full_name, is_paid, plan, paid_until, COALESCE(device_model, '') as device_model FROM users WHERE email = ?", (clean_email,))
        row = cursor.fetchone()
        
        if not row:
            return {"status": "error", "message": "No account found with this email. Please sign up."}
            
        expected_hash, _ = _hash_password(password, row["salt"])
        if not hmac.compare_digest(row["password_hash"], expected_hash):
            return {"status": "error", "message": "Incorrect password. Please verify and try again."}

        user_id = row["id"]
        now = time.time()
        
        # Update device model if provided
        active_device = clean_device or row["device_model"]
        if clean_device:
            try:
                cursor.execute("UPDATE users SET device_model = ?, updated_at = ? WHERE id = ?", (clean_device, now, user_id))
                conn.commit()
            except Exception:
                pass
            if supabase_admin:
                try:
                    supabase_admin.auth.admin.update_user_by_id(user_id, {"user_metadata": {"device_model": clean_device}})
                except Exception:
                    pass

        token = _create_token(user_id, row["email"])

        paid_until = row["paid_until"] or 0
        is_paid = bool(row["is_paid"]) and (paid_until == 0 or paid_until > now)

        remaining_str = ""
        if is_paid and paid_until > now:
            diff = paid_until - now
            if diff < 86400:
                hours = max(1, int(diff / 3600))
                remaining_str = f"{hours}h left"
            else:
                days = int(diff / 86400)
                remaining_str = f"{days}d left"

        return {
            "status": "success",
            "user_id": user_id,
            "email": row["email"],
            "full_name": row["full_name"] or row["email"].split("@")[0],
            "is_paid": is_paid,
            "plan": row["plan"],
            "paid_until": paid_until,
            "remaining_str": remaining_str,
            "device_model": active_device,
            "token": token
        }

def login_or_signup_google_user(email: str, full_name: str = "", google_id: str = "", device_model: str = "") -> dict:
    """
    Authenticate or register a candidate verified via Google Sign-In.
    Bypasses manual OTP verification since Google guarantees email authenticity.
    Captures exact hardware device used for candidate onboarding.
    """
    clean_email = (email or "").strip().lower()
    if not clean_email or "@" not in clean_email:
        return {"status": "error", "message": "Invalid Google email address."}

    is_valid, err_msg = is_valid_candidate_email(clean_email)
    if not is_valid:
        return {"status": "error", "message": err_msg}

    now = time.time()
    clean_device = (device_model or "").strip()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, email, full_name, is_paid, plan, paid_until, COALESCE(device_model, '') as device_model FROM users WHERE email = ?", (clean_email,))
        row = cursor.fetchone()

        if row:
            user_id = row["id"]
            active_device = clean_device or row["device_model"]
            try:
                if clean_device:
                    cursor.execute("UPDATE users SET auth_provider = 'google', device_model = ?, updated_at = ? WHERE id = ?", (clean_device, now, user_id))
                else:
                    cursor.execute("UPDATE users SET auth_provider = 'google', updated_at = ? WHERE id = ?", (now, user_id))
                conn.commit()
            except Exception:
                pass

            if supabase_admin and clean_device:
                try:
                    supabase_admin.auth.admin.update_user_by_id(user_id, {"user_metadata": {"device_model": clean_device}})
                except Exception:
                    pass

            token = _create_token(user_id, row["email"])
            paid_until = row["paid_until"] or 0
            is_paid = bool(row["is_paid"]) and (paid_until == 0 or paid_until > now)

            remaining_str = ""
            if is_paid and paid_until > now:
                diff = paid_until - now
                if diff < 86400:
                    hours = max(1, int(diff / 3600))
                    remaining_str = f"{hours}h left"
                else:
                    days = int(diff / 86400)
                    remaining_str = f"{days}d left"

            return {
                "status": "success",
                "user_id": user_id,
                "email": row["email"],
                "full_name": row["full_name"] or full_name or clean_email.split("@")[0],
                "is_paid": is_paid,
                "plan": row["plan"],
                "paid_until": paid_until,
                "remaining_str": remaining_str,
                "device_model": active_device,
                "token": token
            }
        else:
            user_id = str(uuid.uuid4())
            rand_password = secrets.token_urlsafe(32)
            pw_hash, salt = _hash_password(rand_password)
            name_val = full_name.strip() or clean_email.split("@")[0]

            cursor.execute(
                """
                INSERT INTO users (id, email, password_hash, salt, full_name, is_paid, plan, paid_until, created_at, updated_at, auth_provider, device_model)
                VALUES (?, ?, ?, ?, ?, 0, 'free', 0, ?, ?, 'google', ?)
                """,
                (user_id, clean_email, pw_hash, salt, name_val, now, now, clean_device)
            )
            conn.commit()

            if supabase_admin:
                try:
                    supabase_admin.auth.admin.create_user({
                        "email": clean_email,
                        "password": rand_password,
                        "email_confirm": True,
                        "user_metadata": {
                            "full_name": name_val,
                            "google_id": google_id,
                            "is_paid": False,
                            "local_user_id": user_id,
                            "device_model": clean_device
                        }
                    })
                except Exception as e:
                    print(f"[AUTH_DB] Supabase Google mirror note: {e}")

            token = _create_token(user_id, clean_email)
            return {
                "status": "success",
                "user_id": user_id,
                "email": clean_email,
                "full_name": name_val,
                "is_paid": False,
                "plan": "free",
                "device_model": clean_device,
                "token": token
            }

            token = _create_token(user_id, clean_email)
            return {
                "status": "success",
                "user_id": user_id,
                "email": clean_email,
                "full_name": name_val,
                "is_paid": False,
                "plan": "free",
                "token": token
            }

def get_user_profile(user_id: str) -> dict:
    """Retrieve full candidate profile details by user ID with active expiration calculation."""
    if not user_id:
        return None
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, email, full_name, is_paid, plan, paid_until, created_at FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        if not row:
            return None

        now = time.time()
        paid_until = row["paid_until"] or 0
        is_paid = bool(row["is_paid"]) and (paid_until == 0 or paid_until > now)

        # Check expiration
        if bool(row["is_paid"]) and paid_until > 0 and paid_until <= now:
            cursor.execute("UPDATE users SET is_paid = 0 WHERE id = ?", (user_id,))
            conn.commit()
            is_paid = False

        remaining_str = ""
        if is_paid and paid_until > now:
            diff = paid_until - now
            if diff < 86400:
                hours = max(1, int(diff / 3600))
                remaining_str = f"{hours}h left"
            else:
                days = int(diff / 86400)
                remaining_str = f"{days}d left"

        return {
            "user_id": row["id"],
            "email": row["email"],
            "full_name": row["full_name"] or row["email"].split("@")[0],
            "is_paid": is_paid,
            "plan": row["plan"],
            "paid_until": paid_until,
            "remaining_str": remaining_str,
            "created_at": row["created_at"]
        }

def is_user_paid(user_id: str) -> bool:
    """Check if the user has an active Pro/VIP subscription within valid timestamp bounds."""
    if not user_id:
        return False

    now = time.time()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT is_paid, paid_until FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        if row and row["is_paid"] == 1:
            paid_until = row["paid_until"] or 0
            if paid_until == 0 or paid_until > now:
                return True
            else:
                # Expired: Auto-revert
                cursor.execute("UPDATE users SET is_paid = 0 WHERE id = ?", (user_id,))
                conn.commit()
                return False

        # Also allow guest candidate sessions that completed a verified VIP checkout
        cursor.execute(
            """
            SELECT 1 FROM payments
            WHERE user_id = ? AND status = 'captured' AND created_at > ?
            LIMIT 1
            """,
            (user_id, now - (30 * 86400))
        )
        if cursor.fetchone():
            return True

    return False


def record_contribution_payment(user_id: str, payment_id: str, order_id: str, amount_inr: float, plan_name: str = "Coffee Contribution") -> bool:
    """Record a voluntary supporter contribution without granting VIP Pass access."""
    now = time.time()
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            pay_id = f"tip_{secrets.token_hex(6)}"
            cursor.execute(
                """
                INSERT OR REPLACE INTO payments (id, user_id, payment_id, order_id, amount_inr, plan_name, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, 'contribution', ?)
                """,
                (pay_id, user_id or "guest", payment_id, order_id, amount_inr, plan_name or "Coffee Contribution", now)
            )
            conn.commit()
            print(f"[AUTH_DB] Recorded voluntary contribution {amount_inr} INR for user {user_id or 'guest'}.")
        return True
    except Exception as e:
        print(f"[AUTH_DB] Error recording contribution: {e}")
        return False

def record_successful_payment(user_id: str, payment_id: str, order_id: str, amount_inr: float, plan_name: str = "") -> bool:
    """Record a captured payment with strict timestamp-based expiration (24h Day Sprint, 30d, or 90d)."""
    now = time.time()
    plan_lower = (plan_name or "").lower()

    # Time-bound plan calculation:
    # 1. Day Sprint: 24 Hours
    # 2. 90-Day Mastery: 90 Days
    # 3. 30-Day Pro Hunt: 30 Days (Default)
    if "vip" in plan_lower:
        duration_seconds = 30 * 86400 # 30 days VIP Pass
        plan_code = "vip_pass_30d"
    elif "day" in plan_lower or "24" in plan_lower or amount_inr <= 200:
        duration_seconds = 24 * 3600 # 24 hours
        plan_code = "day_sprint_24h"
    elif "90" in plan_lower or "mastery" in plan_lower or "3-month" in plan_lower or amount_inr > 700:
        duration_seconds = 90 * 86400 # 90 days
        plan_code = "mastery_90d"
    else:
        duration_seconds = 30 * 86400 # 30 days
        plan_code = "pro_hunt_30d"

    paid_until = now + duration_seconds
    
    # 1. Update SQLite
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE users SET is_paid = 1, plan = ?, paid_until = ?, updated_at = ?
                WHERE id = ?
                """,
                (plan_code, paid_until, now, user_id)
            )
            pay_id = f"txn_{secrets.token_hex(6)}"
            cursor.execute(
                """
                INSERT OR REPLACE INTO payments (id, user_id, payment_id, order_id, amount_inr, plan_name, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, 'captured', ?)
                """,
                (pay_id, user_id, payment_id, order_id, amount_inr, plan_name or plan_code, now)
            )
            conn.commit()
            print(f"[AUTH_DB] Upgraded user {user_id} to plan {plan_code} valid until {paid_until} ({duration_seconds//3600} hours).")
    except Exception as e:
        print(f"[AUTH_DB] Error writing payment to SQLite: {e}")

    # 2. Update Supabase if available
    if supabase_admin and user_id:
        try:
            supabase_admin.auth.admin.update_user_by_id(user_id, {
                "user_metadata": {
                    "is_paid": True,
                    "plan": plan_code,
                    "paid_until": paid_until,
                    "payment_id": payment_id,
                    "order_id": order_id,
                    "paid_at": now
                }
            })
        except Exception as e:
            print(f"[AUTH_DB] Error updating Supabase user metadata: {e}")

    return True

# --- CLOUD KANBAN & APPLICATION TRACKING PERSISTENCE ---

def get_user_kanban(user_id: str) -> dict:
    """Retrieve full Kanban application pipeline from SQLite database."""
    result = {"saved": [], "applied": [], "interviewing": [], "offer": []}
    if not user_id:
        return result
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, job_id, company, role, status, url, applied_at, updated_at, notes
            FROM candidate_applications
            WHERE user_id = ?
            ORDER BY updated_at DESC
        """, (user_id,))
        rows = cursor.fetchall()
        for r in rows:
            st = r["status"]
            item = {
                "id": r["id"],
                "job_id": r["job_id"],
                "company": r["company"],
                "role": r["role"],
                "status": st,
                "url": r["url"] or "",
                "applied_at": r["applied_at"],
                "updated_at": r["updated_at"],
                "notes": r["notes"] or ""
            }
            if st in result:
                result[st].append(item)
            else:
                result["applied"].append(item)
    return result

def save_user_kanban_application(user_id: str, app_data: dict) -> dict:
    """Insert or update a single application on candidate's cloud Kanban board."""
    if not user_id:
        return {"status": "error", "message": "user_id is required."}
    app_id = app_data.get("id") or f"app_{secrets.token_hex(6)}"
    job_id = app_data.get("job_id") or app_data.get("id") or app_id
    company = app_data.get("company", "").strip() or "Hiring Company"
    role = app_data.get("role", "").strip() or app_data.get("title", "").strip() or "Engineering Role"
    status = app_data.get("status", "saved").lower()
    url = app_data.get("url", "")
    notes = app_data.get("notes", "")
    now = time.time()
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO candidate_applications
            (id, user_id, job_id, company, role, status, url, applied_at, updated_at, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (app_id, user_id, job_id, company, role, status, url, now, now, notes))
        conn.commit()
    return {"status": "success", "id": app_id}

def sync_full_kanban(user_id: str, kanban_dict: dict) -> dict:
    """Sync an entire client-side Kanban dictionary into SQLite database and return unified state."""
    if not user_id:
        return get_user_kanban(user_id)
    now = time.time()
    with get_db() as conn:
        cursor = conn.cursor()
        for status_key, items in kanban_dict.items():
            if not isinstance(items, list):
                continue
            for item in items:
                app_id = item.get("id") or f"app_{secrets.token_hex(6)}"
                job_id = item.get("job_id") or item.get("id") or app_id
                company = item.get("company", "").strip() or "Hiring Company"
                role = item.get("role", "").strip() or item.get("title", "").strip() or "Engineering Role"
                url = item.get("url", "")
                notes = item.get("notes", "")
                cursor.execute("""
                    INSERT OR REPLACE INTO candidate_applications
                    (id, user_id, job_id, company, role, status, url, applied_at, updated_at, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (app_id, user_id, job_id, company, role, status_key, url, now, now, notes))
        conn.commit()
    return get_user_kanban(user_id)


# ============================================================================
# Telemetry, Traffic Analytics, Device Hardware & Candidate Directory Engine
# ============================================================================

def is_bot_or_scanner(path: str, user_agent: str = "") -> bool:
    """
    Detect automated vulnerability scanners, web scrapers, and malicious exploit crawlers.
    Separates automated noise (e.g. /wp-admin/install.php, xmlrpc, phpmyadmin) from real human candidates.
    """
    clean_path = (path or "").lower().split("?")[0].strip()
    ua_lower = (user_agent or "").lower().strip()

    # Vulnerability scanner target paths
    scanner_patterns = [
        ".php", "wp-admin", "wp-login", "wp-content", "wp-includes", "xmlrpc",
        "phpmyadmin", "pma", "cgi-bin", ".env", ".git", "actuator", "swagger",
        "boaform", "setup.cgi", "eval(", "phpunit", "admin.php", "shell",
        "config.json", ".aws", "jenkins", "solr", "struts", "telescope"
    ]
    if any(pat in clean_path for pat in scanner_patterns):
        return True

    # Missing UA or automated crawler / scanner user agents
    if not ua_lower:
        return True

    bot_ua_patterns = [
        "bot", "crawler", "spider", "curl/", "python-requests", "python-urllib",
        "wget/", "httpclient", "zgrab", "censys", "shodan", "netcraft",
        "semrush", "ahrefs", "bytespider", "go-http-client", "masscan",
        "nikto", "sqlmap", "headless", "phantomjs", "selenium", "puppeteer",
        "screaming frog", "dotbot", "petalbot", "mj12bot", "nmap"
    ]
    if any(b in ua_lower for b in bot_ua_patterns):
        return True

    return False

def parse_device_hardware(user_agent: str = "", client_hints: dict = None) -> dict:
    """
    Parse client user agent & client hints into exact hardware device model, brand, and platform.
    Detects models like:
      - Poco M2 Pro (Xiaomi M2003J6CI)
      - Samsung Galaxy A34 / A35 (SM-A...)
      - Apple iPhone 15 / iOS
      - Windows 11 PC (Chrome)
      - Apple MacBook (macOS)
    """
    hints = client_hints or {}
    model_hint = (hints.get("model") or "").strip().strip('"')
    platform_hint = (hints.get("platform") or "").strip().strip('"')
    platform_version = (hints.get("platform_version") or "").strip().strip('"')

    ua = user_agent or ""
    ua_lower = ua.lower()

    # Check for automated bots/scanners
    if is_bot_or_scanner("", ua):
        return {
            "category": "Bot / Probe",
            "brand": "Automated Bot",
            "model": "Vulnerability Scanner",
            "display": "🤖 Automated Security Scanner / Bot"
        }

    # 1. Android Devices (Samsung, Poco, Xiaomi, Redmi, Pixel, OnePlus, Realme)
    if "android" in ua_lower or platform_hint.lower() == "android":
        category = "Mobile Phone"
        brand = "Android"
        model = "Android Device"

        if "tablet" in ua_lower or ("android" in ua_lower and "mobile" not in ua_lower):
            category = "Tablet"

        # Extract Android OS version
        android_ver_match = re.search(r"android\s+([0-9\.]+)", ua_lower)
        android_ver = f"Android {android_ver_match.group(1)}" if android_ver_match else "Android"

        candidate_model = model_hint
        if not candidate_model:
            paren_match = re.search(r"\(([^)]+)\)", ua)
            if paren_match:
                tokens = [t.strip() for t in paren_match.group(1).split(";")]
                for t in tokens:
                    tl = t.lower()
                    if tl.startswith("linux") or tl.startswith("android") or "build" in tl or "wv" in tl:
                        continue
                    if len(t) > 2:
                        candidate_model = t
                        break

        cm_lower = candidate_model.lower()

        # POCO / XIAOMI (e.g. Poco M2 Pro: M2003J6CI / M2003J6B2G)
        if "m2003j6" in cm_lower or "m2003j6" in ua_lower or "poco m2 pro" in ua_lower or "m2003j6ci" in cm_lower:
            brand = "Poco / Xiaomi"
            model = f"Poco M2 Pro ({candidate_model or 'M2003J6CI'})"
        elif "poco" in ua_lower or "poco" in cm_lower:
            brand = "Poco"
            model = f"Poco {candidate_model}".strip() if candidate_model else "Poco Smartphone"
        elif "redmi" in ua_lower or "redmi" in cm_lower:
            brand = "Xiaomi Redmi"
            model = f"Redmi {candidate_model}".strip() if candidate_model else "Xiaomi Redmi"
        elif any(x in ua_lower for x in ["xiaomi", "mi "]):
            brand = "Xiaomi"
            model = f"Xiaomi {candidate_model}".strip() if candidate_model else "Xiaomi Smartphone"

        # SAMSUNG GALAXY (SM-A346, SM-A336, SM-A325, SM-A546, SM-A..., SM-S..., SM-M...)
        elif "sm-" in cm_lower or "sm-" in ua_lower or "samsung" in ua_lower:
            brand = "Samsung"
            sm_match = re.search(r"(SM-[A-Z0-9]+)", ua, re.IGNORECASE) or re.search(r"(SM-[A-Z0-9]+)", candidate_model, re.IGNORECASE)
            sm_code = sm_match.group(1).upper() if sm_match else candidate_model

            if sm_code.startswith("SM-A346"):
                model = f"Samsung Galaxy A34 5G ({sm_code})"
            elif sm_code.startswith("SM-A356"):
                model = f"Samsung Galaxy A35 5G ({sm_code})"
            elif sm_code.startswith("SM-A336"):
                model = f"Samsung Galaxy A33 5G ({sm_code})"
            elif sm_code.startswith("SM-A325") or sm_code.startswith("SM-A326"):
                model = f"Samsung Galaxy A32 ({sm_code})"
            elif sm_code.startswith("SM-A315"):
                model = f"Samsung Galaxy A31 ({sm_code})"
            elif sm_code.startswith("SM-A546"):
                model = f"Samsung Galaxy A54 5G ({sm_code})"
            elif sm_code.startswith("SM-A536"):
                model = f"Samsung Galaxy A53 5G ({sm_code})"
            elif sm_code.startswith("SM-A556"):
                model = f"Samsung Galaxy A55 5G ({sm_code})"
            elif sm_code.startswith("SM-A"):
                series_num = sm_code[4:6] if len(sm_code) >= 6 else ""
                model = f"Samsung Galaxy A{series_num} ({sm_code})" if series_num else f"Samsung Galaxy A-Series ({sm_code})"
            elif sm_code.startswith("SM-S92"):
                model = f"Samsung Galaxy S24 Ultra ({sm_code})"
            elif sm_code.startswith("SM-S91"):
                model = f"Samsung Galaxy S23 Ultra ({sm_code})"
            elif sm_code.startswith("SM-S"):
                model = f"Samsung Galaxy S-Series ({sm_code})"
            elif sm_code.startswith("SM-M"):
                model = f"Samsung Galaxy M-Series ({sm_code})"
            elif sm_code.startswith("SM-F"):
                model = f"Samsung Galaxy Z Fold/Flip ({sm_code})"
            else:
                model = f"Samsung Galaxy ({sm_code})"

        # GOOGLE PIXEL
        elif "pixel" in ua_lower or "pixel" in cm_lower:
            brand = "Google"
            pix_match = re.search(r"(Pixel\s+[0-9a-zA-Z\s]+)", ua)
            model = pix_match.group(1).strip() if pix_match else (candidate_model or "Google Pixel")

        # ONEPLUS
        elif "oneplus" in ua_lower or cm_lower.startswith("cph") or cm_lower.startswith("in20") or cm_lower.startswith("ne22"):
            brand = "OnePlus"
            model = f"OnePlus ({candidate_model or 'Phone'})"

        # REALME
        elif "realme" in ua_lower or cm_lower.startswith("rmx"):
            brand = "Realme"
            model = f"Realme ({candidate_model or 'Phone'})"

        # MOTOROLA
        elif "moto" in ua_lower or "motorola" in ua_lower:
            brand = "Motorola"
            model = f"Motorola {candidate_model}".strip() if candidate_model else "Motorola Phone"

        # VIVO / IQOO
        elif "vivo" in ua_lower or "iqoo" in ua_lower:
            brand = "Vivo / iQOO"
            model = f"Vivo/iQOO {candidate_model}".strip() if candidate_model else "Vivo Phone"

        else:
            model = f"{candidate_model} ({android_ver})".strip() if candidate_model else f"Android Phone ({android_ver})"

        return {
            "category": category,
            "brand": brand,
            "model": model,
            "display": f"📱 {model}"
        }

    # 2. Apple iOS (iPhone / iPad)
    if "iphone" in ua_lower:
        ios_match = re.search(r"os\s+([0-9_]+)\s+like\s+mac", ua_lower)
        ios_ver = ios_match.group(1).replace("_", ".") if ios_match else ""
        ver_str = f"iOS {ios_ver}" if ios_ver else "iOS"
        return {
            "category": "Mobile Phone",
            "brand": "Apple",
            "model": f"Apple iPhone ({ver_str})",
            "display": f"📱 Apple iPhone ({ver_str})"
        }

    if "ipad" in ua_lower:
        ios_match = re.search(r"os\s+([0-9_]+)\s+like\s+mac", ua_lower)
        ios_ver = ios_match.group(1).replace("_", ".") if ios_match else ""
        ver_str = f"iPadOS {ios_ver}" if ios_ver else "iPadOS"
        return {
            "category": "Tablet",
            "brand": "Apple",
            "model": f"Apple iPad ({ver_str})",
            "display": f"📱 Apple iPad ({ver_str})"
        }

    # 3. Windows Desktop / Laptop
    if "windows" in ua_lower or platform_hint.lower() == "windows":
        browser = "Chrome"
        if "edg/" in ua_lower:
            browser = "Edge"
        elif "firefox/" in ua_lower:
            browser = "Firefox"
        elif "opr/" in ua_lower or "opera" in ua_lower:
            browser = "Opera"

        is_win11 = False
        if platform_version:
            try:
                major = int(platform_version.split(".")[0])
                if major >= 13:
                    is_win11 = True
            except Exception:
                pass

        if is_win11:
            win_name = "Windows 11 PC"
        elif "windows nt 10.0" in ua_lower and "win64" in ua_lower:
            win_name = "Windows 11 / 10 PC"
        elif "windows nt 10.0" in ua_lower:
            win_name = "Windows 10 / 11 PC"
        elif "windows nt 6.3" in ua_lower:
            win_name = "Windows 8.1 PC"
        elif "windows nt 6.1" in ua_lower:
            win_name = "Windows 7 PC"
        else:
            win_name = "Windows PC"

        return {
            "category": "Desktop",
            "brand": "Microsoft",
            "model": f"{win_name} ({browser})",
            "display": f"💻 {win_name} ({browser})"
        }

    # 4. Apple macOS (MacBook, iMac)
    if "macintosh" in ua_lower or "mac os x" in ua_lower or platform_hint.lower() == "macos":
        browser = "Safari"
        if "chrome/" in ua_lower:
            browser = "Chrome"
        elif "edg/" in ua_lower:
            browser = "Edge"
        elif "firefox/" in ua_lower:
            browser = "Firefox"
        return {
            "category": "Desktop",
            "brand": "Apple",
            "model": f"Apple MacBook / Mac ({browser})",
            "display": f"💻 Apple MacBook / Mac ({browser})"
        }

    # 5. Linux Desktop
    if "linux" in ua_lower and "x11" in ua_lower:
        return {
            "category": "Desktop",
            "brand": "Linux",
            "model": "Linux Workstation",
            "display": "💻 Linux PC / Workstation"
        }

    # Fallback Desktop
    return {
        "category": "Desktop",
        "brand": "Generic",
        "model": "Desktop Browser",
        "display": "💻 Desktop Browser"
    }

def record_page_visit(
    path: str,
    client_ip: str,
    user_agent: str = "",
    referrer: str = "",
    client_hints: dict = None,
    device_model: str = ""
) -> bool:
    """
    Record an anonymous, privacy-compliant page visit in SQLite.
    Classifies bot / vulnerability scanners vs real candidate visits,
    and identifies exact hardware device models (e.g. Poco M2 Pro, Samsung Galaxy, Windows 11).
    """
    try:
        clean_path = (path or "/").split("?")[0].strip()
        # Filter out static files, assets, source maps, favicons
        if any(clean_path.endswith(ext) for ext in [".css", ".js", ".png", ".jpg", ".jpeg", ".ico", ".webp", ".svg", ".map", ".woff", ".woff2", ".txt", ".xml"]):
            return False
        # Filter out internal health checks and robots
        if clean_path in ["/health", "/favicon.ico", "/robots.txt", "/sitemap.xml", "/llms.txt"]:
            return False
        if clean_path.startswith("/api/") and not clean_path.startswith("/api/jobs"):
            return False

        # Detect vulnerability scanners & bot probes
        is_bot = 1 if is_bot_or_scanner(clean_path, user_agent) else 0

        # Parse hardware device
        dev_info = parse_device_hardware(user_agent, client_hints or {})
        category = dev_info.get("category", "Desktop")
        if "mobile" in category.lower():
            device_type = "mobile"
        elif "tablet" in category.lower():
            device_type = "tablet"
        elif "bot" in category.lower():
            device_type = "bot"
        else:
            device_type = "desktop"

        final_model = device_model.strip() or dev_info.get("model", "")
        brand_name = dev_info.get("brand", "")

        now = time.time()
        date_str = time.strftime("%Y-%m-%d", time.gmtime(now))
        # Anonymized salted visitor hash
        ua_clean = (user_agent or "").lower()[:60]
        hash_input = f"{client_ip}:{ua_clean}:{date_str}:{AUTH_SECRET_KEY}"
        visitor_hash = hashlib.sha256(hash_input.encode("utf-8")).hexdigest()[:16]

        clean_ref = (referrer or "")[:255]

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO site_traffic (date, path, visitor_hash, device, device_model, device_brand, is_bot, referrer, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (date_str, clean_path, visitor_hash, device_type, final_model, brand_name, is_bot, clean_ref, now)
            )
            conn.commit()
        return True
    except Exception as e:
        print(f"[TRAFFIC_TRACKER] Visit record note: {e}")
        return False

def get_analytics_summary() -> dict:
    """
    Calculate comprehensive real-time site analytics and engagement metrics.
    Distinguishes verified real candidate traffic from automated vulnerability scanner probes,
    provides hardware device breakdowns, and synchronizes real registered candidate tallies.
    """
    now = time.time()
    today_str = time.strftime("%Y-%m-%d", time.gmtime(now))
    
    with get_db() as conn:
        cursor = conn.cursor()

        # 1. Verified Real Candidate Metrics (WHERE is_bot = 0)
        cursor.execute("SELECT COUNT(*) FROM site_traffic WHERE is_bot = 0;")
        verified_total_pageviews = cursor.fetchone()[0] or 0

        cursor.execute("SELECT COUNT(*) FROM site_traffic WHERE is_bot = 0 AND date = ?;", (today_str,))
        verified_today_pageviews = cursor.fetchone()[0] or 0

        cursor.execute("SELECT COUNT(DISTINCT visitor_hash) FROM site_traffic WHERE is_bot = 0;")
        verified_unique_visitors = cursor.fetchone()[0] or 0

        cursor.execute("SELECT COUNT(DISTINCT visitor_hash) FROM site_traffic WHERE is_bot = 0 AND date = ?;", (today_str,))
        verified_today_uniques = cursor.fetchone()[0] or 0

        # Verified Device Breakdown
        cursor.execute("SELECT device, COUNT(*) FROM site_traffic WHERE is_bot = 0 GROUP BY device;")
        device_counts = dict(cursor.fetchall())
        desktop_views = device_counts.get("desktop", 0)
        mobile_views = device_counts.get("mobile", 0) + device_counts.get("tablet", 0)

        # Top 10 Verified Candidate Routes
        cursor.execute("""
            SELECT path, COUNT(*) as hits, COUNT(DISTINCT visitor_hash) as uniques
            FROM site_traffic
            WHERE is_bot = 0
            GROUP BY path
            ORDER BY hits DESC
            LIMIT 10;
        """)
        top_candidate_pages = [
            {"path": r["path"], "hits": r["hits"], "uniques": r["uniques"]}
            for r in cursor.fetchall()
        ]

        # 2. Automated Scanner & Bot Probes Filtered (WHERE is_bot = 1)
        cursor.execute("SELECT COUNT(*) FROM site_traffic WHERE is_bot = 1;")
        bot_probes_total = cursor.fetchone()[0] or 0

        cursor.execute("SELECT COUNT(*) FROM site_traffic WHERE is_bot = 1 AND date = ?;", (today_str,))
        bot_probes_today = cursor.fetchone()[0] or 0

        cursor.execute("""
            SELECT path, COUNT(*) as hits, COUNT(DISTINCT visitor_hash) as uniques
            FROM site_traffic
            WHERE is_bot = 1
            GROUP BY path
            ORDER BY hits DESC
            LIMIT 10;
        """)
        top_blocked_probes = [
            {"path": r["path"], "hits": r["hits"], "uniques": r["uniques"]}
            for r in cursor.fetchall()
        ]

        # 3. Hardware Device Model Breakdown (Samsung, Poco, iPhone, Windows 11, Mac, etc.)
        cursor.execute("""
            SELECT 
                COALESCE(NULLIF(device_model, ''), device) as model,
                COALESCE(NULLIF(device_brand, ''), 'General') as brand,
                COUNT(*) as hits
            FROM site_traffic
            WHERE is_bot = 0 AND device_model != ''
            GROUP BY model
            ORDER BY hits DESC
            LIMIT 8;
        """)
        hardware_devices = [
            {"model": r["model"], "brand": r["brand"], "hits": r["hits"]}
            for r in cursor.fetchall()
        ]

        # 4. Last 7 days verified candidate trend
        cursor.execute("""
            SELECT date, COUNT(*) as pageviews, COUNT(DISTINCT visitor_hash) as uniques
            FROM site_traffic
            WHERE is_bot = 0
            GROUP BY date
            ORDER BY date DESC
            LIMIT 7;
        """)
        history_rows = cursor.fetchall()
        trend = [
            {"date": r["date"], "pageviews": r["pageviews"], "uniques": r["uniques"]}
            for r in reversed(history_rows)
        ]

    # 5. Candidate Accounts synchronized from Supabase + SQLite
    candidates = get_all_users_admin()
    total_users = len(candidates)
    paid_users = sum(1 for c in candidates if c.get("is_paid"))
    google_users = sum(1 for c in candidates if c.get("auth_provider") == "google")

    # If all existing traffic was before migration, ensure default fallback numbers match
    raw_total = verified_total_pageviews + bot_probes_total

    return {
        # Verified Candidate Audience (Headline Metrics)
        "total_pageviews": verified_total_pageviews if (verified_total_pageviews > 0 or bot_probes_total > 0) else raw_total,
        "today_pageviews": verified_today_pageviews if (verified_today_pageviews > 0 or bot_probes_today > 0) else raw_total,
        "unique_visitors_total": verified_unique_visitors,
        "today_unique_visitors": verified_today_uniques,
        "desktop_views": desktop_views,
        "mobile_views": mobile_views,
        "top_pages": top_candidate_pages if top_candidate_pages else top_blocked_probes,
        "daily_trend": trend,
        
        # Bot & Security Scanner Probes Filtered
        "bot_probes_total": bot_probes_total,
        "bot_probes_today": bot_probes_today,
        "top_blocked_probes": top_blocked_probes,
        "raw_total_hits": raw_total,

        # Hardware Model & Device Breakdown
        "hardware_devices": hardware_devices,

        # Candidate Directory Stats
        "total_users": total_users,
        "paid_users": paid_users,
        "google_users": google_users,
        "today_date": today_str
    }

def get_all_users_admin() -> list:
    """
    Retrieve all registered candidates formatted for the executive admin directory.
    Synchronizes seamlessly with Supabase Auth (if configured) so candidate accounts
    never vanish on ephemeral hosting (Render) restarts, and enriches candidates
    with their email, authentication provider, and hardware device models.
    """
    candidates_by_email = {}
    now = time.time()

    # 1. Fetch from local SQLite cache
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, email, full_name, plan, is_paid, paid_until, created_at, auth_provider,
                   COALESCE(device_model, '') as device_model
            FROM users
            ORDER BY created_at DESC;
        """)
        for r in cursor.fetchall():
            email_key = (r["email"] or "").strip().lower()
            if not email_key:
                continue
            created_ts = r["created_at"] or now
            paid_until = r["paid_until"] or 0
            is_active_vip = bool(r["is_paid"]) and (paid_until == 0 or paid_until > now)
            candidates_by_email[email_key] = {
                "id": r["id"],
                "email": r["email"],
                "full_name": r["full_name"] or "Candidate",
                "plan": r["plan"] or "free",
                "is_paid": is_active_vip,
                "auth_provider": r["auth_provider"] or ("google" if "google" in email_key else "email"),
                "device_model": r["device_model"] or "",
                "created_at": created_ts,
                "created_at_str": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(created_ts))
            }

    # 2. Synchronize with live Supabase Auth (guarantees candidate directory persistence on Render)
    if supabase_admin:
        try:
            sp_users = supabase_admin.auth.admin.list_users() or []
            for u in sp_users:
                sp_email = (getattr(u, "email", "") or "").strip().lower()
                if not sp_email:
                    continue
                
                user_meta = getattr(u, "user_metadata", {}) or {}
                app_meta = getattr(u, "app_metadata", {}) or {}

                # Parse created_at
                created_raw = getattr(u, "created_at", None)
                if hasattr(created_raw, "timestamp"):
                    created_ts = created_raw.timestamp()
                elif isinstance(created_raw, str):
                    try:
                        import dateutil.parser
                        created_ts = dateutil.parser.parse(created_raw).timestamp()
                    except Exception:
                        created_ts = now
                else:
                    created_ts = now

                full_name = user_meta.get("full_name") or sp_email.split("@")[0].capitalize()
                provider = app_meta.get("provider") or ("google" if "google" in sp_email or user_meta.get("google_id") else "email")
                sp_device = user_meta.get("device_model") or ""
                sp_is_paid = bool(user_meta.get("is_paid", False))

                if sp_email not in candidates_by_email:
                    local_id = user_meta.get("local_user_id") or getattr(u, "id", str(uuid.uuid4()))
                    candidates_by_email[sp_email] = {
                        "id": local_id,
                        "email": sp_email,
                        "full_name": full_name,
                        "plan": "free" if not sp_is_paid else "vip",
                        "is_paid": sp_is_paid,
                        "auth_provider": provider,
                        "device_model": sp_device,
                        "created_at": created_ts,
                        "created_at_str": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(created_ts))
                    }

                    # Backfill into local SQLite cache
                    try:
                        with get_db() as conn:
                            cursor = conn.cursor()
                            cursor.execute(
                                """
                                INSERT OR IGNORE INTO users 
                                (id, email, password_hash, salt, full_name, is_paid, plan, paid_until, created_at, updated_at, auth_provider, device_model)
                                VALUES (?, ?, 'supabase_managed', 'salt', ?, ?, 'free', 0, ?, ?, ?, ?)
                                """,
                                (local_id, sp_email, full_name, 1 if sp_is_paid else 0, created_ts, created_ts, provider, sp_device)
                            )
                            conn.commit()
                    except Exception as e:
                        print(f"[AUTH_DB] SQLite backfill note: {e}")
                else:
                    if sp_device and not candidates_by_email[sp_email].get("device_model"):
                        candidates_by_email[sp_email]["device_model"] = sp_device
                    if full_name and candidates_by_email[sp_email].get("full_name") in ["Candidate", ""]:
                        candidates_by_email[sp_email]["full_name"] = full_name
        except Exception as e:
            print(f"[AUTH_DB] Supabase user list sync note: {e}")

    # Format device model display for candidates
    candidates = list(candidates_by_email.values())
    for c in candidates:
        dev = c.get("device_model") or ""
        if not dev:
            # Fallback based on sign-in or default
            dev = "Desktop / Web Browser"
        c["device_display"] = dev

    candidates.sort(key=lambda x: x.get("created_at", 0), reverse=True)
    return candidates
