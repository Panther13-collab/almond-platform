import time
from core.config import Config

# In-memory mock store used as secondary fallback
MOCK_USERS = {}
MOCK_PAYMENTS = {}

supabase_client = None
supabase_admin = None

if Config.is_supabase_configured():
    try:
        from supabase import create_client, Client
        supabase_client: Client = create_client(Config.SUPABASE_URL, Config.SUPABASE_ANON_KEY)
        
        # Admin client for server-side trusted operations
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
    print("[AUTH_DB] Notice: Running with local sandbox storage. Supabase keys not yet provided.")

def signup_user(email: str, password: str, full_name: str = ""):
    """Sign up a new user via Supabase Auth or local sandbox."""
    clean_email = email.strip().lower()
    if supabase_client:
        try:
            res = supabase_client.auth.sign_up({
                "email": clean_email,
                "password": password,
                "options": {
                    "data": {
                        "full_name": full_name,
                        "is_paid": False
                    }
                }
            })
            user = res.user
            if user:
                return {
                    "status": "success",
                    "user_id": user.id,
                    "email": user.email,
                    "is_paid": False,
                    "provider": "supabase"
                }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    # Sandbox / Local fallback
    if clean_email in MOCK_USERS:
        return {"status": "error", "message": "Email already registered."}
    
    mock_id = f"usr_{abs(hash(clean_email)) % 1000000}"
    MOCK_USERS[clean_email] = {
        "user_id": mock_id,
        "email": clean_email,
        "password": password,
        "full_name": full_name,
        "is_paid": False,
        "created_at": time.time()
    }
    return {
        "status": "success",
        "user_id": mock_id,
        "email": clean_email,
        "is_paid": False,
        "provider": "sandbox"
    }

def login_user(email: str, password: str):
    """Authenticate an existing user via Supabase Auth."""
    clean_email = email.strip().lower()
    if supabase_client:
        try:
            res = supabase_client.auth.sign_in_with_password({
                "email": clean_email,
                "password": password
            })
            user = res.user
            if user:
                # Check payment flag from profile/metadata
                is_paid = is_user_paid(user.id)
                return {
                    "status": "success",
                    "user_id": user.id,
                    "email": user.email,
                    "access_token": res.session.access_token if res.session else None,
                    "is_paid": is_paid,
                    "provider": "supabase"
                }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    # Sandbox / Local fallback
    user = MOCK_USERS.get(clean_email)
    if not user or user["password"] != password:
        return {"status": "error", "message": "Invalid email or password."}
    
    return {
        "status": "success",
        "user_id": user["user_id"],
        "email": user["email"],
        "is_paid": user.get("is_paid", False),
        "provider": "sandbox"
    }

def is_user_paid(user_id: str) -> bool:
    """Check if the user has an active Pro subscription in Supabase metadata."""
    if not user_id:
        return False

    if supabase_admin:
        try:
            user_res = supabase_admin.auth.admin.get_user_by_id(user_id)
            if user_res and user_res.user:
                meta = user_res.user.user_metadata or {}
                app_meta = user_res.user.app_metadata or {}
                if meta.get("is_paid") is True or app_meta.get("is_paid") is True:
                    return True
        except Exception as e:
            print(f"[AUTH_DB] Metadata query note for {user_id}: {e}")

        try:
            # Check table if user created user_profiles table
            res = supabase_admin.table("user_profiles").select("is_paid").eq("id", user_id).execute()
            if res.data and len(res.data) > 0:
                return bool(res.data[0].get("is_paid", False))
        except Exception:
            pass

    # Check mock payments store
    for pid, p in MOCK_PAYMENTS.items():
        if p.get("user_id") == user_id and p.get("status") == "captured":
            return True

    # Check mock store
    for email, u in MOCK_USERS.items():
        if u.get("user_id") == user_id:
            return bool(u.get("is_paid", False))
    return False

def record_successful_payment(user_id: str, payment_id: str, order_id: str, amount_inr: float):
    """Record a captured payment and upgrade user account to Paid / Pro in Supabase."""
    now = time.time()
    
    # 1. Update in Supabase via admin API
    if supabase_admin and user_id:
        try:
            # Direct persistent upgrade on user record
            supabase_admin.auth.admin.update_user_by_id(user_id, {
                "user_metadata": {
                    "is_paid": True,
                    "plan": "pro_inr_699",
                    "payment_id": payment_id,
                    "order_id": order_id,
                    "paid_at": now
                }
            })
            print(f"[AUTH_DB] Upgraded user {user_id} to Pro in Supabase metadata.")
        except Exception as e:
            print(f"[AUTH_DB] Error upgrading user metadata in Supabase: {e}")

        try:
            # Optional database table record if created
            supabase_admin.table("payments").insert({
                "user_id": user_id,
                "payment_id": payment_id,
                "order_id": order_id,
                "amount": amount_inr,
                "status": "captured"
            }).execute()
        except Exception:
            pass

    # 2. Update local mock store
    MOCK_PAYMENTS[payment_id] = {
        "user_id": user_id,
        "payment_id": payment_id,
        "order_id": order_id,
        "amount": amount_inr,
        "timestamp": now
    }
    for email, u in MOCK_USERS.items():
        if u.get("user_id") == user_id:
            u["is_paid"] = True

    return True
