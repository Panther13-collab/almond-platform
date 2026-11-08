import os

LEGAL_RENDERER_PATH = os.path.join(os.path.dirname(__file__), "legal_renderer.py")
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.py")

OFFICIAL_EMAIL = "almondjobs.official@gmail.com"

def update_legal_renderer():
    with open(LEGAL_RENDERER_PATH, "r", encoding="utf-8") as f:
        c = f.read()

    dummy_emails = [
        "privacy@almondjobs.com",
        "support@almondjobs.com",
        "contact@almondjobs.com",
        "grievance@almondjobs.com"
    ]

    for de in dummy_emails:
        c = c.replace(de, OFFICIAL_EMAIL)

    with open(LEGAL_RENDERER_PATH, "w", encoding="utf-8") as f:
        f.write(c)
    print("Updated all emails in legal_renderer.py to:", OFFICIAL_EMAIL)

def update_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        c = f.read()

    c = c.replace("noreply@almondjobs.com", OFFICIAL_EMAIL)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        f.write(c)
    print("Updated config.py default email to:", OFFICIAL_EMAIL)

if __name__ == "__main__":
    update_legal_renderer()
    update_config()
