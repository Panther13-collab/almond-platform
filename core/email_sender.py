import os
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from core.config import Config

def build_otp_html(otp_code: str, to_email: str) -> str:
    """Render a clean, high-contrast transactional HTML email for Almond Jobs verification."""
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Almond Jobs Verification Code</title>
</head>
<body style="margin: 0; padding: 0; background-color: #f8fafc; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #0f172a;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color: #f8fafc; padding: 40px 15px;">
        <tr>
            <td align="center">
                <table role="presentation" width="100%" max-width="520" style="max-width: 520px; background-color: #ffffff; border-radius: 20px; border: 1px solid #e2e8f0; box-shadow: 0 4px 12px rgba(15, 23, 42, 0.05); overflow: hidden;">
                    <!-- Brand Banner -->
                    <tr>
                        <td style="padding: 32px 36px 20px; text-align: left; border-bottom: 1px solid #f1f5f9;">
                            <div style="font-size: 22px; font-weight: 900; color: #020617; letter-spacing: -0.5px;">
                                Almond Job<span style="color: #9333ea;">s</span>
                            </div>
                            <div style="font-size: 11px; font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: 0.8px; margin-top: 4px;">
                                Candidate-First Career Intelligence &bull; Direct Corporate Feeds
                            </div>
                        </td>
                    </tr>

                    <!-- Body Content -->
                    <tr>
                        <td style="padding: 32px 36px;">
                            <h1 style="font-size: 18px; font-weight: 900; color: #0f172a; margin: 0 0 10px 0;">
                                Candidate Verification Code
                            </h1>
                            <p style="font-size: 13.5px; line-height: 1.5; color: #475569; margin: 0 0 24px 0;">
                                You recently entered <strong>{to_email}</strong> to create or verify your candidate account on Almond Jobs. Use the 6-digit code below to complete your verification:
                            </p>

                            <!-- Big OTP Code Box -->
                            <div style="background-color: #faf5ff; border: 2px dashed #c084fc; border-radius: 14px; padding: 18px; text-align: center; margin: 0 0 24px 0;">
                                <div style="font-size: 11px; font-weight: 800; text-transform: uppercase; letter-spacing: 1.2px; color: #7e22ce; margin-bottom: 6px;">
                                    One-Time Passcode (OTP)
                                </div>
                                <div style="font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; font-size: 32px; font-weight: 900; letter-spacing: 8px; color: #581c87;">
                                    {otp_code}
                                </div>
                                <div style="font-size: 11px; font-weight: 600; color: #9333ea; margin-top: 6px;">
                                    Valid for 10 minutes
                                </div>
                            </div>

                            <p style="font-size: 12px; line-height: 1.4; color: #64748b; margin: 0 0 16px 0;">
                                <strong>Security Notice:</strong> Never share this code with anyone. Almond Jobs technical staff will never ask for your verification code. If you did not initiate this request, you can safely ignore this email.
                            </p>
                        </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                        <td style="padding: 20px 36px; background-color: #f8fafc; border-top: 1px solid #f1f5f9; text-align: center;">
                            <p style="font-size: 11px; color: #94a3b8; margin: 0; line-height: 1.4;">
                                &copy; 2026 Almond Jobs Platform &bull; Zero Recruiter Markup &bull; Direct Enterprise Access<br>
                                Automated Security System &bull; Please do not reply to this email
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>"""

def send_otp_email(to_email: str, otp_code: str) -> dict:
    """
    Dispatch a transactional OTP verification email.
    If SMTP credentials are provided in Config, dispatches via SMTP.
    If unconfigured, safely logs the code and returns simulation status.
    """
    clean_email = to_email.strip().lower()

    if not Config.is_smtp_configured():
        print(f"[EMAIL_SENDER] Notice: SMTP not configured in .env. Verification OTP for {clean_email}: {otp_code}")
        return {
            "delivered": False,
            "simulated": True,
            "reason": "SMTP credentials (SMTP_HOST, SMTP_USER, SMTP_PASS) not configured in environment.",
            "otp_code": otp_code
        }

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"Your Almond Jobs Verification Code: {otp_code}"
        msg["From"] = Config.SMTP_FROM or Config.SMTP_USER
        msg["To"] = clean_email

        # Plain text alternative
        plain_text = f"Your Almond Jobs verification code is: {otp_code}\n\nValid for 10 minutes.\nDo not share this code with anyone."
        msg.attach(MIMEText(plain_text, "plain", "utf-8"))

        # HTML alternative
        html_content = build_otp_html(otp_code, clean_email)
        msg.attach(MIMEText(html_content, "html", "utf-8"))

        # Connect and send
        context = ssl.create_default_context()
        if Config.SMTP_PORT == 465:
            # SSL
            with smtplib.SMTP_SSL(Config.SMTP_HOST, Config.SMTP_PORT, context=context, timeout=12) as server:
                server.login(Config.SMTP_USER, Config.SMTP_PASS)
                server.send_message(msg)
        else:
            # STARTTLS (Port 587 or default)
            with smtplib.SMTP(Config.SMTP_HOST, Config.SMTP_PORT, timeout=12) as server:
                server.ehlo()
                server.starttls(context=context)
                server.ehlo()
                server.login(Config.SMTP_USER, Config.SMTP_PASS)
                server.send_message(msg)

        print(f"[EMAIL_SENDER] Successfully delivered OTP verification email to {clean_email}")
        return {
            "delivered": True,
            "simulated": False,
            "email": clean_email
        }
    except Exception as e:
        print(f"[EMAIL_SENDER] Error delivering email via SMTP: {e}")
        return {
            "delivered": False,
            "simulated": False,
            "error": str(e),
            "otp_code": otp_code
        }
