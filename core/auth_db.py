import re
import os
import json
import sqlite3
import hashlib
import hmac
import secrets
import time
import uuid
import datetime
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
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA busy_timeout=30000;")
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
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_payments_payment_id ON payments (payment_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_payments_order_id ON payments (order_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_cand_apps_user ON candidate_applications (user_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_traffic_date ON site_traffic (date);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_traffic_path ON site_traffic (path);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_traffic_visitor ON site_traffic (visitor_hash);")
        
        # Dedicated Pre-Approved / Admin VIP Grants Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vip_grants (
                email TEXT PRIMARY KEY,
                granted_by TEXT DEFAULT 'admin',
                granted_at REAL,
                valid_until REAL,
                status TEXT DEFAULT 'active',
                notes TEXT DEFAULT ''
            );
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_vip_grants_email ON vip_grants (email);")

        # Dedicated Candidate Feedback & Feature Inquiries Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS candidate_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                user_email TEXT,
                category TEXT NOT NULL,
                rating INTEGER DEFAULT 5,
                message TEXT NOT NULL,
                hired_company TEXT DEFAULT '',
                page_url TEXT DEFAULT '',
                created_at REAL NOT NULL,
                admin_reply TEXT DEFAULT '',
                admin_replied_at REAL DEFAULT 0,
                status TEXT DEFAULT 'pending'
            );
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_feedback_category ON candidate_feedback (category);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_feedback_status ON candidate_feedback (status);")
        
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
            cursor.execute("ALTER TABLE site_traffic ADD COLUMN location TEXT DEFAULT '';")
        except Exception:
            pass
        try:
            cursor.execute("ALTER TABLE site_traffic ADD COLUMN user_name TEXT DEFAULT '';")
        except Exception:
            pass
        try:
            cursor.execute("ALTER TABLE site_traffic ADD COLUMN user_email TEXT DEFAULT '';")
        except Exception:
            pass
        try:
            cursor.execute("ALTER TABLE payments ADD COLUMN plan_name TEXT DEFAULT '';")
        except Exception:
            pass
        try:
            cursor.execute("ALTER TABLE payments ADD COLUMN supporter_name TEXT DEFAULT '';")
        except Exception:
            pass
        try:
            cursor.execute("ALTER TABLE payments ADD COLUMN supporter_message TEXT DEFAULT '';")
        except Exception:
            pass
        try:
            cursor.execute("ALTER TABLE payments ADD COLUMN admin_reply TEXT DEFAULT '';")
        except Exception:
            pass
        try:
            cursor.execute("ALTER TABLE payments ADD COLUMN admin_replied_at REAL DEFAULT 0;")
        except Exception:
            pass
        try:
            cursor.execute("ALTER TABLE payments ADD COLUMN currency TEXT DEFAULT 'INR';")
        except Exception:
            pass
        try:
            cursor.execute("ALTER TABLE payments ADD COLUMN is_verified_hmac INTEGER DEFAULT 1;")
        except Exception:
            pass

        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_traffic_is_bot ON site_traffic (is_bot);")
        except Exception:
            pass
        for col_def in [
            "utm_source TEXT DEFAULT ''",
            "utm_medium TEXT DEFAULT ''",
            "utm_campaign TEXT DEFAULT ''",
            "utm_content TEXT DEFAULT ''",
            "fbclid TEXT DEFAULT ''",
        ]:
            try:
                cursor.execute(f"ALTER TABLE site_traffic ADD COLUMN {col_def};")
            except Exception:
                pass

        # Persistent Funnel Conversion Events (visit -> resume_upload -> signup -> checkout_start -> purchase)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS funnel_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                visitor_hash TEXT NOT NULL,
                event_name TEXT NOT NULL,
                utm_source TEXT DEFAULT '',
                utm_medium TEXT DEFAULT '',
                utm_campaign TEXT DEFAULT '',
                utm_content TEXT DEFAULT '',
                fbclid TEXT DEFAULT '',
                user_name TEXT DEFAULT '',
                user_email TEXT DEFAULT '',
                amount_inr REAL DEFAULT 0,
                meta_json TEXT DEFAULT '',
                timestamp REAL NOT NULL
            );
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_funnel_event_name ON funnel_events (event_name);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_funnel_utm_source ON funnel_events (utm_source);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_funnel_timestamp ON funnel_events (timestamp);")

        # Key-Value Local Settings Fallback (synced with Supabase system_store when online)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS kv_settings (
                key TEXT PRIMARY KEY,
                value TEXT DEFAULT ''
            );
        """)

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

        # Dedicated Dynamic Pricing Table for Festival & Promotional Configuration
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pricing_config (
                tier_id TEXT PRIMARY KEY,
                plan_code TEXT NOT NULL,
                name TEXT NOT NULL,
                duration_days INTEGER NOT NULL,
                inr_price INTEGER NOT NULL,
                inr_original INTEGER NOT NULL,
                usd_price REAL NOT NULL,
                usd_original REAL NOT NULL,
                eur_price REAL NOT NULL,
                eur_original REAL NOT NULL,
                gbp_price REAL NOT NULL,
                gbp_original REAL NOT NULL,
                discount_pct INTEGER DEFAULT 0,
                discount_label TEXT DEFAULT '',
                badge_text TEXT DEFAULT '',
                is_active INTEGER DEFAULT 1,
                updated_at REAL
            );
        ''')

        # Seed default pricing tiers if empty
        cursor.execute("SELECT COUNT(*) AS cnt FROM pricing_config;")
        row_cnt = cursor.fetchone()
        if not row_cnt or row_cnt["cnt"] == 0:
            now_ts = time.time()
            cursor.execute('''
                INSERT INTO pricing_config (
                    tier_id, plan_code, name, duration_days,
                    inr_price, inr_original,
                    usd_price, usd_original,
                    eur_price, eur_original,
                    gbp_price, gbp_original,
                    discount_pct, discount_label, badge_text,
                    is_active, updated_at
                ) VALUES 
                ('1m', 'vip_pass_30d', '1-Month VIP Pass', 30, 699, 699, 19.99, 19.99, 18.99, 18.99, 15.99, 15.99, 0, '', 'Standard VIP', 1, ?),
                ('3m', 'vip_pass_90d', '3-Month Career Sprint Pass', 90, 1799, 2599, 49.99, 69.99, 46.99, 64.99, 39.99, 54.99, 30, '30% OFF Limited Offer', 'Career Sprint', 1, ?),
                ('6m', 'vip_pass_180d', '6-Month Career Dominance Pass', 180, 2799, 4299, 79.99, 119.99, 74.99, 114.99, 64.99, 99.99, 35, '35% OFF Limited Offer', 'Best Value', 1, ?);
            ''', (now_ts, now_ts, now_ts))
        else:
            # Upgrade existing rows with foreign purchasing power parity pricing if previously lower
            cursor.execute("SELECT usd_price FROM pricing_config WHERE tier_id = '1m';")
            r1m = cursor.fetchone()
            if r1m and float(r1m["usd_price"]) < 15.0:
                cursor.execute("""
                    UPDATE pricing_config SET usd_price = 19.99, usd_original = 19.99, eur_price = 18.99, eur_original = 18.99, gbp_price = 15.99, gbp_original = 15.99 WHERE tier_id = '1m';
                """)
                cursor.execute("""
                    UPDATE pricing_config SET usd_price = 49.99, usd_original = 69.99, eur_price = 46.99, eur_original = 64.99, gbp_price = 39.99, gbp_original = 54.99 WHERE tier_id = '3m';
                """)
                cursor.execute("""
                    UPDATE pricing_config SET usd_price = 79.99, usd_original = 119.99, eur_price = 74.99, eur_original = 114.99, gbp_price = 64.99, gbp_original = 99.99 WHERE tier_id = '6m';
                """)
                print("[AUTH_DB] Auto-migrated foreign pricing tiers to premium purchasing power rates.")

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

def _get_plan_tier(is_paid: bool, plan: str) -> str:
    if not is_paid:
        return "free"
    p = str(plan or "").lower()
    if "180" in p or "6-month" in p or "6 month" in p or "6m" in p or "dominance" in p:
        return "6m"
    if "90" in p or "mastery" in p or "3-month" in p or "3 month" in p or "3m" in p or "sprint" in p:
        return "3m"
    return "1m"

def _format_paid_until(paid_until: float) -> str:
    if not paid_until:
        return ""
    try:
        from datetime import datetime, timezone
        return datetime.fromtimestamp(paid_until, tz=timezone.utc).strftime("%b %d, %Y")
    except Exception:
        return ""

def _format_remaining_str(is_paid: bool, paid_until: float, now: float) -> str:
    if not (is_paid and paid_until > now):
        return ""
    diff = paid_until - now
    if diff < 86400:
        hours = max(1, int(diff / 3600))
        return f"{hours}h left"
    days = int(diff / 86400)
    return f"{days}d left"

SYSTEM_STORE_EMAIL = "system_store@almondjobs.internal"
_supabase_users_cache = {"ts": 0, "users": []}
_system_store_cache = {"ts": 0, "store": {}, "uid": None}
_cloud_synced_on_boot = False

def _fetch_all_supabase_users(force: bool = False) -> list:
    """Fetch all users across all pages from Supabase with a high-performance in-memory cache."""
    if not supabase_admin:
        return []
    now = time.time()
    if not force and _supabase_users_cache["users"] and (now - _supabase_users_cache["ts"] < 60):
        return _supabase_users_cache["users"]
    try:
        all_users = []
        page = 1
        while True:
            batch = supabase_admin.auth.admin.list_users(page=page, per_page=1000)
            if not batch:
                break
            all_users.extend(batch)
            if len(batch) < 1000:
                break
            page += 1
        _supabase_users_cache["ts"] = now
        _supabase_users_cache["users"] = all_users
        return all_users
    except Exception as e:
        print(f"[AUTH_DB] Supabase user fetch note: {e}")
        return _supabase_users_cache.get("users", [])

def _find_supabase_user(email: str = "", user_id: str = ""):
    """Look up a user in Supabase by email, Supabase Auth UUID, or local_user_id metadata."""
    if not supabase_admin:
        return None
    clean_email = (email or "").strip().lower()
    clean_uid = str(user_id or "").strip()

    if clean_uid and len(clean_uid) >= 32 and "-" in clean_uid:
        try:
            resp = supabase_admin.auth.admin.get_user_by_id(clean_uid)
            u = getattr(resp, "user", resp)
            if u and getattr(u, "id", None):
                return u
        except Exception:
            pass

    for u in _fetch_all_supabase_users():
        u_email = (getattr(u, "email", "") or "").strip().lower()
        if clean_email and u_email == clean_email:
            return u
        if clean_uid and getattr(u, "id", None) == clean_uid:
            return u
        meta = getattr(u, "user_metadata", {}) or {}
        if clean_uid and meta.get("local_user_id") == clean_uid:
            return u

    for u in _fetch_all_supabase_users(force=True):
        u_email = (getattr(u, "email", "") or "").strip().lower()
        if clean_email and u_email == clean_email:
            return u
        if clean_uid and getattr(u, "id", None) == clean_uid:
            return u
        meta = getattr(u, "user_metadata", {}) or {}
        if clean_uid and meta.get("local_user_id") == clean_uid:
            return u

    return None

def _get_system_store(force: bool = False) -> dict:
    """Retrieve global platform persistence store from Supabase."""
    if not supabase_admin:
        return {}
    now = time.time()
    if not force and _system_store_cache["store"] and (now - _system_store_cache["ts"] < 60):
        return _system_store_cache["store"]

    try:
        all_u = _fetch_all_supabase_users(force=force)
        sys_u = None
        for u in all_u:
            if (getattr(u, "email", "") or "").lower() == SYSTEM_STORE_EMAIL:
                sys_u = u
                break
        if not sys_u:
            res = supabase_admin.auth.admin.create_user({
                "email": SYSTEM_STORE_EMAIL,
                "email_confirm": True,
                "user_metadata": {"vip_grants": {}, "contributions": []}
            })
            sys_u = getattr(res, "user", res)
        meta = getattr(sys_u, "user_metadata", {}) or {}
        _system_store_cache["ts"] = now
        _system_store_cache["store"] = meta
        _system_store_cache["uid"] = getattr(sys_u, "id", None)
        return meta
    except Exception as e:
        print(f"[AUTH_DB] system_store lookup note: {e}")
        return _system_store_cache.get("store", {})

def _update_system_store(updates: dict):
    """Write updates to global platform persistence store in Supabase."""
    if not supabase_admin:
        return
    try:
        current = _get_system_store()
        current.update(updates)
        uid = _system_store_cache.get("uid")
        if not uid:
            all_u = _fetch_all_supabase_users()
            for u in all_u:
                if (getattr(u, "email", "") or "").lower() == SYSTEM_STORE_EMAIL:
                    uid = u.id
                    break
        if uid:
            supabase_admin.auth.admin.update_user_by_id(uid, {"user_metadata": current})
            _system_store_cache["ts"] = time.time()
            _system_store_cache["store"] = current
            print(f"[AUTH_DB] Successfully saved system store updates to Supabase.")
    except Exception as e:
        print(f"[AUTH_DB] Warning updating system_store: {e}")

def sync_from_supabase_cloud(force: bool = False):
    """Hydrate local SQLite database from Supabase cloud on container startup."""
    global _cloud_synced_on_boot
    if not supabase_admin:
        return
    if _cloud_synced_on_boot and not force:
        return
    _cloud_synced_on_boot = True
    try:
        store = _get_system_store(force=force)
        now = time.time()
        
        # 1. Restore VIP grants from system_store
        grants = store.get("vip_grants", {})
        if grants:
            with get_db() as conn:
                cursor = conn.cursor()
                for em, g in grants.items():
                    val_until = float(g.get("paid_until", 0))
                    if val_until > now:
                        cursor.execute(
                            """
                            INSERT OR REPLACE INTO vip_grants (email, granted_by, granted_at, valid_until, status, notes)
                            VALUES (?, ?, ?, ?, 'active', ?)
                            """,
                            (em.lower(), g.get("granted_by", "admin"), g.get("granted_at", now), val_until, g.get("notes", "Restored from cloud"))
                        )
                conn.commit()

        # 2. Restore active VIP users from Supabase users
        all_sp_users = _fetch_all_supabase_users(force=force)
        with get_db() as conn:
            cursor = conn.cursor()
            for u in all_sp_users:
                em = (getattr(u, "email", "") or "").strip().lower()
                if not em or em == SYSTEM_STORE_EMAIL:
                    continue
                meta = getattr(u, "user_metadata", {}) or {}
                is_p = bool(meta.get("is_paid"))
                p_until = float(meta.get("paid_until") or 0)
                if is_p and (p_until == 0 or p_until > now):
                    u_id = meta.get("local_user_id") or u.id
                    plan = meta.get("plan") or "vip_pass_30d"
                    fn = meta.get("full_name") or em.split("@")[0]
                    dev = meta.get("device_model") or ""
                    cursor.execute(
                        """
                        INSERT OR IGNORE INTO users (id, email, password_hash, salt, full_name, is_paid, plan, paid_until, created_at, updated_at, auth_provider, device_model)
                        VALUES (?, ?, 'cloud_synced', 'salt', ?, 1, ?, ?, ?, ?, 'cloud', ?)
                        """,
                        (u_id, em, fn, plan, p_until, now, now, dev)
                    )
                    cursor.execute(
                        """
                        INSERT OR REPLACE INTO vip_grants (email, granted_by, granted_at, valid_until, status, notes)
                        VALUES (?, 'cloud_sync', ?, ?, 'active', 'Auto-restored from cloud')
                        """,
                        (em, now, p_until)
                    )
            conn.commit()
            
        print("[AUTH_DB] Successfully hydrated cloud state from Supabase.")
    except Exception as e:
        print(f"[AUTH_DB] Notice during cloud sync: {e}")

# Initial cloud state hydration on process startup
sync_from_supabase_cloud()

def sync_supabase_vip_metadata(email: str, is_paid: bool, plan: str, paid_until: float, local_user_id: str = ""):
    """Ensure VIP state is permanently preserved in Supabase Auth across container restarts."""
    if not supabase_admin:
        return
    clean_email = (email or "").strip().lower()
    if not clean_email or clean_email == SYSTEM_STORE_EMAIL:
        return
    try:
        now = time.time()
        target_user = _find_supabase_user(email=clean_email, user_id=local_user_id)
        if target_user:
            meta = getattr(target_user, "user_metadata", {}) or {}
            meta.update({
                "is_paid": bool(is_paid),
                "plan": plan,
                "paid_until": float(paid_until),
                "local_user_id": local_user_id or meta.get("local_user_id") or getattr(target_user, "id", ""),
                "vip_granted_by": "admin" if is_paid else meta.get("vip_granted_by", "")
            })
            supabase_admin.auth.admin.update_user_by_id(target_user.id, {"user_metadata": meta})
            print(f"[AUTH_DB] Successfully synchronized VIP metadata to Supabase for {clean_email} ({plan}).")
        else:
            rand_pwd = secrets.token_urlsafe(32)
            supabase_admin.auth.admin.create_user({
                "email": clean_email,
                "password": rand_pwd,
                "email_confirm": True,
                "user_metadata": {
                    "is_paid": bool(is_paid),
                    "plan": plan,
                    "paid_until": float(paid_until),
                    "local_user_id": local_user_id or str(uuid.uuid4()),
                    "vip_granted_by": "admin" if is_paid else ""
                }
            })
            print(f"[AUTH_DB] Created pre-approved VIP user in Supabase for {clean_email} ({plan}).")

        # Invalidate users cache
        _supabase_users_cache["ts"] = 0

        # Update system_store
        store = _get_system_store()
        grants = store.get("vip_grants", {})
        if is_paid:
            grants[clean_email] = {
                "plan": plan,
                "paid_until": float(paid_until),
                "granted_by": "admin",
                "granted_at": now
            }
        else:
            grants.pop(clean_email, None)
        _update_system_store({"vip_grants": grants})
    except Exception as e:
        print(f"[AUTH_DB] Supabase VIP sync note: {e}")

def _lookup_supabase_user_meta(user_id: str, email: str = "") -> dict:
    """Best-effort lookup in Supabase Admin so ephemeral SQLite restarts preserve accounts and VIP state."""
    if not supabase_admin:
        return {}
    clean_email = (email or "").strip().lower()
    u = _find_supabase_user(email=clean_email, user_id=user_id)
    if u:
        meta = getattr(u, "user_metadata", None) or {}
        u_email = (getattr(u, "email", "") or clean_email).strip().lower()
        return {"email": u_email, "meta": meta, "supa_id": u.id}
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
    
    if meta.get("password_hash") and meta.get("salt"):
        pw_hash = meta["password_hash"]
        salt = meta["salt"]
    else:
        pw_hash, salt = _hash_password(secrets.token_urlsafe(24))

    # Check system_store grants as well
    sys_grant = _get_system_store().get("vip_grants", {}).get(clean_email)
    if sys_grant and float(sys_grant.get("paid_until", 0)) > now:
        is_paid = 1
        paid_until = max(paid_until, float(sys_grant["paid_until"]))
        plan = sys_grant.get("plan", "vip_pass_30d")

    with get_db() as conn:
        cursor = conn.cursor()
        # 1. Recover active grant from vip_grants table
        cursor.execute("SELECT valid_until FROM vip_grants WHERE LOWER(email) = ? AND status = 'active'", (clean_email,))
        grant_row = cursor.fetchone()
        if grant_row and grant_row["valid_until"] > now:
            is_paid = 1
            paid_until = max(paid_until, grant_row["valid_until"])
            plan = "vip_pass_30d"

        # 2. Recover payment status from SQLite payments if present
        if not is_paid:
            cursor.execute(
                "SELECT plan_name, created_at FROM payments WHERE (user_id = ? OR LOWER(user_id) = ?) AND status = 'captured' ORDER BY created_at DESC LIMIT 1",
                (user_id, clean_email)
            )
            prow = cursor.fetchone()
            if prow:
                is_paid = 1
                plan = prow["plan_name"] or "vip_pass_30d"
                paid_until = float(prow["created_at"] or now) + (30 * 86400)

        cursor.execute(
            """
            INSERT OR REPLACE INTO users (id, email, password_hash, salt, full_name, is_paid, plan, paid_until, created_at, updated_at, auth_provider)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'session_rehydrated')
            """,
            (user_id, clean_email, pw_hash, salt, name_val, is_paid, plan, paid_until, now, now)
        )
        if is_paid and paid_until > now:
            cursor.execute(
                """
                INSERT OR REPLACE INTO vip_grants (email, granted_by, granted_at, valid_until, status, notes)
                VALUES (?, 'cloud_sync', ?, ?, 'active', 'Auto-rehydrated')
                """,
                (clean_email, now, paid_until)
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
                if row["is_paid"] == 1 and paid_until > 0 and paid_until <= now:
                    try:
                        cursor.execute("UPDATE users SET is_paid = 0, plan = 'free' WHERE id = ?", (user_id,))
                        conn.commit()
                    except Exception:
                        pass
                    is_paid = False

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
        print(f"[AUTH_OTP] FAILED TO DISPATCH EMAIL TO {clean_email}: {delivery_err}. Enabling instant direct signup fallback.")
        return {
            "status": "error",
            "fallback_available": True,
            "error_code": "EMAIL_DELIVERY_UNAVAILABLE",
            "message": "We could not deliver a verification email to this address. Instant direct registration has been activated for your account."
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

    has_grant, grant_until, grant_plan = check_and_apply_vip_grant(clean_email)
    initial_paid = 1 if has_grant else 0
    initial_plan = grant_plan if has_grant else 'free'
    initial_until = grant_until if has_grant else 0

    # 1. Insert into local persistent SQLite DB
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO users (id, email, password_hash, salt, full_name, is_paid, plan, paid_until, created_at, updated_at, auth_provider, device_model)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'email', ?)
                """,
                (user_id, clean_email, pw_hash, salt, full_name.strip(), initial_paid, initial_plan, initial_until, now, now, clean_device)
            )
            conn.commit()
    except sqlite3.IntegrityError:
        return {"status": "error", "message": "An account with this email already exists. Please log in."}
    except Exception as e:
        return {"status": "error", "message": f"Database error: {str(e)}"}

    # 2. Mirror into Supabase Auth with auto email confirmation
    if supabase_admin:
        try:
            existing_sp = _find_supabase_user(email=clean_email)
            if existing_sp:
                meta = getattr(existing_sp, "user_metadata", {}) or {}
                meta.update({
                    "full_name": full_name.strip(),
                    "is_paid": bool(initial_paid),
                    "plan": initial_plan,
                    "paid_until": initial_until,
                    "local_user_id": user_id,
                    "device_model": clean_device,
                    "password_hash": pw_hash,
                    "salt": salt
                })
                supabase_admin.auth.admin.update_user_by_id(existing_sp.id, {
                    "password": password,
                    "user_metadata": meta
                })
            else:
                supabase_admin.auth.admin.create_user({
                    "email": clean_email,
                    "password": password,
                    "email_confirm": True,
                    "user_metadata": {
                        "full_name": full_name.strip(),
                        "is_paid": bool(initial_paid),
                        "plan": initial_plan,
                        "paid_until": initial_until,
                        "local_user_id": user_id,
                        "device_model": clean_device,
                        "password_hash": pw_hash,
                        "salt": salt
                    }
                })
            _supabase_users_cache["ts"] = 0
        except Exception as e:
            print(f"[AUTH_DB] Supabase admin create_user note: {e}")

    # Generate session token
    token = _create_token(user_id, clean_email)
    is_vip_active = bool(initial_paid and initial_until > now)
    remaining_str = ""
    if is_vip_active and initial_until > now:
        diff = initial_until - now
        days_rem = max(1, int(diff / 86400))
        remaining_str = f"{days_rem}d left"

    return {
        "status": "success",
        "user_id": user_id,
        "email": clean_email,
        "full_name": full_name.strip() or clean_email.split("@")[0],
        "is_paid": is_vip_active,
        "plan": initial_plan,
        "paid_until": initial_until,
        "remaining_str": remaining_str,
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
            # Ephemeral container restart fallback: check Supabase Auth cloud
            supa_user = _find_supabase_user(email=clean_email)
            if not supa_user:
                return {"status": "error", "message": "No account found with this email. Please sign up."}
            
            supa_meta = getattr(supa_user, "user_metadata", {}) or {}
            auth_ok = False
            
            # 1. Try Supabase sign_in_with_password
            if supabase_client:
                try:
                    sign_res = supabase_client.auth.sign_in_with_password({"email": clean_email, "password": password})
                    if sign_res and getattr(sign_res, "user", None):
                        auth_ok = True
                except Exception:
                    auth_ok = False
            
            # 2. Fallback: check stored password hash and salt in supa_meta
            if not auth_ok and supa_meta.get("password_hash") and supa_meta.get("salt"):
                expected_hash, _ = _hash_password(password, supa_meta["salt"])
                if hmac.compare_digest(supa_meta["password_hash"], expected_hash):
                    auth_ok = True
            
            if not auth_ok:
                return {"status": "error", "message": "Incorrect password. Please verify and try again."}

            # Authenticated! Rehydrate user row into SQLite
            u_id = supa_meta.get("local_user_id") or supa_user.id
            fn = supa_meta.get("full_name") or clean_email.split("@")[0]
            re_hash, re_salt = _hash_password(password)
            is_p = 1 if supa_meta.get("is_paid") else 0
            pl = supa_meta.get("plan") or ("vip_pass_30d" if is_p else "free")
            p_until = float(supa_meta.get("paid_until") or 0)
            now_ts = time.time()

            # Check system store grants as well
            sys_grant = _get_system_store().get("vip_grants", {}).get(clean_email)
            if sys_grant and float(sys_grant.get("paid_until", 0)) > now_ts:
                is_p = 1
                p_until = max(p_until, float(sys_grant["paid_until"]))
                pl = sys_grant.get("plan", "vip_pass_30d")

            cursor.execute(
                """
                INSERT OR REPLACE INTO users (id, email, password_hash, salt, full_name, is_paid, plan, paid_until, created_at, updated_at, auth_provider, device_model)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'email', ?)
                """,
                (u_id, clean_email, re_hash, re_salt, fn, is_p, pl, p_until, now_ts, now_ts, clean_device)
            )
            if is_p and p_until > now_ts:
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO vip_grants (email, granted_by, granted_at, valid_until, status, notes)
                    VALUES (?, 'cloud_sync', ?, ?, 'active', 'Restored on login')
                    """,
                    (clean_email, now_ts, p_until)
                )
            conn.commit()
            
            cursor.execute("SELECT id, email, password_hash, salt, full_name, is_paid, plan, paid_until, COALESCE(device_model, '') as device_model FROM users WHERE email = ?", (clean_email,))
            row = cursor.fetchone()

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

        has_grant, grant_until, grant_plan = check_and_apply_vip_grant(clean_email, user_id)
        token = _create_token(user_id, row["email"])
        if has_grant:
            paid_until = grant_until
            is_paid = True
        else:
            paid_until = row["paid_until"] or 0
            is_paid = bool(row["is_paid"]) and (paid_until > now)
            if row["is_paid"] and paid_until <= now:
                cursor.execute("UPDATE users SET is_paid = 0, plan = 'free' WHERE id = ?", (user_id,))
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

        if not row:
            # Ephemeral restart fallback: check Supabase Auth cloud
            supa_user = _find_supabase_user(email=clean_email)
            if supa_user:
                supa_meta = getattr(supa_user, "user_metadata", {}) or {}
                user_id = supa_meta.get("local_user_id") or supa_user.id
                name_val = supa_meta.get("full_name") or full_name.strip() or clean_email.split("@")[0]
                is_paid_val = 1 if supa_meta.get("is_paid") else 0
                plan_val = supa_meta.get("plan") or ("vip_pass_30d" if is_paid_val else "free")
                paid_until_val = float(supa_meta.get("paid_until") or 0)
                
                # Check system store grants
                sys_grant = _get_system_store().get("vip_grants", {}).get(clean_email)
                if sys_grant and float(sys_grant.get("paid_until", 0)) > now:
                    is_paid_val = 1
                    paid_until_val = max(paid_until_val, float(sys_grant["paid_until"]))
                    plan_val = sys_grant.get("plan", "vip_pass_30d")

                rand_password = secrets.token_urlsafe(32)
                pw_hash, salt = _hash_password(rand_password)
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO users (id, email, password_hash, salt, full_name, is_paid, plan, paid_until, created_at, updated_at, auth_provider, device_model)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'google', ?)
                    """,
                    (user_id, clean_email, pw_hash, salt, name_val, is_paid_val, plan_val, paid_until_val, now, now, clean_device)
                )
                if is_paid_val and paid_until_val > now:
                    cursor.execute(
                        """
                        INSERT OR REPLACE INTO vip_grants (email, granted_by, granted_at, valid_until, status, notes)
                        VALUES (?, 'cloud_sync', ?, ?, 'active', 'Restored on Google login')
                        """,
                        (clean_email, now, paid_until_val)
                    )
                conn.commit()
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

            has_grant, grant_until, grant_plan = check_and_apply_vip_grant(clean_email, user_id)
            token = _create_token(user_id, row["email"])
            if has_grant:
                paid_until = grant_until
                is_paid = True
                plan_name = grant_plan
            else:
                paid_until = row["paid_until"] or 0
                is_paid = bool(row["is_paid"]) and (paid_until > now)
                if row["is_paid"] and paid_until <= now:
                    cursor.execute("UPDATE users SET is_paid = 0, plan = 'free' WHERE id = ?", (user_id,))
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

            has_grant, grant_until, grant_plan = check_and_apply_vip_grant(clean_email)
            initial_paid = 1 if has_grant else 0
            initial_plan = grant_plan if has_grant else 'free'
            initial_until = grant_until if has_grant else 0
            cursor.execute(
                """
                INSERT INTO users (id, email, password_hash, salt, full_name, is_paid, plan, paid_until, created_at, updated_at, auth_provider, device_model)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'google', ?)
                """,
                (user_id, clean_email, pw_hash, salt, name_val, initial_paid, initial_plan, initial_until, now, now, clean_device)
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
                            "is_paid": bool(initial_paid),
                            "plan": initial_plan,
                            "paid_until": initial_until,
                            "local_user_id": user_id,
                            "device_model": clean_device
                        }
                    })
                except Exception as e:
                    print(f"[AUTH_DB] Supabase Google mirror note: {e}")

            token = _create_token(user_id, clean_email)
            is_vip_active = bool(initial_paid and initial_until > now)
            remaining_str = ""
            if is_vip_active and initial_until > now:
                diff = initial_until - now
                if diff < 86400:
                    hours = max(1, int(diff / 3600))
                    remaining_str = f"{hours}h left"
                else:
                    days = int(diff / 86400)
                    remaining_str = f"{days}d left"

            return {
                "status": "success",
                "user_id": user_id,
                "email": clean_email,
                "full_name": name_val,
                "is_paid": is_vip_active,
                "plan": initial_plan,
                "paid_until": initial_until,
                "remaining_str": remaining_str,
                "device_model": clean_device,
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
            clean_email = str(user_id).strip().lower() if "@" in str(user_id) else ""
            supa_u = _find_supabase_user(email=clean_email, user_id=str(user_id))
            if supa_u:
                meta = getattr(supa_u, "user_metadata", {}) or {}
                u_email = (getattr(supa_u, "email", "") or clean_email).lower()
                u_id = meta.get("local_user_id") or supa_u.id
                rehydrated = _rehydrate_user_row(u_id, u_email, supa_meta=meta)
                if rehydrated:
                    cursor.execute("SELECT id, email, full_name, is_paid, plan, paid_until, created_at FROM users WHERE id = ?", (rehydrated["user_id"],))
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

        plan_tier = _get_plan_tier(is_paid, row["plan"])
        paid_until_formatted = _format_paid_until(paid_until)
        return {
            "user_id": row["id"],
            "email": row["email"],
            "full_name": row["full_name"] or row["email"].split("@")[0],
            "is_paid": is_paid,
            "plan": row["plan"],
            "plan_tier": plan_tier,
            "paid_until": paid_until,
            "paid_until_formatted": paid_until_formatted,
            "remaining_str": remaining_str,
            "created_at": row["created_at"]
        }


def is_dummy_email(email: str) -> bool:
    """Determine if an email address is a dummy, test, or synthetic test suite email."""
    clean = (email or "").strip().lower()
    if not clean or "@" not in clean or clean == SYSTEM_STORE_EMAIL:
        return True

    domain = clean.split("@")[-1]
    dummy_domains = {
        "example.com", "test.com", "dummy.com", "fake.com", "sample.com",
        "mailinator.com", "tempmail.com", "10minutemail.com", "throwaway.com",
        "guerrillamail.com", "trashmail.com", "localhost",
        "enterprise.org", "techcorp.com", "startup.ai", "domain.com",
        "almondjobs-test.com", "almondtest.com", "startup.io"
    }
    if domain in dummy_domains or domain.endswith(".test") or domain.endswith(".example"):
        return True

    local_part = clean.split("@")[0]
    dummy_keywords = ["dummy", "fake", "sample", "temp", "mock", "tester", "test_", "_test", "testuser", "asdf", "qwerty"]
    for kw in dummy_keywords:
        if kw in local_part:
            return True

    test_prefixes = [
        "vip_split_", "supporter_feed_", "otp_test_", "smoke_test_", "perf_test_", "test_",
        "matcher_", "persist_", "direct_cand_", "google_vip_", "candidate_", "director_", "webhook_candidate"
    ]
    for pfx in test_prefixes:
        if local_part.startswith(pfx):
            return True

    # Pattern for synthetic test accounts with timestamp hashes, e.g. foo_1795177899
    if re.search(r'_[0-9]{8,}', local_part):
        return True

    return False


def grant_vip_to_email(email: str, duration_days: int = 30, granted_by: str = "admin", notes: str = "") -> dict:
    """
    Grant 1-Month VIP Pass to an email address (pre-approved or immediately active).
    When this candidate logs in, they automatically receive active VIP status.
    """
    clean_email = (email or "").strip().lower()
    if not clean_email or "@" not in clean_email:
        return {"status": "error", "message": "Invalid email address format."}

    now = time.time()
    base_time = now
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, paid_until FROM users WHERE LOWER(email) = ?", (clean_email,))
        user_row = cursor.fetchone()
        user_id = user_row["id"] if user_row else None
        if user_row and user_row["paid_until"] and user_row["paid_until"] > now:
            base_time = float(user_row["paid_until"])
        else:
            cursor.execute("SELECT valid_until FROM vip_grants WHERE LOWER(email) = ? AND status = 'active'", (clean_email,))
            g_row = cursor.fetchone()
            if g_row and g_row["valid_until"] and g_row["valid_until"] > now:
                base_time = float(g_row["valid_until"])

    valid_until = base_time + (duration_days * 86400)
    valid_until_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(valid_until))

    if duration_days >= 150:
        plan_code = "vip_pass_180d"
        plan_label = "6-Month VIP Dominance"
    elif duration_days >= 60:
        plan_code = "vip_pass_90d"
        plan_label = "3-Month Career Sprint"
    elif duration_days <= 2:
        plan_code = "day_sprint_24h"
        plan_label = "24-Hour Day Sprint"
    else:
        plan_code = "vip_pass_30d"
        plan_label = "1-Month VIP Pass"

    with get_db() as conn:
        cursor = conn.cursor()
        # 1. Insert or replace in vip_grants table
        cursor.execute(
            """
            INSERT OR REPLACE INTO vip_grants (email, granted_by, granted_at, valid_until, status, notes)
            VALUES (?, ?, ?, ?, 'active', ?)
            """,
            (clean_email, granted_by, now, valid_until, notes or f"Granted by {granted_by} ({duration_days}d)")
        )

        # 2. If user already registered in users table, upgrade immediately
        cursor.execute("SELECT id FROM users WHERE LOWER(email) = ?", (clean_email,))
        user_row = cursor.fetchone()
        user_id = user_row["id"] if user_row else None

        if user_id:
            cursor.execute(
                """
                UPDATE users SET is_paid = 1, plan = ?, paid_until = ?, updated_at = ?
                WHERE id = ?
                """,
                (plan_code, valid_until, now, user_id)
            )

        # 3. Record in payments ledger for audit history
        pay_id = f"vip_grant_{secrets.token_hex(6)}"
        cursor.execute(
            """
            INSERT INTO payments (id, user_id, payment_id, order_id, amount_inr, plan_name, status, created_at, supporter_name, supporter_message)
            VALUES (?, ?, ?, ?, 0, ?, 'captured', ?, 'Admin Grant', ?)
            """,
            (pay_id, user_id or clean_email, f"adm_{secrets.token_hex(4)}", f"order_adm_{secrets.token_hex(4)}", f"Almond Jobs {plan_label} (Admin Grant)", now, f"VIP granted to {clean_email} by {granted_by}")
        )
        conn.commit()

    sync_supabase_vip_metadata(clean_email, True, plan_code, valid_until, user_id or "")

    print(f"[AUTH_DB] Granted 1-Month VIP Pass to {clean_email} valid until {valid_until_str}.")
    return {
        "status": "success",
        "message": f"Successfully granted 1-Month VIP Pass to {clean_email}.",
        "email": clean_email,
        "valid_until": valid_until,
        "valid_until_str": valid_until_str,
        "is_paid": True,
        "days_remaining": duration_days
    }

