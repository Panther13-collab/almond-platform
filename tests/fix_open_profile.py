p = r"d:\Projects\AntigtavityApps\JobHunt\SK\platform\static\app.js"
with open(p, "r", encoding="utf-8") as f:
    text = f.read()

target = 'const authFormView = document.getElementById("authFormView");'
replacement = """const welcomeView = document.getElementById("authWelcomeView");
    if (welcomeView) welcomeView.classList.add("hidden");
    const authFormView = document.getElementById("authFormView");"""

if target in text:
    text = text.replace(target, replacement, 1)
    with open(p, "w", encoding="utf-8") as f:
        f.write(text)
    print("Added welcomeView reset to openProfileModal!")
else:
    print("Target not found in app.js")
