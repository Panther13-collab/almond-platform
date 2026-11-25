from datetime import datetime, timezone
import hmac
import hashlib
import re
import time
import razorpay
from core.config import Config
from core.auth_db import record_contribution_payment, record_successful_payment, get_user_profile

MIN_ORDER_AMOUNT_PAISE = 100
VIP_LATEST_FEED_MAX_DAYS = 4
razorpay_client = None

if Config.is_razorpay_configured():
    try:
        razorpay_client = razorpay.Client(auth=(Config.RAZORPAY_KEY_ID, Config.RAZORPAY_KEY_SECRET))
        print("[PAYMENT] Connected to Razorpay API gateway.")
    except Exception as e:
        print(f"[PAYMENT] Warning: Could not initialize Razorpay client: {e}")
        razorpay_client = None
else:
    print("[PAYMENT] Notice: Running in Razorpay Sandbox/Test mode.")


def _is_auth_failure(exc: Exception) -> bool:
    """Detect Razorpay authentication failures so callers return HTTP 401."""
    msg = str(exc).lower()
    return (
        "authentication failed" in msg
        or "unauthorized" in msg
        or "invalid key" in msg
        or "401" in msg
    )


def get_job_age_days(job: dict, now_ts: float = None) -> int | None:
    """Return non-negative age in days for a job item, or None if no valid timestamp."""
    if not isinstance(job, dict):
        return None
    now = now_ts if now_ts is not None else time.time()

    ts = job.get("date_posted_ts")
    if isinstance(ts, (int, float)) and ts > 100000:
        return max(0, int((now - float(ts)) // 86400))

    raw = job.get("posted_at") or job.get("created_at") or job.get("date_posted_str") or ""
    if not raw:
        return None
    text = str(raw).strip().lower()
    if any(tok in text for tok in ("today", "just now", "hour", "min", "recently")):
        return 0
    if "yesterday" in text:
        return 1
    m = re.search(r"\b(\d+)\s*d(?:ays?)?\s*ago\b", text)
    if m:
        return max(0, int(m.group(1)))

    try:
        dt = datetime.fromisoformat(str(raw).strip().replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        now_dt = datetime.fromtimestamp(now, tz=timezone.utc)
        return max(0, int((now_dt - dt).total_seconds() // 86400))
    except Exception:
        return None


def apply_vip_latest_feed_lock(
    jobs: list,
    user_is_paid: bool = False,
    max_days: int = VIP_LATEST_FEED_MAX_DAYS,
    user_is_logged_in: bool = True
) -> list:
    """
    Mask and lock application links:
    - Unauthenticated guests (user_is_logged_in=False): mask ALL direct URLs with '#signup-required'
      so visitors can browse/match resumes cleanly and sign up free to view direct job links.
    - Authenticated Free candidates (user_is_logged_in=True, user_is_paid=False): blur/lock ONLY
      latest postings (age <= max_days, Today through 4 days ago); 5+ day jobs stay unblurred.
    - Active VIP Members: 100% unlocked.
    """
    if not jobs:
        return jobs
    now = time.time()
    for job in jobs:
        if not isinstance(job, dict):
            continue
        age_days = get_job_age_days(job, now_ts=now)
        if age_days is not None:
            job["days_ago"] = age_days

        is_vip_window = (age_days is not None and age_days <= max_days)
        job["is_latest_vip"] = bool(is_vip_window)
        vip_locked = bool(not user_is_paid and is_vip_window)
        auth_locked = not bool(user_is_logged_in)

        job["is_auth_locked"] = auth_locked
        job["is_locked"] = vip_locked

        if auth_locked or vip_locked:
            placeholder = "#signup-required" if auth_locked else "#unlock-vip"
            job["url"] = placeholder
            if "apply_url" in job:
                job["apply_url"] = placeholder
            if "hn_url" in job:
                job["hn_url"] = placeholder
            if "founder_email" in job:
                job["founder_email"] = ""
            if vip_locked:
                # KEEP BOTH COMPANY NAME AND ROLE TITLE VISIBLE; only lock the direct application URL & full text
                if "summary" in job:
                    job["summary"] = "Unlock VIP Pass to view full designation details and direct application portal link."
                if "full_text" in job:
                    job["full_text"] = ""
                if "matched_skills" in job:
                    job["matched_skills"] = []
                if "gap_skills" in job:
                    job["gap_skills"] = []
    return jobs


def create_razorpay_order(
    user_id: str = "",
    amount_inr: int = getattr(Config, "VIP_PRICE_INR", 699),
    amount_paise: int = None,
    currency: str = "INR",
    receipt: str = None,
    plan_name: str = "",
    purchase_type: str = "vip_pass"
):
    """
    Create a Razorpay order in paise (minimum 100 paise / INR 1.00).
    If Razorpay keys are not yet configured, returns a simulated sandbox order.
    """
    resolved_paise = int(amount_paise) if amount_paise is not None else int(amount_inr) * 100
    if resolved_paise < MIN_ORDER_AMOUNT_PAISE:
        return {
            "status": "error",
            "http_status": 400,
            "message": f"Minimum order amount is {MIN_ORDER_AMOUNT_PAISE} paise (INR 1.00)."
        }

    resolved_currency = (currency or "INR").strip().upper()
    resolved_type = "contribution" if str(purchase_type or "").lower() == "contribution" else "vip_pass"
    receipt_id = (receipt or "").strip() or f"rcpt_{int(time.time())}_{user_id[:6] if user_id else 'anon'}"

    if razorpay_client:
        try:
            order_data = {
                "amount": resolved_paise,
                "currency": resolved_currency,
                "receipt": receipt_id,
                "notes": {
                    "user_id": user_id or "guest",
                    "plan_name": plan_name or ("Coffee_Contribution" if resolved_type == "contribution" else "Almond_VIP_Pass"),
                    "purchase_type": resolved_type,
                    "service": "Almond_Jobs_Platform"
                }
            }
            order = razorpay_client.order.create(data=order_data)
            return {
                "status": "success",
                "order_id": order["id"],
                "amount": order.get("amount", resolved_paise),
                "currency": order.get("currency", resolved_currency),
                "receipt": order.get("receipt", receipt_id),
                "purchase_type": resolved_type,
                "key_id": Config.RAZORPAY_KEY_ID,
                "is_sandbox": False
            }
        except Exception as e:
            err_msg = str(e)
            if resolved_currency != "INR" and ("currency" in err_msg.lower() or "not supported" in err_msg.lower()):
                try:
                    fallback_inr_amount = int(amount_inr) if amount_inr else max(int(resolved_paise / 100), 485)
                    fallback_paise = fallback_inr_amount * 100
                    order_data["amount"] = fallback_paise
                    order_data["currency"] = "INR"
                    order = razorpay_client.order.create(data=order_data)
                    return {
                        "status": "success",
                        "order_id": order["id"],
                        "amount": order.get("amount", fallback_paise),
                        "currency": "INR",
                        "receipt": order.get("receipt", receipt_id),
                        "purchase_type": resolved_type,
                        "key_id": Config.RAZORPAY_KEY_ID,
                        "is_sandbox": False,
                        "fallback_currency": True,
                        "note": f"Processed in INR equivalent (₹{fallback_inr_amount}) via domestic gateway."
                    }
                except Exception:
                    pass
            return {
                "status": "error",
                "http_status": 401 if _is_auth_failure(e) else 500,
                "message": err_msg
            }

    # Local Sandbox Order (simulated when keys are not configured)
    fake_order_id = f"order_sandbox_{int(time.time())}"
    return {
        "status": "success",
        "order_id": fake_order_id,
        "amount": resolved_paise,
        "currency": resolved_currency,
        "receipt": receipt_id,
        "purchase_type": resolved_type,
        "key_id": Config.RAZORPAY_KEY_ID,
        "is_sandbox": True
    }


def _compute_expected_signature(order_id: str, payment_id: str, secret: str) -> str:
    payload = f"{order_id}|{payment_id}".encode("utf-8")
    return hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()


def verify_razorpay_signature(
    user_id: str,
    order_id: str,
    payment_id: str,
    signature: str,
    amount_inr: int = 1,
    plan_name: str = "",
    purchase_type: str = "vip_pass",
    supporter_name: str = "",
    supporter_message: str = "",
    currency: str = "INR",
    payer_email: str = ""
):
    """
    Verify payment signature returned by Razorpay Checkout modal via HMAC-SHA256.
    Only VIP Pass purchases activate VIP access; voluntary contributions do not.
    """
    if not order_id or not payment_id or not signature:
        return {
            "status": "error",
            "http_status": 400,
            "message": "Missing payment verification fields."
        }

    resolved_type = "contribution" if str(purchase_type or "").lower() == "contribution" else "vip_pass"
    resolved_currency = (currency or "INR").strip().upper()

    def _finalize_payment():
        if resolved_type == "contribution":
            record_contribution_payment(
                user_id,
                payment_id,
                order_id,
                amount_inr,
                plan_name or "Coffee Contribution",
                supporter_name=supporter_name,
                supporter_message=supporter_message,
                currency=resolved_currency
            )
            return {
                "status": "success",
                "purchase_type": "contribution",
                "is_paid": False,
                "supporter_name": supporter_name,
                "supporter_message": supporter_message,
                "amount_inr": amount_inr,
                "currency": resolved_currency,
                "message": "Thank you for your generous coffee contribution!"
            }
        # Fetch email from Razorpay API payment entity if not provided by client
        effective_email = (payer_email or "").strip().lower()
        if not effective_email and "@" in str(user_id):
            effective_email = str(user_id).strip().lower()
        if not effective_email and razorpay_client:
            try:
                rzp_pay = razorpay_client.payment.fetch(payment_id)
                if rzp_pay and rzp_pay.get("email"):
                    effective_email = str(rzp_pay.get("email")).strip().lower()
            except Exception:
                pass

        # Look up email from SQLite users table if user_id is a registered UUID
        if not effective_email and user_id:
            try:
                from core.auth_db import get_db
                with get_db() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT email FROM users WHERE id = ?", (user_id,))
                    u_row = cursor.fetchone()
                    if u_row and u_row["email"]:
                        effective_email = u_row["email"].strip().lower()
            except Exception:
                pass

        pl_lower = (plan_name or "").lower()
        if "180" in pl_lower or "6-month" in pl_lower or "6 month" in pl_lower or "dominance" in pl_lower or "6m" in pl_lower or amount_inr >= 2500:
            duration = 180
        elif "90" in pl_lower or "mastery" in pl_lower or "3-month" in pl_lower or "3 month" in pl_lower or "sprint" in pl_lower or "3m" in pl_lower or (amount_inr >= 1500 and amount_inr < 2500):
            duration = 90
        elif "day" in pl_lower or "24" in pl_lower:
            duration = 1
        else:
            duration = 30

        # Determine if user_id corresponds to an existing registered candidate
        registered_user = None
        if user_id and not str(user_id).startswith("guest") and not str(user_id).startswith("anon"):
            try:
                from core.auth_db import get_db
                with get_db() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT id, email, paid_until, plan FROM users WHERE id = ? OR LOWER(email) = ?", (user_id, str(user_id).lower()))
                    registered_user = cursor.fetchone()
            except Exception:
                pass

        if registered_user:
            reg_uid = registered_user["id"]
            if not effective_email and registered_user["email"]:
                effective_email = registered_user["email"].strip().lower()
            record_successful_payment(reg_uid, payment_id, order_id, amount_inr, plan_name or "Almond Jobs VIP Pass")
            if effective_email:
                try:
                    from core.auth_db import get_db, sync_supabase_vip_metadata
                    with get_db() as conn:
                        cursor = conn.cursor()
                        cursor.execute("SELECT paid_until, plan FROM users WHERE id = ?", (reg_uid,))
                        u_now = cursor.fetchone()
                        if u_now and u_now["paid_until"]:
                            cursor.execute(
                                """
                                INSERT OR REPLACE INTO vip_grants (email, granted_by, granted_at, valid_until, status, notes)
                                VALUES (?, 'razorpay_checkout', ?, ?, 'active', ?)
                                """,
                                (effective_email, time.time(), u_now["paid_until"], f"Paid via order {order_id} ({plan_name})")
                            )
                            conn.commit()
                            sync_supabase_vip_metadata(effective_email, True, u_now["plan"], u_now["paid_until"], reg_uid)
                except Exception as e:
                    print(f"[PAYMENT] Error syncing registered candidate VIP grant: {e}")
        else:
            # Guest or unauthenticated candidate checkout
            target = effective_email or user_id or "guest"
            record_successful_payment(target, payment_id, order_id, amount_inr, plan_name or "Almond Jobs VIP Pass")
            if effective_email:
                try:
                    from core.auth_db import grant_vip_to_email
                    grant_vip_to_email(effective_email, duration_days=duration, granted_by="razorpay_checkout", notes=f"Paid via order {order_id} ({plan_name})")
                except Exception as e:
                    print(f"[PAYMENT] Error binding VIP to guest email: {e}")

        prof = get_user_profile(user_id) or {}
        return {
            "status": "success",
            "purchase_type": "vip_pass",
            "is_paid": True,
            "plan_tier": prof.get("plan_tier", "1m"),
            "remaining_str": prof.get("remaining_str", ""),
            "paid_until_formatted": prof.get("paid_until_formatted", ""),
            "message": "VIP Pass verified and activated! Latest feed (0-6 days) is now unlocked."
        }

    # Live / Configured Mode: strictly verify HMAC-SHA256 signature with KEY_SECRET
    if razorpay_client or Config.is_razorpay_configured():
        try:
            expected_sig = _compute_expected_signature(order_id, payment_id, Config.RAZORPAY_KEY_SECRET)
            if not hmac.compare_digest(expected_sig, signature):
                return {
                    "status": "error",
                    "http_status": 400,
                    "message": "Invalid payment signature verification failed."
                }
            if razorpay_client:
                razorpay_client.utility.verify_payment_signature({
                    "razorpay_order_id": order_id,
                    "razorpay_payment_id": payment_id,
                    "razorpay_signature": signature
                })
            return _finalize_payment()
        except razorpay.errors.SignatureVerificationError:
            return {
                "status": "error",
                "http_status": 400,
                "message": "Invalid payment signature verification failed."
            }
        except Exception as e:
            return {
                "status": "error",
                "http_status": 400,
                "message": f"Verification error: {str(e)}"
            }

    # Unconfigured Sandbox Mode only
    if order_id.startswith("order_sandbox_"):
        return _finalize_payment()

    return {
        "status": "error",
        "http_status": 400,
        "message": "Payment verification could not be processed."
    }