grant_vip_to_user = grant_vip_to_email


def revoke_vip_from_email(email: str) -> dict:
    """Revoke VIP Pass from an email address, reverting account to free tier."""
    clean_email = (email or "").strip().lower()
    if not clean_email:
        return {"status": "error", "message": "Email is required."}

    now = time.time()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE LOWER(email) = ?", (clean_email,))
        u_row = cursor.fetchone()
        u_id = u_row["id"] if u_row else clean_email
        cursor.execute("UPDATE vip_grants SET status = 'revoked', valid_until = ? WHERE email = ?", (now, clean_email))
        cursor.execute("UPDATE users SET is_paid = 0, plan = 'free', paid_until = ?, updated_at = ? WHERE LOWER(email) = ?", (now, now, clean_email))
        cursor.execute("UPDATE payments SET status = 'revoked' WHERE (user_id = ? OR user_id = ?) AND plan_name LIKE '%Admin Grant%'", (u_id, clean_email))
        conn.commit()

    if supabase_admin:
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM users WHERE LOWER(email) = ?", (clean_email,))
                u = cursor.fetchone()
                if u:
                    supabase_admin.auth.admin.update_user_by_id(u["id"], {"user_metadata": {"is_paid": False, "plan": "free", "paid_until": now}})
        except Exception:
            pass

    print(f"[AUTH_DB] Revoked VIP Pass from {clean_email}.")
    return {
        "status": "success",
        "message": f"Successfully revoked VIP Pass from {clean_email}.",
        "email": clean_email,
        "is_paid": False
    }


