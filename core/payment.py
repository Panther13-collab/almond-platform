from datetime import datetime, timezone
import hmac
import hashlib
import re
import time
import razorpay
from core.config import Config
from core.auth_db import record_contribution_payment, record_successful_payment

MIN_ORDER_AMOUNT_PAISE = 100
VIP_LATEST_FEED_MAX_DAYS = 6
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


def apply_vip_latest_feed_lock(jobs: list, user_is_paid: bool = False, max_days: int = VIP_LATEST_FEED_MAX_DAYS) -> list:
    """
    Blur and lock latest postings (age <= max_days, i.e. Today through 6 days ago)
    unless the user has an active VIP Pass. Keeps days-ago freshness visible.
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

        if not user_is_paid and age_days is not None and age_days <= max_days:
            job["is_locked"] = True
            job["url"] = "#unlock-vip"
            if "apply_url" in job:
                job["apply_url"] = "#unlock-vip"
            if "hn_url" in job:
                job["hn_url"] = "#unlock-vip"
            if "founder_email" in job:
                job["founder_email"] = ""
            job["title"] = "Confidential Role (VIP Pass)"
            if "role" in job:
                job["role"] = "Confidential Role (VIP Pass)"
            # KEEP COMPANY NAME VISIBLE to tempt candidates with employer identity
            if "summary" in job:
                job["summary"] = "Unlock VIP Pass to view full designation details and direct application portal link."
            if "full_text" in job:
                job["full_text"] = ""
            if "matched_skills" in job:
                job["matched_skills"] = []
            if "gap_skills" in job:
                job["gap_skills"] = []
        else:
            job["is_locked"] = False
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
            return {
                "status": "error",
                "http_status": 401 if _is_auth_failure(e) else 500,
                "message": str(e)
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
    supporter_message: str = ""
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

    def _finalize_payment():
        if resolved_type == "contribution":
            record_contribution_payment(
                user_id,
                payment_id,
                order_id,
                amount_inr,
                plan_name or "Coffee Contribution",
                supporter_name=supporter_name,
                supporter_message=supporter_message
            )
            return {
                "status": "success",
                "purchase_type": "contribution",
                "is_paid": False,
                "supporter_name": supporter_name,
                "supporter_message": supporter_message,
                "amount_inr": amount_inr,
                "message": "Thank you for your generous coffee contribution!"
            }
        record_successful_payment(user_id, payment_id, order_id, amount_inr, plan_name or "Almond Jobs VIP Pass")
        return {
            "status": "success",
            "purchase_type": "vip_pass",
            "is_paid": True,
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
