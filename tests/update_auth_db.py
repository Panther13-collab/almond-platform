p = r"d:\Projects\AntigtavityApps\JobHunt\SK\platform\core\auth_db.py"
with open(p, "r", encoding="utf-8") as f:
    text = f.read()

target = 'if not email_delivery.get("delivered") or Config.ENV == "development":'
replacement = '# Only attach dev_otp fallback if email could not be delivered via SMTP\n    if not email_delivery.get("delivered"):'

# Also clean up the comment above if present
if '# If in local dev or SMTP unconfigured, attach dev_otp for seamless testing' in text:
    text = text.replace('# If in local dev or SMTP unconfigured, attach dev_otp for seamless testing\n    if not email_delivery.get("delivered") or Config.ENV == "development":', replacement)
    text = text.replace('# If in local dev or SMTP unconfigured, attach dev_otp for seamless testing\r\n    if not email_delivery.get("delivered") or Config.ENV == "development":', replacement.replace('\n', '\r\n'))
elif target in text:
    text = text.replace(target, 'if not email_delivery.get("delivered"):')

with open(p, "w", encoding="utf-8") as f:
    f.write(text)

print("Updated auth_db.py successfully!")