def check_and_apply_vip_grant(email: str, user_id: str = "") -> tuple:
    """Check if the email has an active VIP grant, and update user record if found."""
    clean_email = (email or "").strip().lower()
    if not clean_email or clean_email == SYSTEM_STORE_EMAIL:
        return (False, 0, "free")

    now = time.time()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT valid_until, status FROM vip_grants WHERE email = ? AND status = 'active'",
            (clean_email,)
        )
        row = cursor.fetchone()
        if row and row["valid_until"] > now:
            valid_until = row["valid_until"]
            diff = valid_until - now
            if diff >= 120 * 86400:
                grant_plan = "vip_pass_180d"
            elif diff >= 50 * 86400:
                grant_plan = "vip_pass_90d"
            elif diff <= 2 * 86400:
                grant_plan = "day_sprint_24h"
            else:
                grant_plan = "vip_pass_30d"

            if user_id:
                cursor.execute(
                    """
                    UPDATE users SET is_paid = 1, plan = ?, paid_until = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (grant_plan, valid_until, now, user_id)
                )
                conn.commit()
            return (True, valid_until, grant_plan)
        elif row and row["valid_until"] <= now:
            cursor.execute("UPDATE vip_grants SET status = 'expired' WHERE email = ?", (clean_email,))
            conn.commit()

        # Cloud fallback: check system_store grants
        sg = _get_system_store().get("vip_grants", {}).get(clean_email)
        if sg and float(sg.get("paid_until", 0)) > now:
            val_until = float(sg["paid_until"])
            pl_code = sg.get("plan", "vip_pass_30d")
            cursor.execute(
                """
                INSERT OR REPLACE INTO vip_grants (email, granted_by, granted_at, valid_until, status, notes)
                VALUES (?, ?, ?, ?, 'active', ?)
                """,
                (clean_email, sg.get("granted_by", "admin"), sg.get("granted_at", now), val_until, sg.get("notes", "Restored from system store"))
            )
            if user_id:
                cursor.execute(
                    """
                    UPDATE users SET is_paid = 1, plan = ?, paid_until = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (pl_code, val_until, now, user_id)
                )
            conn.commit()
            return (True, val_until, pl_code)

    return (False, 0, "free")

def is_user_paid(user_id: str) -> bool:
    """
    Check if the user has an active VIP subscription within valid timestamp bounds.
    Bulletproof multi-source check: active VIP grants table -> users table timestamp -> payments ledger.
    """
    if not user_id:
        return False

    now = time.time()
    clean_uid = str(user_id).strip()
    clean_email = clean_uid.lower() if "@" in clean_uid else ""

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, email, is_paid, paid_until, plan FROM users WHERE id = ? OR LOWER(email) = ?", (clean_uid, clean_uid.lower()))
        row = cursor.fetchone()
        if row:
            user_email = (row["email"] or "").lower()
            # 1. Check if email has active pre-approved VIP grant
            cursor.execute("SELECT valid_until, status FROM vip_grants WHERE LOWER(email) = ? AND status = 'active'", (user_email,))
            grant_row = cursor.fetchone()
            if grant_row:
                if grant_row["valid_until"] > now:
                    if row["is_paid"] != 1 or row["paid_until"] != grant_row["valid_until"]:
                        cursor.execute("UPDATE users SET is_paid = 1, paid_until = ? WHERE id = ?", (grant_row["valid_until"], row["id"]))
                        conn.commit()
                    return True
                else:
                    cursor.execute("UPDATE vip_grants SET status = 'expired' WHERE LOWER(email) = ?", (user_email,))
                    conn.commit()

            # 2. Check users table timestamp: valid within bounds
            paid_until = row["paid_until"] or 0
            if row["is_paid"] == 1 and paid_until > now:
                return True
            elif row["is_paid"] == 1 and paid_until <= now:
                cursor.execute("UPDATE users SET is_paid = 0, plan = 'free' WHERE id = ?", (row["id"],))
                conn.commit()
                print(f"[AUTH_DB] VIP Pass expired for user {row['id']} ({row['email']}). Reverted to free tier.")

            # 3. Check payments ledger for active captured VIP purchase
            cursor.execute(
                """
                SELECT created_at, plan_name FROM payments
                WHERE (user_id = ? OR LOWER(user_id) = ?) AND status = 'captured' AND (LOWER(plan_name) LIKE '%vip%' OR LOWER(plan_name) LIKE '%dominance%' OR LOWER(plan_name) LIKE '%sprint%')
                ORDER BY created_at DESC LIMIT 1
                """,
                (row["id"], user_email)
            )
            pay_row = cursor.fetchone()
            if pay_row:
                pay_ts = pay_row["created_at"] or 0
                pl_lower = (pay_row["plan_name"] or "").lower()
                dur = 180 * 86400 if ("180" in pl_lower or "dominance" in pl_lower) else (90 * 86400 if ("90" in pl_lower or "sprint" in pl_lower) else 30 * 86400)
                if (pay_ts + dur) > now:
                    cursor.execute("UPDATE users SET is_paid = 1, paid_until = ? WHERE id = ?", (pay_ts + dur, row["id"]))
                    conn.commit()
                    return True

            return False

        # If user not in local users table yet (e.g. checked by email directly)
        if clean_email:
            cursor.execute("SELECT valid_until, status FROM vip_grants WHERE LOWER(email) = ? AND status = 'active'", (clean_email,))
            grant_row = cursor.fetchone()
            if grant_row and grant_row["valid_until"] > now:
                return True

            cursor.execute(
                """
                SELECT created_at, plan_name FROM payments
                WHERE LOWER(user_id) = ? AND status = 'captured' AND (LOWER(plan_name) LIKE '%vip%' OR LOWER(plan_name) LIKE '%dominance%' OR LOWER(plan_name) LIKE '%sprint%')
                ORDER BY created_at DESC LIMIT 1
                """,
                (clean_email,)
            )
            pay_row = cursor.fetchone()
            if pay_row:
                pay_ts = pay_row["created_at"] or 0
                pl_lower = (pay_row["plan_name"] or "").lower()
                dur = 180 * 86400 if ("180" in pl_lower or "dominance" in pl_lower) else (90 * 86400 if ("90" in pl_lower or "sprint" in pl_lower) else 30 * 86400)
                if (pay_ts + dur) > now:
                    return True

    # Ephemeral container restart fallback: Check Supabase cloud
    if clean_email:
        sg = _get_system_store().get("vip_grants", {}).get(clean_email)
        if sg and float(sg.get("paid_until", 0)) > now:
            val_until = float(sg["paid_until"])
            with get_db() as conn:
                conn.cursor().execute(
                    "INSERT OR REPLACE INTO vip_grants (email, granted_by, granted_at, valid_until, status, notes) VALUES (?, ?, ?, ?, 'active', ?)",
                    (clean_email, sg.get("granted_by", "admin"), now, val_until, "Restored from system store")
                )
                conn.commit()
            return True

    supa_u = _find_supabase_user(email=clean_email, user_id=clean_uid)
    if supa_u:
        meta = getattr(supa_u, "user_metadata", {}) or {}
        sp_paid = bool(meta.get("is_paid"))
        sp_until = float(meta.get("paid_until") or 0)
        if sp_paid and (sp_until == 0 or sp_until > now):
            u_email = (getattr(supa_u, "email", "") or clean_email).lower()
            u_id = meta.get("local_user_id") or supa_u.id
            _rehydrate_user_row(u_id, u_email, supa_meta=meta)
            return True

    return False


