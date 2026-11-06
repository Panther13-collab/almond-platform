import os
from dotenv import load_dotenv

# Load .env file from project root (explicit path relative to config.py)
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
load_dotenv(dotenv_path=env_path, override=True)

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

    # Outbound Transactional Email (SMTP - Gmail, Resend, Brevo, SendGrid, Amazon SES)
    SMTP_HOST = os.getenv("SMTP_HOST", "").strip()
    SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
    SMTP_USER = os.getenv("SMTP_USER", "").strip()
    SMTP_PASS = os.getenv("SMTP_PASS", "").strip()
    SMTP_FROM = os.getenv("SMTP_FROM", "").strip() or f"Almond Jobs <{os.getenv('SMTP_USER', 'noreply@almondjobs.com')}>"

    # Telemetry & Admin Key
    ADMIN_SECRET_KEY = os.getenv("ALMOND_ADMIN_KEY", "almond2026").strip()
    GA_MEASUREMENT_ID = os.getenv("GA_MEASUREMENT_ID", "").strip()

    @classmethod
    def is_supabase_configured(cls) -> bool:
        return bool(cls.SUPABASE_URL and cls.SUPABASE_ANON_KEY)

    @classmethod
    def is_razorpay_configured(cls) -> bool:
        return bool(cls.RAZORPAY_KEY_ID and not cls.RAZORPAY_KEY_ID.startswith("rzp_test_placeholder"))

    @classmethod
    def is_smtp_configured(cls) -> bool:
        return bool(cls.SMTP_HOST and cls.SMTP_USER and cls.SMTP_PASS)
