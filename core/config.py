import os
from dotenv import load_dotenv

# Load .env file from project root
load_dotenv()

class Config:
    # Environment
    ENV = os.getenv("ENVIRONMENT", "development")
    PORT = int(os.getenv("PORT", 8000))

    # Pricing
    PRICE_INR = int(os.getenv("ALMOND_PRICE_INR", 699))
    PRICE_USD = int(os.getenv("ALMOND_PRICE_USD", 19))

    # Supabase (Auth & Postgres Database)
    SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
    SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "").strip()
    SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()

    # Razorpay (India Payments - UPI, RuPay, NetBanking)
    RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "rzp_test_placeholder").strip()
    RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "test_secret_placeholder").strip()

    @classmethod
    def is_supabase_configured(cls) -> bool:
        return bool(cls.SUPABASE_URL and cls.SUPABASE_ANON_KEY)

    @classmethod
    def is_razorpay_configured(cls) -> bool:
        return bool(cls.RAZORPAY_KEY_ID and not cls.RAZORPAY_KEY_ID.startswith("rzp_test_placeholder"))