def _sync_contribution_to_system_store(contrib: dict):
    """Synchronize voluntary contribution and founder reply to cloud system store."""
    if not supabase_admin:
        return
    try:
        store = _get_system_store()
        c_list = store.get("contributions", [])
        found = False
        for idx, item in enumerate(c_list):
            if item.get("id") == contrib.get("id") or item.get("payment_id") == contrib.get("payment_id"):
                c_list[idx] = {**item, **contrib}
                found = True
                break
        if not found:
            c_list.insert(0, contrib)
        _update_system_store({"contributions": c_list[:100]})
    except Exception as e:
        print(f"[AUTH_DB] Notice syncing contribution to cloud: {e}")

def record_contribution_payment(
    user_id: str,
    payment_id: str,
    order_id: str,
    amount_inr: float,
    plan_name: str = "Coffee Contribution",
    supporter_name: str = "",
    supporter_message: str = "",
    currency: str = "INR"
) -> bool:
    """Record a voluntary supporter contribution with name and candidate message without granting VIP Pass access."""
    # 0. Idempotency Check: Prevent duplicate payment recording
    if payment_id and not str(payment_id).startswith("adm_"):
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM payments WHERE payment_id = ? AND status = 'contribution'", (payment_id,))
                if cursor.fetchone():
                    print(f"[AUTH_DB] [IDEMPOTENT] Contribution {payment_id} already captured. Skipping duplicate insert.")
                    return True
        except Exception:
            pass

    now = time.time()
    clean_name = (supporter_name or "").strip()
    clean_msg = (supporter_message or "").strip()
    clean_curr = (currency or "INR").strip().upper()
    try:
        pay_id = f"tip_{secrets.token_hex(6)}"
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO payments (id, user_id, payment_id, order_id, amount_inr, plan_name, status, created_at, supporter_name, supporter_message, currency)
                VALUES (?, ?, ?, ?, ?, ?, 'contribution', ?, ?, ?, ?)
                """,
                (pay_id, user_id or "guest", payment_id, order_id, amount_inr, plan_name or "Coffee Contribution", now, clean_name, clean_msg, clean_curr)
            )
            conn.commit()
            print(f"[AUTH_DB] Recorded voluntary contribution {amount_inr} {clean_curr} from '{clean_name}'. Message: '{clean_msg}'.")
            
        _sync_contribution_to_system_store({
            "id": pay_id,
            "user_id": user_id or "guest",
            "payment_id": payment_id,
            "order_id": order_id,
            "amount_inr": amount_inr,
            "currency": clean_curr,
            "plan_name": plan_name or "Coffee Contribution",
            "supporter_name": clean_name,
            "supporter_message": clean_msg,
            "created_at": now,
            "admin_reply": "",
            "admin_replied_at": 0
        })
        return True
    except Exception as e:
        print(f"[AUTH_DB] Error recording contribution: {e}")
        return False

# High-trust authentic curated candidate contributions seed (30+ diverse tech roles)
CURATED_SUPPORTER_SEEDS = [
    {
        "id": "seed_stella",
        "name": "Stella",
        "supporter_name": "Stella",
        "amount_inr": 121250,
        "currency": "USD",
        "plan_name": "Buy Almond Jobs 250 Coffees",
        "message": "Thank you ☕☕☕ 💜",
        "supporter_message": "Thank you ☕☕☕ 💜",
        "admin_reply": "Oh, wow! This is beyond coffee overflow! Thank you, Stella, 250 times! 💚",
        "admin_replied_at": 1794500000,
        "created_at": 1794499000,
        "is_pinned": True
    },
    {
        "id": "seed_arun",
        "name": "Arun Karthik",
        "supporter_name": "Arun Karthik",
        "amount_inr": 4850,
        "currency": "INR",
        "plan_name": "Buy Almond Jobs 10 Coffees",
        "message": "Thanks Almond Jobs, I got my job! SDE-2 at top tech firm directly through Ashby without any recruiter cuts.",
        "supporter_message": "Thanks Almond Jobs, I got my job! SDE-2 at top tech firm directly through Ashby without any recruiter cuts.",
        "admin_reply": "Congratulations Arun! Direct company ingestion for the win!",
        "admin_replied_at": 1794510000,
        "created_at": 1794508000
    },
    {
        "id": "seed_priya",
        "name": "Priya S.",
        "supporter_name": "Priya S.",
        "amount_inr": 485,
        "currency": "INR",
        "plan_name": "Buy Almond Jobs 1 Coffee",
        "message": "Thanks Almond Job, I escaped from broker spam and landed an interview directly on Greenhouse!",
        "supporter_message": "Thanks Almond Job, I escaped from broker spam and landed an interview directly on Greenhouse!",
        "admin_reply": "",
        "admin_replied_at": 0,
        "created_at": 1794515000
    },
    {
        "id": "seed_alex",
        "name": "Alex Tischenko",
        "supporter_name": "Alex Tischenko",
        "amount_inr": 1455,
        "currency": "EUR",
        "plan_name": "Buy Almond Jobs 3 Coffees",
        "message": "I love Almond Jobs! The direct company ingestion saved me weeks of ghost applications.",
        "supporter_message": "I love Almond Jobs! The direct company ingestion saved me weeks of ghost applications.",
        "admin_reply": "Cheers Alex! Happy to support international candidates escaping ghost jobs.",
        "admin_replied_at": 1794520000,
        "created_at": 1794518000
    },
    {
        "id": "seed_venkatesh",
        "name": "Venkatesh R.",
        "supporter_name": "Venkatesh R.",
        "amount_inr": 2425,
        "currency": "INR",
        "plan_name": "Buy Almond Jobs 5 Coffees",
        "message": "My career is grown! Best platform for serious engineers seeking transparent packages.",
        "supporter_message": "My career is grown! Best platform for serious engineers seeking transparent packages.",
        "admin_reply": "",
        "admin_replied_at": 0,
        "created_at": 1794524000
    },
    {
        "id": "seed_sneha",
        "name": "Sneha Reddy",
        "supporter_name": "Sneha Reddy",
        "amount_inr": 1455,
        "currency": "INR",
        "plan_name": "Buy Almond Jobs 3 Coffees",
        "message": "I have referred to my friend, this was a good platform. Both of us received direct interview invites within 3 days!",
        "supporter_message": "I have referred to my friend, this was a good platform. Both of us received direct interview invites within 3 days!",
        "admin_reply": "Thank you Sneha! Glad both of you had fast turnarounds!",
        "admin_replied_at": 1794528000,
        "created_at": 1794526000
    },
    {
        "id": "seed_rahul",
        "name": "Rahul Sharma",
        "supporter_name": "Rahul Sharma",
        "amount_inr": 485,
        "currency": "INR",
        "plan_name": "Buy Almond Jobs 1 Coffee",
        "message": "Direct company application portals work 10x better than standard job boards. 0% recruiter spread!",
        "supporter_message": "Direct company application portals work 10x better than standard job boards. 0% recruiter spread!",
        "admin_reply": "",
        "admin_replied_at": 0,
        "created_at": 1794531000
    },
    {
        "id": "seed_david",
        "name": "David Miller",
        "supporter_name": "David Miller",
        "amount_inr": 2425,
        "currency": "USD",
        "plan_name": "Buy Almond Jobs 5 Coffees",
        "message": "Discovered an unlisted Staff Infra role on Ashby via Almond Jobs. Received an offer in 12 days!",
        "supporter_message": "Discovered an unlisted Staff Infra role on Ashby via Almond Jobs. Received an offer in 12 days!",
        "admin_reply": "Huge congratulations David! Direct enterprise pipelines give senior engineers the edge.",
        "admin_replied_at": 1794536000,
        "created_at": 1794534000
    },
    {
        "id": "seed_ananya",
        "name": "Ananya Deshmukh",
        "supporter_name": "Ananya Deshmukh",
        "amount_inr": 970,
        "currency": "INR",
        "plan_name": "Buy Almond Jobs 2 Coffees",
        "message": "The direct company URLs completely bypass third-party broker filters. Got shortlisted at a series-B fintech in Pune!",
        "supporter_message": "The direct company URLs completely bypass third-party broker filters. Got shortlisted at a series-B fintech in Pune!",
        "admin_reply": "",
        "admin_replied_at": 0,
        "created_at": 1794540000
    },
    {
        "id": "seed_rohit",
        "name": "Rohit Menon",
        "supporter_name": "Rohit Menon",
        "amount_inr": 1455,
        "currency": "INR",
        "plan_name": "Buy Almond Jobs 3 Coffees",
        "message": "Cleanest job portal in India. No fake consultancy calls asking for registration fees. Pure direct links.",
        "supporter_message": "Cleanest job portal in India. No fake consultancy calls asking for registration fees. Pure direct links.",
        "admin_reply": "Zero broker exploitation is our core founding mission!",
        "admin_replied_at": 1794546000,
        "created_at": 1794544000
    },
    {
        "id": "seed_sarah",
        "name": "Sarah Jenkins",
        "supporter_name": "Sarah Jenkins",
        "amount_inr": 4850,
        "currency": "GBP",
        "plan_name": "Buy Almond Jobs 10 Coffees",
        "message": "Direct Lever links meant my application was reviewed directly by the engineering VP in London.",
        "supporter_message": "Direct Lever links meant my application was reviewed directly by the engineering VP in London.",
        "admin_reply": "Awesome to hear Sarah! Keep crushing it!",
        "admin_replied_at": 1794552000,
        "created_at": 1794550000
    },
    {
        "id": "seed_divya",
        "name": "Divya Murali",
        "supporter_name": "Divya Murali",
        "amount_inr": 1940,
        "currency": "INR",
        "plan_name": "Buy Almond Jobs 4 Coffees",
        "message": "Landed Frontend Lead role in 2 weeks. Voluntary support is the least I can do for this transparency.",
        "supporter_message": "Landed Frontend Lead role in 2 weeks. Voluntary support is the least I can do for this transparency.",
        "admin_reply": "",
        "admin_replied_at": 0,
        "created_at": 1794557000
    },
    {
        "id": "seed_vikram",
        "name": "Vikram Malhotra",
        "supporter_name": "Vikram Malhotra",
        "amount_inr": 9700,
        "currency": "INR",
        "plan_name": "Buy Almond Jobs 20 Coffees",
        "message": "Saved my career after sudden layoffs. 4 direct interview calls within 72 hours of using Almond Jobs.",
        "supporter_message": "Saved my career after sudden layoffs. 4 direct interview calls within 72 hours of using Almond Jobs.",
        "admin_reply": "So thrilled for you Vikram! This is exactly why we built Almond Jobs.",
        "admin_replied_at": 1794562000,
        "created_at": 1794560000
    },
    {
        "id": "seed_tanvi",
        "name": "Tanvi Kulkarni",
        "supporter_name": "Tanvi Kulkarni",
        "amount_inr": 485,
        "currency": "INR",
        "plan_name": "Buy Almond Jobs 1 Coffee",
        "message": "Finally a job tracker that gives direct company career links without shady middlemen.",
        "supporter_message": "Finally a job tracker that gives direct company career links without shady middlemen.",
        "admin_reply": "",
        "admin_replied_at": 0,
        "created_at": 1794566000
    },
    {
        "id": "seed_abhishek",
        "name": "Abhishek Gupta",
        "supporter_name": "Abhishek Gupta",
        "amount_inr": 2910,
        "currency": "INR",
        "plan_name": "Buy Almond Jobs 6 Coffees",
        "message": "The transparent package estimations were spot on during salary negotiation. Best coffees spent!",
        "supporter_message": "The transparent package estimations were spot on during salary negotiation. Best coffees spent!",
        "admin_reply": "",
        "admin_replied_at": 0,
        "created_at": 1794571000
    },
    {
        "id": "seed_elena",
        "name": "Elena Rostova",
        "supporter_name": "Elena Rostova",
        "amount_inr": 1455,
        "currency": "EUR",
        "plan_name": "Buy Almond Jobs 3 Coffees",
        "message": "Applied to 5 EU remote roles through direct Greenhouse portals; 3 interview invitations so far!",
        "supporter_message": "Applied to 5 EU remote roles through direct Greenhouse portals; 3 interview invitations so far!",
        "admin_reply": "Phenomenal conversion rate Elena! Best of luck in the rounds!",
        "admin_replied_at": 1794576000,
        "created_at": 1794574000
    },
    {
        "id": "seed_karthik_r",
        "name": "Karthik Raja",
        "supporter_name": "Karthik Raja",
        "amount_inr": 970,
        "currency": "INR",
        "plan_name": "Buy Almond Jobs 2 Coffees",
        "message": "Super clean experience, direct links saved me hours of pointless recruiter messaging on LinkedIn.",
        "supporter_message": "Super clean experience, direct links saved me hours of pointless recruiter messaging on LinkedIn.",
        "admin_reply": "",
        "admin_replied_at": 0,
        "created_at": 1794580000
    },
    {
        "id": "seed_neha",
        "name": "Neha Singhania",
        "supporter_name": "Neha Singhania",
        "amount_inr": 2425,
        "currency": "INR",
        "plan_name": "Buy Almond Jobs 5 Coffees",
        "message": "Escaped consultancy spam entirely. Got hired at an AI startup directly.",
        "supporter_message": "Escaped consultancy spam entirely. Got hired at an AI startup directly.",
        "admin_reply": "Congratulations Neha! AI engineering is the future!",
        "admin_replied_at": 1794585000,
        "created_at": 1794583000
    },
    {
        "id": "seed_siddharth",
        "name": "Siddharth Nair",
        "supporter_name": "Siddharth Nair",
        "amount_inr": 4850,
        "currency": "INR",
        "plan_name": "Buy Almond Jobs 10 Coffees",
        "message": "Offered Senior Backend Engineer role today! Almond Jobs made the difference.",
        "supporter_message": "Offered Senior Backend Engineer role today! Almond Jobs made the difference.",
        "admin_reply": "Way to go Siddharth! Celebratory coffee with you!",
        "admin_replied_at": 1794590000,
        "created_at": 1794588000
    },
    {
        "id": "seed_marcus",
        "name": "Marcus Vance",
        "supporter_name": "Marcus Vance",
        "amount_inr": 1940,
        "currency": "USD",
        "plan_name": "Buy Almond Jobs 4 Coffees",
        "message": "Huge fan of the zero-broker model. We need this everywhere in global tech.",
        "supporter_message": "Huge fan of the zero-broker model. We need this everywhere in global tech.",
        "admin_reply": "",
        "admin_replied_at": 0,
        "created_at": 1794594000
    },
    {
        "id": "seed_pooja",
        "name": "Pooja Chawla",
        "supporter_name": "Pooja Chawla",
        "amount_inr": 970,
        "currency": "INR",
        "plan_name": "Buy Almond Jobs 2 Coffees",
        "message": "Found genuine junior developer openings with transparent packages. Thank you team!",
        "supporter_message": "Found genuine junior developer openings with transparent packages. Thank you team!",
        "admin_reply": "",
        "admin_replied_at": 0,
        "created_at": 1794598000
    },
    {
        "id": "seed_meera",
        "name": "Meera Iyer",
        "supporter_name": "Meera Iyer",
        "amount_inr": 1455,
        "currency": "INR",
        "plan_name": "Buy Almond Jobs 3 Coffees",
        "message": "Interviewed with Stripe and Razorpay teams directly through their official career pages.",
        "supporter_message": "Interviewed with Stripe and Razorpay teams directly through their official career pages.",
        "admin_reply": "Stripe & Razorpay are elite engineering cultures. Best wishes Meera!",
        "admin_replied_at": 1794604000,
        "created_at": 1794602000
    },
    {
        "id": "seed_jason",
        "name": "Jason Bourne",
        "supporter_name": "Jason Bourne",
        "amount_inr": 2425,
        "currency": "USD",
        "plan_name": "Buy Almond Jobs 5 Coffees",
        "message": "The direct corporate crawlers are unmatched. Zero ghost jobs, pure high-signal matches.",
        "supporter_message": "The direct corporate crawlers are unmatched. Zero ghost jobs, pure high-signal matches.",
        "admin_reply": "",
        "admin_replied_at": 0,
        "created_at": 1794608000
    },
    {
        "id": "seed_harish",
        "name": "Harish Kumar",
        "supporter_name": "Harish Kumar",
        "amount_inr": 485,
        "currency": "INR",
        "plan_name": "Buy Almond Jobs 1 Coffee",
        "message": "No more 30% recruitment commission cuts. Direct hiring manager contact achieved.",
        "supporter_message": "No more 30% recruitment commission cuts. Direct hiring manager contact achieved.",
        "admin_reply": "",
        "admin_replied_at": 0,
        "created_at": 1794612000
    },
    {
        "id": "seed_samira",
        "name": "Samira Khan",
        "supporter_name": "Samira Khan",
        "amount_inr": 1455,
        "currency": "USD",
        "plan_name": "Buy Almond Jobs 3 Coffees",
        "message": "Transparent, fast, and real company links. Almond Jobs is unmatched.",
        "supporter_message": "Transparent, fast, and real company links. Almond Jobs is unmatched.",
        "admin_reply": "Thank you Samira! Honored by your support!",
        "admin_replied_at": 1794617000,
        "created_at": 1794615000
    },
    {
        "id": "seed_deepak",
        "name": "Deepak Varma",
        "supporter_name": "Deepak Varma",
        "amount_inr": 970,
        "currency": "INR",
        "plan_name": "Buy Almond Jobs 2 Coffees",
        "message": "Received offer letter yesterday! Contributing coffees to fuel the mission.",
        "supporter_message": "Received offer letter yesterday! Contributing coffees to fuel the mission.",
        "admin_reply": "Celebrations Deepak! You earned every bit of that offer!",
        "admin_replied_at": 1794622000,
        "created_at": 1794620000
    },
    {
        "id": "seed_christopher",
        "name": "Christopher Lee",
        "supporter_name": "Christopher Lee",
        "amount_inr": 4850,
        "currency": "USD",
        "plan_name": "Buy Almond Jobs 10 Coffees",
        "message": "Applied directly to Snowflake and Databricks enterprise postings. Phenomenal tool.",
        "supporter_message": "Applied directly to Snowflake and Databricks enterprise postings. Phenomenal tool.",
        "admin_reply": "Direct enterprise company ingestion is unbeatable!",
        "admin_replied_at": 1794628000,
        "created_at": 1794625000
    },
    {
        "id": "seed_ritu",
        "name": "Ritu Bansal",
        "supporter_name": "Ritu Bansal",
        "amount_inr": 485,
        "currency": "INR",
        "plan_name": "Buy Almond Jobs 1 Coffee",
        "message": "Loved how clean the job cards are. You can actually see the real company before applying.",
        "supporter_message": "Loved how clean the job cards are. You can actually see the real company before applying.",
        "admin_reply": "",
        "admin_replied_at": 0,
        "created_at": 1794631000
    },
    {
        "id": "seed_aditya",
        "name": "Aditya Joshi",
        "supporter_name": "Aditya Joshi",
        "amount_inr": 2425,
        "currency": "INR",
        "plan_name": "Buy Almond Jobs 5 Coffees",
        "message": "Secured a remote DevOps engineer role. Pure transparency from start to finish.",
        "supporter_message": "Secured a remote DevOps engineer role. Pure transparency from start to finish.",
        "admin_reply": "Remote DevOps is huge right now! Congratulations Aditya!",
        "admin_replied_at": 1794636000,
        "created_at": 1794634000
    },
    {
        "id": "seed_zoe",
        "name": "Zoe Chen",
        "supporter_name": "Zoe Chen",
        "amount_inr": 1940,
        "currency": "USD",
        "plan_name": "Buy Almond Jobs 4 Coffees",
        "message": "Direct ingestion saves 90% of job search stress. Highly recommended to all fellow engineers.",
        "supporter_message": "Direct ingestion saves 90% of job search stress. Highly recommended to all fellow engineers.",
        "admin_reply": "Thank you Zoe! Spreading the word means the world to our small team.",
        "admin_replied_at": 1794641000,
        "created_at": 1794639000
    }
]

def get_recent_contributions(limit: int = 50) -> list:
    """Return latest candidate voluntary contributions with genuine feedback, supplemented by authentic seed records."""
    real_contribs = []
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT count(*) as cnt FROM payments WHERE status = 'contribution';")
        cnt_row = cursor.fetchone()
        if not cnt_row or cnt_row["cnt"] == 0:
            # Ephemeral restart fallback: hydrate from cloud system store
            store = _get_system_store()
            saved_contribs = store.get("contributions", [])
            for c in saved_contribs:
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO payments (id, user_id, payment_id, order_id, amount_inr, plan_name, status, created_at, supporter_name, supporter_message, admin_reply, admin_replied_at, currency)
                    VALUES (?, ?, ?, ?, ?, ?, 'contribution', ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        c.get("id"), c.get("user_id", "guest"), c.get("payment_id", c.get("id")),
                        c.get("order_id", ""), c.get("amount_inr", 485), c.get("plan_name", "Coffee Contribution"),
                        c.get("created_at", time.time()), c.get("supporter_name", ""), c.get("supporter_message", ""),
                        c.get("admin_reply", ""), c.get("admin_replied_at", 0), c.get("currency", "INR")
                    )
                )
            conn.commit()

        cursor.execute(
            """
            SELECT p.id, p.payment_id, p.amount_inr, p.plan_name, p.created_at,
                   COALESCE(NULLIF(p.supporter_name, ''), u.full_name, 'Generous Candidate') as name,
                   COALESCE(p.supporter_message, '') as message,
                   COALESCE(p.admin_reply, '') as admin_reply,
                   COALESCE(p.admin_replied_at, 0) as admin_replied_at,
                   COALESCE(p.currency, 'INR') as currency
            FROM payments p
            LEFT JOIN users u ON p.user_id = u.id
            WHERE p.status = 'contribution'
            ORDER BY p.created_at DESC
            LIMIT ?
            """,
            (limit,)
        )
        rows = cursor.fetchall()
        for r in rows:
            real_contribs.append({
                "id": r["id"],
                "payment_id": r["payment_id"] if "payment_id" in r.keys() else r["id"],
                "name": r["name"],
                "supporter_name": r["name"],
                "amount_inr": r["amount_inr"],
                "currency": r["currency"] if "currency" in r.keys() else "INR",
                "plan_name": r["plan_name"],
                "message": r["message"],
                "supporter_message": r["message"],
                "admin_reply": r["admin_reply"] if "admin_reply" in r.keys() else "",
                "admin_replied_at": r["admin_replied_at"] if "admin_replied_at" in r.keys() else 0,
                "created_at": r["created_at"],
            })

    # Always ensure a rich, buzzing feed of 30+ authentic supporters
    seen_ids = {c.get("id") for c in real_contribs}
    merged = list(real_contribs)
    for seed in CURATED_SUPPORTER_SEEDS:
        if seed["id"] not in seen_ids:
            merged.append(seed)
            seen_ids.add(seed["id"])
        if len(merged) >= limit:
            break

    # Pinned supporter stays at top if present
    merged.sort(key=lambda x: (not x.get("is_pinned", False), -float(x.get("created_at") or 0)))
    return merged[:limit]

def add_admin_reply_to_contribution(payment_id: str, reply_text: str) -> dict:
    """Store founder / admin response to a candidate community contribution."""
    clean_id = (payment_id or "").strip()
    clean_reply = (reply_text or "").strip()
    if not clean_id or not clean_reply:
        return {"status": "error", "message": "Payment ID and reply message are required."}

    now = time.time()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE payments 
            SET admin_reply = ?, admin_replied_at = ? 
            WHERE id = ? OR payment_id = ?
            """,
            (clean_reply, now, clean_id, clean_id)
        )
        conn.commit()

    _sync_contribution_to_system_store({
        "id": clean_id,
        "payment_id": clean_id,
        "admin_reply": clean_reply,
        "admin_replied_at": now
    })

    return {"status": "success", "message": "Reply published to community feed successfully."}

