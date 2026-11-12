import hmac
import hashlib
import time
import razorpay
from core.config import Config
from core.auth_db import record_successful_payment

MIN_ORDER_AMOUNT_PAISE = 100
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


def create_razorpay_order(
    user_id: str = "",
    amount_inr: int = 699,
    amount_paise: int = None,
    currency: str = "INR",
    receipt: str = None,
    plan_name: str = ""
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
    receipt_id = (receipt or "").strip() or f"rcpt_{int(time.time())}_{user_id[:6] if user_id else 'anon'}"

    if razorpay_client:
        try:
            order_data = {
                "amount": resolved_paise,
                "currency": resolved_currency,
                "receipt": receipt_id,
                "notes": {
                    "user_id": user_id or "guest",
                    "plan_name": plan_name or "Almond_Pro",
                    "service": "Almond_AI_Pro_Verified_ATS_Access"
                }
            }
            order = razorpay_client.order.create(data=order_data)
            return {
                "status": "success",
                "order_id": order["id"],
                "amount": order.get("amount", resolved_paise),
                "currency": order.get("currency", resolved_currency),
                "receipt": order.get("receipt", receipt_id),
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
    amount_inr: int = 699,
    plan_name: str = ""
):
    """
    Verify payment signature returned by Razorpay Checkout modal via HMAC-SHA256.
    """
    if not order_id or not payment_id or not signature:
        return {
            "status": "error",
            "http_status": 400,
            "message": "Missing payment verification fields."
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
            record_successful_payment(user_id, payment_id, order_id, amount_inr, plan_name)
            return {"status": "success", "message": "Payment verified and account upgraded."}
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
        record_successful_payment(user_id, payment_id, order_id, amount_inr, plan_name)
        return {"status": "success", "message": "Sandbox payment approved and account upgraded."}

    return {
        "status": "error",
        "http_status": 400,
        "message": "Payment verification could not be processed."
    }
