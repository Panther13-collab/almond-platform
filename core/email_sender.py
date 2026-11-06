import os
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from core.config import Config

def build_otp_html(otp_code: str, to_email: str) -> str:
    """
    Render an ultra-professional, high-contrast, responsive HTML email
    for Almond Jobs candidate authentication.
    Styled according to luxury Almond design standards (dark slate, warm gold, deep violet).
    """
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Almond Jobs Verification Code</title>
</head>
<body style="margin: 0; padding: 0; background-color: #f8fafc; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #0f172a; -webkit-font-smoothing: antialiased;">
    <!-- Hidden preheader text for inbox preview snippet -->
    <div style="display: none; font-size: 1px; color: #f8fafc; line-height: 1px; max-height: 0px; max-width: 0px; opacity: 0; overflow: hidden;">
        Your Almond Jobs candidate verification passcode is {otp_code}. Valid for 10 minutes.
    </div>

    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color: #f8fafc; padding: 40px 16px;">
        <tr>
            <td align="center">
                <!-- Main Container Card -->
                <table role="presentation" width="100%" style="max-width: 540px; background-color: #ffffff; border-radius: 20px; border: 1px solid #e2e8f0; box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.06); overflow: hidden; text-align: left;">
                    
                    <!-- Top Brand Header -->
                    <tr>
                        <td style="padding: 28px 36px; border-bottom: 1px solid #f1f5f9; background: linear-gradient(180deg, #ffffff 0%, #fafafa 100%);">
                            <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
                                <tr>
                                    <td style="vertical-align: middle;">
                                        <div style="display: inline-block; vertical-align: middle; margin-right: 10px;">
                                            <img src="cid:almond_logo" alt="Almond Logo" width="34" height="34" style="display: block; width: 34px; height: 34px; border-radius: 8px;">
                                        </div>
                                        <div style="display: inline-block; vertical-align: middle;">
                                            <span style="font-size: 21px; font-weight: 900; color: #020617; letter-spacing: -0.5px;">Almond Job<span style="color: #7c3aed;">s</span></span>
                                        </div>
                                    </td>
                                    <td align="right" style="vertical-align: middle;">
                                        <span style="display: inline-block; background-color: #f0fdf4; border: 1px solid #bbf7d0; color: #15803d; font-size: 11px; font-weight: 700; padding: 4px 10px; border-radius: 9999px; letter-spacing: 0.3px;">
                                            &bull; Verified Dispatch
                                        </span>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- Card Body -->
                    <tr>
                        <td style="padding: 36px 36px 28px;">
                            <h1 style="font-size: 20px; font-weight: 800; color: #0f172a; margin: 0 0 12px 0; letter-spacing: -0.3px;">
                                Candidate Access Passcode
                            </h1>
                            <p style="font-size: 14px; line-height: 1.6; color: #475569; margin: 0 0 26px 0;">
                                You recently initiated account verification for <strong style="color: #0f172a;">{to_email}</strong> on Almond Jobs. Use the single-use passcode below to confirm your candidate credentials:
                            </p>

                            <!-- High-Contrast OTP Card -->
                            <div style="background: linear-gradient(135deg, #faf5ff 0%, #f5f3ff 100%); border: 2px dashed #c084fc; border-radius: 16px; padding: 24px; text-align: center; margin: 0 0 28px 0;">
                                <div style="font-size: 11px; font-weight: 800; text-transform: uppercase; letter-spacing: 1.5px; color: #6b21a8; margin-bottom: 10px;">
                                    One-Time Passcode (OTP)
                                </div>
                                <div style="font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; font-size: 38px; font-weight: 900; letter-spacing: 12px; color: #4c1d95; padding-left: 12px; margin: 6px 0;">
                                    {otp_code}
                                </div>
                                <div style="display: inline-block; background-color: #ede9fe; color: #6d28d9; font-size: 11.5px; font-weight: 700; padding: 4px 12px; border-radius: 20px; margin-top: 8px;">
                                    ⏱ Valid for 10 minutes &bull; Single Use Only
                                </div>
                            </div>

                            <!-- Platform Value Props -->
                            <div style="background-color: #f8fafc; border-radius: 12px; border: 1px solid #f1f5f9; padding: 16px 18px; margin: 0 0 24px 0;">
                                <div style="font-size: 11px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.8px; color: #64748b; margin-bottom: 8px;">
                                    Direct Corporate Intelligence Guarantee
                                </div>
                                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="font-size: 12.5px; color: #334155; line-height: 1.5;">
                                    <tr>
                                        <td style="padding: 2px 0;">&#10003; <strong>0% Recruiter Spread</strong> &mdash; 100% direct corporate ATS portal URLs</td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 2px 0;">&#10003; <strong>Vector Skill Gap Match</strong> &mdash; Instant keyword alignment before you apply</td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 2px 0;">&#10003; <strong>P75 Compensation Feeds</strong> &mdash; Verified candidate package intelligence</td>
                                    </tr>
                                </table>
                            </div>

                            <!-- Security Notice -->
                            <div style="border-left: 3px solid #f59e0b; background-color: #fffbeb; padding: 12px 14px; border-radius: 0 8px 8px 0; margin-bottom: 6px;">
                                <p style="font-size: 12px; line-height: 1.5; color: #92400e; margin: 0;">
                                    <strong>Security Notice:</strong> Almond Jobs staff will never ask for your verification code. Never share this code with anyone. If you did not initiate this request, you can safely disregard this email.
                                </p>
                            </div>
                        </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                        <td style="padding: 24px 36px; background-color: #f8fafc; border-top: 1px solid #f1f5f9; text-align: center;">
                            <div style="font-size: 12px; font-weight: 700; color: #334155; margin-bottom: 4px;">
                                Almond Jobs Platform &bull; Move First. Apply Unseen.
                            </div>
                            <div style="font-size: 11px; color: #64748b; margin-bottom: 12px;">
                                Direct Enterprise Application Portals &bull; <a href="https://almondsjob.com" style="color: #7c3aed; text-decoration: none; font-weight: 600;">almondsjob.com</a>
                            </div>
                            <div style="font-size: 11px; color: #64748b; background-color: #f1f5f9; border-radius: 10px; padding: 10px 14px; margin-bottom: 14px; text-align: left; line-height: 1.5;">
                                &#128161; <strong>Inbox Deliverability Tip:</strong> If this code arrived in your Spam / Junk folder, please click <em>"Report Not Spam"</em> and add <strong style="color: #0f172a;">almondjobs.official@gmail.com</strong> to your contacts to guarantee all future direct corporate feeds arrive straight into your primary inbox.
                            </div>
                            <div style="font-size: 10.5px; color: #94a3b8; line-height: 1.4;">
                                &copy; 2026 Almond Jobs. All rights reserved.<br>
                                Automated Security System &bull; Please do not reply directly to this transmission.
                            </div>
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
    If SMTP credentials are provided in Config, dispatches via SMTP with inline branded logo.
    If unconfigured, safely logs the code and returns simulation status.
    """
    clean_email = to_email.strip().lower()

    if not Config.is_smtp_configured():
        print(f"[EMAIL_SENDER] Warning: Outbound SMTP credentials not configured in host environment.")
        return {
            "delivered": False,
            "simulated": False,
            "error": "SMTP credentials (SMTP_HOST, SMTP_USER, SMTP_PASS) not configured in host environment."
        }

    try:
        # Multipart related allows inline CID images
        msg_root = MIMEMultipart("related")
        msg_root["Subject"] = f"Your Almond Jobs Verification Code: {otp_code}"
        msg_root["From"] = Config.SMTP_FROM or f"Almond Jobs <{Config.SMTP_USER}>"
        msg_root["To"] = clean_email
        msg_root["Reply-To"] = Config.SMTP_USER
        msg_root["Auto-Submitted"] = "auto-generated"
        msg_root["X-Auto-Response-Suppress"] = "All"
        msg_root["Importance"] = "high"
        msg_root["Priority"] = "urgent"

        # Multipart alternative container for plain text and HTML
        msg_alt = MIMEMultipart("alternative")
        msg_root.attach(msg_alt)

        # Plain text fallback
        plain_text = (
            f"Almond Jobs Verification Code: {otp_code}\n\n"
            f"You recently entered {clean_email} to access Almond Jobs.\n"
            f"Your one-time passcode is: {otp_code}\n\n"
            f"This code expires in 10 minutes.\n"
            f"Never share this code with anyone. Almond Jobs technical staff will never ask for your code."
        )
        msg_alt.attach(MIMEText(plain_text, "plain", "utf-8"))

        # HTML formatted template
        html_content = build_otp_html(otp_code, clean_email)
        msg_alt.attach(MIMEText(html_content, "html", "utf-8"))

        # Attach inline brand logo if present
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        logo_path = os.path.join(base_dir, "static", "logo.png")
        if os.path.exists(logo_path):
            with open(logo_path, "rb") as img_file:
                logo_img = MIMEImage(img_file.read())
                logo_img.add_header("Content-ID", "<almond_logo>")
                logo_img.add_header("Content-Disposition", "inline", filename="logo.png")
                msg_root.attach(logo_img)

        # Connect and send via SSL or STARTTLS
        context = ssl.create_default_context()
        if Config.SMTP_PORT == 465:
            with smtplib.SMTP_SSL(Config.SMTP_HOST, Config.SMTP_PORT, context=context, timeout=15) as server:
                server.login(Config.SMTP_USER, Config.SMTP_PASS)
                server.send_message(msg_root)
        else:
            with smtplib.SMTP(Config.SMTP_HOST, Config.SMTP_PORT, timeout=15) as server:
                server.ehlo()
                server.starttls(context=context)
                server.ehlo()
                server.login(Config.SMTP_USER, Config.SMTP_PASS)
                server.send_message(msg_root)

        print(f"[EMAIL_SENDER] Successfully delivered branded OTP email to {clean_email}")
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
            "error": str(e)
        }