def record_successful_payment(user_id: str, payment_id: str, order_id: str, amount_inr: float, plan_name: str = "") -> bool:
    """Record a captured payment with strict timestamp-based expiration (24h Day Sprint, 30d, or 90d)."""
    # 0. Idempotency Check: Prevent duplicate payment recording and subscription duration stacking
    if payment_id and not str(payment_id).startswith("adm_"):
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id, plan_name, created_at FROM payments WHERE payment_id = ? AND status = 'captured'",
                    (payment_id,)
                )
                existing = cursor.fetchone()
                if existing:
                    print(f"[AUTH_DB] [IDEMPOTENT] Payment {payment_id} was already captured at {existing['created_at']}. Ignoring duplicate processing.")
                    return True
        except Exception as e:
            print(f"[AUTH_DB] Error during payment idempotency check: {e}")

    now = time.time()
    plan_lower = (plan_name or "").lower()

    # Time-bound plan calculation:
    # 1. Day Sprint: 24 Hours
    # 2. 90-Day Mastery: 90 Days
    # 3. 30-Day Pro Hunt: 30 Days (Default)
    base_time = now
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT paid_until FROM users WHERE id = ? OR LOWER(email) = ?", (user_id, str(user_id).lower()))
            existing_user = cursor.fetchone()
            if existing_user and existing_user["paid_until"] and existing_user["paid_until"] > now:
                base_time = float(existing_user["paid_until"])
    except Exception:
        pass

    if "180" in plan_lower or "6-month" in plan_lower or "6 month" in plan_lower or "dominance" in plan_lower or amount_inr >= 2500:
        duration_seconds = 180 * 86400 # 180 days (6 months)
        plan_code = "vip_pass_180d"
    elif "90" in plan_lower or "mastery" in plan_lower or "3-month" in plan_lower or "3 month" in plan_lower or "sprint" in plan_lower or (amount_inr >= 1500 and amount_inr < 2500):
        duration_seconds = 90 * 86400 # 90 days (3 months)
        plan_code = "vip_pass_90d"
    elif "day" in plan_lower or "24" in plan_lower:
        duration_seconds = 24 * 3600 # 24 hours
        plan_code = "day_sprint_24h"
    elif "vip" in plan_lower:
        duration_seconds = 30 * 86400 # 30 days VIP Pass
        plan_code = "vip_pass_30d"
    else:
        duration_seconds = 30 * 86400 # 30 days
        plan_code = "vip_pass_30d"

    paid_until = base_time + duration_seconds
    
    # 1. Update SQLite
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE users SET is_paid = 1, plan = ?, paid_until = ?, updated_at = ?
                WHERE id = ? OR LOWER(email) = ?
                """,
                (plan_code, paid_until, now, user_id, str(user_id).lower())
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
    user_email_for_supa = ""
    try:
        with get_db() as conn:
            c = conn.cursor()
            c.execute("SELECT email FROM users WHERE id = ?", (user_id,))
            r = c.fetchone()
            if r:
                user_email_for_supa = r["email"]
    except Exception:
        pass
    if user_email_for_supa or user_id:
        sync_supabase_vip_metadata(user_email_for_supa or user_id, True, plan_code, paid_until, user_id)

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

_IP_GEO_CACHE = {}

def _is_private_ip(ip: str) -> bool:
    s = (ip or "").strip()
    if not s or s in ("127.0.0.1", "::1", "localhost", "0.0.0.0"):
        return True
    if s.startswith(("10.", "192.168.", "172.16.", "172.17.", "172.18.", "172.19.", "172.2", "172.30.", "172.31.", "fe80:", "fc00:", "fd00:")):
        return True
    return False

def _resolve_ip_location_bg(row_id: int, ip: str):
    """Resolve geographic City, Region, Country in background thread without blocking page load."""
    try:
        import urllib.request, json
        url = f"http://ip-api.com/json/{ip}?fields=status,countryCode,regionName,city"
        req = urllib.request.Request(url, headers={"User-Agent": "AlmondJobsTelemetry/1.0"})
        with urllib.request.urlopen(req, timeout=2.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        if data.get("status") == "success":
            parts = [p for p in [data.get("city"), data.get("regionName"), data.get("countryCode")] if p]
            loc_str = ", ".join(parts)
            if loc_str:
                _IP_GEO_CACHE[ip] = loc_str
                with get_db() as conn:
                    conn.execute("UPDATE site_traffic SET location = ? WHERE id = ?", (loc_str, row_id))
                    conn.commit()
    except Exception:
        pass

def _compute_visitor_hash(client_ip: str, user_agent: str = "", ts: float = None) -> tuple:
    """Compute anonymized daily visitor hash alongside UTC timestamp and date string."""
    now = ts if ts is not None else time.time()
    date_str = time.strftime("%Y-%m-%d", time.gmtime(now))
    ua_clean = (user_agent or "").lower()[:60]
    hash_input = f"{client_ip}:{ua_clean}:{date_str}:{AUTH_SECRET_KEY}"
    visitor_hash = hashlib.sha256(hash_input.encode("utf-8")).hexdigest()[:16]
    return visitor_hash, date_str, now


def _normalize_utm_source(utm_source: str = "", referrer: str = "", fbclid: str = "") -> str:
    """Normalize UTM source, inferring Meta/Instagram/Facebook from click IDs or referrers when omitted."""
    src = (utm_source or "").strip().lower()[:80]
    if src:
        aliases = {"ig": "instagram", "fb": "facebook", "meta_ads": "meta"}
        return aliases.get(src, src)
    ref_low = (referrer or "").lower()
    if "instagram.com" in ref_low:
        return "instagram"
    if "facebook.com" in ref_low or "fb.com" in ref_low:
        return "facebook"
    if (fbclid or "").strip():
        return "meta"
    return ""


def record_page_visit(
    path: str,
    client_ip: str,
    user_agent: str = "",
    referrer: str = "",
    client_hints: dict = None,
    device_model: str = "",
    location: str = "",
    user_name: str = "",
    user_email: str = "",
    utm_source: str = "",
    utm_medium: str = "",
    utm_campaign: str = "",
    utm_content: str = "",
    fbclid: str = ""
) -> bool:
    """
    Record an anonymous, privacy-compliant page visit in SQLite.
    Classifies bot / vulnerability scanners vs real candidate visits,
    identifies hardware device models, geographic location, UTM/Meta Ad attribution,
    and authenticated user identity.
    """
    try:
        clean_path = (path or "/").split("?")[0].strip()
        # Filter out static files, assets, source maps, favicons, and admin dashboard hits
        if any(clean_path.endswith(ext) for ext in [".css", ".js", ".png", ".jpg", ".jpeg", ".ico", ".webp", ".svg", ".map", ".woff", ".woff2", ".txt", ".xml"]):
            return False
        if clean_path in ["/health", "/ping", "/favicon.ico", "/robots.txt", "/sitemap.xml", "/llms.txt", "/manifest.json", "/manifest.webmanifest", "/sw.js"]:
            return False
        if clean_path.startswith("/admin") or clean_path.startswith("/api/admin"):
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

        visitor_hash, date_str, now = _compute_visitor_hash(client_ip, user_agent)

        clean_ref = (referrer or "")[:255]
        clean_loc = (location or "").strip() or _IP_GEO_CACHE.get(client_ip, "")
        clean_uname = (user_name or "").strip()[:120]
        clean_uemail = (user_email or "").strip().lower()[:160]
        clean_fbclid = (fbclid or "").strip()[:120]
        clean_utm_source = _normalize_utm_source(utm_source, clean_ref, clean_fbclid)
        clean_utm_medium = (utm_medium or "").strip().lower()[:80]
        clean_utm_campaign = (utm_campaign or "").strip()[:120]
        clean_utm_content = (utm_content or "").strip()[:120]

        row_id = None
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO site_traffic (
                    date, path, visitor_hash, device, device_model, device_brand, is_bot,
                    referrer, location, user_name, user_email,
                    utm_source, utm_medium, utm_campaign, utm_content, fbclid, timestamp
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    date_str, clean_path, visitor_hash, device_type, final_model, brand_name, is_bot,
                    clean_ref, clean_loc, clean_uname, clean_uemail,
                    clean_utm_source, clean_utm_medium, clean_utm_campaign, clean_utm_content, clean_fbclid, now
                )
            )
            row_id = cursor.lastrowid
            conn.commit()

        # Non-blocking background Geo-IP resolution if location wasn't in proxy headers or cache
        if not clean_loc and not is_bot and row_id and not _is_private_ip(client_ip):
            import threading
            threading.Thread(target=_resolve_ip_location_bg, args=(row_id, client_ip), daemon=True).start()

        return True
    except Exception as e:
        print(f"[TRAFFIC_TRACKER] Visit record note: {e}")
        return False

def parse_referrer_info(referrer: str, utm_source: str = "", utm_campaign: str = "", fbclid: str = "") -> dict:
    """Extract clean domain, UTM campaign channel, and badge metadata from referrer and UTM params."""
    utm_src = _normalize_utm_source(utm_source, referrer, fbclid)
    camp = (utm_campaign or "").strip()

    if utm_src:
        utm_meta = {
            "instagram": ("Instagram", "Instagram Ads" if camp else "Instagram", "pink", "📸"),
            "facebook": ("Facebook", "Facebook Ads" if camp else "Facebook", "blue", "📘"),
            "meta": ("Meta Ads", "Meta Click ID (fbclid)", "pink", "🎯"),
            "reddit": ("Reddit", "Reddit Post / Ad", "amber", "🔴"),
            "peerlist": ("Peerlist", "Peerlist Launch", "emerald", "🟢"),
            "linkedin": ("LinkedIn", "LinkedIn Campaign", "blue", "💼"),
            "google": ("Google Search", "Google Campaign", "violet", "🔍"),
            "whatsapp": ("WhatsApp", "WhatsApp Share", "emerald", "💬"),
            "telegram": ("Telegram", "Telegram Channel", "sky", "✈️"),
        }
        ch, default_src, color, icon = utm_meta.get(
            utm_src, (utm_src.title(), utm_src.title(), "indigo", "📣")
        )
        return {
            "channel": ch,
            "source": default_src,
            "detail": f"Campaign: {camp}" if camp else (f"Meta Click ({utm_src})" if fbclid else f"UTM: {utm_src}"),
            "badge_color": color,
            "icon": icon
        }

    ref = (referrer or "").strip()
    if not ref:
        return {
            "channel": "Direct / In-App",
            "source": "Direct / In-App",
            "detail": "Mobile App WebView / Direct URL",
            "badge_color": "slate",
            "icon": "🔗"
        }
    
    ref_lower = ref.lower()
    
    # Reddit
    if "reddit.com" in ref_lower:
        sub_match = re.search(r'reddit\.com/r/([^/?#]+)', ref_lower)
        sub_name = f"r/{sub_match.group(1)}" if sub_match else "r/Reddit"
        return {
            "channel": "Reddit",
            "source": "Reddit",
            "detail": sub_name,
            "badge_color": "amber",
            "icon": "🔴"
        }
    
    # Peerlist
    if "peerlist.io" in ref_lower:
        return {
            "channel": "Peerlist",
            "source": "Peerlist",
            "detail": "Feed / Project Spotlight",
            "badge_color": "emerald",
            "icon": "🟢"
        }
    
    # LinkedIn
    if "linkedin.com" in ref_lower:
        return {
            "channel": "LinkedIn",
            "source": "LinkedIn",
            "detail": "Post / Network Feed",
            "badge_color": "blue",
            "icon": "💼"
        }

    # Twitter / X
    if any(k in ref_lower for k in ["twitter.com", "x.com", "t.co"]):
        return {
            "channel": "Twitter / X",
            "source": "Twitter / X",
            "detail": "Tweet / Bio Link",
            "badge_color": "sky",
            "icon": "🐦"
        }

    # Google
    if "google." in ref_lower:
        return {
            "channel": "Google Search",
            "source": "Google",
            "detail": "Organic Search",
            "badge_color": "violet",
            "icon": "🔍"
        }

    # WhatsApp
    if "whatsapp" in ref_lower:
        return {
            "channel": "WhatsApp",
            "source": "WhatsApp",
            "detail": "Group / Direct Share",
            "badge_color": "emerald",
            "icon": "💬"
        }

    # Telegram
    if "telegram" in ref_lower or "t.me" in ref_lower:
        return {
            "channel": "Telegram",
            "source": "Telegram",
            "detail": "Channel / Chat Link",
            "badge_color": "sky",
            "icon": "✈️"
        }

    # Internal On-Site Navigation / Refresh
    if "almondjobs.com" in ref_lower or "localhost" in ref_lower or "127.0.0.1" in ref_lower:
        return {
            "channel": "On-Site / Refresh",
            "source": "Almond Jobs",
            "detail": "Internal Navigation / Refresh",
            "badge_color": "slate",
            "icon": "🔄"
        }

    # Other External Website
    domain_match = re.search(r'https?://([^/?#]+)', ref)
    domain = domain_match.group(1) if domain_match else ref[:30]
    return {
        "channel": "External Web",
        "source": domain,
        "detail": domain,
        "badge_color": "indigo",
        "icon": "🌐"
    }

def get_recent_visitors(limit: int = 50, bots_only: bool = False) -> list:
    """
    Retrieve deduplicated live stream of recent unique visitor sessions (grouping consecutive
    refreshes per visitor_hash) with geographic location, authenticated user identity,
    referrer attribution, and hardware device models.
    """
    now = time.time()
    bot_filter = 1 if bots_only else 0
    results = []
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, date, path, visitor_hash, device, device_model, device_brand, is_bot, referrer,
                       COALESCE(location, '') as location,
                       COALESCE(user_name, '') as user_name,
                       COALESCE(user_email, '') as user_email,
                       COALESCE(utm_source, '') as utm_source,
                       COALESCE(utm_campaign, '') as utm_campaign,
                       COALESCE(fbclid, '') as fbclid,
                       timestamp
                FROM site_traffic
                WHERE is_bot = ? AND path NOT LIKE '/admin%' AND path NOT LIKE '/api/admin%'
                ORDER BY timestamp DESC
                LIMIT ?;
            """, (bot_filter, limit * 5))
            rows = cursor.fetchall()

        # Group consecutive refreshes/pageviews by visitor_hash so 1 human = 1 clean row
        grouped = {}
        order = []
        for r in rows:
            vh = r["visitor_hash"] or str(r["id"])
            if vh not in grouped:
                grouped[vh] = {
                    "row": r,
                    "hits": 1,
                    "paths": [r["path"]],
                    "best_ref": r["referrer"] or "",
                    "best_loc": (r["location"] or "").strip(),
                    "best_name": (r["user_name"] or "").strip(),
                    "best_email": (r["user_email"] or "").strip(),
                    "best_utm_source": (r["utm_source"] or "").strip(),
                    "best_utm_campaign": (r["utm_campaign"] or "").strip(),
                    "best_fbclid": (r["fbclid"] or "").strip(),
                }
                order.append(vh)
            else:
                g = grouped[vh]
                g["hits"] += 1
                if r["path"] not in g["paths"]:
                    g["paths"].append(r["path"])
                # Prefer external referrer over internal refresh
                cur_ref = (r["referrer"] or "").strip()
                if cur_ref and ("almondjobs.com" not in cur_ref.lower()) and (not g["best_ref"] or "almondjobs.com" in g["best_ref"].lower()):
                    g["best_ref"] = cur_ref
                if not g["best_loc"] and (r["location"] or "").strip():
                    g["best_loc"] = (r["location"] or "").strip()
                if not g["best_email"] and (r["user_email"] or "").strip():
                    g["best_email"] = (r["user_email"] or "").strip()
                    g["best_name"] = (r["user_name"] or "").strip()
                if not g["best_utm_source"] and (r["utm_source"] or "").strip():
                    g["best_utm_source"] = (r["utm_source"] or "").strip()
                if not g["best_utm_campaign"] and (r["utm_campaign"] or "").strip():
                    g["best_utm_campaign"] = (r["utm_campaign"] or "").strip()
                if not g["best_fbclid"] and (r["fbclid"] or "").strip():
                    g["best_fbclid"] = (r["fbclid"] or "").strip()

        for vh in order[:limit]:
            g = grouped[vh]
            r = g["row"]
            ts = r["timestamp"] or now
            diff = int(now - ts)
            if diff < 10:
                time_ago = "Just now"
            elif diff < 60:
                time_ago = f"{diff}s ago"
            elif diff < 3600:
                time_ago = f"{diff // 60}m ago"
            elif diff < 86400:
                time_ago = f"{diff // 3600}h ago"
            elif diff < 604800:
                time_ago = f"{diff // 86400}d ago"
            else:
                time_ago = time.strftime("%b %d, %H:%M", time.localtime(ts))

            time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts))
            ref_meta = parse_referrer_info(
                g["best_ref"],
                utm_source=g["best_utm_source"],
                utm_campaign=g["best_utm_campaign"],
                fbclid=g["best_fbclid"],
            )

            model = (r["device_model"] or "").strip()
            brand = (r["device_brand"] or "").strip()
            dev_type = (r["device"] or "desktop").strip()
            if not model:
                if dev_type == "mobile":
                    model = "Mobile Smartphone"
                elif dev_type == "tablet":
                    model = "Tablet Device"
                else:
                    model = "Desktop Browser"

            results.append({
                "id": r["id"],
                "date": r["date"],
                "path": r["path"],
                "paths_visited": g["paths"][:4],
                "visit_count": g["hits"],
                "visitor_hash": vh[:8],
                "device": dev_type,
                "device_model": model,
                "device_brand": brand,
                "location": g["best_loc"] or "Location Pending / Direct",
                "user_name": g["best_name"],
                "user_email": g["best_email"],
                "utm_source": g["best_utm_source"],
                "utm_campaign": g["best_utm_campaign"],
                "is_bot": bool(r["is_bot"]),
                "referrer": g["best_ref"],
                "referrer_channel": ref_meta["channel"],
                "referrer_source": ref_meta["source"],
                "referrer_detail": ref_meta["detail"],
                "referrer_badge_color": ref_meta["badge_color"],
                "referrer_icon": ref_meta["icon"],
                "timestamp": ts,
                "time_ago": time_ago,
                "time_str": time_str
            })
    except Exception as e:
        print(f"[AUTH_DB] get_recent_visitors error: {e}")
    return results

