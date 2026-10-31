import hmac
import hashlib
import time
import razorpay
from core.config import Config
from core.auth_db import record_successful_payment

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

def create_razorpay_order(user_id: str, amount_inr: int = 699):
    """
    Create a Razorpay order in paise (₹699 = 69900 paise).
    If Razorpay keys are not yet configured, returns a simulated sandbox order.
    """
    receipt_id = f"rcpt_{int(time.time())}_{user_id[:6] if user_id else 'anon'}"
    amount_paise = amount_inr * 100

    if razorpay_client:
        try:
            order_data = {
                "amount": amount_paise,
                "currency": "INR",
                "receipt": receipt_id,
                "notes": {
                    "user_id": user_id,
                    "service": "Almond_AI_Pro_Verified_ATS_Access"
                }
            }
            order = razorpay_client.order.create(data=order_data)
            return {
                "status": "success",
                "order_id": order["id"],
                "amount": amount_paise,
                "currency": "INR",
                "key_id": Config.RAZORPAY_KEY_ID,
                "is_sandbox": False
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    # Local Sandbox Order (simulated for immediate testing before keys are added)
    fake_order_id = f"order_sandbox_{int(time.time())}"
    return {
        "status": "success",
        "order_id": fake_order_id,
        "amount": amount_paise,
        "currency": "INR",
        "key_id": Config.RAZORPAY_KEY_ID,
        "is_sandbox": True
    }

def verify_razorpay_signature(user_id: str, order_id: str, payment_id: str, signature: str, amount_inr: int = 699):
    """
    Verify payment signature returned by Razorpay Checkout modal via HMAC SHA256.
    """
    if razorpay_client and not order_id.startswith("order_sandbox_"):
        try:
            # Razorpay official verification
            razorpay_client.utility.verify_payment_signature({
                'razorpay_order_id': order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature
            })
            # Signature verified! Upgrade user in database
            record_successful_payment(user_id, payment_id, order_id, amount_inr)
            return {"status": "success", "message": "Payment verified and account upgraded."}
        except razorpay.errors.SignatureVerificationError:
            return {"status": "error", "message": "Invalid payment signature verification failed."}
        except Exception as e:
            return {"status": "error", "message": f"Verification error: {str(e)}"}

    # Sandbox / Local Testing verification
    if order_id.startswith("order_sandbox_"):
        record_successful_payment(user_id, payment_id, order_id, amount_inr)
        return {"status": "success", "message": "Sandbox payment approved and account upgraded."}

    return {"status": "error", "message": "Payment verification could not be processed."}
