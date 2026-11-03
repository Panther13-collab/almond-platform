import smtplib
import ssl
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

smtp_host = 'smtp.gmail.com'
smtp_port = 587
smtp_user = 'almondjobs.official@gmail.com'
smtp_pass = 'eqesczkngkboudee'
logo_path = os.path.join(os.path.dirname(__file__), '..', 'static', 'logo.png')

msg_root = MIMEMultipart('related')
msg_root['Subject'] = 'Your Almond Jobs Verification Passcode: 849201'
msg_root['From'] = f'Almond Jobs <{smtp_user}>'
msg_root['To'] = smtp_user

msg_alt = MIMEMultipart('alternative')
msg_root.attach(msg_alt)

plain = 'Your Almond Jobs verification code is: 849201. Valid for 10 minutes.'
msg_alt.attach(MIMEText(plain, 'plain', 'utf-8'))

html = """<!DOCTYPE html>
<html>
<body style="margin:0;padding:20px;background:#f8fafc;font-family:sans-serif;">
  <div style="max-width:500px;margin:auto;background:#fff;padding:24px;border-radius:16px;">
    <div style="display:flex;align-items:center;margin-bottom:16px;">
      <img src="cid:almond_logo" width="32" height="32" style="margin-right:10px;vertical-align:middle;">
      <span style="font-size:20px;font-weight:900;color:#0f172a;">Almond Job<span style="color:#7c3aed;">s</span></span>
    </div>
    <div style="background:#f5f3ff;border:2px dashed #c084fc;padding:16px;text-align:center;border-radius:12px;margin:20px 0;">
      <div style="font-size:32px;font-weight:900;letter-spacing:8px;color:#581c87;">849201</div>
    </div>
  </div>
</body>
</html>"""

msg_alt.attach(MIMEText(html, 'html', 'utf-8'))

if os.path.exists(logo_path):
    with open(logo_path, 'rb') as f:
        img = MIMEImage(f.read())
        img.add_header('Content-ID', '<almond_logo>')
        img.add_header('Content-Disposition', 'inline', filename='logo.png')
        msg_root.attach(img)
    print(f"Attached logo from {logo_path}")

context = ssl.create_default_context()
with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as s:
    s.ehlo()
    s.starttls(context=context)
    s.ehlo()
    s.login(smtp_user, smtp_pass)
    s.send_message(msg_root)
    print('Inline CID Image Test Sent successfully!')