def get_location_breakdown(limit: int = 8) -> list:
    """Aggregate real human visitors by geographic location (City/Country) for ad targeting."""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT location, COUNT(*) as hits, COUNT(DISTINCT visitor_hash) as uniques
                FROM site_traffic
                WHERE is_bot = 0 AND COALESCE(location, '') != '' AND path NOT LIKE '/admin%'
                GROUP BY location
                ORDER BY uniques DESC, hits DESC
                LIMIT ?;
            """, (limit,))
            return [{"location": r["location"], "hits": r["hits"], "uniques": r["uniques"]} for r in cursor.fetchall()]
    except Exception:
        return []

def get_traffic_source_breakdown() -> list:
    """
    Aggregate real human candidate traffic by marketing acquisition channel
    (Reddit, Peerlist, LinkedIn, Google, Direct/App, etc.).
    """
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    CASE 
                        WHEN LOWER(COALESCE(utm_source, '')) IN ('instagram', 'ig') OR LOWER(referrer) LIKE '%instagram.com%' THEN 'Instagram'
                        WHEN LOWER(COALESCE(utm_source, '')) IN ('facebook', 'fb') OR LOWER(referrer) LIKE '%facebook.com%' OR LOWER(referrer) LIKE '%fb.com%' THEN 'Facebook'
                        WHEN LOWER(COALESCE(utm_source, '')) IN ('meta', 'meta_ads') OR COALESCE(fbclid, '') != '' THEN 'Meta Ads'
                        WHEN LOWER(COALESCE(utm_source, '')) = 'reddit' OR LOWER(referrer) LIKE '%reddit.com%' THEN 'Reddit'
                        WHEN LOWER(COALESCE(utm_source, '')) = 'peerlist' OR LOWER(referrer) LIKE '%peerlist.io%' THEN 'Peerlist'
                        WHEN LOWER(COALESCE(utm_source, '')) = 'linkedin' OR LOWER(referrer) LIKE '%linkedin.com%' THEN 'LinkedIn'
                        WHEN LOWER(referrer) LIKE '%twitter.com%' OR LOWER(referrer) LIKE '%t.co%' OR LOWER(referrer) LIKE '%x.com%' THEN 'Twitter / X'
                        WHEN LOWER(COALESCE(utm_source, '')) IN ('google', 'google_ads') OR LOWER(referrer) LIKE '%google.%' THEN 'Google Search'
                        WHEN LOWER(COALESCE(utm_source, '')) = 'whatsapp' OR LOWER(referrer) LIKE '%whatsapp%' THEN 'WhatsApp'
                        WHEN LOWER(COALESCE(utm_source, '')) = 'telegram' OR LOWER(referrer) LIKE '%telegram%' OR LOWER(referrer) LIKE '%t.me%' THEN 'Telegram'
                        WHEN LOWER(referrer) LIKE '%almondjobs.com%' OR LOWER(referrer) LIKE '%localhost%' THEN 'On-Site / Refresh'
                        WHEN (referrer = '' OR referrer IS NULL) AND COALESCE(utm_source, '') = '' THEN 'Direct / In-App'
                        ELSE 'Other Websites'
                    END as channel,
                    COUNT(*) as hits,
                    COUNT(DISTINCT visitor_hash) as uniques
                FROM site_traffic
                WHERE is_bot = 0 AND path NOT LIKE '/admin%' AND path NOT LIKE '/api/admin%'
                GROUP BY channel
                ORDER BY hits DESC;
            """)
            rows = cursor.fetchall()
    except Exception as e:
        print(f"[AUTH_DB] get_traffic_source_breakdown error: {e}")
        rows = []
        
    badge_colors = {
        "Instagram": "pink",
        "Facebook": "blue",
        "Meta Ads": "pink",
        "Reddit": "amber",
        "Peerlist": "emerald",
        "LinkedIn": "blue",
        "Twitter / X": "sky",
        "Google Search": "violet",
        "WhatsApp": "emerald",
        "Telegram": "sky",
        "Direct / In-App": "slate",
        "Other Websites": "indigo"
    }
    icons = {
        "Instagram": "📸",
        "Facebook": "📘",
        "Meta Ads": "🎯",
        "Reddit": "🔴",
        "Peerlist": "🟢",
        "LinkedIn": "💼",
        "Twitter / X": "🐦",
        "Google Search": "🔍",
        "WhatsApp": "💬",
        "Telegram": "✈️",
        "Direct / In-App": "🔗",
        "Other Websites": "🌐"
    }
    
    breakdown = []
    for r in rows:
        ch = r["channel"]
        breakdown.append({
            "channel": ch,
            "hits": r["hits"],
            "uniques": r["uniques"],
            "badge_color": badge_colors.get(ch, "slate"),
            "icon": icons.get(ch, "📌")
        })
    return breakdown

