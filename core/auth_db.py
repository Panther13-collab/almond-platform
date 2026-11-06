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
                updated_at REAL
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
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users (email);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_payments_user_id ON payments (user_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_cand_apps_user ON candidate_applications (user_id);")
        
        # Auto-migrate existing database tables if columns are missing
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN paid_until REAL DEFAULT 0;")
        except Exception:
            pass
        try:
            cursor.execute("ALTER TABLE payments ADD COLUMN plan_name TEXT DEFAULT '';")
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

def verify_session_token(token: str) -> dict:
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
            
        # Verify HMAC signature
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, email, full_name, is_paid, plan, paid_until, created_at FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            if not row:
                return None
            
            data = f"{user_id}:{row['email']}:{timestamp}"
            expected_sig = hmac.new(AUTH_SECRET_KEY.encode("utf-8"), data.encode("utf-8"), hashlib.sha256).hexdigest()
            if not hmac.compare_digest(sig, expected_sig):
                return None
            
            now = time.time()
            paid_until = row["paid_until"] or 0
            is_paid = bool(row["is_paid"]) and (paid_until == 0 or paid_until > now)

            # Human-readable remaining string
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
                "id": row["id"],
                "user_id": row["id"],
                "email": row["email"],
                "full_name": row["full_name"],
                "is_paid": is_paid,
                "plan": row["plan"],
                "paid_until": paid_until,
                "remaining_str": remaining_str,
                "created_at": row["created_at"]
            }
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

def verify_otp_and_signup(email: str, otp_code: str, password: str, full_name: str = "") -> dict:
    """Verify submitted 6-digit OTP code and create candidate account."""
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

    # Now create account
    return signup_user(clean_email, password, full_name)

def signup_user(email: str, password: str, full_name: str = "") -> dict:
    """Sign up a new candidate user into persistent SQLite and sync with Supabase."""
    clean_email = email.strip().lower()
    if not clean_email or "@" not in clean_email:
        return {"status": "error", "message": "Please provide a valid email address."}
    if not password or len(password) < 6:
        return {"status": "error", "message": "Password must be at least 6 characters long."}

    user_id = str(uuid.uuid4())
    pw_hash, salt = _hash_password(password)
    now = time.time()

    # 1. Insert into local persistent SQLite DB
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO users (id, email, password_hash, salt, full_name, is_paid, plan, paid_until, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, 0, 'free', 0, ?, ?)
                """,
                (user_id, clean_email, pw_hash, salt, full_name.strip(), now, now)
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
                    "local_user_id": user_id
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
        "token": token
    }

def login_user(email: str, password: str) -> dict:
    """Authenticate an existing user via SQLite credentials and return persistent token."""
    clean_email = email.strip().lower()
    if not clean_email or not password:
        return {"status": "error", "message": "Email and password are required."}

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, email, password_hash, salt, full_name, is_paid, plan, paid_until FROM users WHERE email = ?", (clean_email,))
        row = cursor.fetchone()
        
        if not row:
            return {"status": "error", "message": "No account found with this email. Please sign up."}
            
        expected_hash, _ = _hash_password(password, row["salt"])
        if not hmac.compare_digest(row["password_hash"], expected_hash):
            return {"status": "error", "message": "Incorrect password. Please verify and try again."}

        user_id = row["id"]
        token = _create_token(user_id, row["email"])

        now = time.time()
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

    return False

def record_successful_payment(user_id: str, payment_id: str, order_id: str, amount_inr: float, plan_name: str = "") -> bool:
    """Record a captured payment with strict timestamp-based expiration (24h Day Sprint, 30d, or 90d)."""
    now = time.time()
    plan_lower = (plan_name or "").lower()

    # Time-bound plan calculation:
    # 1. Day Sprint: 24 Hours
    # 2. 90-Day Mastery: 90 Days
    # 3. 30-Day Pro Hunt: 30 Days (Default)
    if "day" in plan_lower or "24" in plan_lower or amount_inr <= 200:
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