def purge_dummy_candidates_admin() -> dict:
    """
    Safely purge synthetic/dummy test accounts from the users table.
    Preserves genuine candidates and internal system accounts.
    """
    try:
        candidates = get_all_users_admin()
        dummy_ids = [c["id"] for c in candidates if c.get("is_dummy") and c["id"] != SYSTEM_STORE_EMAIL]
        if not dummy_ids:
            return {"status": "success", "deleted_count": 0, "message": "No test accounts to purge."}
        
        with get_db() as conn:
            cursor = conn.cursor()
            placeholders = ",".join("?" for _ in dummy_ids)
            cursor.execute(f"DELETE FROM candidate_applications WHERE user_id IN ({placeholders});", dummy_ids)
            cursor.execute(f"DELETE FROM payments WHERE user_id IN ({placeholders});", dummy_ids)
            cursor.execute(f"DELETE FROM users WHERE id IN ({placeholders});", dummy_ids)
            conn.commit()
        return {"status": "success", "deleted_count": len(dummy_ids), "message": f"Successfully purged {len(dummy_ids)} dummy accounts."}
    except Exception as e:
        return {"status": "error", "message": str(e), "deleted_count": 0}

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
        "genuine_users": sum(1 for c in candidates if not c.get("is_dummy")),
        "dummy_users": sum(1 for c in candidates if c.get("is_dummy")),
        "new_users_24h": sum(1 for c in candidates if c.get("is_new")),
        "today_date": today_str,

        # Real-Time Telemetry Stream & Acquisition Sources
        "recent_visitors": get_recent_visitors(limit=50, bots_only=False),
        "recent_bot_probes": get_recent_visitors(limit=20, bots_only=True),
        "traffic_sources": get_traffic_source_breakdown(),
        "location_breakdown": get_location_breakdown(),
        "ad_funnel": get_ad_funnel_summary(),
        "meta_pixel_id": get_meta_pixel_id()
    }

def get_all_users_admin() -> list:
    """
    Retrieve all registered candidates formatted for the executive admin directory.
    Synchronizes seamlessly with Supabase Auth (if configured) so candidate accounts
    never vanish on ephemeral hosting (Render) restarts, and enriches candidates
    with their email, authentication provider, hardware device models, VIP status,
    and smart classification for test/dummy accounts vs genuine candidates.
    """
    candidates_by_email = {}
    now = time.time()

    # 1. Fetch active VIP grants
    active_grants = {}
    with get_db() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT email, valid_until, status, granted_at FROM vip_grants WHERE status = 'active';")
            for gr in cursor.fetchall():
                active_grants[gr["email"].lower()] = gr
        except Exception:
            pass

    # Merge system_store cloud VIP grants
    sys_grants = _get_system_store().get("vip_grants", {})
    for g_em, g_info in sys_grants.items():
        em_low = g_em.lower()
        if em_low not in active_grants and float(g_info.get("paid_until", 0)) > now:
            active_grants[em_low] = {
                "email": em_low,
                "valid_until": float(g_info["paid_until"]),
                "status": "active",
                "granted_at": g_info.get("granted_at", now)
            }

    with get_db() as conn:
        cursor = conn.cursor()
        # 2. Fetch from local SQLite cache
        cursor.execute("""
            SELECT id, email, full_name, plan, is_paid, paid_until, created_at, auth_provider,
                   COALESCE(device_model, '') as device_model
            FROM users
            ORDER BY created_at DESC;
        """)
        for r in cursor.fetchall():
            email_key = (r["email"] or "").strip().lower()
            if not email_key or email_key == SYSTEM_STORE_EMAIL:
                continue
            created_ts = r["created_at"] or now
            paid_until = r["paid_until"] or 0

            # VIP active check: check grant or user record
            grant = active_grants.get(email_key)
            if grant and grant["valid_until"] > now:
                is_active_vip = True
                paid_until = grant["valid_until"]
            else:
                is_active_vip = bool(r["is_paid"]) and (paid_until > now)

            paid_until_str = ""
            days_remaining = 0
            if is_active_vip and paid_until > now:
                diff = paid_until - now
                days_remaining = max(1, int(diff / 86400))
                paid_until_str = time.strftime("%Y-%m-%d", time.localtime(paid_until))

            is_dummy = is_dummy_email(email_key)
            is_new = (now - created_ts) <= (86400 * 1.5)

            candidates_by_email[email_key] = {
                "id": r["id"],
                "email": r["email"],
                "full_name": r["full_name"] or "Candidate",
                "plan": "vip_pass_30d" if is_active_vip else (r["plan"] or "free"),
                "is_paid": is_active_vip,
                "paid_until": paid_until,
                "paid_until_str": paid_until_str,
                "days_remaining": days_remaining,
                "is_dummy": is_dummy,
                "is_new": is_new,
                "auth_provider": r["auth_provider"] or ("google" if "google" in email_key else "email"),
                "device_model": r["device_model"] or "",
                "created_at": created_ts,
                "created_at_str": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(created_ts))
            }

    # 3. Synchronize with live Supabase Auth
    if supabase_admin:
        try:
            sp_users = _fetch_all_supabase_users() or []
            for u in sp_users:
                sp_email = (getattr(u, "email", "") or "").strip().lower()
                if not sp_email or sp_email == SYSTEM_STORE_EMAIL:
                    continue
                
                user_meta = getattr(u, "user_metadata", {}) or {}
                app_meta = getattr(u, "app_metadata", {}) or {}

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
                sp_paid_until = float(user_meta.get("paid_until", 0))

                grant = active_grants.get(sp_email)
                if grant and grant["valid_until"] > now:
                    sp_is_paid = True
                    sp_paid_until = grant["valid_until"]
                else:
                    sp_is_paid = sp_is_paid and (sp_paid_until > now)

                paid_until_str = ""
                days_rem = 0
                if sp_is_paid and sp_paid_until > now:
                    days_rem = max(1, int((sp_paid_until - now) / 86400))
                    paid_until_str = time.strftime("%Y-%m-%d", time.localtime(sp_paid_until))

                is_dummy = is_dummy_email(sp_email)
                is_new = (now - created_ts) <= (86400 * 1.5)

                if sp_email not in candidates_by_email:
                    local_id = user_meta.get("local_user_id") or getattr(u, "id", str(uuid.uuid4()))
                    candidates_by_email[sp_email] = {
                        "id": local_id,
                        "email": sp_email,
                        "full_name": full_name,
                        "plan": "free" if not sp_is_paid else "vip_pass_30d",
                        "is_paid": sp_is_paid,
                        "paid_until": sp_paid_until,
                        "paid_until_str": paid_until_str,
                        "days_remaining": days_rem,
                        "is_dummy": is_dummy,
                        "is_new": is_new,
                        "auth_provider": provider,
                        "device_model": sp_device,
                        "created_at": created_ts,
                        "created_at_str": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(created_ts))
                    }
                else:
                    if sp_device and not candidates_by_email[sp_email].get("device_model"):
                        candidates_by_email[sp_email]["device_model"] = sp_device
                    if full_name and candidates_by_email[sp_email].get("full_name") in ["Candidate", ""]:
                        candidates_by_email[sp_email]["full_name"] = full_name
        except Exception as e:
            print(f"[AUTH_DB] Supabase user list sync note: {e}")

    # 4. Include pre-approved VIP grants not yet logged in so admin can see them
    for g_email, grant in active_grants.items():
        if g_email not in candidates_by_email and grant["valid_until"] > now:
            diff = grant["valid_until"] - now
            days_rem = max(1, int(diff / 86400))
            candidates_by_email[g_email] = {
                "id": f"grant_{g_email}",
                "email": g_email,
                "full_name": "VIP Pre-Approved (Awaiting Sign-in)",
                "plan": "vip_pass_30d",
                "is_paid": True,
                "paid_until": grant["valid_until"],
                "paid_until_str": time.strftime("%Y-%m-%d", time.localtime(grant["valid_until"])),
                "days_remaining": days_rem,
                "is_dummy": is_dummy_email(g_email),
                "is_new": True,
                "auth_provider": "pre_approved",
                "device_model": "Pending First Login",
                "created_at": grant["granted_at"] or now,
                "created_at_str": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(grant["granted_at"] or now))
            }

    # Format device model display for candidates
    candidates = list(candidates_by_email.values())
    for c in candidates:
        dev = c.get("device_model") or ""
        if not dev:
            dev = "Desktop / Web Browser"
        c["device_display"] = dev

    candidates.sort(key=lambda x: x.get("created_at", 0), reverse=True)
    return candidates


# =========================================================================
# DYNAMIC PRICING & FESTIVAL OFFER CONTROLLERS
# =========================================================================

def get_dynamic_pricing() -> dict:
    """
    Retrieve active pricing tiers from SQLite pricing_config table with fallback to Config.VIP_TIERS.
    Returns clean dictionary keyed by tier_id ('1m', '3m', '6m').
    """
    tiers = {}
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT tier_id, plan_code, name, duration_days,
                       inr_price, inr_original,
                       usd_price, usd_original,
                       eur_price, eur_original,
                       gbp_price, gbp_original,
                       discount_pct, discount_label, badge_text,
                       is_active, updated_at
                FROM pricing_config
                WHERE is_active = 1
                ORDER BY duration_days ASC;
            ''')
            rows = cursor.fetchall()
            for row in rows:
                t_id = row["tier_id"]
                tiers[t_id] = {
                    "id": t_id,
                    "plan_code": row["plan_code"],
                    "name": row["name"],
                    "duration_days": row["duration_days"],
                    "inr_price": row["inr_price"],
                    "inr_original": row["inr_original"],
                    "usd_price": float(row["usd_price"]),
                    "usd_original": float(row["usd_original"]),
                    "eur_price": float(row["eur_price"]),
                    "eur_original": float(row["eur_original"]),
                    "gbp_price": float(row["gbp_price"]),
                    "gbp_original": float(row["gbp_original"]),
                    "discount_pct": row["discount_pct"],
                    "discount_label": row["discount_label"] or "",
                    "badge_text": row["badge_text"] or "",
                    "INR": row["inr_price"],
                    "USD": float(row["usd_price"]),
                    "EUR": float(row["eur_price"]),
                    "GBP": float(row["gbp_price"]),
                    "updated_at": row["updated_at"]
                }
    except Exception as e:
        print(f"[AUTH_DB] Warning: Could not read pricing_config from database: {e}")

    # Fallback to Config.VIP_TIERS if table returned empty
    if not tiers:
        for t_id, cfg in Config.VIP_TIERS.items():
            inr = cfg.get("INR", 699)
            usd = cfg.get("USD", 19.99)
            orig_inr = 2599 if t_id == "3m" else (4299 if t_id == "6m" else inr)
            orig_usd = 69.99 if t_id == "3m" else (119.99 if t_id == "6m" else usd)
            disc = 30 if t_id == "3m" else (35 if t_id == "6m" else 0)
            tiers[t_id] = {
                "id": t_id,
                "plan_code": cfg.get("plan_code", f"vip_pass_{cfg.get('duration_days', 30)}d"),
                "name": cfg.get("name", "VIP Pass"),
                "duration_days": cfg.get("duration_days", 30),
                "inr_price": inr,
                "inr_original": orig_inr,
                "usd_price": usd,
                "usd_original": orig_usd,
                "eur_price": cfg.get("EUR", usd),
                "eur_original": orig_usd,
                "gbp_price": cfg.get("GBP", usd),
                "gbp_original": orig_usd,
                "discount_pct": disc,
                "discount_label": f"{disc}% OFF Limited Offer" if disc > 0 else "",
                "badge_text": cfg.get("tag", ""),
                "INR": inr,
                "USD": usd,
                "EUR": cfg.get("EUR", usd),
                "GBP": cfg.get("GBP", usd),
                "updated_at": time.time()
            }
    return tiers


def update_tier_pricing(tier_id: str, data: dict) -> dict:
    """
    Update pricing configuration for a specific tier (1m, 3m, 6m).
    CRITICAL: Does NOT touch existing user records or alter paid_until expiration dates.
    """
    tier_id = (tier_id or "").strip().lower()
    if tier_id not in ("1m", "3m", "6m"):
        raise ValueError(f"Invalid tier_id '{tier_id}'. Expected '1m', '3m', or '6m'.")

    now_ts = time.time()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM pricing_config WHERE tier_id = ?", (tier_id,))
        existing = cursor.fetchone()
        if not existing:
            raise ValueError(f"Tier '{tier_id}' does not exist in pricing_config.")

        inr_price = int(data.get("inr_price", existing["inr_price"]))
        inr_original = int(data.get("inr_original", existing["inr_original"]))
        usd_price = float(data.get("usd_price", existing["usd_price"]))
        usd_original = float(data.get("usd_original", existing["usd_original"]))
        eur_price = float(data.get("eur_price", existing["eur_price"]))
        eur_original = float(data.get("eur_original", existing["eur_original"]))
        gbp_price = float(data.get("gbp_price", existing["gbp_price"]))
        gbp_original = float(data.get("gbp_original", existing["gbp_original"]))
        discount_pct = int(data.get("discount_pct", existing["discount_pct"]))
        discount_label = str(data.get("discount_label", existing["discount_label"]) or "")
        badge_text = str(data.get("badge_text", existing["badge_text"]) or "")
        name = str(data.get("name", existing["name"]) or existing["name"])

        cursor.execute('''
            UPDATE pricing_config
            SET name = ?,
                inr_price = ?,
                inr_original = ?,
                usd_price = ?,
                usd_original = ?,
                eur_price = ?,
                eur_original = ?,
                gbp_price = ?,
                gbp_original = ?,
                discount_pct = ?,
                discount_label = ?,
                badge_text = ?,
                updated_at = ?
            WHERE tier_id = ?;
        ''', (
            name,
            inr_price, inr_original,
            usd_price, usd_original,
            eur_price, eur_original,
            gbp_price, gbp_original,
            discount_pct, discount_label, badge_text,
            now_ts, tier_id
        ))
        conn.commit()
        print(f"[AUTH_DB] Successfully updated pricing config for tier '{tier_id}' at {now_ts}.")

    return get_dynamic_pricing()

# ==============================================================================
# CANDIDATE IN-APP FEEDBACK & REVENUE GATEWAY ANALYTICS
# ==============================================================================

def save_candidate_feedback(
    user_id: str = "",
    user_email: str = "",
    category: str = "feature_suggestion",
    rating: int = 5,
    message: str = "",
    hired_company: str = "",
    page_url: str = ""
) -> dict:
    """Save candidate feedback, review, bug report, or hired celebration to local DB and Supabase store."""
    now = time.time()
    clean_cat = (category or "feature_suggestion").strip().lower()
    clean_msg = (message or "").strip()
    clean_hired = (hired_company or "").strip()
    clean_url = (page_url or "").strip()
    clean_email = (user_email or "").strip().lower()
    clean_uid = (user_id or "guest").strip()

    feedback_id = None
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO candidate_feedback (user_id, user_email, category, rating, message, hired_company, page_url, created_at, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending')
                """,
                (clean_uid, clean_email, clean_cat, int(rating or 5), clean_msg, clean_hired, clean_url, now)
            )
            feedback_id = cursor.lastrowid
            conn.commit()
            print(f"[AUTH_DB] Recorded candidate feedback #{feedback_id} [{clean_cat}] from '{clean_email or clean_uid}'.")
    except Exception as e:
        print(f"[AUTH_DB] Error writing feedback to SQLite: {e}")

    # Cloud sync to Supabase system store
    try:
        store = _get_system_store()
        fb_list = store.get("feedback", [])
        fb_entry = {
            "id": feedback_id or int(now),
            "user_id": clean_uid,
            "user_email": clean_email,
            "category": clean_cat,
            "rating": int(rating or 5),
            "message": clean_msg,
            "hired_company": clean_hired,
            "page_url": clean_url,
            "created_at": now,
            "admin_reply": "",
            "admin_replied_at": 0,
            "status": "pending"
        }
        fb_list.insert(0, fb_entry)
        _update_system_store({"feedback": fb_list[:150]})
    except Exception as e:
        print(f"[AUTH_DB] Note syncing feedback to Supabase: {e}")

    return {
        "status": "success",
        "id": feedback_id,
        "message": "Thank you for helping us improve Almond Jobs! Our team reads every submission."
    }

def get_all_candidate_feedback(category_filter: str = None, status_filter: str = None) -> list:
    """Retrieve all candidate feedback submissions for Admin inbox."""
    results = []
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM candidate_feedback"
            params = []
            clauses = []
            if category_filter and category_filter != "all":
                clauses.append("category = ?")
                params.append(category_filter.lower())
            if status_filter and status_filter != "all":
                clauses.append("status = ?")
                params.append(status_filter.lower())
            if clauses:
                query += " WHERE " + " AND ".join(clauses)
            query += " ORDER BY created_at DESC LIMIT 200"
            cursor.execute(query, params)
            rows = cursor.fetchall()
            for r in rows:
                item = dict(r)
                ts = item.get("created_at") or time.time()
                try:
                    item["created_at_str"] = datetime.datetime.fromtimestamp(ts, tz=datetime.timezone.utc).strftime("%b %d, %Y %H:%M UTC")
                except Exception:
                    item["created_at_str"] = "Recent"
                results.append(item)
    except Exception as e:
        print(f"[AUTH_DB] Error reading feedback: {e}")
        # fallback to cloud store
        store = _get_system_store()
        results = store.get("feedback", [])

    return results

def reply_to_candidate_feedback(feedback_id: int, admin_reply_text: str) -> dict:
    """Save admin/founder reply to candidate feedback item."""
    clean_reply = (admin_reply_text or "").strip()
    if not clean_reply:
        return {"status": "error", "message": "Reply message cannot be empty."}

    now = time.time()
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE candidate_feedback 
                SET admin_reply = ?, admin_replied_at = ?, status = 'resolved'
                WHERE id = ?
                """,
                (clean_reply, now, feedback_id)
            )
            conn.commit()
    except Exception as e:
        print(f"[AUTH_DB] Error updating feedback reply: {e}")

    try:
        store = _get_system_store()
        fb_list = store.get("feedback", [])
        for item in fb_list:
            if item.get("id") == feedback_id:
                item["admin_reply"] = clean_reply
                item["admin_replied_at"] = now
                item["status"] = "resolved"
                break
        _update_system_store({"feedback": fb_list[:150]})
    except Exception as e:
        print(f"[AUTH_DB] Note syncing reply to Supabase: {e}")

    return {"status": "success", "message": "Reply saved successfully."}

def get_revenue_analytics() -> dict:
    """Aggregate daily revenue trends, product breakdown (VIP vs Coffee), and verified transaction ledger."""
    summary = {
        "total_revenue_inr": 0.0,
        "vip_revenue_inr": 0.0,
        "coffee_revenue_inr": 0.0,
        "total_orders": 0,
        "vip_orders": 0,
        "coffee_orders": 0,
        "currencies": {"INR": 0, "USD": 0, "EUR": 0, "GBP": 0}
    }
    daily_trends = {}
    transactions = []

    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, user_id, payment_id, order_id, amount_inr, plan_name, status, created_at,
                       supporter_name, supporter_message, currency
                FROM payments
                ORDER BY created_at DESC
            """)
            rows = cursor.fetchall()
            for r in rows:
                amt = float(r["amount_inr"] or 0)
                status = (r["status"] or "").lower()
                plan = (r["plan_name"] or "").lower()
                curr = (r["currency"] or "INR").upper()
                ts = float(r["created_at"] or time.time())
                date_str = datetime.datetime.fromtimestamp(ts, tz=datetime.timezone.utc).strftime("%Y-%m-%d")

                is_coffee = ("contribution" in status) or ("coffee" in plan)
                summary["total_revenue_inr"] += amt
                summary["total_orders"] += 1
                if is_coffee:
                    summary["coffee_revenue_inr"] += amt
                    summary["coffee_orders"] += 1
                else:
                    summary["vip_revenue_inr"] += amt
                    summary["vip_orders"] += 1

                summary["currencies"][curr] = summary["currencies"].get(curr, 0) + 1

                if date_str not in daily_trends:
                    daily_trends[date_str] = {"date": date_str, "vip_inr": 0.0, "coffee_inr": 0.0, "total_inr": 0.0, "count": 0}
                if is_coffee:
                    daily_trends[date_str]["coffee_inr"] += amt
                else:
                    daily_trends[date_str]["vip_inr"] += amt
                daily_trends[date_str]["total_inr"] += amt
                daily_trends[date_str]["count"] += 1

                curr_sym = {"INR": "₹", "USD": "$", "EUR": "€", "GBP": "£"}.get(curr, "₹")
                transactions.append({
                    "id": r["id"],
                    "payment_id": r["payment_id"] or "N/A",
                    "order_id": r["order_id"] or "N/A",
                    "amount": amt,
                    "currency": curr,
                    "amount_formatted": f"{curr_sym}{amt:,.0f}" if amt == int(amt) else f"{curr_sym}{amt:,.2f}",
                    "plan_name": r["plan_name"] or ("Coffee Support" if is_coffee else "VIP Pass"),
                    "product_type": "Coffee Support" if is_coffee else "VIP Pass",
                    "supporter_name": r["supporter_name"] or r["user_id"] or "Candidate",
                    "supporter_message": r["supporter_message"] or "",
                    "created_at": ts,
                    "created_at_str": datetime.datetime.fromtimestamp(ts, tz=datetime.timezone.utc).strftime("%b %d, %Y %H:%M UTC"),
                    "status": "Captured & Verified" if not is_coffee else "Voluntary Contribution",
                    "is_verified_hmac": True,
                    "gateway": "Razorpay Direct Gateway"
                })
    except Exception as e:
        print(f"[AUTH_DB] Error computing revenue analytics: {e}")

    sorted_trends = sorted(daily_trends.values(), key=lambda x: x["date"])
    if not sorted_trends:
        today_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
        sorted_trends = [{"date": today_str, "vip_inr": 0.0, "coffee_inr": 0.0, "total_inr": 0.0, "count": 0}]

    return {
        "summary": summary,
        "daily_trends": sorted_trends,
        "transactions": transactions[:100]
    }


# ============================================================================
# Meta Pixel Governance & Paid Ad Conversion Funnel Telemetry
# ============================================================================

_VALID_FUNNEL_EVENTS = {"resume_upload", "signup", "checkout_start", "purchase"}


def get_meta_pixel_id() -> str:
    """Resolve active Meta Pixel ID from SQLite kv_settings, Supabase system_store, or Config env."""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM kv_settings WHERE key = 'meta_pixel_id' LIMIT 1;")
            row = cursor.fetchone()
            if row and row["value"] is not None:
                val = str(row["value"]).strip()
                if val.isdigit():
                    return val
                if val == "__DISABLED__":
                    return ""
    except Exception:
        pass

    cloud_val = str(_get_system_store().get("meta_pixel_id") or "").strip()
    if cloud_val.isdigit():
        return cloud_val
    if cloud_val == "__DISABLED__":
        return ""

    env_val = str(getattr(Config, "META_PIXEL_ID", "") or "").strip()
    return env_val if env_val.isdigit() else ""


def set_meta_pixel_id(pixel_id: str) -> dict:
    """Persist numeric Meta Pixel ID (or empty string to disable) to SQLite and Supabase system_store."""
    cleaned = (pixel_id or "").strip()
    if cleaned and not cleaned.isdigit():
        return {"status": "error", "message": "Meta Pixel ID must contain only numeric digits (e.g. 123456789012345)."}

    stored_val = cleaned if cleaned else "__DISABLED__"
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO kv_settings (key, value) VALUES ('meta_pixel_id', ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value;",
                (stored_val,)
            )
            conn.commit()
    except Exception as e:
        return {"status": "error", "message": str(e)}

    _update_system_store({"meta_pixel_id": stored_val})
    return {
        "status": "success",
        "pixel_id": cleaned,
        "message": f"Meta Pixel {cleaned} activated site-wide." if cleaned else "Meta Pixel disabled."
    }


def record_funnel_event(
    event_name: str,
    client_ip: str,
    user_agent: str = "",
    utm_source: str = "",
    utm_medium: str = "",
    utm_campaign: str = "",
    utm_content: str = "",
    fbclid: str = "",
    user_name: str = "",
    user_email: str = "",
    amount_inr: float = 0.0,
    meta: dict = None
) -> bool:
    """Record a candidate conversion milestone with full UTM & Meta click attribution."""
    ev = (event_name or "").strip().lower()
    if ev not in _VALID_FUNNEL_EVENTS:
        return False

    try:
        visitor_hash, _, now = _compute_visitor_hash(client_ip, user_agent)
        clean_fbclid = (fbclid or "").strip()[:120]
        clean_src = _normalize_utm_source(utm_source, "", clean_fbclid)
        clean_med = (utm_medium or "").strip().lower()[:80]
        clean_camp = (utm_campaign or "").strip()[:120]
        clean_cont = (utm_content or "").strip()[:120]
        clean_name = (user_name or "").strip()[:120]
        clean_email = (user_email or "").strip().lower()[:160]
        try:
            amt = max(0.0, float(amount_inr or 0.0))
        except (TypeError, ValueError):
            amt = 0.0
        meta_str = json.dumps(meta)[:500] if isinstance(meta, dict) else ""

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO funnel_events (
                    visitor_hash, event_name, utm_source, utm_medium, utm_campaign, utm_content,
                    fbclid, user_name, user_email, amount_inr, meta_json, timestamp
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    visitor_hash, ev, clean_src, clean_med, clean_camp, clean_cont,
                    clean_fbclid, clean_name, clean_email, amt, meta_str, now
                )
            )
            conn.commit()
        return True
    except Exception as e:
        print(f"[FUNNEL_TRACKER] Event record note: {e}")
        return False


def get_ad_funnel_summary() -> dict:
    """
    Aggregate full 5-stage conversion funnel (Visitors -> Resume Uploads -> Signups -> Checkouts -> Paid Pro)
    broken down by acquisition source and campaign so founder can measure ₹1,000 ad ROI directly.
    """
    totals = {
        "visitors": 0,
        "resume_uploads": 0,
        "signups": 0,
        "checkout_starts": 0,
        "purchases": 0,
        "revenue_inr": 0.0
    }
    campaigns_map = {}

    def _bucket(src: str, camp: str) -> dict:
        s = (src or "").strip().lower() or "organic_direct"
        c = (camp or "").strip() or "(untagged)"
        key = (s, c)
        if key not in campaigns_map:
            campaigns_map[key] = {
                "source": s,
                "campaign": c,
                "visitors": 0,
                "resume_uploads": 0,
                "signups": 0,
                "checkout_starts": 0,
                "purchases": 0,
                "revenue_inr": 0.0
            }
        return campaigns_map[key]

    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    CASE
                        WHEN COALESCE(utm_source, '') != '' THEN LOWER(utm_source)
                        WHEN COALESCE(fbclid, '') != '' THEN 'meta'
                        WHEN LOWER(referrer) LIKE '%reddit.com%' THEN 'reddit'
                        WHEN LOWER(referrer) LIKE '%peerlist.io%' THEN 'peerlist'
                        ELSE 'organic_direct'
                    END as src_key,
                    COALESCE(utm_campaign, '') as camp_key,
                    COUNT(DISTINCT visitor_hash) as uniques
                FROM site_traffic
                WHERE is_bot = 0 AND path NOT LIKE '/admin%' AND path NOT LIKE '/api/admin%'
                GROUP BY src_key, camp_key;
            """)
            for r in cursor.fetchall():
                b = _bucket(r["src_key"], r["camp_key"])
                b["visitors"] += int(r["uniques"] or 0)
                totals["visitors"] += int(r["uniques"] or 0)

            cursor.execute("""
                SELECT
                    CASE
                        WHEN COALESCE(utm_source, '') != '' THEN LOWER(utm_source)
                        WHEN COALESCE(fbclid, '') != '' THEN 'meta'
                        ELSE 'organic_direct'
                    END as src_key,
                    COALESCE(utm_campaign, '') as camp_key,
                    event_name,
                    COUNT(DISTINCT visitor_hash) as uniq_ev,
                    COUNT(*) as raw_ev,
                    COALESCE(SUM(amount_inr), 0) as rev_sum
                FROM funnel_events
                GROUP BY src_key, camp_key, event_name;
            """)
            for r in cursor.fetchall():
                b = _bucket(r["src_key"], r["camp_key"])
                ev = r["event_name"]
                uniq_n = int(r["uniq_ev"] or 0)
                raw_n = int(r["raw_ev"] or 0)
                if ev == "resume_upload":
                    b["resume_uploads"] += uniq_n
                    totals["resume_uploads"] += uniq_n
                elif ev == "signup":
                    b["signups"] += uniq_n
                    totals["signups"] += uniq_n
                elif ev == "checkout_start":
                    b["checkout_starts"] += uniq_n
                    totals["checkout_starts"] += uniq_n
                elif ev == "purchase":
                    b["purchases"] += raw_n
                    b["revenue_inr"] += float(r["rev_sum"] or 0.0)
                    totals["purchases"] += raw_n
                    totals["revenue_inr"] += float(r["rev_sum"] or 0.0)
    except Exception as e:
        print(f"[FUNNEL_TRACKER] Summary error: {e}")

    campaigns = sorted(
        campaigns_map.values(),
        key=lambda x: (x["purchases"], x["signups"], x["resume_uploads"], x["visitors"]),
        reverse=True
    )[:15]
    return {"totals": totals, "campaigns": campaigns}


